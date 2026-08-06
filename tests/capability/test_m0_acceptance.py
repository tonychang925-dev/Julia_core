"""M0 Acceptance Tests — Capability Runtime Kernel v1.

ADR-026 AC-1 through AC-5: gate conditions that must pass before M0→M1.

Run:
  python -m pytest tests/capability/test_m0_acceptance.py -v
"""

import asyncio
import pytest

from julia_core.capability.models import (
    CapabilityDefinition,
    CapabilityLayer,
    CapabilityRequest,
    CapabilityStatus,
)
from julia_core.capability.policy import PermissionPolicy, PermissionRule
from julia_core.capability.providers import MockTimeProvider, MockDenyProvider
from julia_core.capability.registry import CapabilityRegistry
from julia_core.capability.manager import CapabilityManager


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def registry():
    r = CapabilityRegistry()
    r.register_definition(CapabilityDefinition(
        name="system.time.read",
        description="Read current system time",
        layer=CapabilityLayer.WORLD,
        provider="mock_time",
        permission_scope="system.read",
        status=CapabilityStatus.AVAILABLE,
    ))
    r.register_definition(CapabilityDefinition(
        name="market.snapshot.read",
        description="Read today's market overview",
        layer=CapabilityLayer.INTELLIGENCE,
        provider="market_mock",
        permission_scope="market.observe",
        status=CapabilityStatus.AVAILABLE,
    ))
    r.register_definition(CapabilityDefinition(
        name="trade.execute",
        description="Execute a trade order",
        layer=CapabilityLayer.INTELLIGENCE,
        provider="market_mock",
        permission_scope="market.trade.execute",
        status=CapabilityStatus.AVAILABLE,
    ))
    return r


@pytest.fixture
def policy():
    return PermissionPolicy.with_defaults()


@pytest.fixture
def providers():
    return {
        "mock_time": MockTimeProvider(simulated_time="2026-08-06T10:00:00+08:00"),
        "mock_deny": MockDenyProvider(),
    }


@pytest.fixture
def manager(registry, policy, providers):
    return CapabilityManager(registry, policy, providers)


# ── AC-1: Registry Lookup ────────────────────────────────────────────────────

def test_registry_register_and_lookup(registry):
    """Register a capability, then look it up."""
    definition = registry.get("system.time.read")
    assert definition is not None
    assert definition.name == "system.time.read"
    assert definition.layer == CapabilityLayer.WORLD
    assert definition.provider == "mock_time"


def test_registry_list_all(registry):
    """List all registered definitions."""
    definitions = registry.all()
    assert len(definitions) >= 3
    names = {d.name for d in definitions}
    assert "system.time.read" in names
    assert "market.snapshot.read" in names
    assert "trade.execute" in names


def test_registry_by_layer(registry):
    """Filter definitions by layer."""
    world = registry.by_layer(CapabilityLayer.WORLD)
    assert len(world) >= 1
    assert all(d.layer == CapabilityLayer.WORLD for d in world)

    intelligence = registry.by_layer(CapabilityLayer.INTELLIGENCE)
    assert len(intelligence) >= 2
    assert all(d.layer == CapabilityLayer.INTELLIGENCE for d in intelligence)


def test_registry_unknown_returns_none(registry):
    """Unknown capability returns None."""
    assert registry.get("does.not.exist") is None


# ── AC-2: Permission Policy ──────────────────────────────────────────────────

def test_permission_allow_system_read(policy):
    """system.read is allowed."""
    allowed, reason = policy.check("system.read")
    assert allowed
    assert "read-only" in reason


def test_permission_deny_trade_execute(policy):
    """trade.execute is denied."""
    allowed, reason = policy.check("market.trade.execute")
    assert not allowed
    assert "never trades" in reason


def test_permission_unknown_scope_denied(policy):
    """Unknown scopes default to deny."""
    allowed, reason = policy.check("nuclear.launch")
    assert not allowed
    assert "unknown scope" in reason


def test_permission_custom_rule(policy):
    """Custom rules can be added."""
    policy.add_rule(PermissionRule("custom.scope", allow=True, reason="test"))
    allowed, _ = policy.check("custom.scope")
    assert allowed


# ── AC-3: Provider Routing ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_manager_routes_to_mock_time(manager):
    """system.time.read routes to MockTimeProvider."""
    result = await manager.execute(CapabilityRequest("system.time.read"))
    assert result.status == "success"
    assert result.data["time"] == "2026-08-06T10:00:00+08:00"
    assert result.data["source"] == "mock_time_provider"
    assert result.provider == "mock_time"


@pytest.mark.asyncio
async def test_manager_denies_trade_execute(manager):
    """trade.execute is blocked by permission policy before any provider call."""
    result = await manager.execute(CapabilityRequest("trade.execute"))
    assert result.status == "denied"
    assert "never trades" in result.error_message


@pytest.mark.asyncio
async def test_manager_unknown_capability(manager):
    """Unknown capability returns 'unknown' status."""
    result = await manager.execute(CapabilityRequest("does.not.exist"))
    assert result.status == "unknown"


@pytest.mark.asyncio
async def test_manager_permission_blocks_before_provider_call(registry, policy):
    """Denied capability never reaches the provider (AC-3 verification)."""
    providers = {"mock_deny": MockDenyProvider()}

    registry.register_definition(CapabilityDefinition(
        name="blocked.capability",
        description="Should never execute",
        layer=CapabilityLayer.WORLD,
        provider="mock_deny",
        permission_scope="market.trade.execute",  # denied scope
        status=CapabilityStatus.AVAILABLE,
    ))

    mgr = CapabilityManager(registry, policy, providers)
    result = await mgr.execute(CapabilityRequest("blocked.capability"))

    assert result.status == "denied"
    # Evidence shows denied — no provider was called
    last = mgr.evidence.last()
    assert last is not None
    assert last.status == "denied"


# ── AC-4: Evidence Trace ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_evidence_recorded_on_success(manager):
    """Successful invocation records evidence."""
    await manager.execute(CapabilityRequest("system.time.read"))
    last = manager.evidence.last()
    assert last is not None
    assert last.capability_name == "system.time.read"
    assert last.provider == "mock_time"
    assert last.status == "success"
    assert last.timestamp != ""


@pytest.mark.asyncio
async def test_evidence_recorded_on_deny(manager):
    """Denied invocation records evidence (with denied status)."""
    await manager.execute(CapabilityRequest("trade.execute"))
    assert manager.evidence.count >= 1
    # Find the denied entry
    denied = [e for e in manager.evidence.entries if e.status == "denied"]
    assert len(denied) >= 1


@pytest.mark.asyncio
async def test_evidence_multiple_calls(manager):
    """Multiple calls produce multiple evidence entries."""
    await manager.execute(CapabilityRequest("system.time.read"))
    await manager.execute(CapabilityRequest("system.time.read"))
    assert manager.evidence.count >= 2


# ── AC-5: Isolation — no new mcp_server imports ──────────────────────────────

def test_no_mcp_server_import():
    """AC-1: Julia Core must not directly import external system internals.

    This test scans the new M0 modules for any mcp_server import.
    The old mcp_client/ path is exempt (marked legacy).
    """
    import ast
    from pathlib import Path

    julia_core_dir = Path(__file__).resolve().parent.parent.parent / "julia_core"

    # Modules created or modified in M0
    m0_modules = [
        julia_core_dir / "capability" / "models.py",
        julia_core_dir / "capability" / "manager.py",
        julia_core_dir / "capability" / "policy.py",
        julia_core_dir / "capability" / "providers" / "__init__.py",
    ]

    for module_path in m0_modules:
        if not module_path.exists():
            continue
        source = module_path.read_text()
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "mcp_server" not in alias.name, (
                        f"{module_path.name}: imports 'mcp_server' — "
                        f"violates AC-1 Capability Isolation"
                    )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    assert "mcp_server" not in node.module, (
                        f"{module_path.name}: imports from 'mcp_server' — "
                        f"violates AC-1 Capability Isolation"
                    )


def test_no_ai_theme_app_import():
    """AC-1: Julia Core must not import ai_theme_app internals."""
    import ast
    from pathlib import Path

    julia_core_dir = Path(__file__).resolve().parent.parent.parent / "julia_core"
    m0_modules = [
        julia_core_dir / "capability" / "models.py",
        julia_core_dir / "capability" / "manager.py",
        julia_core_dir / "capability" / "policy.py",
        julia_core_dir / "capability" / "providers" / "__init__.py",
    ]

    for module_path in m0_modules:
        if not module_path.exists():
            continue
        source = module_path.read_text()
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "ai_theme_app" not in alias.name, (
                        f"{module_path.name}: imports 'ai_theme_app' — "
                        f"violates AC-1 Capability Isolation"
                    )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    assert "ai_theme_app" not in node.module, (
                        f"{module_path.name}: imports from 'ai_theme_app' — "
                        f"violates AC-1 Capability Isolation"
                    )


# ── Bonus: Graceful Degradation ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_graceful_degradation_unavailable_provider(registry, policy):
    """AC-5: When provider is unavailable, Julia gets 'unavailable' not 'error'."""
    registry.register_definition(CapabilityDefinition(
        name="market.snapshot.read",
        description="Read today's market overview",
        layer=CapabilityLayer.INTELLIGENCE,
        provider="offline_mcp",
        permission_scope="market.observe",
        status=CapabilityStatus.AVAILABLE,
    ))

    # Provider not registered → unavailable
    mgr = CapabilityManager(registry, policy, {"mock_time": MockTimeProvider()})
    result = await mgr.execute(CapabilityRequest("market.snapshot.read"))

    assert result.status == "unavailable"
    assert "offline_mcp" in result.provider or "offline_mcp" in result.error_message


@pytest.mark.asyncio
async def test_disabled_capability_returns_denied(registry, policy, providers):
    """DISABLED capability returns denied even if permission allows it."""
    registry.register_definition(CapabilityDefinition(
        name="disabled.feature",
        description="A disabled capability",
        layer=CapabilityLayer.WORLD,
        provider="mock_time",
        permission_scope="system.read",
        status=CapabilityStatus.DISABLED,
    ))

    mgr = CapabilityManager(registry, policy, providers)
    result = await mgr.execute(CapabilityRequest("disabled.feature"))

    assert result.status == "denied"
    assert "DISABLED" in result.error_message
