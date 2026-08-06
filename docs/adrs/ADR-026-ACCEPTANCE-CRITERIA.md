# ADR-026 Acceptance Criteria — Capability Runtime v1

> **Date:** 2026-08-06
> **Status:** FROZEN
> **Parent:** ADR-026 Capability Runtime & MCP Adapter Architecture v1
> **Purpose:** Gate conditions that must pass before M0→M1 transition.

---

## AC-1: Capability Isolation

### Statement

Julia Core must never directly import external system internals.

### Pass Condition

```
❌ julia_core imports mcp_server           → BLOCKED
❌ julia_core imports ai_theme_app          → BLOCKED
❌ julia_core imports external_sdk          → BLOCKED
✅ julia_core imports mcp.client           → ALLOWED (pure transport)
✅ julia_core imports mcp.adapter          → ALLOWED (capability boundary)
✅ julia_core imports mcp.schemas          → ALLOWED (contract mirror)
```

### Verification

```bash
# Must return zero results
grep -r "from mcp_server" julia_core/ --include="*.py" | grep -v test | grep -v mcp_client/legacy
grep -r "import ai_theme_app" julia_core/ --include="*.py"
```

---

## AC-2: Provider Swap

### Statement

The same capability (`market.snapshot.read`) can be served by different providers without changing Reasoning or Context OS.

### Pass Condition

```
market.snapshot.read → ai_theme_app MCP     → DecisionEnvelope → ContextBlock → Reasoning
market.snapshot.read → mock_provider         → DecisionEnvelope → ContextBlock → Reasoning
market.snapshot.read → future_api_provider   → DecisionEnvelope → ContextBlock → Reasoning
```

All three paths produce the same ContextBlock structure. The Reasoning layer cannot tell which provider was used.

### Verification

```python
# Mock provider test
async def test_provider_swap():
    registry = CapabilityRegistry()
    policy = CapabilityPermissionPolicy()

    # Register same capability with mock adapter
    mock = MockAdapter("market.snapshot.read", return_value=mock_snapshot)
    manager = CapabilityManager(registry, policy, {"mock": mock})

    result1 = await manager.resolve(CapabilityRequest("market.snapshot.read"))
    assert result1.status == "success"

    # Swap to real MCP adapter (offline → health check fails → graceful)
    mcp = MCPAdapter(MCPClient("http://localhost:9999"), mapping)
    manager.adapters["mcp"] = mcp
    result2 = await manager.resolve(CapabilityRequest("market.snapshot.read"))
    assert result2.status == "unavailable"  # not "error"
```

---

## AC-3: Permission Enforcement

### Statement

CapabilityPermissionPolicy must block denied scopes before any adapter is called.

### Pass Condition

```
market.observe    → CapabilityManager.resolve() → ALLOW   → MCP Adapter called
trade.execute     → CapabilityManager.resolve() → DENY    → MCP Adapter NOT called
file.write        → CapabilityManager.resolve() → CONFIRM → requires user confirmation
memory.delete     → CapabilityManager.resolve() → DENY    → requires Tony explicit action
```

### Verification

```python
async def test_permission_enforcement():
    policy = CapabilityPermissionPolicy(rules={
        "market.observe": PermissionRule(allow=True),
        "market.trade.execute": PermissionRule(allow=False),
    })

    # Allowed
    allowed, reason = policy.check("market.observe")
    assert allowed

    # Denied
    allowed, reason = policy.check("market.trade.execute")
    assert not allowed
    assert "denied" in reason.lower()

    # Adapter not called on deny
    adapter = SpyAdapter()
    manager = CapabilityManager(registry, policy, {"mcp": adapter})
    result = await manager.resolve(CapabilityRequest("market.trade.execute"))
    assert result.status == "denied"
    assert adapter.call_count == 0  # never reached
```

---

## AC-4: Evidence Trace

### Statement

Every capability invocation must produce an auditable evidence record.

### Pass Condition

```
Capability Request → Execute → Evidence Entry:
  {
    capability_id: "market.snapshot.read",
    provider: "ai_theme_app_mcp",
    timestamp: "2026-08-06T08:30:00+08:00",
    input: {"date": "2026-08-06"},
    output_schema: "MarketSnapshot",
    status: "success",
    duration_ms: 245
  }
```

This evidence record enters the Evidence Ledger (`runtime/capability.py:EvidenceLedger`) and is traceable from Julia's response back to the capability call.

### Verification

```python
async def test_evidence_trace():
    manager = CapabilityManager(registry, policy, adapters)
    evidence = EvidenceLedger()

    result = await manager.resolve(
        CapabilityRequest("market.snapshot.read"),
        evidence=evidence
    )

    entry = evidence.last()
    assert entry is not None
    assert entry.tool == "market.snapshot.read"
    assert entry.status == "success"
    assert "provider" in entry.details
    assert "timestamp" in entry.details
    assert "output_schema" in entry.details
```

---

## AC-5: Graceful Degradation

### Statement

When an external provider is unavailable, Julia must report it gracefully, not crash or hallucinate.

### Pass Condition

```
MCP Server offline → CapabilityManager.resolve() → status: "unavailable"
  → Julia: "暂时无法获取市场数据，请稍后再试。"
  → NOT: silent error / crash / fabricated data
```

### Verification

```python
async def test_graceful_degradation():
    # Point to non-existent server
    mcp = MCPAdapter(MCPClient("http://localhost:9999"), mapping)
    manager = CapabilityManager(registry, policy, {"mcp": mcp})

    result = await manager.resolve(CapabilityRequest("market.snapshot.read"))
    assert result.status == "unavailable"
    assert result.error_message is not None
    # Context OS receives unavailable → Julia generates graceful response
```

---

## Gate Checklist (M0 → M1)

- [ ] AC-1: Zero direct imports of external system internals
- [ ] AC-2: Mock provider swap produces identical ContextBlock structure
- [ ] AC-3: Denied scopes blocked before adapter call
- [ ] AC-4: All invocations produce evidence entries
- [ ] AC-5: Unavailable provider → graceful degradation, not crash
- [ ] All 5 ACs pass in CI before M1 migration begins
