# Context OS API v1.0 — FROZEN

Context OS is the single context authority. Every model-facing input passes through it.

## Input: ContextRequest

```python
ContextRequest(
    task_intent: str,          # what the caller wants
    intent: str,               # cognitive intent
    domain: str | None = None, # target domain
)
```

## Output: ContextBlock

```python
ContextBlock(
    source: str,               # provider identity
    content: object,           # domain facts
    authority: str,            # source authority
    evidence_refs: tuple,      # traceable references
)
```

## Rules

- Context OS assembles context; does NOT reason or decide.
- Domain providers supply ContextBlock candidates; do NOT bypass this API.
- Every ContextBlock carries evidence_refs.

## Example: Hello World

```python
from julia_core.context_os.request import ContextRequest
from julia_core.context_os.block import ContextBlock

request = ContextRequest(task_intent="greeting", intent="chat", domain="demo")
# Provider returns ContextBlock → Context OS assembles → Model receives
```

FROZEN. No new fields without ADR.
