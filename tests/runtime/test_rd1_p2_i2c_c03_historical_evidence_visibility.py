"""RD1-P2-I2C C03: historical turn-evidence-ledger entries stay model-visible (#189).

Uses REAL provider outputs (tests/fixtures/c03/rd1_historical_evidence_real_outputs.json):
the Research structured_output is verbatim from the natural E2E evidence, the
Market payload has the real READY quote shape. The latest tool_result must render
exactly as before; only historical ledger entries change.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from julia_core.capability.models import (
    Evidence,
    EvidenceSourceType,
    ToolResult,
    ToolResultStatus,
)
from julia_core.runtime.context_execution_runtime import (
    CognitiveContextPackage,
    ContextExecutionRuntime,
)

_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "c03"
    / "rd1_historical_evidence_real_outputs.json"
)
_REAL = json.loads(_FIXTURE.read_text(encoding="utf-8"))
RESEARCH_OUT = _REAL["research_structured_output"]
MARKET_OUT = _REAL["market_structured_output"]


def _observation(gid: str, provider: str, output: dict, status: ToolResultStatus):
    evidence = Evidence(
        evidence_id=f"ev-{gid}",
        source_type=EvidenceSourceType.TOOL_OBSERVATION,
        source_ref=f"s-{gid}",
        observed_at="2026-09-29T00:00:00Z",
        content_ref=f"c-{gid}",
        provenance={"capability_id": gid, "provider": provider},
    )
    result = ToolResult(
        capability_call_id=f"call-{gid}",
        status=status,
        structured_output=copy.deepcopy(output),
        evidence_refs=(f"ev-{gid}",),
        provider=provider,
    )
    return result, evidence


def _market(gid: str = "market"):
    return _observation(gid, "market", MARKET_OUT, ToolResultStatus.SUCCESS)


def _research(gid: str = "research", output: dict | None = None):
    return _observation(gid, "research", output or RESEARCH_OUT, ToolResultStatus.PARTIAL)


def _project(seq) -> CognitiveContextPackage:
    pkg = CognitiveContextPackage(conversation_id="c", turn_id="t", generation_id="g0")
    runtime = ContextExecutionRuntime()
    for index, (result, evidence) in enumerate(seq):
        pkg = runtime.project_tool_result(
            parent_package=pkg,
            tool_result=result,
            evidence=(evidence,),
            generation_id=f"g{index + 1}",
        )
    return pkg


def _render(pkg: CognitiveContextPackage) -> str:
    return pkg._render_frame("evidence", pkg.evidence_frame)


def _assert_market_visible(text: str) -> None:
    payload = MARKET_OUT["payload"]
    for key in ("close_price", "pct_chg", "high_price", "low_price", "trade_date"):
        assert str(payload[key]) in text, key


def _assert_research_visible(text: str, *, urls: bool) -> None:
    flat = "".join(text.split())
    for finding in RESEARCH_OUT["findings"]:
        assert "".join(finding["material"].split())[:12] in flat
    for source in RESEARCH_OUT["sources"]:
        assert source["title"][:12] in text
        if urls:
            assert source["url"] in text


def test_f2_single_research_renders_sources_and_references_latest_once():
    pkg = _project([_research()])
    text = _render(pkg)

    _assert_research_visible(text, urls=True)
    assert "generation_id=g1, tool_result=<current tool_result above>" in text
    # The latest result is not rendered a second time from the ledger.
    assert text.count(f"query={RESEARCH_OUT['query']}") == 1
    assert len(text) <= CognitiveContextPackage._RENDER_MAX_FRAME_CHARS


def test_market_then_research_keeps_historical_market_values():
    text = _render(_project([_market(), _research()]))

    _assert_market_visible(text)
    _assert_research_visible(text, urls=True)
    assert "generation_id=g2, tool_result=<current tool_result above>" in text
    assert len(text) <= CognitiveContextPackage._RENDER_MAX_FRAME_CHARS


def test_research_then_market_keeps_historical_research_findings_and_titles():
    text = _render(_project([_research(), _market()]))

    _assert_market_visible(text)
    _assert_research_visible(text, urls=False)
    assert "generation_id=g2, tool_result=<current tool_result above>" in text
    assert len(text) <= CognitiveContextPackage._RENDER_MAX_FRAME_CHARS


def test_latest_tool_result_rendering_is_unchanged_by_history():
    alone = _render(_project([_market()]))
    after_research = _render(_project([_research(), _market()]))

    def latest_part(text: str) -> str:
        return text.split("\nturn_evidence_ledger: ")[0]

    assert latest_part(after_research) == latest_part(alone)


def test_rendering_does_not_mutate_structured_ledger():
    pkg = _project([_market(), _research()])
    before = copy.deepcopy(pkg.evidence_frame)
    _render(pkg)
    pkg.to_messages([], "q")
    assert pkg.evidence_frame == before


def test_lone_surrogate_in_historical_entry_does_not_crash_rendering():
    hostile = copy.deepcopy(RESEARCH_OUT)
    hostile["findings"][0]["material"] = "bad \ud800 text " + hostile["findings"][0]["material"]
    hostile["deep"] = {"a": {"b": {"c": {"d": {"\udc00key": "v\ud800"}}}}}
    pkg = _project([_research(output=hostile), _market()])

    messages = pkg.to_messages([], "q")
    system_text = messages[0]["content"]
    system_text.encode("utf-8")  # must not raise
    _assert_market_visible(system_text)
    assert "\\ud800" in system_text


def test_frame_budget_bounds_many_historical_entries():
    seq = [_research(f"r{i}") for i in range(6)] + [_market("m")]
    pkg = _project(seq)
    text = _render(pkg)

    assert len(text) <= CognitiveContextPackage._RENDER_MAX_FRAME_CHARS
    _assert_market_visible(text)  # latest stays intact under pressure
    assert CognitiveContextPackage._RENDER_TRUNC_MARKER in text
    # Each historical entry still gets a share instead of the first starving the rest.
    for i in range(6):
        assert f"capability_call_id=call-r{i}" in text


@pytest.mark.parametrize("depth_exhausted", [{"x": 1}, [1, 2]])
def test_depth_exhausted_containers_are_flattened_in_history(depth_exhausted):
    output = {"a": {"b": {"c": {"d": depth_exhausted, "e": "leaf-value"}}}}
    pkg = _project([_research(output=output), _market()])
    text = _render(pkg)

    assert "{…}" not in text.split("turn_evidence_ledger: ")[1]
    assert "[…]" not in text.split("turn_evidence_ledger: ")[1]
    assert "leaf-value" in text
