"""RD1-P2-I2E C03: need-based render budget with real Market payloads (#194).

Fixtures are real persisted provider outputs:
- tests/fixtures/c03/rd1_need_based_render_real_market_outputs.json
  (market.state.read verbatim; market.analysis.read with its evidence lists trimmed)
- tests/fixtures/c03/rd1_historical_evidence_real_outputs.json (research.web.query)
"""

from __future__ import annotations

import copy
import json
import time
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

_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "c03"
_MARKET = json.loads(
    (_FIXTURES / "rd1_need_based_render_real_market_outputs.json").read_text(encoding="utf-8")
)
_RESEARCH = json.loads(
    (_FIXTURES / "rd1_historical_evidence_real_outputs.json").read_text(encoding="utf-8")
)["research_structured_output"]
STATE_OUT = _MARKET["market.state.read"]
ANALYSIS_OUT = _MARKET["market.analysis.read"]

STATE_VALUES = ("2357", "2642", "289258.22")
REGIME_VALUES = ("bearish_adverse", "retreat", "mainline_tradable")
BUDGET = CognitiveContextPackage._RENDER_MAX_FRAME_CHARS
MARKER = CognitiveContextPackage._RENDER_TRUNC_MARKER


def _observation(gid: str, output: dict, status=ToolResultStatus.SUCCESS):
    evidence = Evidence(
        evidence_id=f"ev-{gid}",
        source_type=EvidenceSourceType.TOOL_OBSERVATION,
        source_ref=f"s-{gid}",
        observed_at="2026-09-29T00:00:00Z",
        content_ref=f"c-{gid}",
        provenance={"capability_id": gid, "provider": "test"},
    )
    result = ToolResult(
        capability_call_id=f"call-{gid}",
        status=status,
        structured_output=copy.deepcopy(output),
        evidence_refs=(f"ev-{gid}",),
        provider="test",
    )
    return result, evidence


STATE = _observation("state", STATE_OUT)
ANALYSIS = _observation("analysis", ANALYSIS_OUT)
RESEARCH = _observation("research", _RESEARCH, ToolResultStatus.PARTIAL)


def _render(seq) -> str:
    pkg = CognitiveContextPackage(conversation_id="c", turn_id="t", generation_id="g0")
    runtime = ContextExecutionRuntime()
    for index, (result, evidence) in enumerate(seq):
        pkg = runtime.project_tool_result(
            parent_package=pkg,
            tool_result=result,
            evidence=(evidence,),
            generation_id=f"g{index + 1}",
        )
    return pkg._render_frame("evidence", pkg.evidence_frame)


def _assert_all(text: str, values) -> None:
    missing = [value for value in values if value not in text]
    assert not missing, missing


def _assert_research(text: str, *, urls: bool) -> None:
    flat = "".join(text.split())
    for finding in _RESEARCH["findings"]:
        assert "".join(finding["material"].split())[:12] in flat
    for source in _RESEARCH["sources"]:
        assert source["title"][:12] in text
        if urls:
            assert source["url"] in text


def test_analysis_latest_regime_values_are_visible():
    text = _render([ANALYSIS])

    _assert_all(text, REGIME_VALUES)
    assert "{…}" not in text  # depth-exhausted evidence items are flattened
    assert len(text) <= BUDGET


def test_state_then_research_keeps_breadth_and_sources():
    text = _render([STATE, RESEARCH])

    _assert_all(text, STATE_VALUES)
    _assert_research(text, urls=True)
    assert len(text) <= BUDGET


def test_three_tool_history_keeps_state_regime_and_research():
    text = _render([STATE, ANALYSIS, RESEARCH])

    _assert_all(text, STATE_VALUES)
    _assert_all(text, REGIME_VALUES)
    _assert_research(text, urls=False)
    assert len(text) <= BUDGET


def test_short_sibling_is_not_cut_while_long_sibling_takes_the_rest():
    pkg = CognitiveContextPackage(conversation_id="c", turn_id="t", generation_id="g")
    value = {"a_long": "x" * 5000, "b_short": "keep-me-289258.22", "c_mid": "y" * 300}

    text = pkg._render_value(value, depth=0, char_budget=1000)

    assert "b_short=keep-me-289258.22" in text
    assert "c_mid=" + "y" * 300 in text
    assert MARKER in text
    # Budget is used, not left idle while a sibling is truncated.
    assert 950 <= len(text) <= 1000


def test_flatten_on_latest_path_instead_of_collapse():
    output = {"a": {"b": {"c": {"d": {"leaf": "deep-latest-value"}, "e": [1, [2, 3]]}}}}
    text = _render([_observation("deep", output)])

    latest = text.split("\nturn_evidence_ledger: ")[0]
    assert "deep-latest-value" in latest
    assert "{…}" not in latest and "[…]" not in latest


def test_list_truncation_stays_explicit():
    text = _render([ANALYSIS])
    omitted = len(ANALYSIS_OUT["payload"]["evidence"]) - CognitiveContextPackage._RENDER_MAX_ITEMS
    assert f"{MARKER}[{omitted} more]" in text


@pytest.mark.parametrize("budget", [0, 1, 5, 13, 40, 200, 777, 3000, 9000, 16000])
def test_rendering_is_bounded_for_any_budget(budget):
    pkg = CognitiveContextPackage(conversation_id="c", turn_id="t", generation_id="g")
    for value in (ANALYSIS_OUT, STATE_OUT, _RESEARCH):
        assert len(pkg._render_value(value, depth=0, char_budget=budget)) <= budget


def test_many_tools_stay_within_frame_budget_and_fast():
    seq = [_observation(f"a{i}", ANALYSIS_OUT) for i in range(4)] + [STATE, RESEARCH]
    started = time.perf_counter()
    text = _render(seq)
    elapsed = time.perf_counter() - started

    assert len(text) <= BUDGET
    assert elapsed < 1.0
    assert MARKER in text


def test_lone_surrogate_is_still_safe_on_latest_and_historical_paths():
    hostile = copy.deepcopy(STATE_OUT)
    hostile["payload"]["\udc00key"] = "bad \ud800 value"
    hostile["deep"] = {"a": {"b": {"c": {"d": {"\ud800": "v\udc00"}}}}}
    seq = [_observation("hostile-old", hostile), _observation("hostile-new", hostile)]
    pkg = CognitiveContextPackage(conversation_id="c", turn_id="t", generation_id="g0")
    runtime = ContextExecutionRuntime()
    for index, (result, evidence) in enumerate(seq):
        pkg = runtime.project_tool_result(
            parent_package=pkg, tool_result=result, evidence=(evidence,), generation_id=f"g{index + 1}"
        )

    system_text = pkg.to_messages([], "q")[0]["content"]
    system_text.encode("utf-8")  # must not raise
    assert "\\ud800" in system_text
    _assert_all(system_text, STATE_VALUES)
