# Domain Provider Interface Contract v1.0

> **Phase**: A3 — Domain Provider Interface Contract  
> **Date**: 2026-07-31  
> **Status**: FROZEN  
> **Predecessor**: A2.2.1 — Context OS Runtime Integration Skeleton ✅  
> **Successor**: A4 — Financial Provider Binding  

---

## 1. Purpose

A2 completed: *how Julia runs.*

A3 defines: *how external capabilities enter Julia.*

A Domain Provider is a **plugin** — it supplies domain facts and evidence as context candidates. It is NOT a co-owner of Julia's cognitive architecture.

---

## 2. Provider Identity

Every Domain Provider MUST declare:

```python
@dataclass(frozen=True, slots=True)
class ProviderIdentity:
    provider_id: str        # e.g. "financial-market-state"
    provider_name: str      # e.g. "Financial Market State Provider"
    version: str            # semantic version
    domain: str             # e.g. "financial", "healthcare", "coding"
    capabilities: tuple[str, ...]  # e.g. ("market_state", "theme_analysis")
```

A Provider without an identity cannot be registered.

---

## 3. Provider Lifecycle

```
REGISTERED  →  READY  →  ACTIVE
                  ↓
              DISABLED
```

| State | Meaning |
|-------|---------|
| REGISTERED | Provider identity declared, not yet validated |
| READY | Provider loaded, capabilities verified, not serving |
| ACTIVE | Provider serving context blocks |
| DISABLED | Provider unloaded or failed health check |

Runtime manages lifecycle transitions. Provider cannot change its own state.

---

## 4. Provider Input Contract

A Domain Provider MUST accept only `ContextRequest` as input.

```python
class DomainProvider(Protocol):
    domain: str
    
    def metadata(self) -> ProviderIdentity: ...
    
    def capabilities(self) -> tuple[str, ...]: ...
    
    def provide(self, request: ContextRequest) -> tuple[ContextBlock, ...]: ...
```

**Allowed input**: `ContextRequest` only.

**Forbidden input**:
- Raw user prompt
- Memory fragments
- Identity data
- Conversation history
- Any domain not declared in `metadata().domain`

---

## 5. Provider Output Contract

A Domain Provider MUST output only `ContextBlock` instances.

**Allowed output**:
- `ContextBlock` (facts, evidence, domain data)
- Evidence references
- Capability result metadata

**Forbidden output**:
- Final answer text (that's the model's job)
- Agent decision (that's Action Governance)
- Memory mutation (that's Memory OS)
- Trading action (that's M7 Risk Gate)
- Provider modifying its own authority score

---

## 6. Evidence Ownership

```
Domain Provider        →  OWNS: evidence generation, evidence references, domain facts
Context OS             →  OWNS: context orchestration, provenance, budget, routing
Action Governance      →  OWNS: action decisions
Memory OS              →  OWNS: persistence and retrieval
```

A Provider cannot:
- Mark its own output as "governed fact"
- Promote its own evidence to identity truth
- Claim authority over another domain's facts

---

## 7. Provider Isolation

```
runtime/core/              ← Julia Core (Context OS, Runtime, Memory)
    context_os/
    runtime/
    providers/             ← Provider contract + registry only

runtime/providers/         ← Domain implementations (external to core)
    financial/
    healthcare/             (future)
    coding/                 (future)
```

Domain Providers live in `runtime/providers/`, NOT in `runtime/core/`.

Core does not import from domain providers. Providers import from core.

---

## 8. Registry Contract

```python
class ProviderRegistry:
    """Maps domain → provider. Does not reason about which provider is better."""
    
    def register(self, provider: DomainProvider) -> None: ...
    def get(self, domain: str) -> DomainProvider | None: ...
    def list_domains(self) -> tuple[str, ...]: ...
```

Registry is a **lookup table**, not a **domain router**.

Allowed:
```python
registry.get("financial")  # → FinancialProvider
```

Forbidden:
```python
registry.choose_best("financial")   # Registry must not compare providers
registry.is_better(provider_a, provider_b)  # Registry must not rank
```

---

## 9. Provider Registration Flow

```
Provider declares metadata() + capabilities()
        ↓
ProviderRegistry.register()
        ↓
Provider state → REGISTERED
        ↓
Runtime verifies capabilities() match declared domain
        ↓
Provider state → READY
        ↓
Runtime.activate_provider(domain)
        ↓
Provider state → ACTIVE
        ↓
ContextResolver can now resolve this domain
```

---

## 10. A3 Acceptance Criteria

1. `DomainProvider` protocol frozen — no new required methods
2. `ProviderIdentity` dataclass frozen — no mutable fields
3. Provider lifecycle states defined and gated
4. Provider input = ContextRequest only (contract enforced)
5. Provider output = ContextBlock only (contract enforced)
6. Evidence ownership boundary frozen
7. Provider isolation: core never imports from `runtime/providers/`
8. Registry is lookup table, not domain router
9. Test: mock provider registered → resolved → blocks returned
10. Test: registry rejects provider without metadata

---

## 11. What A3 Does NOT Include

- ❌ Financial provider implementation (A4)
- ❌ Provider-to-provider communication
- ❌ Provider hot-reload
- ❌ Provider health checking (future)
- ❌ Cross-domain evidence merging
- ❌ Provider-specific caching
- ❌ Provider metrics/telemetry

---

## 12. Next Phase

```
A3  Domain Provider Interface Contract  ← THIS DOCUMENT
        ↓
A3.1 Provider Registry Implementation
        ↓
A4  Financial Provider Binding
```

---

## Document History

| Version | Date | Change |
|---------|------|--------|
| v1.0 | 2026-07-31 | Initial freeze — Domain Provider Interface Contract |
