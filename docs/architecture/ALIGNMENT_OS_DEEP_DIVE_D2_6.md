# D2.6 — Alignment OS Deep Dive

## Core Question

Same Persona + Different Providers = Different Behavior.

Alignment OS exists so Runtime can preserve the same agent identity and behavior envelope across provider differences.

## Authority Split

| Layer | Owns | Does Not Own |
|---|---|---|
| Persona Engine | identity definition, style, stable persona facts | provider-specific adaptation |
| Alignment OS | behavior contracts, capability-aware constraints, provider profiles | private memory, persona truth, provider execution |
| Provider Layer | inference/audio/domain capability execution | identity, memory authority, behavior policy |
| Memory OS | stored experiences and governed recall | provider-specific behavior adaptation |

## Generic Constraint Model

Alignment OS uses generic behavior constraints:

```python
BehaviorConstraint(dimension="intimacy", max="L4")
BehaviorConstraint(dimension="technical_depth", level="expert")
BehaviorConstraint(dimension="empathy", level="high")
```

This prevents Julia-specific fields from becoming universal Core API.

## Provider Behavioral Alignment

Alignment OS is provider-wide, not LLM-only. Future provider classes may include:

- LLM providers: model behavior and expression profile
- Voice providers: emotion fidelity, style tags, latency/capability constraints
- Avatar providers: expression and gesture capability constraints
- Domain providers: evidence / authority constraints when relevant

## Initial Profiles

| Persona | Provider | Domain | Constraint | Profile |
|---|---|---|---|---|
| julia | deepseek | private_voice | `intimacy.max=L4` | `identity_anchored` |
| julia | codex/openai/gpt | private_voice | `intimacy.max=L3` | `warm_intimate_boundary` |
| any | any | technical | `technical_depth.level=expert` | `trace_grounded_precision` |
| any | any | emotional | `empathy.level=high` | `stable_voice` |
