# ADR-026: Julia Capability Runtime & MCP Adapter Architecture v1

**Date:** 2026-08-06
**Status:** PROPOSED → FROZEN
**Supersedes:** None (new capability operating layer)

---

## Summary

Julia Core Runtime owns identity, memory, reasoning, and decision. But it currently has no unified Capability Operating Layer. External systems (ai_theme_app MCP Server, voice, filesystem, calendar, future IoT) each form their own integration path, creating ad-hoc channels that bypass the Runtime Authority.

This ADR establishes:
1. **CapabilityRegistry** — what Julia CAN do (exists, needs extension)
2. **CapabilityManager** — what Julia SHOULD do for a given request (new, missing)
3. **CapabilityPermissionPolicy** — what Julia is ALLOWED to do (new)
4. **MCP Adapter** — transforms external MCP servers into Julia Capabilities (new, replaces direct mcp_client imports)

The Capability Operating Layer is the unified external-world interface for Julia OS. Voice, MCP, filesystem, calendar, GitHub, email, IoT — all connect through this single layer.

---

## 1. Problem Statement

### 1.1 Current State (Audit Findings)

**Two parallel execution paths exist:**

```
Path A (correct):
  JuliaSession → provider.chat() → tool_call → capability.execute()

Path B (boundary violation):
  MarketBrainClient → direct import from mcp_server.server → tool function
```

Path B violates JULIA_CORE_PRINCIPLES.md Principle 4: "Provider supplies capability, not cognition." The MarketBrainClient simultaneously serves as MCP transport, tool registry, tool executor, and schema mapper — it is not a Capability, it is four concerns collapsed into one.

### 1.2 Root Cause

The CapabilityLayer exists (`capability/registry.py`, `capability/tool_protocol.py`), but:

- **No CapabilityManager** — Registry answers "what exists?" but nobody answers "what should be called for this request?"
- **No MCP Adapter** — MCP tools are exposed raw, not adapted into Julia's cognitive interface
- **No CapabilityPermissionPolicy** — File permissions exist, but no generalized capability-level permissions
- **No INTELLIGENCE layer** — CapabilityLayer enum has PERCEPTION, KNOWLEDGE, MEMORY, WORLD, ACTION — but nothing for external intelligence domains

### 1.3 Why This Matters Beyond MCP

Voice Runtime, Runtime Gateway, and MCP are not three separate problems. They are all **Capability Boundary Design**:

| Provider Type | Example | Capability |
|---|---|---|
| Client Capability | Voice I/O | `voice.speak`, `voice.listen` |
| Local Capability | Filesystem | `file.read`, `file.search` |
| External Intelligence | ai_theme_app | `market.snapshot.read` |
| Future Device | Robot body | `body.move`, `body.express` |

Without a unified Capability Operating Layer, each new provider type adds another ad-hoc channel. The Capability Layer is the missing kernel of Julia OS.

---

## 2. Architecture

### 2.1 Target State

```
                     Julia Runtime
                          |
                   CapabilityManager
                   (request → route)
                          |
                   CapabilityRegistry
                   (what exists)
                          |
              +-----------+-----------+
              |                       |
       Local Capability        External Capability
       (filesystem,             (ai_theme_app,
        voice, memory)           calendar, github)
              |                       |
              |                 MCP Adapter
              |                 (tool → capability)
              |                       |
              |                 MCP Client
              |                 (transport only)
              |                       |
              +-----------+-----------+
                          |
                    External World
```

### 2.2 Request Flow

```
Tony: "Julia, today's market?"

Step 1 — LLM/Reasoning produces:
  action.request { capability: "market.snapshot.read" }

Step 2 — CapabilityManager:
  1. Registry lookup: market.snapshot.read → provider=ai_theme_app_mcp
  2. Permission check: market.observe → allowed=true
  3. Provider health: ai_theme_app MCP → online
  4. Route: → MCP Adapter

Step 3 — MCP Adapter:
  Maps: market.snapshot.read → review_market_snapshot()
  Calls: MCP Client → ai_theme_app MCP Server

Step 4 — MCP Client:
  Pure transport: HTTP → MCP protocol → JSON response
  No knowledge of "market" semantics

Step 5 — Response flows back through CapabilityManager → ContextBlock → Context OS → Julia Reasoning
```

### 2.3 Directory Structure

```
julia_core/
  capability/
    __init__.py
    registry.py          # CapabilityRegistry (extend)
    manager.py           # CapabilityManager (NEW)
    policy.py            # CapabilityPermissionPolicy (NEW)
    models.py            # Capability, CapabilityRequest, CapabilityResult (NEW)
    tool_protocol.py     # ToolSchema, ToolRegistry (existing)
    ...

  mcp/
    __init__.py
    client.py            # MCPClient — pure transport (NEW, extract from mcp_client/)
    adapter.py           # MCPAdapter — tool → capability mapping (NEW)
    schemas/
      __init__.py
      common.py          # MCP protocol types (NEW)
      market.py          # ai_theme_app capability definitions (NEW)

  mcp_client/            # Legacy — deprecated, replaced by mcp/ above
    __init__.py          # Keep for M0-M1 backward compat
    client.py
    models.py

  runtime/
    capability_runtime.py  # CapabilityRuntime (existing, extend with manager + policy)
    ...
```

---

## 3. Capability Layer Design

### 3.1 CapabilityLayer — Add INTELLIGENCE

```python
class CapabilityLayer(str, Enum):
    PERCEPTION    = "perception"     # voice, vision
    KNOWLEDGE     = "knowledge"      # files, search
    MEMORY        = "memory"         # diary, long-term
    WORLD         = "world"          # weather, time, web
    INTELLIGENCE  = "intelligence"   # market, news, analysis (NEW)
    ACTION        = "action"         # write, execute
```

Not `MARKET` — `INTELLIGENCE`. Because calendar analytics, GitHub insights, news sentiment, IoT sensor analysis all belong here. The layer describes what kind of capability it is, not which domain it serves.

### 3.2 Capability Model

```python
@dataclass
class Capability:
    """A capability Julia can invoke — external-world interface."""
    name: str                    # "market.snapshot.read"
    description: str             # "Read today's market overview"
    layer: CapabilityLayer
    provider: str                # "ai_theme_app_mcp" | "local_filesystem" | "voice_os"
    permission_scope: str        # "market.observe"
    input_schema: dict[str, str]
    handler: Callable | None     # None for external (routed through adapter)
    adapter: str | None          # "mcp" | "http" | None for local
    example: str
```

### 3.3 CapabilityRegistry (Extend)

Existing `capability/registry.py` works but needs:
- `provider` field on capabilities
- `adapter` routing tag
- `permission_scope` binding

### 3.4 CapabilityManager (NEW)

```python
class CapabilityManager:
    """Request → Capability resolution with policy enforcement."""

    def __init__(self, registry, policy, adapters):
        ...

    async def resolve(self, request: CapabilityRequest) -> CapabilityResult:
        """Resolve a capability request to execution."""
        # 1. Lookup in registry
        cap = self.registry.get(request.name)
        if not cap:
            return CapabilityResult.unknown(request.name)

        # 2. Permission check
        allowed, reason = self.policy.check(cap.permission_scope)
        if not allowed:
            return CapabilityResult.denied(request.name, reason)

        # 3. Provider health
        if cap.adapter:
            adapter = self.adapters.get(cap.adapter)
            if not adapter or not await adapter.health():
                return CapabilityResult.unavailable(request.name, cap.provider)

        # 4. Route
        if cap.adapter == "mcp":
            result = await self.adapters["mcp"].execute(cap, request.arguments)
        elif cap.handler:
            result = cap.handler(**request.arguments)
        else:
            return CapabilityResult.error(request.name, "no handler or adapter")

        return CapabilityResult.success(request.name, result)
```

---

## 4. Permission Policy

### 4.1 CapabilityPermissionPolicy

```python
@dataclass
class CapabilityPermissionPolicy:
    """Controls what capabilities Julia can invoke."""

    rules: dict[str, PermissionRule]

    def check(self, scope: str) -> tuple[bool, str]:
        ...

class PermissionRule:
    scope: str           # "market.observe"
    allow: bool
    require_confirmation: bool = False
    rate_limit: str | None = None  # "10/hour"
```

### 4.2 Default Rules

| Scope | Allow | Confirm | Reason |
|-------|-------|---------|--------|
| `market.observe` | true | false | Read-only market data |
| `market.trade.execute` | false | — | Julia never trades |
| `file.read` | true | false | Within allowed paths |
| `file.write` | true | true | Confirmation required |
| `memory.delete` | false | — | Requires Tony explicit action |
| `calendar.read` | true | false | Read-only |
| `calendar.write` | false | — | Future: with confirmation |
| `email.send` | false | — | Future: requires confirmation |

---

## 5. MCP Adapter

### 5.1 MCPClient — Pure Transport

`mcp/client.py` responsibilities (and ONLY these):
- MCP session lifecycle (initialize, heartbeat, close)
- Tool call request/response serialization
- Error handling (timeout, connection refused, protocol error)
- Health check

`mcp/client.py` must NOT know:
- What `market.snapshot.read` means
- What `DecisionEnvelope` is
- How to map tool names to capability names

```python
class MCPClient:
    """Pure MCP transport. No domain knowledge."""

    def __init__(self, server_endpoint: str):
        self.endpoint = server_endpoint

    async def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """Raw MCP tool call. Returns parsed JSON response."""
        ...

    async def list_tools(self) -> list[dict]:
        """Discover available tools on the server."""
        ...

    async def health(self) -> bool:
        """Check if MCP server is reachable."""
        ...
```

### 5.2 MCPAdapter — Tool → Capability

`mcp/adapter.py` owns the mapping between Julia capabilities and MCP tools:

```python
class MCPAdapter:
    """Adapts external MCP servers into Julia Capabilities.

    Owns the mapping: Julia capability name → MCP tool name.
    Julia thinks in capabilities. MCP speaks in tools.
    The adapter translates.
    """

    def __init__(self, client: MCPClient, mapping: dict[str, str]):
        self.client = client
        self.mapping = mapping  # capability → tool_name

    async def execute(self, capability: Capability, arguments: dict) -> dict:
        tool_name = self.mapping[capability.name]
        raw = await self.client.call_tool(tool_name, arguments)
        return self._validate_schema(raw, capability.name)

    async def health(self) -> bool:
        return await self.client.health()
```

### 5.3 ai_theme_app Capability Mapping

`mcp/schemas/market.py`:

```python
AI_THEME_APP_CAPABILITIES = {
    "market.snapshot.read": {
        "tool": "review_market_snapshot",
        "description": "Read today's market overview — sentiment, active themes, top signals, risk alerts",
        "permission_scope": "market.observe",
        "schema_version": "1.1",
    },
    "market.alert.query": {
        "tool": "list_active_alerts",
        "description": "Query active market alerts at or above a given level",
        "permission_scope": "market.observe",
        "schema_version": "1.1",
    },
    "market.decision.explain": {
        "tool": "explain_decision",
        "description": "Get structured explanation for a market decision — causal chain, evidence, risks",
        "permission_scope": "market.observe",
        "schema_version": "1.1",
    },
    "market.theme.observe": {
        "tool": "query_theme_status",
        "description": "Observe a theme's current lifecycle, heat, leaders, and causal context",
        "permission_scope": "market.observe",
        "schema_version": "1.1",
    },
    "market.event.subscribe": {
        "tool": "subscribe_agent_channel",
        "description": "Subscribe to market observation channels by domain",
        "permission_scope": "market.observe",
        "schema_version": "1.1",
    },
}
```

These are Julia's **cognitive interface names**, not MCP technical tool names. Julia thinks in `market.snapshot.read`, not `review_market_snapshot`.

---

## 6. External Contract Schema

### 6.1 DecisionEnvelope Dual-Source Governance

Two systems share the protocol, not the code. This principle stands. But schema drift protection is needed.

`mcp/schemas/common.py`:

```python
@dataclass
class ExternalContractVersion:
    """Governs schema compatibility between Julia and external providers."""
    schema_name: str         # "DecisionEnvelope"
    schema_version: str      # "1.1"
    provider: str            # "ai_theme_app"
    frozen_at: str           # ISO date

    def validate(self, incoming: dict) -> tuple[bool, str]:
        """Check incoming data against expected schema version.

        If schema_version mismatch:
          - Minor (1.0 → 1.1 with backward compat): warning
          - Major (1.x → 2.0): reject, emit runtime.contract.error
        """
        incoming_version = incoming.get("schema_version")
        if incoming_version is None:
            return True, "no version — assuming compatible"
        if incoming_version != self.schema_version:
            return False, f"schema version mismatch: expected {self.schema_version}, got {incoming_version}"
        return True, "ok"
```

Julia never silently parses data with unknown schema versions. Unknown versions produce `runtime.contract.warning` events.

### 6.2 Separation from ai_theme_app

Julia does NOT import `ai_theme_app.core.contracts.decision_envelope`. The `mcp_client/models.py` mirror is acceptable but must:
1. Match the frozen schema version from ai_theme_app
2. Include version check on deserialization
3. Never add fields that don't exist upstream

---

## 7. ai_theme_app Integration

### 7.1 Capability Registration (M2)

```python
def register_ai_theme_app_capabilities(registry, adapter):
    from julia_core.mcp.schemas.market import AI_THEME_APP_CAPABILITIES

    for name, spec in AI_THEME_APP_CAPABILITIES.items():
        cap = Capability(
            name=name,
            description=spec["description"],
            layer=CapabilityLayer.INTELLIGENCE,
            provider="ai_theme_app_mcp",
            permission_scope=spec["permission_scope"],
            input_schema={},
            handler=None,
            adapter="mcp",
            example="",
        )
        registry.register(cap)
```

### 7.2 Morning Brief Flow (M3)

```
Runtime Scheduler (08:30 daily)
  → CapabilityManager.resolve("market.snapshot.read")
  → MCPAdapter → ai_theme_app MCP → MarketSnapshot
  → ContextBlock (source=ai_theme_app, authority=market_data, evidence_refs=...)
  → Context OS assembly
  → Julia Reasoning (interprets, does NOT just recite)
  → Morning Brief (natural language, Tony-customized)
```

### 7.3 M7 Feedback Loop (Future)

```
Day T:   Julia calls market.decision.explain → prediction_id recorded
Day T+N: Market truth arrives → accuracy score computed
         → Market Memory updated (ADR from ai_theme_app v1.1 Section 5)
         → Julia's future interpretations weighted by historical accuracy
```

---

## 8. Future Capability Providers

The Capability Operating Layer is designed for extension:

| Provider | Type | Adapter | Capabilities |
|----------|------|---------|-------------|
| ai_theme_app | INTELLIGENCE | MCP | market.* |
| Local FS | KNOWLEDGE | local | file.* |
| Voice OS | PERCEPTION | local | voice.* |
| Calendar (future) | WORLD | CalDAV/API | calendar.* |
| GitHub (future) | INTELLIGENCE | MCP | github.* |
| Email (future) | WORLD | IMAP/API | email.* |
| IoT/Robot (future) | PERCEPTION | MQTT/HTTP | body.*, device.* |

Each new provider:
1. Registers capabilities in CapabilityRegistry
2. Sets permission scopes in CapabilityPermissionPolicy
3. If external, implements an Adapter
4. If MCP-based, uses the MCP Adapter + tool mapping

---

## 9. Migration Plan

### M0 — Skeleton (current)
- `capability/manager.py` — CapabilityManager (NEW)
- `capability/policy.py` — CapabilityPermissionPolicy (NEW)
- `capability/models.py` — Capability, CapabilityRequest, CapabilityResult (NEW)
- `mcp/client.py` — MCPClient, pure transport (NEW, extract from mcp_client/)
- `mcp/adapter.py` — MCPAdapter, tool→capability mapping (NEW)
- `mcp/schemas/common.py` — ExternalContractVersion (NEW)
- `mcp/schemas/market.py` — ai_theme_app capability definitions (NEW)
- Keep `mcp_client/` as legacy, unchanged

### M1 — Migration
- `MarketBrainClient` → `AiThemeMCPAdapter` using MCPClient
- Register ai_theme_app capabilities in CapabilityRegistry
- Old `mcp_client/` marked deprecated, kept for backward compat

### M2 — Registration
- Register `market.snapshot.read`, `market.alert.query`, `market.decision.explain`
- Wire through CapabilityManager → MCPAdapter → MCPClient
- Contract tests: schema version validation

### M3 — Morning Brief
- Runtime Scheduler → CapabilityManager → market.snapshot.read
- Context OS integration: market data as ContextBlock
- Julia reasons, not recites

### M4 — Cleanup
- Remove `mcp_client/` legacy path
- All MCP access through CapabilityManager

---

## 10. Anti-Patterns (Explicitly Rejected)

1. **Direct MCP tool exposure to LLM** — LLM sees capabilities, not MCP tools. The mapping stays in the adapter.
2. **MarketBrainClient as capability** — It is a transport + adapter concern, not a capability.
3. **ai_theme_app-specific code in capability/manager.py** — Manager is provider-agnostic. ai_theme_app is one provider among many.
4. **Schema drift without version check** — All external contracts carry `schema_version`. Unknown versions are rejected, not silently parsed.
5. **Capability calls without permission check** — Every resolve() passes through policy.check().

---

## 11. Relationship to JULIA_CORE_PRINCIPLES.md

| Principle | How ADR-026 satisfies it |
|-----------|--------------------------|
| P1: Runtime is Authority | CapabilityManager is Runtime-owned. External systems are adapted, not directly accessed. |
| P2: Context OS is Single Authority | MCP results enter through ContextBlock, not raw prompt injection. |
| P3: Identity ≠ Memory | Market data is INTELLIGENCE (knowledge), not MEMORY. Clear layer separation. |
| P4: Provider supplies capability, not cognition | MCP Adapter returns facts. Context OS + Reasoning own interpretation. |
| P5: Provider output ≠ Identity truth | ExternalContractVersion validation + EvidenceLedger + governance before memory. |

---

## 12. Approval Checklist

- [ ] CapabilityLayer.INTELLIGENCE addition approved
- [ ] CapabilityManager design approved
- [ ] CapabilityPermissionPolicy scope definitions approved
- [ ] MCP Adapter pattern (tool ↔ capability mapping) approved
- [ ] ExternalContractVersion schema governance approved
- [ ] ai_theme_app 5-capability mapping approved
- [ ] Migration plan (M0 → M4) approved
- [ ] Anti-patterns explicitly rejected

---

*This ADR establishes the Capability Operating Layer. No MCP integration code until this design is reviewed and frozen.*
