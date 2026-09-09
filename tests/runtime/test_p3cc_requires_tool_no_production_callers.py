"""P3-CC I2-A — requires_tool(user_text) semantic retirement gate.

RuntimeCapabilityBridge.requires_tool remains code-present for legacy
compatibility, but its production caller count must be zero and no session
control-flow may consult user-text keywords to decide capability need.
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _ast_call_targets(source: str, attr: str) -> list[int]:
    tree = ast.parse(source)
    lines = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == attr
        ):
            lines.append(node.lineno)
    return lines


def test_requires_tool_has_zero_production_callers():
    bridge_source = (ROOT / "julia_core" / "runtime" / "capability_bridge.py").read_text()
    session_source = (ROOT / "julia_core" / "runtime" / "julia_session.py").read_text()

    # Definition exists (legacy surface kept) ...
    tree = ast.parse(bridge_source)
    method_lines = [
        n.lineno for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        and n.name == "requires_tool"
    ]
    assert method_lines, "requires_tool definition missing"

    # ... but no production caller invokes requires_tool(...) anywhere.

    # Scan all production modules under julia_core/ for `.requires_tool(` calls.
    total = 0
    for path in sorted((ROOT / "julia_core").rglob("*.py")):
        if path.name.startswith("__"):
            continue
        try:
            source = path.read_text()
        except Exception:
            continue
        total += len(_ast_call_targets(source, "requires_tool"))
    assert total == 0, f"production requires_tool call sites: {total}"

    # And JuliaSession never calls it.
    assert ".requires_tool(" not in session_source or "requires_tool(text)" not in session_source


def test_no_user_text_semantic_gate_replacement_in_session():
    session_source = (ROOT / "julia_core" / "runtime" / "julia_session.py").read_text()
    for renamed_gate in (
        "requires_research(",
        "should_use_capability(",
        "needs_external_evidence(",
        "intent_router(",
        "semantic_gate(",
    ):
        assert renamed_gate not in session_source, renamed_gate


# ── P3-CC I2-B: legacy pre-cognitive Market router caller inventory ──────────
# AST-based proof that the retired semantic routers keep ZERO production
# authority after the cutover. Only the fenced Context OS compatibility seam
# (_resolve_market_context → "") remains callable.

def _production_py_files():
    return sorted((ROOT / "julia_core").rglob("*.py"))


def _attribute_calls(attr: str) -> list[tuple[str, int, str]]:
    """Return (relative_path, lineno, receiver_source) for every `.attr(...)`
    call in production julia_core source."""
    found: list[tuple[str, int, str]] = []
    for path in _production_py_files():
        if path.name.startswith("__"):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == attr
                and isinstance(node.func.value, ast.AST)
            ):
                receiver = ast.unparse(node.func.value)
                found.append((str(path.relative_to(ROOT)), node.lineno, receiver))
    return found


def _method_names(path: str, class_name: str) -> set[str]:
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {
                item.name
                for item in node.body
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
    return set()


def test_is_market_intent_deleted_and_zero_production_calls():
    names = _method_names("julia_core/runtime/julia_session.py", "JuliaSession")
    assert "_is_market_intent" not in names
    calls = _attribute_calls("_is_market_intent")
    assert calls == []


def test_build_research_desk_resolver_call_absent():
    names = _method_names("julia_core/runtime/julia_session.py", "JuliaSession")
    assert "_build_research_desk_resolver_call" not in names
    calls = _attribute_calls("_build_research_desk_resolver_call")
    assert calls == []


def test_workflow_router_route_zero_production_callers():
    # JuliaSession must never invoke `workflow_router.route(...)`.
    calls = [
        (path, lineno, receiver)
        for (path, lineno, receiver) in _attribute_calls("route")
        if "workflow_router" in receiver
    ]
    assert calls == []
    # JuliaSession may still construct the legacy router (frozen C1-R2.9
    # reachability contract), but construction is not semantic authority.


def test_market_brief_intent_resolver_legacy_only_callers():
    # `.resolve(` on a MarketBriefIntentResolver instance may only occur inside
    # the retired legacy cluster (WorkflowRouter / MarketBriefPipeline) whose
    # own production callers are zero (proved above for route(), and by
    # test_resolve_market_intent_legacy_only_callers below).
    calls = [
        (path, lineno, receiver)
        for (path, lineno, receiver) in _attribute_calls("resolve")
        if "_market_resolver" in receiver or "intent_resolver" in receiver
    ]
    allowed = {
        "julia_core/runtime/workflow_router.py",
        "julia_core/reasoning/market_brief_pipeline.py",
    }
    assert {path for path, _, _ in calls} <= allowed, calls


def test_to_capability_request_legacy_only_callers():
    # IntentResult → CapabilityRequest conversion may only occur inside the
    # retired legacy pipeline — never on the Julia cognition production path.
    calls = _attribute_calls("to_capability_request")
    assert {path for path, _, _ in calls} <= {
        "julia_core/reasoning/market_brief_pipeline.py"
    }


def test_resolve_market_intent_legacy_only_callers():
    # bridge.resolve_market_intent(...) may only be reached from the retired
    # WorkflowRouter — zero Julia cognition callers.
    calls = _attribute_calls("resolve_market_intent")
    assert {path for path, _, _ in calls} <= {
        "julia_core/runtime/workflow_router.py"
    }


def test_resolve_market_context_seam_is_the_only_production_caller_and_empty():
    # The Context OS compatibility seam is the ONLY production caller, and the
    # seam body is `return ""` (non-semantic / non-executing / non-prefetching).
    calls = _attribute_calls("_resolve_market_context")
    assert calls == [("julia_core/runtime/context_execution_runtime.py", 604, "self._js")]
    tree = ast.parse(
        (ROOT / "julia_core" / "runtime" / "julia_session.py").read_text(encoding="utf-8")
    )
    seam = None
    for node in ast.walk(tree):
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "_resolve_market_context"
        ):
            seam = node
    assert seam is not None
    returns = [n for n in ast.walk(seam) if isinstance(n, ast.Return)]
    assert len(returns) == 1
    assert isinstance(returns[0].value, ast.Constant) and returns[0].value.value == ""


def test_no_renamed_precognitive_market_gate_replacement_in_session():
    session_source = (ROOT / "julia_core" / "runtime" / "julia_session.py").read_text()
    for renamed_gate in (
        "_should_prefetch_market(",
        "_is_market_related(",
        "_needs_market_context(",
        "_market_semantic_gate(",
        "_resolve_market_intent(",
    ):
        assert renamed_gate not in session_source, renamed_gate
