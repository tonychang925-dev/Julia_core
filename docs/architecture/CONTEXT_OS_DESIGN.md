# Context OS Design v1.0

> **Status**: FROZEN  
> **Date**: 2026-08-01  
> **Layer**: Cognitive Layer (Layer 2)  
> **Principle**: Context OS is the single context authority (ADR-001, P2)

---

## 1. What Context OS Is

Context OS answers one question:

> **"What does the agent need to know right now?"**

It is the single pipeline through which every piece of information reaches the model. No domain, no provider, no external system bypasses Context OS.

```
              Context OS

     "What does Julia need to know?"
                    │
    ┌───────────────┼───────────────┐
    │               │               │
 Planner         Resolver         Budget
 (what?)         (from whom?)     (how much?)
    │               │               │
    └───────────────┼───────────────┘
                    │
                    ▼
           ContextBlock[]
     (frozen context candidates
      with provenance, evidence, TTL)
```

---

## 2. What Context OS Does NOT Do

> **Context OS prepares the world for reasoning; it does not perform reasoning.**

Context OS is a **context pipeline**, not a hidden agent. It selects, organizes, compresses, and delivers context. It does NOT judge, reason, decide, or act.

| Does NOT | Why | Who DOES |
|----------|-----|----------|
| Generate judgments | Context assembly, not reasoning | LLM (interpreter) |
| Decide what is true | Facts have provenance; truth is evaluated elsewhere | Evidence layer, governance |
| Store long-term memory | ContextBlocks are short-lived candidates with TTL | Memory OS |
| Understand domain semantics | Domain-agnostic planning and resolution | Domain Providers |
| Assemble prompts directly | Outputs structured blocks, not prompt text | Context Assembly module |
| Define agent identity | Persona is a separate governed layer | Persona Engine |
| Perform reasoning | If Context OS reasons about what to include, it becomes a hidden agent competing with Runtime → violates P1 | Runtime (authority) |

The boundary is clear:

```
✅ Context OS:     Select → Organize → Compress → Deliver
❌ Context OS:     Judge → Reason → Decide → Act
```

---

## 3. Core Pipeline

Context OS is the single authority for ALL model-visible context.
Six ContextSources produce ContextBlock candidates. No source bypasses Context OS.

```
                    Runtime
                       │
                 ContextRequest
                       │
                       ▼
                  Context OS
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   PersonaSource  ConversationSource  InteractionSource
   (behavioral     (ActiveTail,       (derived session
    identity)       Compact)           state)
        │              │              │
   ExperienceSource  CapabilitySource  DomainEvidenceSource
   (governed memory  (tool manifest,   (Market Brain,
    refs)             capability list)  provider facts)
        │              │              │
        └──────────────┴──────────────┘
                       │
                  ContextBlock[]
                       │
                     Planner
                  "What is needed?"
                       │
                     Resolver
             "De-duplicate, rank, budget"
                       │
                     Budget
                "Apply token limits"
                       │
                   Projection
            "Format for model consumption"
                       │
                    Assembly
           "Single model-visible context"
                       │
                 Alignment OS
           "Provider-specific adaptation"
                       │
                  Model Provider
```

### ContextBlock

ContextBlock is a generic governed model-context unit. It can originate from
any of the six ContextSources — not only from domain providers.

```
ContextBlock(
    source:        str       — "persona", "conversation", "memory", "capability", "domain", "interaction"
    content:       object    — opaque to Context OS
    authority:     str       — provenance label
    block_type:    str       — "identity", "transcript", "evidence", "reference", "capability"
    evidence_refs: tuple     — traceable source references
    authority_score: float   — 0.0 - 1.0
    ttl_seconds:   int|None  — expiration
    required:      bool      — must be included
    estimated_tokens: int    — budget hint
)
```

### Key Rules

1. Persona must enter Context OS as a source, not be added after assembly.
2. Conversation transcript enters Context OS via ConversationContextSource — never bypasses.
3. Domain/Provider evidence is one of six sources — Context OS is NOT a ProviderRegistry wrapper.
4. Context Assembly is an execution stage of Context OS — not an independent authority.
5. Alignment OS adapts the finalized projection for a specific provider — it does not select what Julia should know.

---

## 4. Key Data Structures

### ContextRequest — "What does the agent need?"

```python
@dataclass(frozen=True, slots=True)
class ContextRequest:
    task_intent: str              # "market_review", "greeting", "code_review"
    intent: str                   # "analysis", "chat", "generation"
    domain: str | None            # "financial", "medical", "coding", None
    domain_object_type: str | None  # "theme", "patient", "repository"
    domain_object_id: str | None    # "9043089", "patient_42", None
    cognitive_mode: str           # "conversation", "analysis", "creation"
    required_capabilities: tuple  # ["market_intelligence", "evidence_lookup"]
    evidence_intents: tuple       # ["why_theme_rose", "supporting_news"]
    required_blocks: tuple        # blocks that MUST be present
    optional_blocks: tuple        # blocks that are nice to have
    exclusions: tuple             # blocks to explicitly exclude
    target_budget_tokens: int     # max tokens for assembled context
```

Key design decisions:
- **Frozen** (immutable dataclass) — request can't be modified mid-pipeline
- **Domain-independent** — no financial/medical/coding specific fields
- **Intent pointer pattern** — `domain_object_id` carries a reference, not payload
- **Budget-aware** — `target_budget_tokens` constrains total context size

### ContextBlock — "Here's a piece of context."

```python
@dataclass(frozen=True, slots=True)
class ContextBlock:
    source: str              # "financial_v1", "hello_world_provider"
    content: object          # Domain facts (opaque to Context OS)
    authority: str           # "market_intelligence", "user_input"
    block_type: str          # "generic", "evidence", "reference"
    evidence_refs: tuple     # ["src_theme_9043089", "news_20260801_001"]
    authority_score: float   # 0.0 - 1.0, how much to trust this source
    ttl_seconds: int | None  # How long before this block expires
    required: bool           # Must be included in assembled context
    estimated_tokens: int    # Estimated token count
```

Key design decisions:
- **Frozen** (immutable) — once created, content cannot change
- **Provenance** — `evidence_refs` traces back to source data
- **TTL** — context has an expiration; stale data is automatically dropped
- **Opaque content** — Context OS does not interpret `content`; it passes it through
- **Not memory** — ContextBlock is transient; it does not persist beyond the session

---

## 5. Authority Scoring

ContextBlocks from different sources carry different authority. The resolver uses `authority_score` to rank and allocate budget:

| Source | Typical authority_score | Why |
|--------|------------------------|-----|
| User (Tony) explicit input | 1.0 | Highest authority — user intent |
| Governed memory | 0.9 | Validated, provenance-tracked |
| Domain provider (trusted) | 0.85 | Facts with evidence_refs |
| Diary / relationship memory | 0.7 | Personal but subjective |
| Model self-report | 0.5 | LLM output, needs governance |
| External API (unverified) | 0.3 | Untrusted source |

The resolver allocates token budget to higher-authority blocks first. Lower-authority blocks may be dropped if budget is tight.

---

## 6. Context Lifecycle

```
ContextBlock Created (by Provider, with TTL)
        │
        ▼
ContextBlock Submitted (to Resolver)
        │
        ├── Check: is_expired()? → DROP
        ├── Check: budget available? → QUEUE
        └── Check: required=True? → MUST INCLUDE
        │
        ▼
ContextBlock Assembled (into model context)
        │
        ▼
Model Consumes Context
        │
        ▼
Post-Turn: ContextBlock Discarded
           (or compacted if session-boundary)
```

ContextBlocks **do not** automatically become memory. Post-turn, the Memory OS governance layer evaluates which blocks (if any) warrant persistence.

---

## 7. Boundary: Context OS ↔ Other Subsystems

```
Context OS ──→ Context Assembly    "Here are blocks. Format for model."
Context OS ──→ Provider Registry   "Find providers that can handle this."
Context OS ←── Domain Providers    "Here are ContextBlock candidates."
Context OS ──→ Memory OS           "Turn complete. Evaluate for persistence."
Context OS ←── Memory OS           "Here are governed memory blocks (score 0.9)."

Context OS ⊥   Model Provider      (Context OS never calls model directly)
Context OS ⊥   Persona Engine      (Persona is applied AFTER context resolution)
Context OS ⊥   Voice OS            (Voice OS consumes model output, not context)
```

---

## 8. Anti-Patterns

### ❌ Domain-Specific Context Assembly

```python
# DO NOT DO THIS
class FinancialContextOS:
    def get_context(self, theme_id):
        return f"Market theme {theme_id} analysis prompt..."
```

**Why wrong**: Bypasses Context OS. Financial owns its own prompt. Adding Medical means adding MedicalContextOS → fragmentation.

### ❌ ContextBlock as Memory

```python
# DO NOT DO THIS
memory.save(context_block)  # Direct write, no governance
```

**Why wrong**: Provider output ≠ truth. ContextBlocks are candidates, not governed facts.

### ❌ Provider Returns Prompt Text

```python
# DO NOT DO THIS
class MyProvider:
    def get_context(self, request):
        return "Here is the assembled prompt for the model..."
```

**Why wrong**: Provider owns prompt assembly. Violates ADR-002 (provider supplies facts, not cognition).

---

## 9. Correct Usage

```python
from julia_core.context_os.request import ContextRequest
from julia_core.context_os.planner import ContextPlanner
from julia_core.providers.registry import ProviderRegistry

# 1. Create request
request = ContextRequest(
    task_intent="market_review",
    intent="analysis",
    domain="financial",
    domain_object_type="theme",
    domain_object_id="9043089",
    target_budget_tokens=4000,
)

# 2. Plan context needs
planner = ContextPlanner()
plan = planner.plan(request)

# 3. Resolve providers
registry = ProviderRegistry()
blocks = registry.resolve(request)

# 4. Blocks ready for assembly
# → Context Assembly → Persona → Model
```
