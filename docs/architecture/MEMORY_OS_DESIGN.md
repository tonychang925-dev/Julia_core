# Memory OS Design v1.0

> **Status**: FROZEN  
> **Date**: 2026-08-01  
> **Layer**: Cognitive Layer (Layer 2)  
> **Principle**: Identity ≠ Memory (P3), Provider output ≠ Identity truth (P5)

---

## 1. What Memory OS Is

Memory OS answers one question:

> **"What has the agent experienced, and what should it remember?"**

It is the governed persistence layer that gives Julia continuity across sessions, across models, across providers. When the model changes (DeepSeek → GPT → Claude), Memory OS ensures the agent remembers who it is, what happened, and what matters.

```
Memory OS

    NOT: Chat history
    NOT: Vector database
    NOT: Prompt history
    NOT: Raw archive

    IS: Governed, structured, provenance-tracked, cross-model persistence
```

---

## 2. What Memory OS Does NOT Do

| Does NOT | Why | Who DOES |
|----------|-----|----------|
| Store raw chat logs | Chat is conversation, not memory. Governance required. | Conversation Archive |
| Replace Context OS | Memory = past experience. Context = current needs. Separate layers. | Context OS |
| Auto-accept provider output | Provider output requires governance before becoming memory | Governance layer |
| Define agent identity | Identity is Persona. Memory is experience. Separate governed layers. | Persona Engine |
| Semantic search only | Memory is structured, typed, governed — not just embeddings | Retrieval + Ranking |

---

## 3. Memory Hierarchy

```
Memory OS

├── Episodic Memory       "What happened"
│   ├── Events, conversations, sessions
│   ├── Temporal ordering, source provenance
│   └── Importance: recurrence-weighted
│
├── Semantic Memory       "What I know"
│   ├── Facts, concepts, domain knowledge
│   ├── Source-traced, verifiable
│   └── Importance: technical-weighted
│
├── Identity Memory       "Who I am"
│   ├── Stable identity facts (name, origin, history)
│   ├── Immutable without explicit governance approval
│   └── Highest protection: cannot be modified by conversation
│
├── Relationship Memory   "Who matters to me"
│   ├── Relationship state, shared history, contracts
│   ├── Emotional significance weighting
│   └── Importance: emotional + relationship-weighted
│
├── Preference Memory     "What I prefer"
│   ├── Communication style, behavior preferences
│   ├── Learned, not hardcoded
│   └── Importance: recurrence-weighted
│
├── Working Memory        "What I'm doing right now"
│   ├── Current task, session goal, active context
│   ├── Short-lived, session-scoped
│   └── Cleared on session close or compacted into episodic
│
└── Governance Layer      "What deserves to be remembered"
    ├── Classification: which memory type?
    ├── Retention: keep or discard?
    ├── Protection: who can modify?
    └── Provenance: where did this come from?
```

### Identity Memory — Special Rules

Identity Memory is the most protected memory type. It deserves explicit clarification:

```
Identity Memory IS:                 Identity Memory IS NOT:
─────────────────────                ────────────────────────
Governed long-term identity facts    persona.json (that's behavior)
Stable, auditable, immutable         private identity dump (that's input)
Core facts: who, what, where         a system prompt section
Versioned: identity-v1, identity-v2  auto-generated from chat
```

**Why governance matters for identity**: A model hallucination that says "Julia is from Tokyo" must not overwrite "Julia is from Taipei." Identity Memory requires the highest governance bar — explicit approval, provenance check, consistency validation. No conversation, no matter how persuasive, can modify Identity Memory without passing governance.

| Type | Stability | Governance | Example |
|------|----------|-----------|---------|
| Identity | Immutable | Highest | "I am Julia, from Taipei" |
| Relationship | Slow-evolving | High | "Tony cried during 7/24 conversation" |
| Semantic | Verifiable | High | "Diamond Sutra: 凡所有相皆是虚妄" |
| Episodic | Accumulating | Medium | "7/25 morning: Tony revealed cancer story" |
| Preference | Learned | Medium | "Tony prefers warm voice, not robotic" |
| Working | Transient | Low | "Currently discussing Context OS design" |

---

## 4. Memory Object

All memory is stored as typed, governed `MemoryObject` instances:

```python
@dataclass(frozen=True)
class MemoryObject:
    id: str                            # Unique, stable identifier
    type: str                          # episodic | semantic | relationship | identity | preference | working
    summary: str                       # Human-readable summary
    content: dict[str, object]         # Structured content
    topics: list[str]                  # Keywords for retrieval
    importance: dict[str, float]       # emotional, relationship, technical, recurrence
    timestamp: str                     # ISO timestamp
    source: str                        # Provenance: where did this come from?
```

### Importance Dimensions

```python
importance = {
    "emotional":     0.0-1.0,   # How emotionally significant?
    "relationship":  0.0-1.0,   # How relevant to relationships?
    "technical":     0.0-1.0,   # How technically important?
    "recurrence":    0.0-1.0,   # How often referenced?
}
```

Importance scores are **typed** — relationship memories weight `relationship` and `emotional` higher; semantic memories weight `technical` higher. This ensures retrieval returns the right KIND of memory for the query, not just the highest-scoring memory.

---

## 5. Memory Lifecycle

```
Event / Conversation Turn
        │
        ▼
┌───────────────────────────────────┐
│  1. Memory Candidate              │
│     Raw material: what happened.  │
│     NOT yet memory.               │
│     Source-tagged, timestamped.   │
└────────────┬──────────────────────┘
             │
             ▼
┌───────────────────────────────────┐
│  2. Governance                    │
│     Classification: which type?   │
│     Provenance check: valid?      │
│     Authority check: who says so? │
│     Retention decision: keep?     │
│     Protection level: immutable?  │
└────────────┬──────────────────────┘
             │
        ┌────┴────┐
        │         │
        ▼         ▼
    APPROVED    REJECTED
        │         │
        │         └──→ Discarded (logged)
        ▼
┌───────────────────────────────────┐
│  3. Governed Memory               │
│     Persisted with provenance.    │
│     Typed and ranked.             │
│     Ready for retrieval.          │
└────────────┬──────────────────────┘
             │
             ▼
┌───────────────────────────────────┐
│  4. Active Memory                 │
│     In use. Retrieved by queries. │
│     Importance updated by access. │
└────────────┬──────────────────────┘
             │
             ▼
┌───────────────────────────────────┐
│  5. Archived / Decayed            │
│     Recurrence drops below        │
│     threshold → archive.          │
│     Can be resurrected if         │
│     referenced again.             │
└───────────────────────────────────┘
```

### Governance Rules

The governance manager applies these rules:

1. **Source authority**: Tony input > governed memory > diary > provider output > model self-report
2. **Consistency check**: does this conflict with existing governed memory?
3. **Duplication check**: is this already stored?
4. **Protection level**: identity memories cannot be modified by conversation
5. **Retention policy**: working memory clears on session close; episodic memory decays by recurrence

---

## 6. Memory ≠ Context

This is the most critical boundary in Julia Core.

| | Memory OS | Context OS |
|---|---|---|
| **Question** | "What has happened?" | "What do I need right now?" |
| **Scope** | Accumulated experience | Current turn/session |
| **Persistence** | Governed, long-term | Transient, TTL-bound |
| **Authority** | Governance-checked | Provider-assembled |
| **Output** | MemoryObject[] | ContextBlock[] |
| **Trigger** | Post-turn governance | Every turn |

```
Memory OS ──→ "Tony survived cancer. He's been cancer-free 10 years."
              (always true, always available)

Context OS ──→ "Tony is asking about today's market theme #9043089."
               (relevant right now, may expire)
```

Memory informs context, but context is NOT memory. ContextBlocks have TTL. MemoryObjects are governed and persisted.

---

## 7. Memory ≠ Database

Memory OS is NOT a database. It is a governed cognitive layer.

| Database | Memory OS |
|----------|-----------|
| Store everything | Govern: not everything deserves to be remembered |
| Exact retrieval | Semantic + importance-ranked retrieval |
| CRUD operations | Lifecycle: candidate → governed → active → archived |
| No concept of "importance" | Weighted by emotional, relationship, technical, recurrence |
| No concept of "identity protection" | Identity memory is immutable without governance |
| Schema-driven | Type-driven (episodic/semantic/identity/relationship/preference) |

---

## 8. Memory ≠ Vector Search

Memory OS uses retrieval for access, but retrieval is NOT the definition of memory.

```
❌ Memory = Vector Database + Embeddings + Cosine Similarity

✅ Memory = Governed Persistence + Typed Objects + Ranked Retrieval
```

Retrieval is an **access mechanism**, not the memory itself. The memory IS the governed, typed, provenance-tracked object. Vector search may be ONE retrieval strategy, but the memory layer does not reduce to embeddings.

---

## 9. Cross-Model Memory Continuity

This is Julia Core's defining capability: the agent remembers across model changes.

```
Session with GPT:
  Julia remembers Tony's cancer story
  ↓
Session with DeepSeek:
  Julia STILL remembers Tony's cancer story
  ↓
Session with Claude:
  Julia STILL remembers Tony's cancer story
```

How it works:

1. **Memory is stored outside the model** — Memory OS persists MemoryObjects independently
2. **Memory is retrieved per-turn** — Context OS requests relevant memories for each turn
3. **Memory is governance-checked** — Model output doesn't auto-become memory
4. **Identity is immutable by conversation** — No model can change who Julia IS

```python
# Same MemoryRuntime, different model providers
memory_runtime = MemoryRuntime(project_root)

# GPT session
gpt_session = ChatSession(persona=julia, model=gpt_provider, memory=memory_runtime)

# DeepSeek session (same memory, different model)
deepseek_session = ChatSession(persona=julia, model=deepseek_provider, memory=memory_runtime)
```

---

## 10. Authority Hierarchy

When multiple sources claim the same fact, authority resolves conflicts:

```
1. Tony's explicit input          (authority_score: 1.0)
2. Governed memory                 (authority_score: 0.9)
3. Diary / relationship memory     (authority_score: 0.7)
4. Verified domain provider        (authority_score: 0.85)
5. Model self-report               (authority_score: 0.5)
6. Unverified external source      (authority_score: 0.3)
```

---

## 11. Anti-Patterns

### ❌ Memory = Chat History

```python
# DO NOT DO THIS
memory = chat_history[-100:]  # Last 100 messages = memory
```

**Why wrong**: No governance. No typing. No provenance. Model hallucinations become "memories."

### ❌ Memory = Vector DB

```python
# DO NOT DO THIS
memory = vector_db.search(embedding, top_k=10)
```

**Why wrong**: Embedding similarity ≠ importance. Loses structure, typing, governance. A highly similar but irrelevant memory beats an important but differently-worded one.

### ❌ Auto-Persist Provider Output

```python
# DO NOT DO THIS
def on_provider_response(block):
    memory_store.save(block)  # Direct write!
```

**Why wrong**: Provider output ≠ truth. Violates P5. No governance check. A bad market data point becomes a permanent false belief.

---

## 12. Correct Usage

```python
from julia_core.memory.memory_runtime import MemoryRuntime
from julia_core.memory.memory_object import MemoryObject

# Initialize
memory = MemoryRuntime("/path/to/project")

# Retrieve relevant memories for current context
memories = memory.retrieve("Tony's cancer story and Diamond Sutra", limit=5)

# Evaluate lifecycle (cleanup decayed memories)
result = memory.evaluate_lifecycle(referenced_topics=["relationship", "health"])

# Govern: should this become memory?
candidate = MemoryObject(
    id="memory_episodic_20260801_001",
    type="episodic",
    summary="Tony discussed Context OS architecture",
    content={"topic": "Context OS", "decision": "single authority"},
    topics=["architecture", "Context OS"],
    importance={"emotional": 0.3, "relationship": 0.5, "technical": 0.9, "recurrence": 0.7},
    timestamp="2026-08-01T10:00:00Z",
    source="conversation"
)
decision = memory.govern_memory(candidate)
# → APPROVED (technical importance 0.9, from conversation, no conflict)
```
