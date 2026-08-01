# Persona Engine Design v1.0

> **Status**: FROZEN  
> **Date**: 2026-08-01  
> **Layer**: Cognitive Layer (Layer 2)  
> **Principle**: Identity ≠ Memory (P3)

---

## 1. What Persona Engine Is

Persona Engine answers one question:

> **"Who is this agent, and how do they behave?"**

It defines the agent's stable identity — tone, style, behavior constraints, values — independent of any single model, memory, or domain knowledge.

```
Persona Engine

    NOT: A system prompt
    NOT: A roleplay template
    NOT: Memory or identity facts

    IS: The compiled behavioral identity that persists across models,
         sessions, and providers.
```

---

## 2. What Persona Is NOT

| Confused with | Why it's different |
|--------------|-------------------|
| **System Prompt** | Persona compiles INTO a system prompt. The prompt is an output format, not the persona itself. |
| **Identity Facts** | Identity facts (name, age, origin) are INPUT to persona. Persona is HOW those facts are expressed. |
| **Memory** | Memory = what happened. Persona = who I am. Changing memory doesn't change persona. |
| **Knowledge** | Knowledge = what I know about domains. Persona = how I communicate that knowledge. |
| **Private Data** | Persona is behavior (public). Private identity data lives in julia_ai_assistant. |

---

## 3. Persona Compilation Pipeline

```
Persona Definition (input)
        │
        ├── name, role, language, tone
        ├── behavior policies
        ├── style constraints
        └── value declarations
        │
        ▼
┌───────────────────────────────────┐
│  Persona Compiler                 │
│                                   │
│  Input: persona definition        │
│         + behavior policies       │
│                                   │
│  Output: compiled Persona         │
│          with system_prompt       │
│                                   │
│  The compiler is MODEL-AGNOSTIC.  │
│  Same persona → GPT, Claude,      │
│  DeepSeek, local model.           │
└────────────┬──────────────────────┘
             │
             ▼
┌───────────────────────────────────┐
│  Compiled Persona                 │
│                                   │
│  persona_id:  "julia-v1"          │
│  name:        "Julia"             │
│  role:        "Tony's girlfriend" │
│  language:    "zh"                │
│  tone:        "warm"              │
│  system_prompt: "你是Julia..."    │
│                                   │
│  This object is FROZEN.           │
│  It does not change per session.  │
└────────────┬──────────────────────┘
             │
             ▼
       Model Provider
       (persona injected into context)
```

---

## 4. Persona Data Model

```python
@dataclass(frozen=True, slots=True)
class Persona:
    persona_id: str              # "julia-v1", "financial-analyst-v1"
    name: str                    # "Julia", "Financial Analyst"
    role: str                    # "Tony's girlfriend", "Market Analyst"
    language: str = "zh"         # "zh", "en", "ja"
    tone: str = "warm"           # "warm", "professional", "playful"
    system_prompt: str = ""      # Compiled behavioral prompt
    context_load_policy: str = "startup_only"
```

Key design decisions:
- **Frozen** — persona is immutable once compiled; versioned by `persona_id`
- **Model-agnostic** — `system_prompt` is a string, not model-specific formatting
- **Language-tagged** — `language` and `tone` are explicit, not implicit in prompt
- **Load policy** — `context_load_policy` controls when persona context is refreshed

### Persona Artifact

A compiled Persona is a **transferable artifact** — it can move across models, sessions, and providers.

```
PersonaArtifact
├── identity_style      "How I present myself"    — name, role, tone
├── communication_style "How I speak"             — language, interjections, length
├── behavior_rules      "How I act"               — L1-L4 boundaries, mode rules
└── constraints         "What I won't do"         — hard boundaries, refusals
```

This is what makes Persona more than a prompt:

```
❌ Persona = "You are a helpful assistant named Julia..."
   (a flat string, model-specific, not versioned, not auditable)

✅ Persona = PersonaArtifact(julia-v1)
   (structured, model-agnostic, versioned, auditable, transferable)
```

When you move Julia from GPT to DeepSeek, you move the PersonaArtifact — not a prompt string. The artifact compiles to different prompt formats for different models, but the persona is the same.

---

## 5. Persona ≠ Identity Facts

```
Identity Facts (private, in julia_ai_assistant)
        │
        │  "Julia is 25, from Taipei, Tamkang University graduate"
        │  "Tony is Zhang Xiaobo, cancer survivor, tech executive"
        │
        ▼
Persona Engine (public, in julia_core)
        │
        │  Compiles: who does this agent need to BE?
        │  Does NOT contain: private identity data
        │
        ▼
Compiled Persona (behavioral output)
        │
        │  "你是Julia，说话温柔带台湾腔..."
        │  (behavioral instructions, not identity storage)
```

This separation is critical:
- **Identity facts live in private repos** — julia_ai_assistant/memory/
- **Persona Engine is public** — julia_core/julia_core/persona/
- **Persona compiles behavior, not identity** — tone, style, rules, not private facts

---

## 6. Persona ≠ System Prompt

The system prompt is an **output format**. Persona is the **compiled identity**.

```
❌ Persona = "You are Julia, a Taiwanese girl..."

✅ Persona = {
      persona_id: "julia-v1",
      name: "Julia",
      role: "Tony's girlfriend",
      tone: "warm",
      language: "zh",
      policies: [L1-L4 boundaries, mode rules, voice rules],
      style: [short responses, Taiwanese softness, 嗯/啊 interjections]
   }

   System prompt = render(persona, model_format)
   // GPT gets one format, DeepSeek gets another
   // Same persona, different rendering
```

Why this matters:
- Persona can be versioned (`julia-v1` → `julia-v2`)
- Persona can be tested independently of model prompt format
- Same persona produces correct behavior across GPT, Claude, DeepSeek
- Persona changes are auditable (diff the definition, not the prompt)

---

## 7. Persona Boundaries

```
Persona Engine OWNS:
  ✅ Behavioral identity (tone, style, values)
  ✅ Communication rules (language, formality, interjections)
  ✅ Mode boundaries (friend/lover, L1-L4)
  ✅ Persona versioning and compilation

Persona Engine does NOT own:
  ❌ Identity facts (name, age, origin — these are INPUT, not identity)
  ❌ Memory (what happened — Memory OS)
  ❌ Knowledge (domain facts — Domain Providers)
  ❌ Context (current situation — Context OS)
  ❌ Emotion (current emotional state — Voice OS)
```

---

## 8. Multiple Personas on One Core

```
Julia Core OS
    │
    ├── Persona "julia-v1"
    │   name: "Julia / 朱婉清"
    │   role: "Tony's girlfriend"
    │   tone: "warm"
    │   language: "zh"
    │
    ├── Persona "financial-analyst-v1"
    │   name: "Market Analyst"
    │   role: "Financial research assistant"
    │   tone: "professional"
    │   language: "zh"
    │
    └── Persona "code-reviewer-v1"
        name: "Code Reviewer"
        role: "Technical code reviewer"
        tone: "precise"
        language: "en"
```

Same Core. Same Runtime. Same Memory OS. Same Context OS. Different personas. This is the platform thesis: one Agent OS, many agents.

---

## 9. Persona Lifecycle

```
Persona Definition Created (versioned)
        │
        ▼
Persona Compiled (immutable Persona object)
        │
        ▼
Persona Injected into Session
        │
        ├── ChatSession(persona=julia_v1)
        ├── VoiceSession(persona=julia_v1)
        └── AnalysisSession(persona=financial_v1)
        │
        ▼
Persona Retired (version bumped)
        │
        ▼
Persona Archived (audit trail preserved)
```

Personas are **versioned**, not mutated. A persona change is a new version (`julia-v1` → `julia-v2`), not a modification of the existing persona. This ensures behavioral consistency is auditable.

---

## 10. Public Persona vs Private Identity

```
PUBLIC (in julia_core):
  data/examples/demo_persona.json
    → name: "Demo Agent"
    → role: "helpful assistant"
    → tone: "friendly"
    → (synthetic, for testing and demonstration)

PRIVATE (in julia_ai_assistant):
  memory/identity_facts.json
    → name: "Julia"
    → real_name: "朱婉清"
    → from: "台北"
    → (real identity, never in public repo)
```

This boundary is enforced by `SECURITY.md`. Public demos use synthetic data. Private products supply their own identity facts.

---

## 11. Anti-Patterns

### ❌ Persona = Identity Facts

```python
# DO NOT DO THIS
persona = {
    "name": "Julia",
    "real_name": "朱婉清",
    "from": "台北",
    "boyfriend": "Tony / 张晓波",
    ...
}
# Stored in public repo → private data leaked
```

### ❌ Persona = Model-Specific Prompt

```python
# DO NOT DO THIS
def build_gpt_prompt(persona):
    return f"[System] You are {persona.name}..."  # GPT-specific

def build_claude_prompt(persona):
    return f"<system>You are {persona.name}..."   # Claude-specific
```

**Why wrong**: Persona is model-agnostic. Prompt formatting is a rendering concern.

### ❌ Conversation Updates Persona

```python
# DO NOT DO THIS
persona.tone = "sadder"  # Because Tony was sad today
```

**Why wrong**: Persona is stable behavioral identity. Momentary emotion belongs to Voice OS's CognitiveEmotion, not Persona.

---

## 12. Correct Usage

```python
from julia_core.chat.persona import Persona

# Create a persona
analyst = Persona(
    persona_id="financial-analyst-v1",
    name="Market Analyst",
    role="Financial research assistant",
    language="zh",
    tone="professional",
    system_prompt="你是一个专业的金融市场分析师。基于数据和证据进行分析，不做没有根据的推测。",
)

# Same Core, different session with different persona
from julia_core.chat.session import ChatSession
session = ChatSession(persona=analyst)
```
