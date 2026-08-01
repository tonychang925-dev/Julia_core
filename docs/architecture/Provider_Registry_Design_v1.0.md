# Provider Registry Design v1.0

> **Phase**: A3.1 — Provider Registry  
> **Date**: 2026-07-31  
> **Status**: FROZEN  
> **Predecessor**: A3 — Domain Provider Interface Contract ✅  
> **Successor**: A4 — Financial Provider Binding  

---

## 1. Ownership

```
Julia Runtime
       │
 Provider Registry          ← infrastructure, not domain logic
       │
 Provider Interface         ← contract, not implementation
       │
 runtime/providers/         ← domain implementations (external)
```

Registry belongs to Runtime infrastructure. It is NOT part of Context OS. It is NOT part of any domain.

---

## 2. Provider Lifecycle

```
UNREGISTERED → REGISTERED → READY → ACTIVE
                              ↓         ↓
                          DISABLED ←─────
```

| State | Meaning |
|-------|---------|
| UNREGISTERED | Provider unknown to Runtime |
| REGISTERED | Provider identity declared, metadata stored |
| READY | Provider loaded, capabilities verified |
| ACTIVE | Provider serving context blocks |
| DISABLED | Provider unloaded, not serving |

Lifecycle transitions are Runtime-managed. Provider cannot change its own state.

---

## 3. Registry Contract

```python
class ProviderRegistry:
    """Lookup table — not a domain router."""

    def register(self, provider: DomainProvider) -> str:
        """Register provider. Returns provider_id. State → REGISTERED."""
        ...

    def activate(self, provider_id: str) -> None:
        """State → ACTIVE. Verifies capabilities match declared domain."""
        ...

    def disable(self, provider_id: str) -> None:
        """State → DISABLED."""
        ...

    def get(self, provider_id: str) -> DomainProvider | None:
        """Lookup by provider_id."""
        ...

    def get_by_domain(self, domain: str) -> tuple[DomainProvider, ...]:
        """All ACTIVE providers for a domain."""
        ...

    def list_active(self) -> tuple[str, ...]:
        """All ACTIVE provider_ids."""
        ...

    def list_capabilities(self) -> tuple[str, ...]:
        """All capabilities across ACTIVE providers."""
        ...
```

---

## 4. Lookup Contract

Allowed:
```python
registry.get("financial-market-state")     # single lookup
registry.get_by_domain("financial")        # domain lookup
registry.list_capabilities()               # capability listing
```

Forbidden:
```python
registry.choose_best(request)   # Registry must not rank providers
registry.recommend(domain)      # Registry must not select
registry.compare(a, b)          # Registry must not evaluate
```

---

## 5. Provider Metadata

```json
{
  "provider_id": "financial-market-state",
  "provider_name": "Financial Market State Provider",
  "version": "1.0.0",
  "domain": "financial",
  "capabilities": ["market_state", "risk_state"]
}
```

Metadata describes. It does not rank, compare, or reason.

---

## 6. Conflict Handling

When multiple ACTIVE providers declare the same capability:

Registry returns ALL matching providers. Decision is deferred to upper orchestration. Registry does not choose.

---

## 7. Failure Model

| Error | Trigger |
|-------|---------|
| `ProviderNotFoundError` | get() on unknown provider_id |
| `ProviderNotActiveError` | activate() on a DISABLED provider |
| `ProviderVersionMismatchError` | version constraint not satisfied |
| `DuplicateProviderError` | register() with existing provider_id |

Exceptions are typed, not generic. Upper layers can handle them.

---

## 8. A3.1 Acceptance Criteria

1. Register provider → REGISTERED state
2. Activate → READY → ACTIVE
3. get(provider_id) returns provider
4. get_by_domain("test") returns tuple of providers
5. list_active() reflects current ACTIVE set
6. list_capabilities() aggregates across ACTIVE providers
7. disable() → DISABLED, get() returns None for active-only queries
8. Duplicate registration raises DuplicateProviderError
9. Registry has zero domain imports
10. Registry has no select/recommend/compare/rank methods

---

## 9. Next

```
A3.1 Provider Registry     ← THIS DOCUMENT
    ↓
A4   Financial Provider Binding
```

---

## Document History

| Version | Date | Change |
|---------|------|--------|
| v1.0 | 2026-07-31 | Initial freeze |
