"""R2-P3.2.0 Bridge typed delivery acceptance overlay.

Protected contracts: C-08 / C-03 / P3.2 typed delivery design.

P3.2.2 will make the bridge deliver the exact typed execution carrier
(AuthorizationDecision / CapabilityCall / ToolResult / Evidence) to Context OS
instead of flattening execution results into a fenced prompt string.

UNKNOWN / DISABLED resolution and streaming are out of scope here.
"""

from __future__ import annotations

from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.xfail(
    strict=True,
    reason="R2-P3.2: bridge must deliver typed execution carrier, not flattened text",
)
def test_bridge_delivers_typed_execution_carrier_not_flattened_string():
    source = (ROOT / "julia_core" / "runtime" / "capability_bridge.py").read_text()
    assert "_format_tool_result" not in source
    assert "```tool_result" not in source
    # The bridge must reference the canonical typed artifacts (ToolResult /
    # Evidence) rather than stringify them into a prompt fence.
    assert "ToolResult" in source
    assert "Evidence" in source
