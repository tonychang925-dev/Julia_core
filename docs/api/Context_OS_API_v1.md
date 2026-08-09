# Context OS API v1.0 — ARCH-R1b corrected

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

ContextBlock is a generic governed model-context unit. It can originate from
any of the six ContextSources — persona, conversation, interaction, experience,
capability, or domain evidence.

```python
ContextBlock(
    source: str,               # "persona"|"conversation"|"interaction"|"memory"|"capability"|"domain"
    content: object,           # opaque to Context OS
    authority: str,            # provenance label
    block_type: str,           # "identity"|"transcript"|"evidence"|"reference"|"capability"
    evidence_refs: tuple,      # traceable references
)
```

## Six ContextSources

```
PersonaSource        — behavioral identity (tone, style, constraints)
ConversationSource   — canonical transcript (ActiveTail, StructuredCompact)
InteractionSource    — derived session state (mood, phase, patterns)
ExperienceSource     — governed memory refs (episodic, relationship)
CapabilitySource     — tool manifest, capability list
DomainEvidenceSource — provider facts (Market Brain, external data)
```

## Rules

- Context OS assembles context; does NOT reason or decide.
- ALL six sources feed through Context OS. No source has a direct model path.
- Persona enters as a ContextSource — NOT added after Context OS assembly.
- Conversation enters via ConversationContextSource — never bypasses.
- Domain/Provider evidence is one of six sources — Context OS is NOT a ProviderRegistry wrapper.
- Every ContextBlock carries evidence_refs.
- Alignment OS adapts the finalized projection; it does not select what Julia should know.

## Example: Julia Conversation Turn

```python
from julia_core.context_os.request import ContextRequest
from julia_core.context_os.block import ContextBlock

request = ContextRequest(task_intent="conversation", intent="chat")
# Six ContextSources feed ContextBlocks → Planner → Resolver → Budget → Projection → Assembly → Alignment → Model
# Persona, conversation history, interaction state, memory refs, capabilities, and domain evidence
# ALL pass through Context OS. None bypasses it.
```

ARCH-R1b corrected. Supersedes prior ContextBlock = provider output definition.
