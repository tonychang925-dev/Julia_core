# Alignment OS Design v1.0

## Purpose

Alignment OS is a Julia Core subsystem that keeps an agent's identity and behavior contract stable across different providers.

It answers one Core OS question:

> When the model provider changes, how does the same agent remain the same agent?

Alignment OS is not a product prompt template and not a system-prompt string builder. It owns provider-neutral behavior contracts and provider-specific expression profiles that are consumed by runtimes before provider calls.

## Boundary

Alignment OS owns:

- provider-neutral behavior contracts
- provider behavior profiles
- provider capability / boundary metadata
- adaptation request / profile resolution
- prompt-message adaptation as an implementation adapter

Alignment OS does not own:

- private persona facts
- private memories
- domain-provider facts
- voice rendering
- action execution authority
- provider API clients

## Runtime Flow

```text
User
  |
Runtime
  |
Persona Engine
  |
Alignment OS
  |
Provider
```

The runtime sends an `AlignmentRequest` containing provider, persona key, and mode. Alignment OS returns an `AlignmentProfile` containing a provider-neutral `AlignmentContract` and a provider-specific `ProviderBehaviorProfile`.

## Core Data Contracts

```python
AlignmentRequest(
    provider="deepseek",
    persona="julia",
    mode="private_voice_continuity",
)
```

returns:

```python
AlignmentProfile(
    provider_id="deepseek",
    persona_id="julia",
    mode="private_voice_continuity",
    contract=AlignmentContract(...),
    provider_profile=ProviderBehaviorProfile(...),
)
```

The provider profile may declare structured ceilings through generic behavior constraints such as `BehaviorConstraint(dimension="intimacy", max="L4")`. Product-private meaning belongs to the product persona/memory package, not to Core.

## Package Layout

```text
julia_core/alignment_os/
├── __init__.py
├── contracts.py
├── registry.py
├── resolver.py
├── adapter.py
└── policies/
    ├── __init__.py
    ├── intimacy_policy.py
    ├── safety_policy.py
    └── expression_policy.py
```

## Design Principles

1. Alignment belongs to Core, not a domain product.
2. Provider-specific adaptation must not change identity, memory, or action authority.
3. Persona defines who the agent is; Alignment OS defines how behavior boundaries survive provider differences.
4. Memory defines what happened; Alignment OS does not store product-private experiences.
5. Providers execute capabilities; Alignment OS supplies runtime-owned behavioral metadata for provider behavioral alignment.

## Initial Frozen Profiles

The canonical API is generic `BehaviorConstraint`; any `max_intimacy_level` access is a derived compatibility view, not a Core field.

| Persona | Provider | Mode Domain | Profile | Strategy | Canonical Constraint |
|---|---|---|---|---|---|
| julia | deepseek | private_voice | `julia.deepseek.private_voice.identity_anchored.v1` | `identity_anchored_expression` | `intimacy.max=L4` |
| julia | codex/openai/gpt | private_voice | `julia.<provider>.private_voice.warm_intimate_boundary.v1` | `warm_intimate_boundary` | `intimacy.max=L3` |
| any | deepseek/codex/openai/gpt | technical | `*.technical.precision.v1` | `trace_grounded_precision` | `technical_depth.level=expert` |
| any | any | emotional/general | `*.stable_voice.v1` | `stable_julia_voice` / `stable_agent_voice` | `empathy.level=high` / optional `intimacy.max=L1` |

These profiles are generic Core metadata. Product packages remain responsible for their own persona and memory content.
