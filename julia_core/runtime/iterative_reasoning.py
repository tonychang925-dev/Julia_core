"""Turn-scoped iterative cognition loop owned by JuliaSession."""

from __future__ import annotations

import json
import re
import uuid
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

from julia_core.capability.models import ToolResultStatus


MAX_COGNITION_PASSES_PER_TURN = 7
MAX_CAPABILITY_EXECUTIONS_PER_TURN = 6
MAX_STRUCTURED_TOOL_CALLS_PER_MODEL_RESPONSE = 1

_LEGACY_TOOL_NAMES = {
    "read_file": "file.read",
    "search_files": "file.search",
    "list_directory": "file.list",
}
_EXACT_TOOL_CALL = re.compile(
    r"^```tool_call[ \t]*\n(.*)\n```$",
    re.DOTALL,
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
    if match is None:
        return StrictModelResponse(
            "TOOL_CALL_CONTROL_FAILURE",
            trimmed,
            failure_reason="INVALID_CALL_SHAPE",
        )

    raw_json = match.group(1).strip()
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

    def run(self) -> IterativeTurnResult:
        reply = ""
        final_response_kind = "NONE"
        termination = "completed"

        for pass_index in range(1, MAX_COGNITION_PASSES_PER_TURN + 1):
            self.cognition_pass_count = pass_index
            execution_budget = self._execution_budget(pass_index)
            budget_package = self.session.context_os.project_execution_budget_overlay(
                self.parent_package,
                **execution_budget,
            )
            response = self.session.provider.chat(
                budget_package.to_messages(budget_package.active_tail_messages, self.text),
                cognitive_mode="private_voice_continuity",
            )
            parsed = parse_strict_model_response(response)
            pass_trace = {
                "pass_index": pass_index,
                **execution_budget,
                "parsed_response_kind": parsed.kind,
                "capability_execution_count": self.capability_execution_count,
                "termination": "",
            }
            self.cognition_pass_trace.append(pass_trace)

            if parsed.kind == "FINAL_TEXT":
                if execution_budget["finalization_required"] and not parsed.text:
                    final_response_kind = "CONTROL_FAILURE"
                    termination = "finalization_no_text"
                    reply = "Final cognition pass reserved for finalization; no final text was produced."
                    pass_trace["termination"] = termination
                    break
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
                final_response_kind = "CONTROL_FAILURE"
                termination = "finalization_no_text"
                reply = "Final cognition pass reserved for finalization; no final text was produced."
                pass_trace["termination"] = termination
                break

            if self._post_budget_tool_request():
                final_response_kind = "CONTROL_FAILURE"
                termination = "post_limit_tool_request"
                reply = "Capability execution limit reached; no additional tool was executed."
                pass_trace["termination"] = termination
                break

            if parsed.kind == "TOOL_CALL_CONTROL_FAILURE":
                self._project_decode_failure(parsed.failure_reason, pass_index)
                pass_trace["termination"] = "continued"
                continue

            tool_call = parsed.tool_call
            assert tool_call is not None
            if tool_call.fingerprint in self.seen_fingerprints:
                self._project_duplicate(tool_call, pass_index)
                pass_trace["termination"] = "continued"
                continue

            if self.capability_execution_count >= self.capability_execution_limit:
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

    def _project_decode_failure(self, reason: str | None, pass_index: int) -> None:
        package = self.session.context_os.project_tool_call_decode_failure(
            parent_package=self.parent_package,
            reason=reason or "INVALID_CALL_SHAPE",
            generation_id=self._generation_id(pass_index, "decode_failure"),
        )
        self._register_projection(package)
        self.messages = self._continuation_messages(package, "")

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
