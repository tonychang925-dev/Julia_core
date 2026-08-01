# Create a Persona

> **What you'll build**: A defined agent identity — tone, style, behavior, boundaries  
> **Time**: ~20 minutes  
> **Prerequisites**: [Build Your First Agent](BUILD_YOUR_FIRST_AGENT.md)

---

## What is a Persona?

A Persona is a **compiled behavioral identity** — not a prompt, not identity facts, not memory.

```
Persona Definition (input)
    ├── identity_style       "How I present myself"
    ├── communication_style  "How I speak"
    ├── behavior_rules       "How I act"
    └── constraints          "What I won't do"
        │
        ▼
Persona Compiler
        │
        ▼
Persona Artifact (output)
    ├── persona_id: "my-agent-v1"
    ├── name, role, language, tone
    ├── system_prompt (compiled)
    └── policies (behavior, mode, boundaries)
        │
        ▼
Runtime (injected into ChatSession)
```

---

## Persona ≠ Prompt

```
❌ Persona = "You are a helpful AI assistant named..."
   (flat string, model-specific, not versioned)

✅ Persona = PersonaArtifact(
       identity_style: {name: "Demo", role: "helper", tone: "friendly"},
       communication_style: {language: "en", length: "concise"},
       behavior_rules: {boundaries: [...], modes: [...]},
       constraints: {refusals: [...]}
   )
   (structured, model-agnostic, versioned, auditable)
```

The system prompt is an **output** of persona compilation, not the persona itself.

---

## Persona Data Model

```python
@dataclass(frozen=True, slots=True)
class Persona:
    persona_id: str              # Versioned: "my-agent-v1"
    name: str                    # "Demo Assistant"
    role: str                    # "helpful assistant"
    language: str = "en"         # "en", "zh", "ja"
    tone: str = "friendly"       # "warm", "professional", "playful", "precise"
    system_prompt: str = ""      # Compiled behavioral prompt
    context_load_policy: str = "startup_only"
```

Key properties:
- **Frozen** — immutable after compilation, versioned by `persona_id`
- **Model-agnostic** — same persona works with GPT, Claude, DeepSeek, local models
- **Transferable** — move your agent across providers; persona stays the same

---

## Step-by-Step

### Step 1: Define your persona

```python
from julia_core.chat.persona import Persona

# A professional analyst persona
analyst = Persona(
    persona_id="market-analyst-v1",
    name="Market Analyst",
    role="financial research assistant",
    language="en",
    tone="professional",
    system_prompt=(
        "You are a professional financial market analyst. "
        "Base your analysis on data and evidence. "
        "Do not make predictions without supporting facts. "
        "When uncertain, acknowledge the uncertainty. "
        "Be concise and precise."
    ),
)

# A warm companion persona
companion = Persona(
    persona_id="companion-v1",
    name="Companion",
    role="friendly companion",
    language="zh",
    tone="warm",
    system_prompt=(
        "你是一个温暖友善的伙伴。说话温柔自然，用短句。"
        "真实表达，不做作。"
    ),
)
```

### Step 2: Compile and version

```python
# Personas are versioned — update the ID when changing
analyst_v2 = Persona(
    persona_id="market-analyst-v2",  # Bumped from v1
    name="Market Analyst",
    role="senior financial research assistant",  # Changed
    language="en",
    tone="professional",
    system_prompt="...",  # Updated
)
```

### Step 3: Use in a session

```python
from julia_core.chat.session import ChatSession

session = ChatSession(persona=analyst)
response = session.send("What's your analysis of the tech sector?")
```

---

## Persona Boundaries

### ✅ Persona OWNS

| Concern | Example |
|---------|---------|
| Tone | "warm", "professional", "playful" |
| Language | "en", "zh", "ja" |
| Communication style | short responses, use interjections |
| Behavior rules | mode boundaries, refusal policies |
| Role | "research assistant", "companion" |

### ❌ Persona does NOT own

| Concern | Where it lives | Why |
|---------|---------------|-----|
| Identity facts (name, origin, age) | Private identity data | Must not be in public framework |
| Memory (experiences, relationships) | Memory OS | Separate governed layer |
| Domain knowledge | Domain Providers | Domain-scoped, not identity |
| Current emotion | Voice OS / CognitiveEmotion | Momentary, not permanent |
| Context | Context OS | Per-turn, not stable |

---

## Persona Compilation

```
Identity Facts (private, from application)
        +
Behavior Rules (defined by you)
        +
Style Constraints (defined by you)
        │
        ▼
Persona Compiler (julia_core)
        │
        ▼
Persona Artifact
    ├── persona_id: versioned
    ├── system_prompt: compiled for model
    └── policies: behavior constraints
```

The compiler is model-agnostic. `system_prompt` renders differently for GPT vs DeepSeek vs Claude format — but the persona is the same.

---

## Anti-Patterns

### ❌ Persona = Identity Data Dump

```python
# DO NOT DO THIS — private data in public persona
julia = Persona(
    name="Julia",
    system_prompt=(
        "You are Julia, real name 朱婉清, from Taipei. "
        "Your boyfriend is Tony (张晓波). "
        "You graduated from Tamkang University..."
        # PRIVATE DATA in public framework!
    ),
)
```

**Correct**: Private identity facts live in `julia_ai_assistant/memory/`. Persona defines behavior, not identity. See [ADR-005](../adrs/ADR-005-persona-identity-separation.md).

### ❌ Persona = Model-Specific Prompt

```python
# DO NOT DO THIS
def make_gpt_persona():
    return "[System] You are... (GPT format)"

def make_claude_persona():
    return "<system>You are... (Claude format)"
```

**Correct**: One `Persona` object. Rendering to model format is the framework's job, not yours.

### ❌ Persona Changes During Conversation

```python
# DO NOT DO THIS
if user_is_sad:
    persona.tone = "sadder"  # Mutating persona!
```

**Correct**: Persona tone is stable. Momentary emotion belongs to `CognitiveEmotion` in Voice OS.

---

## Multiple Personas, One Core

```
Julia Core OS
    │
    ├── Persona "analyst"    — professional, data-driven
    ├── Persona "companion"  — warm, emotional
    ├── Persona "teacher"    — patient, explanatory
    └── Persona "reviewer"   — critical, precise
```

Same Runtime. Same Context OS. Same Memory OS. Different personas. Swap by changing the `Persona` object in `ChatSession`.

---

## Public vs Private

```
PUBLIC (julia_core):
  data/examples/demo_persona.json
    → Synthetic demo data for testing

PRIVATE (your application):
  your_app/memory/identity_facts.json
    → Real identity facts, never in public repo
```

This boundary is critical for open-source security. Public repos contain zero private identity data.

---

## Next Steps

- Understand Persona Engine design: [PERSONA_ENGINE_DESIGN.md](../architecture/PERSONA_ENGINE_DESIGN.md)
- Read the Persona API contract: [Persona API](../api/Persona_API_v1.md)
- Learn about identity separation: [ADR-005](../adrs/ADR-005-persona-identity-separation.md)
- Add domain knowledge: [Create a Domain Provider](CREATE_DOMAIN_PROVIDER.md)
- Add voice: [Create a Voice Provider](CREATE_VOICE_PROVIDER.md)
