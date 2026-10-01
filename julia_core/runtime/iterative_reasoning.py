"""Turn-scoped iterative cognition loop owned by JuliaSession."""

from __future__ import annotations

import json
import re
import uuid
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from julia_core.capability.models import ToolResultStatus
from julia_core.capability.providers.local.security import DEFAULT_ALLOWED_ROOTS
from julia_core.runtime.turn_ledger import (
    LIMITED_REPLY,
    TurnLedger,
    check_completion_claims,
    check_denied_execution,
    check_requested_claims,
    check_requested_not_executed,
    environment_facts,
    FORMAL_MEMORY_LOCATIONS,
    resolve_hmac_key,
)


MAX_COGNITION_PASSES_PER_TURN = 7
MAX_CAPABILITY_EXECUTIONS_PER_TURN = 6
MAX_STRUCTURED_TOOL_CALLS_PER_MODEL_RESPONSE = 1
MAX_CLAIM_CORRECTION_PASSES_PER_TURN = 1


_LEGACY_TOOL_NAMES = {
    "read_file": "file.read",
    "search_files": "file.search",
    "list_directory": "file.list",
}
_EXACT_TOOL_CALL = re.compile(
    r"^```tool_call[ \t]*\n(.*)\n```$",
    re.DOTALL,
)
# One ```tool_call block on its own lines inside surrounding prose. Used only
# when the reply has exactly one tool_call marker and no other fence, so the
# call intent is unambiguous; every other shape still fails closed.
_EMBEDDED_TOOL_CALL = re.compile(
    r"^```tool_call[ \t]*\r?\n(.*?)\r?\n```[ \t]*$",
    re.DOTALL | re.MULTILINE,
)
# A malformed tool-call carrier: an ordinary fenced block (no info string)
# whose first non-blank line is the literal token `tool_call`. Models emit this
# family when they mean to make a structured call but do not produce the exact
# whole-response ```tool_call form. Treating it as final prose leaks the
# internal carrier to the user and silently skips the capability, so it must be
# classified as a control failure instead.
#
# Detection is structural only: the body is never parsed and the intended
# capability is never inferred. A fenced block with an info string, or whose
# first line is not `tool_call`, is not matched.
_MALFORMED_TOOL_CARRIER = re.compile(
    r"^[ \t]*```[ \t]*\r?\n(?:[ \t]*\r?\n)*[ \t]*tool_call[ \t]*\r?$",
    re.MULTILINE,
)


@dataclass(frozen=True, slots=True)
class StrictToolCall:
    name: str
    arguments: dict[str, Any]
    raw_json: str

    @property
    def capability_id(self) -> str:
        return _LEGACY_TOOL_NAMES.get(self.name, self.name)

    @property
    def fingerprint(self) -> tuple[str, str]:
        canonical_arguments = json.dumps(
            self.arguments,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        return self.capability_id, canonical_arguments


@dataclass(frozen=True, slots=True)
class StrictModelResponse:
    kind: str
    text: str
    tool_call: StrictToolCall | None = None
    failure_reason: str | None = None
    surrounding_prose: bool = False


def parse_strict_model_response(response: str) -> StrictModelResponse:
    trimmed = str(response).strip()
    marker_count = trimmed.count("```tool_call")
    if marker_count == 0:
        if _MALFORMED_TOOL_CARRIER.search(trimmed):
            # Structurally recognizable call intent in a malformed carrier must
            # fail closed, not become the final user-facing answer. The existing
            # decode-failure projection then asks for the exact shape again.
            return StrictModelResponse(
                "TOOL_CALL_CONTROL_FAILURE",
                trimmed,
                failure_reason="INVALID_CALL_SHAPE",
            )
        return StrictModelResponse("FINAL_TEXT", trimmed)

    match = _EXACT_TOOL_CALL.fullmatch(trimmed)
    if match is not None:
        return _decode_tool_call_block(trimmed, match.group(1), surrounding_prose=False)

    # Prose around exactly one tool_call block is unambiguous: execute the
    # block, never the prose. Anything else (several markers, other fences,
    # a block not on its own lines) stays a control failure.
    embedded = _EMBEDDED_TOOL_CALL.search(trimmed)
    if marker_count == 1 and trimmed.count("```") == 2 and embedded is not None:
        parsed = _decode_tool_call_block(trimmed, embedded.group(1), surrounding_prose=True)
        if parsed.kind == "EXACTLY_ONE_STRUCTURED_CALL":
            return parsed
    return StrictModelResponse(
        "TOOL_CALL_CONTROL_FAILURE",
        trimmed,
        failure_reason="INVALID_CALL_SHAPE",
    )


def _decode_tool_call_block(
    trimmed: str, block: str, *, surrounding_prose: bool
) -> StrictModelResponse:
    raw_json = block.strip()
    try:
        payload = json.loads(raw_json)
    except json.JSONDecodeError:
        return StrictModelResponse(
            "TOOL_CALL_CONTROL_FAILURE",
            trimmed,
            failure_reason="MALFORMED_JSON",
        )
    if not isinstance(payload, dict):
        return StrictModelResponse(
            "TOOL_CALL_CONTROL_FAILURE",
            trimmed,
            failure_reason="INVALID_CALL_SHAPE",
        )
    name = payload.get("name")
    arguments = payload.get("arguments")
    if not isinstance(name, str) or not name.strip():
        return StrictModelResponse(
            "TOOL_CALL_CONTROL_FAILURE",
            trimmed,
            failure_reason="MISSING_NAME",
        )
    if not isinstance(arguments, dict):
        return StrictModelResponse(
            "TOOL_CALL_CONTROL_FAILURE",
            trimmed,
            failure_reason="INVALID_CALL_SHAPE",
        )
    return StrictModelResponse(
        "EXACTLY_ONE_STRUCTURED_CALL",
        trimmed,
        tool_call=StrictToolCall(name=name, arguments=arguments, raw_json=raw_json),
        surrounding_prose=surrounding_prose,
    )


@dataclass(slots=True)
class IterativeTurnResult:
    reply: str
    final_response_kind: str
    termination: str
    cognition_pass_count: int = 0
    capability_execution_count: int = 0
    executed_capability_ids: list[str] = field(default_factory=list)
    projection_generation_ids: list[str] = field(default_factory=list)
    evidence_generation_ids: list[str] = field(default_factory=list)
    cognition_pass_trace: list[dict[str, Any]] = field(default_factory=list)
    ledger_view: dict[str, Any] = field(default_factory=dict)


class IterativeReasoningLoop:
    """Execute one Julia-owned bounded turn; retain no state after return."""

    def __init__(
        self,
        session,
        text: str,
        turn_context,
        messages,
        parent_package,
        _capability_execution_limit: int | None = None,
    ):
        self.session = session
        self.text = text
        self.turn_context = turn_context
        self.messages = list(messages)
        self.parent_package = parent_package
        self.cognition_pass_count = 0
        self.capability_execution_count = 0
        self.capability_execution_limit = (
            MAX_CAPABILITY_EXECUTIONS_PER_TURN
            if _capability_execution_limit is None
            else _capability_execution_limit
        )
        self.seen_fingerprints: set[tuple[str, str]] = set()
        self.generation_ids: set[str] = set()
        self.executed_capability_ids: list[str] = []
        self.projection_generation_ids: list[str] = []
        self.evidence_generation_ids: list[str] = []
        self.cognition_pass_trace: list[dict[str, Any]] = []
        self.unresolved_unavailable = False
        self.claim_correction_count = 0
        hmac_key, hmac_status = resolve_hmac_key()
        self.ledger = TurnLedger(
            conversation_id=getattr(turn_context, "conversation_id", "") or "",
            turn_id=getattr(turn_context, "turn_id", "") or "",
            correlation_id=getattr(turn_context, "correlation_id", "") or "",
            hmac_key=hmac_key,
            hmac_status=hmac_status,
            allowed_roots=tuple(DEFAULT_ALLOWED_ROOTS),
        )
        self._environment_facts = environment_facts()
        self._correction_check_index: int | None = None

    def run(self) -> IterativeTurnResult:
        reply = ""
        final_response_kind = "NONE"
        termination = "completed"

        for pass_index in range(1, MAX_COGNITION_PASSES_PER_TURN + 1):
            self.cognition_pass_count = pass_index
            execution_budget = self._execution_budget(pass_index)
            # The execution block is regenerated from the ledger before every pass
            # so Julia always sees what this turn has (not) executed so far.
            self.parent_package.execution_frame = self.ledger.execution_frame(
                self._environment_facts
            )
            budget_package = self.session.context_os.project_execution_budget_overlay(
                self.parent_package,
                **execution_budget,
            )
            model_messages = budget_package.to_messages(
                budget_package.active_tail_messages, self.text
            )
            response = self.session.provider.chat(
                model_messages,
                cognitive_mode="private_voice_continuity",
            )
            parsed = parse_strict_model_response(response)
            self.ledger.record_pass(
                pass_index=pass_index,
                parsed_response_kind=parsed.kind,
                surrounding_prose=parsed.surrounding_prose,
                messages=model_messages,
                blocks=budget_package.block_metrics(),
            )
            pass_trace = {
                "pass_index": pass_index,
                **execution_budget,
                "parsed_response_kind": parsed.kind,
                "capability_execution_count": self.capability_execution_count,
                "termination": "",
            }
            if parsed.surrounding_prose:
                pass_trace["surrounding_prose"] = True
            self.cognition_pass_trace.append(pass_trace)

            if parsed.kind == "FINAL_TEXT":
                if execution_budget["finalization_required"] and not parsed.text:
                    final_response_kind = "CONTROL_FAILURE"
                    termination = "finalization_no_text"
                    reply = "Final cognition pass reserved for finalization; no final text was produced."
                    pass_trace["termination"] = termination
                    break
                denied = check_denied_execution(parsed.text, self.ledger)
                if denied:
                    # CARD 8: record only; never corrected, never blocked.
                    self.ledger.record_claim_check(
                        pass_index=pass_index,
                        categories=denied,
                        corrected=False,
                        outcome="recorded_only",
                    )
                categories = check_completion_claims(parsed.text, self.ledger)
                categories += check_requested_claims(parsed.text, self.ledger, self.text)
                if not categories:
                    unexecuted = check_requested_not_executed(parsed.text, self.ledger, self.text)
                    if unexecuted:
                        # CARD 8 (g): record only; never corrected, never blocked.
                        self.ledger.record_claim_check(
                            pass_index=pass_index,
                            categories=unexecuted,
                            corrected=False,
                            outcome="recorded_only",
                        )
                if categories:
                    if (
                        self.claim_correction_count < MAX_CLAIM_CORRECTION_PASSES_PER_TURN
                        and not execution_budget["finalization_required"]
                    ):
                        self.claim_correction_count += 1
                        self._correction_check_index = len(self.ledger.claim_checks)
                        self.ledger.record_claim_check(
                            pass_index=pass_index,
                            categories=categories,
                            corrected=True,
                            outcome="correction_requested",
                        )
                        self._project_claim_correction(categories, pass_index, response)
                        pass_trace["termination"] = "continued"
                        continue
                    outcome = (
                        "limited_reply_after_correction"
                        if self.claim_correction_count
                        else "limited_reply_no_pass_left"
                    )
                    self._finish_claim_check(pass_index, categories, outcome)
                    final_response_kind = "LIMITATION"
                    termination = "claim_check_limited"
                    reply = LIMITED_REPLY
                    pass_trace["termination"] = termination
                    break
                if self._correction_check_index is not None:
                    self.ledger.claim_checks[self._correction_check_index]["outcome"] = "compliant_after_correction"
                control_frame = getattr(self.parent_package, "control_frame", {})
                budget_limitation = (
                    isinstance(control_frame, dict)
                    and control_frame.get("kind") == "tool_call_budget_exceeded"
                )
                limitation = budget_limitation or self.unresolved_unavailable
                final_response_kind = "LIMITATION" if limitation else "JUDGMENT"
                termination = (
                    "completed_with_limitation"
                    if limitation
                    else "completed"
                )
                reply = parsed.text
                pass_trace["termination"] = termination
                break

            if execution_budget["finalization_required"]:
                self._ledger_not_executed(parsed, pass_index, "FINALIZATION_TOOL_REQUEST")
                final_response_kind = "CONTROL_FAILURE"
                termination = "finalization_no_text"
                reply = "Final cognition pass reserved for finalization; no final text was produced."
                pass_trace["termination"] = termination
                break

            if self._post_budget_tool_request():
                self._ledger_not_executed(parsed, pass_index, "POST_LIMIT_TOOL_REQUEST")
                final_response_kind = "CONTROL_FAILURE"
                termination = "post_limit_tool_request"
                reply = "Capability execution limit reached; no additional tool was executed."
                pass_trace["termination"] = termination
                break

            if parsed.kind == "TOOL_CALL_CONTROL_FAILURE":
                self.ledger.record_not_executed(
                    pass_index=pass_index,
                    reason=parsed.failure_reason or "INVALID_CALL_SHAPE",
                )
                self._project_decode_failure(parsed.failure_reason, pass_index, response)
                pass_trace["termination"] = "continued"
                continue

            tool_call = parsed.tool_call
            assert tool_call is not None
            if tool_call.fingerprint in self.seen_fingerprints:
                self.ledger.record_not_executed(
                    pass_index=pass_index,
                    reason="DUPLICATE_CALL",
                    capability_id=tool_call.capability_id,
                    arguments=tool_call.arguments,
                )
                self._project_duplicate(tool_call, pass_index)
                pass_trace["termination"] = "continued"
                continue

            if self.capability_execution_count >= self.capability_execution_limit:
                self.ledger.record_not_executed(
                    pass_index=pass_index,
                    reason="BUDGET_EXCEEDED",
                    capability_id=tool_call.capability_id,
                    arguments=tool_call.arguments,
                )
                self._project_budget_exceeded(pass_index)
                pass_trace["termination"] = "continued"
                continue

            self.seen_fingerprints.add(tool_call.fingerprint)
            self.session._execute_tool_with_action(tool_call.raw_json, self.turn_context)
            outcome = self.session._execute_typed_tool(tool_call.raw_json)
            if getattr(outcome, "capability_call", None) is not None:
                self.capability_execution_count += 1
                self.executed_capability_ids.append(tool_call.capability_id)
                status = outcome.tool_result.status
                status_value = status.value if hasattr(status, "value") else str(status)
                self.unresolved_unavailable = status_value == ToolResultStatus.UNAVAILABLE.value
            self._ledger_outcome(outcome, tool_call, pass_index)
            package = self.session._dispatch_typed_outcome(
                outcome,
                self.turn_context,
                parent_package=self.parent_package,
                generation_id=self._generation_id(pass_index, "tool"),
            )
            self._register_projection(package)
            evidence_frame = getattr(package, "evidence_frame", {})
            if isinstance(evidence_frame, dict) and evidence_frame.get("turn_evidence_ledger"):
                self.evidence_generation_ids.append(getattr(package, "generation_id", ""))
            self.session.action.finish(
                self.session._outcome_action_status(outcome),
                correlation_id=self.turn_context.correlation_id,
            )
            self.messages = self._continuation_messages(package, response)
            pass_trace["capability_execution_count"] = self.capability_execution_count
            pass_trace["termination"] = "continued"

        if final_response_kind == "NONE":
            final_response_kind = "CONTROL_FAILURE"
            termination = "cognition_pass_limit"
            reply = "Cognition pass limit reached before Julia could produce a final answer."

        return IterativeTurnResult(
            reply=reply,
            final_response_kind=final_response_kind,
            termination=termination,
            cognition_pass_count=self.cognition_pass_count,
            capability_execution_count=self.capability_execution_count,
            executed_capability_ids=list(self.executed_capability_ids),
            projection_generation_ids=list(self.projection_generation_ids),
            evidence_generation_ids=list(self.evidence_generation_ids),
            cognition_pass_trace=deepcopy(self.cognition_pass_trace),
            ledger_view=self.ledger.event_view(),
        )

    def _execution_budget(self, pass_index: int) -> dict[str, int | bool]:
        remaining_cognition_passes = (
            MAX_COGNITION_PASSES_PER_TURN - pass_index + 1
        )
        remaining_capability_executions = max(
            self.capability_execution_limit - self.capability_execution_count,
            0,
        )
        finalization_required = remaining_cognition_passes == 1
        return {
            "remaining_cognition_passes": remaining_cognition_passes,
            "remaining_capability_executions": remaining_capability_executions,
            "finalization_required": finalization_required,
            "tool_execution_available": (
                not finalization_required and remaining_capability_executions > 0
            ),
        }

    def _post_budget_tool_request(self) -> bool:
        if self.parent_package is None:
            return False
        control_frame = getattr(self.parent_package, "control_frame", {})
        return (
            isinstance(control_frame, dict)
            and control_frame.get("kind") == "tool_call_budget_exceeded"
        )

    def _project_decode_failure(
        self, reason: str | None, pass_index: int, response: str
    ) -> None:
        package = self.session.context_os.project_tool_call_decode_failure(
            parent_package=self.parent_package,
            reason=reason or "INVALID_CALL_SHAPE",
            generation_id=self._generation_id(pass_index, "decode_failure"),
        )
        self._register_projection(package)
        # Keep Julia's own malformed response as her assistant turn, exactly as
        # a successful call is kept, so the retry still sees what she intended.
        self.messages = self._continuation_messages(package, response)

    def _project_duplicate(self, tool_call: StrictToolCall, pass_index: int) -> None:
        package = self.session.context_os.project_duplicate_capability_call_rejected(
            parent_package=self.parent_package,
            capability_id=tool_call.capability_id,
            arguments=tool_call.arguments,
            generation_id=self._generation_id(pass_index, "duplicate"),
        )
        self._register_projection(package)
        self.messages = self._continuation_messages(package, "")

    def _project_budget_exceeded(self, pass_index: int) -> None:
        package = self.session.context_os.project_tool_budget_exceeded(
            parent_package=self.parent_package,
            limit=self.capability_execution_limit,
            generation_id=self._generation_id(pass_index, "budget"),
        )
        self._register_projection(package)
        self.messages = self._continuation_messages(package, "")

    def _ledger_not_executed(self, parsed, pass_index: int, reason: str) -> None:
        call = getattr(parsed, "tool_call", None)
        self.ledger.record_not_executed(
            pass_index=pass_index,
            reason=reason,
            capability_id=call.capability_id if call is not None else "",
            arguments=call.arguments if call is not None else None,
        )

    def _ledger_outcome(self, outcome, tool_call, pass_index: int) -> None:
        """Classify one typed capability outcome into the ledger (duck-typed)."""
        tool_result = getattr(outcome, "tool_result", None)
        if getattr(outcome, "capability_call", None) is not None and tool_result is not None:
            self.ledger.record_executed(
                pass_index=pass_index,
                capability_id=tool_call.capability_id,
                arguments=tool_call.arguments,
                tool_result=tool_result,
            )
            return
        if tool_result is None and hasattr(outcome, "capability_id") and hasattr(outcome, "reason"):
            reason = f"{str(outcome.reason).upper()}_CAPABILITY"
        elif tool_result is None and hasattr(outcome, "reason"):
            reason = str(outcome.reason)  # decode failure reported by the bridge
        else:
            decision = getattr(outcome, "authorization_decision", None)
            value = getattr(getattr(decision, "decision", None), "value", None)
            reason = f"AUTHORIZATION_{str(value).upper()}" if value else "NOT_EXECUTED"
        self.ledger.record_not_executed(
            pass_index=pass_index,
            reason=reason,
            capability_id=tool_call.capability_id,
            arguments=tool_call.arguments,
        )

    def _finish_claim_check(self, pass_index: int, categories: list[str], outcome: str) -> None:
        index = self._correction_check_index
        if index is not None and self.ledger.claim_checks[index]["outcome"] == "correction_requested":
            self.ledger.claim_checks[index]["outcome"] = outcome
            self.ledger.claim_checks[index]["categories_after_correction"] = list(categories)
        else:
            self.ledger.record_claim_check(
                pass_index=pass_index, categories=categories, corrected=False, outcome=outcome
            )

    def _project_claim_correction(
        self, categories: list[str], pass_index: int, response: str
    ) -> None:
        package = self.session.context_os.project_completion_claim_correction(
            parent_package=self.parent_package,
            categories=categories,
            generation_id=self._generation_id(pass_index, "claim_correction"),
        )
        self._register_projection(package)
        # The rejected reply stays visible to Julia only for this correction pass.
        self.messages = self._continuation_messages(package, response)

    def _register_projection(self, package) -> None:
        self.parent_package = package
        self.projection_generation_ids.append(getattr(package, "generation_id", ""))

    def _continuation_messages(self, package, assistant_response: str) -> list[dict]:
        if assistant_response:
            package.active_tail_messages = [
                *package.active_tail_messages,
                {"role": "assistant", "content": assistant_response},
            ]
        return package.to_messages(package.active_tail_messages, self.text)

    def _generation_id(self, pass_index: int, suffix: str) -> str:
        turn_id = re.sub(r"[^a-zA-Z0-9_-]", "-", self.turn_context.turn_id or "turn")
        generation_id = f"gen_{turn_id}_pass_{pass_index}_{suffix}_{uuid.uuid4().hex[:12]}"
        if generation_id in self.generation_ids:
            raise ValueError(f"duplicate generation_id: {generation_id}")
        self.generation_ids.add(generation_id)
        return generation_id
