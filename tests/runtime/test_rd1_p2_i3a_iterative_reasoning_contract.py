from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest


SOURCE_ROOT = Path(__file__).resolve().parents[2]
JULIA_SESSION = SOURCE_ROOT / "julia_core/runtime/julia_session.py"


@dataclass(frozen=True)
class ToolRequest:
    capability_id: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class ToolOutcome:
    request: ToolRequest
    status: str
    structured_output: dict[str, Any] | None = None


@dataclass
class ContextPackage:
    generation_id: str
    parent: "ContextPackage | None"
    evidence: list[dict[str, Any]] = field(default_factory=list)
    control: dict[str, Any] | None = None
    invocation_policy: dict[str, Any] = field(
        default_factory=lambda: {
            "structured_call_required": True,
            "raw_user_text_routing": False,
            "max_tool_calls_per_model_response": 1,
            "tools_are_evidence_not_judgment": True,
        }
    )
    identity: dict[str, Any] = field(
        default_factory=lambda: {"persona_generation": "immutable"}
    )
    continuity: dict[str, Any] = field(
        default_factory=lambda: {"checkpoint": "immutable"}
    )


@dataclass
class TurnResult:
    reply: str
    cognition_passes: list[list[dict[str, Any]]]
    executions: list[ToolRequest]
    lineage: list[ContextPackage]
    termination: str
    final_judgment: bool
    authority_snapshots: list[dict[str, dict[str, Any]]]


class IterativeReasoningHarness:
    """Test-only executable form of the P2-I3 contract; not production code."""

    max_cognition_passes = 4
    max_tool_calls = 2

    def __init__(self, responses: list[str], outcomes: list[ToolOutcome]) -> None:
        self.responses = list(responses)
        self.outcomes = list(outcomes)
        self.cognition_passes: list[list[dict[str, Any]]] = []
        self.executions: list[ToolRequest] = []
        self.lineage: list[ContextPackage] = []
        self.seen_fingerprints: set[tuple[str, str]] = set()
        self.authority_snapshots: list[dict[str, dict[str, Any]]] = []

    def run(self, user_text: str) -> TurnResult:
        current = self._project("gen_pass_1", None)
        self.lineage.append(current)
        termination = "completed"
        final_judgment = False
        reply = ""

        for pass_index in range(1, self.max_cognition_passes + 1):
            self._snapshot_authorities(current)
            messages = [
                {"role": "system", "content": self._render_system(current)},
                {"role": "user", "content": user_text},
            ]
            self.cognition_passes.append(messages)
            response = self.responses.pop(0)
            request = self._parse_one(response)

            if request is None:
                reply = response
                final_judgment = (
                    pass_index == 1
                    or bool(current.evidence)
                    or current.control is not None
                )
                if not final_judgment:
                    termination = "final_without_required_c03_reentry"
                break

            if len(self.executions) >= self.max_tool_calls:
                termination = "tool_call_limit"
                break
            if pass_index == self.max_cognition_passes:
                termination = "cognition_pass_limit"
                break

            fingerprint = (
                request.capability_id,
                json.dumps(request.arguments, sort_keys=True),
            )
            if fingerprint in self.seen_fingerprints:
                current = self._project(
                    f"gen_pass_{pass_index}_duplicate",
                    current,
                    control={"kind": "duplicate_rejected", "request": request.__dict__},
                )
                self.lineage.append(current)
                continue

            self.seen_fingerprints.add(fingerprint)
            self.executions.append(request)
            outcome = self._outcome_for(request)
            evidence = {
                "capability_id": request.capability_id,
                "status": outcome.status,
                "structured_output": outcome.structured_output,
            }
            current = self._project(
                f"gen_pass_{pass_index}_tool_{len(self.executions)}",
                current,
                evidence=evidence,
            )
            self.lineage.append(current)
        else:
            termination = "cognition_pass_limit"

        return TurnResult(
            reply=reply,
            cognition_passes=self.cognition_passes,
            executions=self.executions,
            lineage=self.lineage,
            termination=termination,
            final_judgment=final_judgment,
            authority_snapshots=self.authority_snapshots,
        )

    def _outcome_for(self, request: ToolRequest) -> ToolOutcome:
        for outcome in self.outcomes:
            if outcome.request == request:
                return outcome
        raise AssertionError(f"no outcome fixture for {request}")

    @staticmethod
    def _parse_one(response: str) -> ToolRequest | None:
        calls = re.findall(r"```tool_call\s*(\{.*?\})\s*```", response, flags=re.DOTALL)
        if not calls:
            if "tool_call" in response:
                raise ValueError("malformed structured tool call")
            return None
        if len(calls) != 1 or response.strip() != f"```tool_call\n{calls[0]}\n```":
            raise ValueError("exactly one complete structured tool call is required")
        payload = json.loads(calls[0])
        capability_id = payload.get("name")
        arguments = payload.get("arguments")
        if not isinstance(capability_id, str) or not isinstance(arguments, dict):
            raise ValueError("invalid structured tool call")
        return ToolRequest(capability_id, arguments)

    @staticmethod
    def _project(
        generation_id: str, parent: ContextPackage | None, **changes: Any
    ) -> ContextPackage:
        package = ContextPackage(generation_id=generation_id, parent=parent)
        if parent is not None:
            package.evidence = list(parent.evidence)
            package.invocation_policy = dict(parent.invocation_policy)
            package.identity = dict(parent.identity)
            package.continuity = dict(parent.continuity)
        if "evidence" in changes:
            package.evidence.append(changes["evidence"])
        if "control" in changes:
            package.control = changes["control"]
        return package

    @staticmethod
    def _render_system(package: ContextPackage) -> str:
        policy = json.dumps(package.invocation_policy, sort_keys=True)
        evidence = json.dumps(package.evidence, sort_keys=True)
        control = json.dumps(package.control, sort_keys=True)
        return f"validated_invocation_policy={policy}\nevidence={evidence}\ncontrol={control}"

    @staticmethod
    def _snapshot_authorities(package: ContextPackage) -> None:
        global _AUTHORITY_STATE
        _AUTHORITY_STATE["tool_observations_seen"].append(package.evidence)


_AUTHORITY_STATE: dict[str, Any] = {"tool_observations_seen": []}


def _tool(response_text: str) -> str:
    return f"```tool_call\n{response_text}\n```"


def market_request() -> ToolRequest:
    return ToolRequest("market.event.resolve", {"query": "JYHF event"})


def research_request() -> ToolRequest:
    return ToolRequest("research.web.query", {"query": "JYHF external evidence"})


def success(request: ToolRequest, marker: str) -> ToolOutcome:
    return ToolOutcome(
        request=request,
        status="SUCCESS",
        structured_output={"operation_status": "SUCCESS", "marker": marker},
    )


def test_i3a_01_market_then_research_final_judgment():
    result = IterativeReasoningHarness(
        [
            _tool(
                json.dumps(
                    {
                        "name": market_request().capability_id,
                        "arguments": market_request().arguments,
                    }
                )
            ),
            _tool(
                json.dumps(
                    {
                        "name": research_request().capability_id,
                        "arguments": research_request().arguments,
                    }
                )
            ),
            "JULIA_FINAL_MARKET_AND_RESEARCH",
        ],
        [success(market_request(), "market"), success(research_request(), "research")],
    ).run("Assess JYHF")

    assert [request.capability_id for request in result.executions] == [
        "market.event.resolve",
        "research.web.query",
    ]
    assert result.reply == "JULIA_FINAL_MARKET_AND_RESEARCH"
    assert result.termination == "completed"
    assert result.final_judgment is True


def test_i3a_02_research_then_market_final_judgment():
    result = IterativeReasoningHarness(
        [
            _tool(
                json.dumps(
                    {
                        "name": research_request().capability_id,
                        "arguments": research_request().arguments,
                    }
                )
            ),
            _tool(
                json.dumps(
                    {
                        "name": market_request().capability_id,
                        "arguments": market_request().arguments,
                    }
                )
            ),
            "JULIA_FINAL_RESEARCH_AND_MARKET",
        ],
        [success(research_request(), "research"), success(market_request(), "market")],
    ).run("Assess JYHF")

    assert [request.capability_id for request in result.executions] == [
        "research.web.query",
        "market.event.resolve",
    ]
    assert result.final_judgment is True


def test_i3a_03_second_success_accumulates_evidence_and_preserves_lineage():
    first = market_request()
    second = ToolRequest("market.event.resolve", {"query": "JYHF follow-up"})
    result = IterativeReasoningHarness(
        [
            _tool(
                json.dumps({"name": first.capability_id, "arguments": first.arguments})
            ),
            _tool(
                json.dumps(
                    {"name": second.capability_id, "arguments": second.arguments}
                )
            ),
            "JULIA_FINAL_AFTER_TWO_SUCCESSES",
        ],
        [success(first, "first"), success(second, "second")],
    ).run("Assess JYHF")

    assert len(result.executions) == 2
    assert result.lineage[-1].evidence[0]["structured_output"]["marker"] == "first"
    assert result.lineage[-1].evidence[1]["structured_output"]["marker"] == "second"
    assert result.lineage[-1].parent is result.lineage[-2]
    assert len({package.generation_id for package in result.lineage}) == len(
        result.lineage
    )


def test_i3a_04_partial_leads_to_complementary_research_request():
    partial = ToolOutcome(
        request=market_request(),
        status="PARTIAL",
        structured_output={
            "operation_status": "PARTIAL",
            "failures": ["market coverage incomplete"],
        },
    )
    result = IterativeReasoningHarness(
        [
            _tool(
                json.dumps(
                    {
                        "name": market_request().capability_id,
                        "arguments": market_request().arguments,
                    }
                )
            ),
            _tool(
                json.dumps(
                    {
                        "name": research_request().capability_id,
                        "arguments": research_request().arguments,
                    }
                )
            ),
            "JULIA_FINAL_WITH_COMPLEMENTARY_EVIDENCE",
        ],
        [partial, success(research_request(), "research")],
    ).run("Assess JYHF")

    assert result.lineage[-2].evidence[0]["status"] == "PARTIAL"
    assert result.lineage[-1].evidence[1]["capability_id"] == "research.web.query"
    assert result.final_judgment is True


def test_i3a_05_unavailable_revises_plan_without_fallback():
    unavailable = ToolOutcome(
        request=research_request(),
        status="UNAVAILABLE",
        structured_output={
            "operation_status": "FAILURE",
            "failures": [
                {
                    "code": "provider_not_found",
                    "message": "Research provider is not bound",
                }
            ],
        },
    )
    result = IterativeReasoningHarness(
        [
            _tool(
                json.dumps(
                    {
                        "name": research_request().capability_id,
                        "arguments": research_request().arguments,
                    }
                )
            ),
            "Research evidence is unavailable; I will not substitute a hidden provider.",
        ],
        [unavailable],
    ).run("Research JYHF")

    assert len(result.executions) == 1
    assert result.final_judgment is True
    assert "provider_not_found" in json.dumps(result.lineage[-1].evidence)


def test_i3a_06_duplicate_request_is_rejected_before_execution_then_reenters_c03():
    first = market_request()
    duplicate = _tool(
        json.dumps({"name": first.capability_id, "arguments": first.arguments})
    )
    result = IterativeReasoningHarness(
        [
            duplicate,
            duplicate,
            "JULIA_FINAL_AFTER_DUPLICATE_REJECTION",
        ],
        [success(first, "market")],
    ).run("Assess JYHF")

    assert len(result.executions) == 1
    assert result.lineage[-1].control == {
        "kind": "duplicate_rejected",
        "request": {"capability_id": first.capability_id, "arguments": first.arguments},
    }
    assert result.final_judgment is True


def test_i3a_07_hard_cognition_limit_fails_closed_without_fabricated_judgment():
    request = market_request()
    call = _tool(
        json.dumps({"name": request.capability_id, "arguments": request.arguments})
    )
    result = IterativeReasoningHarness(
        [call, call, call, call],
        [success(request, "market")],
    ).run("Assess JYHF")

    assert result.termination == "cognition_pass_limit"
    assert result.final_judgment is False
    assert result.reply == ""


@pytest.mark.xfail(
    strict=True,
    reason="P2-I3 production gap: JuliaSession still routes on raw user text",
)
def test_i3a_08_production_has_no_raw_user_text_capability_router():
    source = JULIA_SESSION.read_text(encoding="utf-8")
    assert "requires_tool(text)" not in source
    assert "_is_market_intent" not in source


def test_i3a_09_hidden_second_tool_call_is_rejected_before_execution():
    request = market_request()
    two_calls = (
        _tool(
            json.dumps({"name": request.capability_id, "arguments": request.arguments})
        )
        + "\n"
        + _tool(
            json.dumps(
                {
                    "name": research_request().capability_id,
                    "arguments": research_request().arguments,
                }
            )
        )
    )
    harness = IterativeReasoningHarness([two_calls], [success(request, "market")])

    with pytest.raises(ValueError, match="exactly one complete structured tool call"):
        harness.run("Assess JYHF")

    assert harness.executions == []


def test_i3a_10_final_response_requires_c03_reentry_after_evidence():
    request = market_request()
    result = IterativeReasoningHarness(
        [
            _tool(
                json.dumps(
                    {"name": request.capability_id, "arguments": request.arguments}
                )
            ),
            "JULIA_FINAL_AFTER_C03",
        ],
        [success(request, "market")],
    ).run("Assess JYHF")

    assert result.final_judgment is True
    assert result.cognition_passes[1][0]["role"] == "system"
    assert "market.event.resolve" in result.cognition_passes[1][0]["content"]


def test_i3a_11_validated_policy_is_visible_on_every_continuation():
    first = market_request()
    second = research_request()
    result = IterativeReasoningHarness(
        [
            _tool(
                json.dumps({"name": first.capability_id, "arguments": first.arguments})
            ),
            _tool(
                json.dumps(
                    {"name": second.capability_id, "arguments": second.arguments}
                )
            ),
            "JULIA_FINAL",
        ],
        [success(first, "market"), success(second, "research")],
    ).run("Assess JYHF")

    for messages in result.cognition_passes:
        policy_text = messages[0]["content"].splitlines()[0]
        assert '"structured_call_required": true' in policy_text
        assert '"raw_user_text_routing": false' in policy_text
        assert '"max_tool_calls_per_model_response": 1' in policy_text


def test_i3a_12_tool_evidence_does_not_mutate_authority_state():
    _AUTHORITY_STATE["tool_observations_seen"] = []
    request = market_request()
    result = IterativeReasoningHarness(
        [
            _tool(
                json.dumps(
                    {"name": request.capability_id, "arguments": request.arguments}
                )
            ),
            "JULIA_FINAL",
        ],
        [success(request, "market")],
    ).run("Assess JYHF")

    for package in result.lineage:
        assert package.identity == {"persona_generation": "immutable"}
        assert package.continuity == {"checkpoint": "immutable"}
    assert _AUTHORITY_STATE == {
        "tool_observations_seen": [
            [],
            [
                {
                    "capability_id": "market.event.resolve",
                    "status": "SUCCESS",
                    "structured_output": {
                        "operation_status": "SUCCESS",
                        "marker": "market",
                    },
                }
            ],
        ]
    }
