# Create a Domain Provider

> **What you'll build**: A provider that supplies domain facts and evidence to your agent  
> **Time**: ~30 minutes  
> **Prerequisites**: [Build Your First Agent](BUILD_YOUR_FIRST_AGENT.md)

---

## What is a Domain Provider?

A Domain Provider supplies **facts and evidence** — not reasoning, not prompts, not identity.

```
Context OS asks: "What does the agent need to know?"
        │
        ▼
Domain Provider answers: "Here are the relevant facts."
        │
        ▼
ContextBlock(s) returned to Context OS for assembly.
```

---

## The Provider Contract

Every Domain Provider must implement this contract:

```python
# Input: ContextRequest — "what does the agent need?"
# Output: ContextBlock(s) — "here are the relevant facts"

class DomainProvider(Protocol):
    provider_id: str

    def resolve(self, request: ContextRequest) -> list[ContextBlock]:
        """Supply facts and evidence for this request."""
        ...
```

### ContextRequest (Input)

```python
ContextRequest(
    task_intent="market_review",     # What the caller wants
    intent="analysis",               # Cognitive intent
    domain="financial",              # Target domain
    domain_object_type="theme",      # What kind of thing
    domain_object_id="9043089",      # Which specific thing
    target_budget_tokens=4000,       # Token budget
)
```

### ContextBlock (Output)

```python
ContextBlock(
    source="financial_provider_v1",   # Your provider identity
    content={"market_data": ...},     # Domain facts (opaque to Core)
    authority="market_intelligence",  # What authority does this come from?
    evidence_refs=("src_001",),       # Traceable data references
    authority_score=0.85,             # 0.0 - 1.0
    ttl_seconds=3600,                 # How long before this expires?
)
```

---

## Step-by-Step

### Step 1: Create your provider

```python
# my_providers/weather_provider.py
from julia_core.context_os.request import ContextRequest
from julia_core.context_os.block import ContextBlock
from julia_core.providers.interface import DomainProvider


class WeatherProvider(DomainProvider):
    provider_id = "weather_provider_v1"

    def resolve(self, request: ContextRequest) -> list[ContextBlock]:
        # Only respond to weather-related requests
        if request.domain != "weather":
            return []

        # Extract what we need from the request
        city = request.payload.get("city", "unknown")

        # Fetch facts (replace with real API call)
        weather_data = self._fetch_weather(city)

        # Return as ContextBlock(s)
        return [
            ContextBlock(
                source=self.provider_id,
                content={
                    "city": city,
                    "temperature": weather_data["temp"],
                    "condition": weather_data["condition"],
                },
                authority="weather_api",
                evidence_refs=(f"weather_{city}_{weather_data['timestamp']}",),
                authority_score=0.8,
                ttl_seconds=1800,  # Weather data expires in 30 min
            )
        ]

    def _fetch_weather(self, city: str) -> dict:
        # Your data fetching logic here
        return {"temp": 22, "condition": "sunny", "timestamp": "2026-08-01T12:00:00Z"}
```

### Step 2: Register your provider

```python
from julia_core.providers.registry import ProviderRegistry

registry = ProviderRegistry()
registry.register(WeatherProvider())
```

### Step 3: Use in context resolution

```python
from julia_core.context_os.request import ContextRequest
from julia_core.context_os.planner import ContextPlanner
from julia_core.context_os.resolver import ContextResolver

# Create request
request = ContextRequest(
    task_intent="weather_check",
    intent="query",
    domain="weather",
    payload={"city": "Taipei"},
)

# Plan context needs
planner = ContextPlanner()
plan = planner.plan(request)

# Resolve — your provider is called here
resolver = ContextResolver(registry=registry)
blocks = resolver.resolve(request)

for block in blocks:
    print(f"Source: {block.source}")
    print(f"Content: {block.content}")
    print(f"Authority: {block.authority} (score: {block.authority_score})")
```

---

## Provider Lifecycle

```
REGISTERED     Provider known to Registry
    │
    ▼
ACTIVE         Provider responding to requests
    │
    ▼
DISABLED       Provider removed from resolution (graceful degradation)
```

---

## Provider Rules

### ✅ Your Provider MUST

| Rule | Why |
|------|-----|
| Return `list[ContextBlock]` | Standard output — empty list if not applicable |
| Include `evidence_refs` | Every fact must be traceable to source data |
| Set appropriate `ttl_seconds` | Stale data should expire, not mislead |
| Be domain-specific | Weather provider handles weather. Not everything. |
| Return quickly | Context resolution is synchronous per turn |

### ❌ Your Provider MUST NOT

| Rule | Why |
|------|-----|
| Assemble prompts | Provider output is `ContextBlock`, not prompt text |
| Write to memory | Memory writes require governance. Provider has no memory access. |
| Own context | Context assembly belongs to Context OS |
| Decide what the model sees | Provider supplies candidates; Resolver selects |
| Include reasoning in output | Facts, not judgments. "Price is $100" not "Price is high." |

---

## Anti-Patterns

### ❌ Provider Returns a Prompt

```python
# DO NOT DO THIS
class BadProvider:
    def resolve(self, request):
        return f"As a financial analyst, consider the following market data..."
        # This is a PROMPT, not a ContextBlock.
```

**Correct**: Return structured `ContextBlock` with facts. Context OS assembles the prompt.

### ❌ Provider Writes to Memory

```python
# DO NOT DO THIS
class BadProvider:
    def resolve(self, request):
        data = self.fetch_data()
        self.memory.save(data)  # DIRECT WRITE — no governance!
        return [ContextBlock(...)]
```

**Correct**: Return `ContextBlock`. Memory OS governance layer decides what to persist.

### ❌ Provider Handles Multiple Domains

```python
# DO NOT DO THIS — "God Provider"
class EverythingProvider:
    def resolve(self, request):
        if request.domain == "weather": ...
        elif request.domain == "financial": ...
        elif request.domain == "medical": ...
        elif request.domain == "coding": ...
```

**Correct**: One provider per domain. Multiple small providers > one giant provider.

---

## Reference Implementation

See `julia_core/providers/examples/` for a complete Hello World provider:

```bash
julia_core/
└── providers/
    └── examples/
        └── hello_provider.py    ← Minimal DomainProvider example
```

---

## Next Steps

- Learn about the DomainProvider protocol: [Provider API](../api/Provider_API_v1.md)
- Understand ContextRequest/ContextBlock: [Context OS API](../api/Context_OS_API_v1.md)
- Add voice: [Create a Voice Provider](CREATE_VOICE_PROVIDER.md)
- Define personality: [Create a Persona](CREATE_PERSONA.md)
