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
