# Provider API v1.0 — FROZEN

Domain Providers are Julia Core's extension mechanism.

## Protocol

```python
class DomainProvider(Protocol):
    domain: str
    def metadata(self) -> ProviderIdentity: ...
    def capabilities(self) -> tuple[str, ...]: ...
    def provide(self, request: ContextRequest) -> tuple[ContextBlock, ...]: ...
```

## Rules

- Provider supplies facts; does NOT own cognition.
- Provider accepts ContextRequest; returns ContextBlock(s).
- Provider must not: assemble prompts, write memory, control runtime, make decisions.
- All blocks carry evidence_refs.

## Example

See `providers/examples/hello_provider.py`

FROZEN. Domain is the extension point. Domain ≠ core.
