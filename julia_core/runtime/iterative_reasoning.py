"""Turn-scoped iterative cognition loop owned by JuliaSession."""

from __future__ import annotations

import json
import re
import uuid
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
_EXACT_EVIDENCE_OBLIGATION = re.compile(
    r"^```evidence_obligation[ \t]*\n(.*)\n```$",
    re.DOTALL,
)
_GENERIC_EVIDENCE_INTENT = re.compile(r"^[a-z][a-z0-9_]*$")

_EVIDENCE_OBLIGATION_CHECK_INSTRUCTION = """
[evidence_obligation_check]
This is a bounded Julia cognition control check, not a user-facing answer and not a capability-selection step.
Using the current turn context, available_tools, existing ToolResult/evidence/control state, and the candidate FINAL_TEXT immediately before this instruction, decide whether REQUIRED external evidence remains unresolved.
Set unresolved_required_evidence=true only when the candidate final must not be returned yet because the current user request or Julia's already-formed reasoning requires external evidence that has not reached a ToolResult or typed unavailable/error outcome. A typed unavailable/error outcome counts as an execution outcome for this obligation check.
Do not select, name, or recommend a concrete capability. Return exactly one block and no surrounding prose. Use exactly one of these shapes:
```evidence_obligation
{"unresolved_required_evidence":false,"evidence_intents":[]}
```
or
```evidence_obligation
{"unresolved_required_evidence":true,"evidence_intents":["external_evidence"]}
```
For true, evidence_intents may use other generic evidence-intent labels, but must never contain a concrete capability_id.
""".strip()


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


@dataclass(frozen=True, slots=True)
class EvidenceObligationDecision:
    unresolved_required_evidence: bool
    evidence_intents: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EvidenceObligationCheckResult:
    kind: str
    decision: EvidenceObligationDecision | None = None
    failure_reason: str | None = None


def parse_evidence_obligation_response(response: str) -> EvidenceObligationCheckResult:
    """Strict parser for the bounded Julia-owned finalization obligation check.

    This contract is deliberately independent from the normal tool-call parser.
    Runtime consumes only the boolean obligation plus opaque generic intent labels;
    it does not infer evidence need from user text or Julia prose.
    """
    trimmed = str(response).strip()
    match = _EXACT_EVIDENCE_OBLIGATION.fullmatch(trimmed)
    if match is None:
        return EvidenceObligationCheckResult(
            kind="CONTROL_FAILURE",
            failure_reason="INVALID_EVIDENCE_OBLIGATION_SHAPE",
        )
    try:
        payload = json.loads(match.group(1).strip())
    except json.JSONDecodeError:
        return EvidenceObligationCheckResult(
            kind="CONTROL_FAILURE",
            failure_reason="MALFORMED_EVIDENCE_OBLIGATION_JSON",
        )
    if not isinstance(payload, dict) or set(payload) != {
        "unresolved_required_evidence",
        "evidence_intents",
    }:
        return EvidenceObligationCheckResult(
            kind="CONTROL_FAILURE",
            failure_reason="INVALID_EVIDENCE_OBLIGATION_SHAPE",
        )
    unresolved = payload.get("unresolved_required_evidence")
    intents = payload.get("evidence_intents")
    if type(unresolved) is not bool or not isinstance(intents, list):
        return EvidenceObligationCheckResult(
            kind="CONTROL_FAILURE",
            failure_reason="INVALID_EVIDENCE_OBLIGATION_TYPES",
        )
    if any(not isinstance(intent, str) or not intent.strip() for intent in intents):
        return EvidenceObligationCheckResult(
            kind="CONTROL_FAILURE",
            failure_reason="INVALID_EVIDENCE_INTENT",
        )
    normalized = tuple(intent.strip() for intent in intents)
    if any(_GENERIC_EVIDENCE_INTENT.fullmatch(intent) is None for intent in normalized):
        return EvidenceObligationCheckResult(
            kind="CONTROL_FAILURE",
            failure_reason="INVALID_EVIDENCE_INTENT",
        )
    if len(set(normalized)) != len(normalized):
        return EvidenceObligationCheckResult(
            kind="CONTROL_FAILURE",
            failure_reason="DUPLICATE_EVIDENCE_INTENT",
        )
    if unresolved and not normalized:
        return EvidenceObligationCheckResult(
            kind="CONTROL_FAILURE",
            failure_reason="MISSING_REQUIRED_EVIDENCE_INTENT",
        )
    if not unresolved and normalized:
        return EvidenceObligationCheckResult(
            kind="CONTROL_FAILURE",
            failure_reason="UNEXPECTED_EVIDENCE_INTENT",
        )
    return EvidenceObligationCheckResult(
        kind="DECISION",
        decision=EvidenceObligationDecision(
            unresolved_required_evidence=unresolved,
            evidence_intents=normalized,
        ),
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
    evidence_obligation_check_count: int = 0
    evidence_obligation_required_count: int = 0


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
        self.evidence_obligation_check_count = 0
        self.evidence_obligation_required_count = 0
        self.unresolved_unavailable = False

    def run(self) -> IterativeTurnResult:
        reply = ""
        final_response_kind = "NONE"
        termination = "completed"

        for pass_index in range(1, MAX_COGNITION_PASSES_PER_TURN + 1):
            self.cognition_pass_count = pass_index
            response = self.session.provider.chat(
                self.messages,
                cognitive_mode="private_voice_continuity",
            )
            parsed = parse_strict_model_response(response)

            if parsed.kind == "FINAL_TEXT":
                control_frame = getattr(self.parent_package, "control_frame", {})
                budget_limitation = (
                    isinstance(control_frame, dict)
                    and control_frame.get("kind") == "tool_call_budget_exceeded"
                )
                limitation = budget_limitation or self.unresolved_unavailable

                if not limitation and self._external_evidence_check_applicable():
                    obligation = self._check_evidence_obligation(parsed.text)
                    if obligation.kind != "DECISION" or obligation.decision is None:
                        final_response_kind = "CONTROL_FAILURE"
                        termination = "evidence_obligation_check_invalid"
                        reply = (
                            "Evidence obligation check failed closed before Julia's "
                            "candidate final response could be accepted."
                        )
                        break
                    if obligation.decision.unresolved_required_evidence:
                        self.evidence_obligation_required_count += 1
                        self._project_required_tool_missing(
                            obligation.decision.evidence_intents,
                            parsed.text,
                            pass_index,
                        )
                        continue

                final_response_kind = "LIMITATION" if limitation else "JUDGMENT"
                termination = (
                    "completed_with_limitation"
                    if limitation
                    else "completed"
                )
                reply = parsed.text
                break

            if self._post_budget_tool_request():
                final_response_kind = "CONTROL_FAILURE"
                termination = "post_limit_tool_request"
                reply = "Capability execution limit reached; no additional tool was executed."
                break

            if parsed.kind == "TOOL_CALL_CONTROL_FAILURE":
                if pass_index == MAX_COGNITION_PASSES_PER_TURN:
                    final_response_kind = "CONTROL_FAILURE"
                    termination = "cognition_pass_limit"
                    reply = "Cognition pass limit reached before Julia could produce a final answer."
                    break
                self._project_decode_failure(parsed.failure_reason, parsed.text, pass_index)
                continue

            tool_call = parsed.tool_call
            assert tool_call is not None
            if pass_index == MAX_COGNITION_PASSES_PER_TURN:
                final_response_kind = "CONTROL_FAILURE"
                termination = "cognition_pass_limit"
                reply = "Cognition pass limit reached before Julia could produce a final answer."
                break

            if tool_call.fingerprint in self.seen_fingerprints:
                self._project_duplicate(tool_call, pass_index)
                continue

            if self.capability_execution_count >= self.capability_execution_limit:
                self._project_budget_exceeded(pass_index)
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
            evidence_obligation_check_count=self.evidence_obligation_check_count,
            evidence_obligation_required_count=self.evidence_obligation_required_count,
        )

    def _external_evidence_check_applicable(self) -> bool:
        """Mechanical applicability check from the validated capability contract.

        This does not inspect user text or Julia prose. It only asks whether the
        current package advertises at least one capability covered by the
        already-validated external_evidence capability prefixes.
        """
        if self.parent_package is None:
            return False
        policy = getattr(self.parent_package, "validated_invocation_policy", {})
        if not isinstance(policy, dict):
            return False
        epistemic_rules = policy.get("epistemic_rules")
        if not isinstance(epistemic_rules, dict):
            return False
        external_rule = epistemic_rules.get("external_evidence")
        if not isinstance(external_rule, dict):
            return False
        prefixes = external_rule.get("capability_prefixes")
        if not isinstance(prefixes, list):
            return False
        capability_frame = getattr(self.parent_package, "capability_frame", {})
        if not isinstance(capability_frame, dict):
            return False
        available_tools = capability_frame.get("available_tools")
        if not isinstance(available_tools, list):
            return False
        normalized_prefixes = tuple(
            prefix[:-1] if isinstance(prefix, str) and prefix.endswith("*") else prefix
            for prefix in prefixes
            if isinstance(prefix, str) and prefix
        )
        return any(
            isinstance(tool, dict)
            and isinstance(tool.get("capability_id"), str)
            and any(tool["capability_id"].startswith(prefix) for prefix in normalized_prefixes)
            for tool in available_tools
        )

    def _check_evidence_obligation(self, candidate_final: str) -> EvidenceObligationCheckResult:
        messages = list(self.messages)
        messages.append({"role": "assistant", "content": candidate_final})
        messages.append({
            "role": "system",
            "content": _EVIDENCE_OBLIGATION_CHECK_INSTRUCTION,
        })
        self.evidence_obligation_check_count += 1
        response = self.session.provider.chat(
            messages,
            cognitive_mode="evidence_obligation_check",
        )
        return parse_evidence_obligation_response(response)

    def _project_required_tool_missing(
        self,
        evidence_intents: tuple[str, ...],
        candidate_final: str,
        pass_index: int,
    ) -> None:
        package = self.session.context_os.project_retry_control(
            parent_package=self.parent_package,
            reason="required_tool_call_missing",
            evidence_intents=evidence_intents,
            generation_id=self._generation_id(pass_index, "required_tool"),
        )
        self._register_projection(package)
        self.messages = self._continuation_messages(package, candidate_final)

    def _post_budget_tool_request(self) -> bool:
        if self.parent_package is None:
            return False
        control_frame = getattr(self.parent_package, "control_frame", {})
        return (
            isinstance(control_frame, dict)
            and control_frame.get("kind") == "tool_call_budget_exceeded"
        )

    def _project_decode_failure(
        self,
        reason: str | None,
        assistant_response: str,
        pass_index: int,
    ) -> None:
        package = self.session.context_os.project_tool_call_decode_failure(
            parent_package=self.parent_package,
            reason=reason or "INVALID_CALL_SHAPE",
            generation_id=self._generation_id(pass_index, "decode_failure"),
        )
        self._register_projection(package)
        self.messages = self._continuation_messages(package, assistant_response)

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
        messages = package.to_messages(package.active_tail_messages, self.text)
        if assistant_response:
            messages.insert(-1, {"role": "assistant", "content": assistant_response})
        return messages

    def _generation_id(self, pass_index: int, suffix: str) -> str:
        turn_id = re.sub(r"[^a-zA-Z0-9_-]", "-", self.turn_context.turn_id or "turn")
        generation_id = f"gen_{turn_id}_pass_{pass_index}_{suffix}_{uuid.uuid4().hex[:12]}"
        if generation_id in self.generation_ids:
            raise ValueError(f"duplicate generation_id: {generation_id}")
        self.generation_ids.add(generation_id)
        return generation_id
