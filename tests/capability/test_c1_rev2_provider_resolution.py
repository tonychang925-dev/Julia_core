"""C1-R2.4 Provider resolution gate tests.

Protected contracts: C-08 / REV2 R2-I03/R2-I04/R2-I11
Expected baseline: XFAIL for confirmed local provider mapping defect; PASS for
explicit unavailable/no-fallback semantics already present in CapabilityManager.
Known gaps: B-P0 provider mapping defect from conformance audit
Resolving phase: R2-P3

TC-ID: C1-R2.4-PROVIDER-001 local provider mapping correctness
TC-ID: C1-R2.4-PROVIDER-002 unresolved providers fail closed as unavailable
TC-ID: C1-R2.4-PROVIDER-003 no implicit provider fallback
TC-ID: C1-R2.4-PROVIDER-004 provider mapping cannot be released without filesystem security gate

These tests intentionally keep local-provider reachability coupled to filesystem
canonical authorization. Fixing provider mapping alone must not satisfy the local
provider release gate.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from julia_core.capability.manager import CapabilityManager
from julia_core.capability.models import CapabilityDefinition, CapabilityLayer, CapabilityRequest, CapabilityStatus
from julia_core.capability.policy import PermissionPolicy
from julia_core.capability.registry import CapabilityRegistry
from julia_core.runtime.capability_bridge import RuntimeCapabilityBridge


ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.xfail(
    strict=True,
    reason="B-P0/C-08: local definitions use provider='local' but manager receives local_file_read/local_file_search/local_directory_list; pending R2-P3",
)
@pytest.mark.asyncio
async def test_runtime_bridge_resolves_enabled_file_read_to_local_provider():
    """TC-ID: C1-R2.4-PROVIDER-001. Enabled local capability must resolve uniquely."""
    bridge = RuntimeCapabilityBridge()
    bridge.initialize()

    target = ROOT / "README.md"
    result = await bridge.manager.execute(CapabilityRequest("file.read", {"path": str(target)}))

    assert result.status == "success"
    assert result.provider == "local"
    assert "content" in result.data


@pytest.mark.xfail(
    strict=True,
    reason="B-P0/C-08: current flattened providers are capability-specific keys, not provider namespace records; pending R2-P3",
)
def test_runtime_bridge_local_provider_namespace_is_registered_for_manager_lookup():
    """TC-ID: C1-R2.4-PROVIDER-001. provider='local' must exist as manager lookup key."""
    bridge = RuntimeCapabilityBridge()
    bridge.initialize()

    definition = bridge.registry.get("file.read")
    assert definition is not None
    assert definition.provider == "local"
    assert "local" in bridge.manager.providers


@pytest.mark.asyncio
async def test_unresolved_provider_returns_unavailable_not_wrong_provider_success():
    """TC-ID: C1-R2.4-PROVIDER-002. Missing provider fails closed as unavailable."""
    registry = CapabilityRegistry()
    registry.register_definition(CapabilityDefinition(
        name="file.read",
        description="Read local file",
        layer=CapabilityLayer.KNOWLEDGE,
        provider="missing_local",
        permission_scope="file.read",
        status=CapabilityStatus.AVAILABLE,
    ))
    manager = CapabilityManager(registry, PermissionPolicy.with_defaults(), providers={})

    result = await manager.execute(CapabilityRequest("file.read", {"path": str(ROOT / "README.md")}))

    assert result.status == "unavailable"
    assert result.provider == "missing_local"
    assert "No provider 'missing_local' registered" in result.error_message


@pytest.mark.asyncio
async def test_provider_resolution_does_not_fallback_to_unrelated_provider():
    """TC-ID: C1-R2.4-PROVIDER-003. Provider lookup must be exact; no implicit fallback."""

    class WrongProvider:
        called = False

        async def health(self):
            return True, "wrong provider available"

        async def execute(self, request):  # pragma: no cover - must not be called
            self.called = True
            return {"status": "success", "content": "wrong-provider-data"}

    wrong = WrongProvider()
    registry = CapabilityRegistry()
    registry.register_definition(CapabilityDefinition(
        name="file.read",
        description="Read local file",
        layer=CapabilityLayer.KNOWLEDGE,
        provider="local",
        permission_scope="file.read",
        status=CapabilityStatus.AVAILABLE,
    ))
    manager = CapabilityManager(
        registry,
        PermissionPolicy.with_defaults(),
        providers={"local_file_read": wrong},
    )

    result = await manager.execute(CapabilityRequest("file.read", {"path": str(ROOT / "README.md")}))

    assert result.status == "unavailable"
    assert wrong.called is False


def test_local_provider_release_gate_requires_filesystem_security_contract_file():
    """TC-ID: C1-R2.4-PROVIDER-004. Mapping fix and filesystem security are one release gate."""
    security_test = ROOT / "tests" / "capability" / "test_c1_rev2_filesystem_security.py"
    assert security_test.exists()
    source = security_test.read_text()
    required_terms = {
        "canonical",
        "traversal",
        "symlink",
        "Desktop_evil",
        "file.list",
        "file.search",
    }
    assert all(term in source for term in required_terms)
