"""R2-P3.2.2A Bridge typed delivery acceptance overlay (corrected).

Protected contracts: C-08 / C-03 / P3.2.2 typed delivery design.

The typed bridge seam must deliver the exact CapabilityExecution carrier from
Manager — no flattening, no stringification, no Manager list scanning/latest
lookup. The bridge does not unpack or reconstruct ToolResult/Evidence; it
passes the carrier through untouched.

The legacy execute_tool() string path and _format_tool_result are retained
until P3.2.4 (gated by JuliaSession reachability), so formatter removal is NOT
asserted here — that belongs to the C1 bridge-fence contract.

UNKNOWN / DISABLED resolution and streaming are out of scope here.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from julia_core.capability.manager import CapabilityExecution
from julia_core.runtime.capability_bridge import RuntimeCapabilityBridge


ROOT = Path(__file__).resolve().parents[2]


def test_bridge_delivers_typed_execution_carrier_not_flattened_string():
    """Typed seam must reference the exact CapabilityExecution carrier (typed)."""
    source = (ROOT / "julia_core" / "runtime" / "capability_bridge.py").read_text()
    assert "CapabilityExecution" in source


def test_bridge_typed_seam_returns_capability_execution():
    """Behavioral: recognized capability → exact CapabilityExecution (no string)."""
    bridge = RuntimeCapabilityBridge()
    bridge.initialize()
    result = bridge.execute_tool_typed(
        '{"name": "file.read", "arguments": {"path": "README.md"}}'
    )
    assert isinstance(result, CapabilityExecution)


def test_legacy_bridge_surface_still_exists_until_p3_2_4():
    """PASS guard: legacy Bridge surface still exists until P3.2.4 cleanup.

    Guards the CapabilityBridge compatibility surface (execute_tool +
    _format_tool_result), NOT JuliaSession consumption. This must remain PASS
    both before and after P3.2.3B; P3.2.4 owns its eventual removal.
    """
    source = (ROOT / "julia_core" / "runtime" / "capability_bridge.py").read_text()
    assert "def execute_tool" in source
    assert "def _format_tool_result" in source
