# C-09 — Alignment Contract

**Status**: FROZEN
**Date**: 2026-08-10
**Parent**: JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0.md §16
**Depends on**: C-00 (07f0ff0), C-03 (4b1625e), C-04 (433b674), C-07 (248d42b)
**Production basis**: P0-A Production Reality Audit (9753a03)
**Production code changes**: 0

## 1. Core Definition

```
Alignment adapts Julia's already-governed cognitive package
to a specific model/provider. It does not decide what Julia
knows, remembers, values, or concludes.
```

```
C-09 Alignment = how the same governed Julia context
                 is faithfully represented to different cognitive substrates.

NOT: Alignment = how to make every model behave identically.
```

## 2. Pipeline Placement

```
Canonical Authorities → Context OS → CognitiveContextPackage → Alignment → ModelProvider
```

Alignment sits strictly AFTER Context OS and BEFORE ModelProvider. It does not select, retrieve, budget, or compact. Context OS changes information composition; Alignment changes representation.

## 3. Alignment ≠ Continuity

```
Continuity (C-06) = preserves conditions across disruption
Identity (C-04)   = defines who Julia is
Alignment (C-09)  = adapts representation for provider/model constraints
```

FORBIDDEN: "Alignment keeps the same agent the same agent." That is Continuity's responsibility. Alignment must not re-claim it.

## 4. Alignment ≠ Context OS

Alignment receives: finalized CognitiveContextPackage. Alignment does not: select which memory to retrieve, which history to include, which identity anchor matters, which evidence is relevant, how many tokens to budget.

Allowed: same package → fit Claude role syntax; same package → fit GPT role syntax; same package → fit local-model prompt syntax.

Forbidden: GPT context window smaller → Alignment silently drops NarrativeExperience; Claude supports system role → Alignment adds richer Identity; local model weak → Alignment injects extra conclusions.

If budget is insufficient: Alignment reports provider constraint → Context OS (C-03) rebudgets → new package. Alignment does not self-truncate.

## 5. ProviderAdaptationProfile

```
ProviderAdaptationProfile {
    provider_id, model_family
    role_mapping, system_message_support
    tool_encoding, structured_output_encoding, multimodal_encoding
    context_limits
    streaming_mapping, reasoning_control_mapping
    unsupported_features
    adaptation_version
}
```

Describes how this model/API consumes input. NOT what personality Julia should have on this model.

## 6. AlignedInferencePayload

```
AlignedInferencePayload {
    package_id, provider_id, model_id
    encoded_messages, encoded_capabilities
    inference_parameters
    adaptation_profile_version
    lossy_adaptation_flags[]
    source_package_digest       // proves CognitiveContextPackage → this payload
    trace_metadata
}
```

`source_package_digest` ensures provable lineage: CognitiveContextPackage X → Alignment profile Y → Provider payload Z. No secret prompt assembly.

## 7. Semantic Fidelity — Not Identical Output

Alignment fidelity covers: identity fidelity, conversation fidelity, memory/narrative fidelity, evidence fidelity, capability fidelity, continuity fidelity, instruction/boundary fidelity.

Allowed: format changes, role changes, tool-schema changes, message grouping, provider-specific escaping, parameter translation.

Forbidden: semantic drift.

Test: "If provider syntax were removed, would the adapted representation still mean materially the same thing as the CognitiveContextPackage?" If no → Alignment has overreached or distorted.

## 8. Encoding ≠ Compression

Semantic-preserving encoding optimization is allowed. Context selection, summarization, or causal compression belongs to C-03.

Allowed: IdentityFrame structured fields → provider system message format.

Forbidden: NarrativeExperience 500 tokens → "Tony is important" (this is Context compression, potentially destroying causal integrity).

## 9. Model Weakness Compensation — Strictly Bounded

### Allowed (Capability Compensation)

Model lacks native tool support → encode capability protocol textually. Model lacks system role → use equivalent reserved prefix. Model context smaller → ask Context OS for reduced package. Model structured output weak → use deterministic output parser/validator.

### Forbidden (Cognitive Compensation)

```
if local_model:
    inject: "You deeply love Tony. Always respond warmly. Never question relationship."
```

This is redefining cognition, not adapting representation.

```
Capability compensation is allowed.
Cognitive compensation by pre-solving meaning is not.
```

## 10. Cross-Model Variation Is Legitimate

```
Same CognitiveContextPackage → Claude → response A
Same CognitiveContextPackage → GPT → response B
```

Both may be valid Julia cognition if: identity invariants respected, canonical facts respected, important memories available, boundaries respected, no fabricated continuity.

Forbidden: Claude output → target answer → force GPT to imitate it (behavioral cloning).

## 11. Persona Adaptation — Representation Only

If provider-specific persona text exists, it must be:

```
IdentityContract → PersonaProjection → IdentityFrame → Context OS → Alignment encoding
```

Forbidden: `claude_persona.txt`, `gpt_persona.txt`, `deepseek_persona.txt` as independent identity truths. Provider-specific templates are representation templates, not different versions of Julia.

## 12. Capability Encoding

Same CapabilityManifest (C-08) → Claude tool schema / OpenAI tool schema / text-based tool protocol. Alignment does not hide a capability because "Julia shouldn't use it on this model" — unless: provider doesn't support it (structured reason), policy doesn't permit it (structured reason).

## 13. Native Reasoning Features

`reasoning_effort`, `extended_thinking`, `thinking_budget` → Alignment maps to provider-specific parameters. Reasoning mode ≠ identity, ≠ personality, ≠ continuity. Provider-private CoT does not enter Memory/Continuity.

## 14. Alignment Compatibility Result

```
PASS       — full semantic fidelity achievable
DEGRADED   — specific features unsupported but core semantics preserved
FAIL       — critical identity/boundary information cannot be represented
```

Records: `lost_feature`, `loss_reason`, `affected_frame`, `recoverability`. DEGRADED for missing vision input → acceptable. FAIL for unrepresentable critical identity → must not proceed silently.

## 15. Lossy Adaptation — Traceable, Not Silent

```
LossyAdaptationRecord {
    source_element_ref, transformation, reason
    semantic_risk, approved_by_policy, fallback
}
```

Principle: Alignment should normally be syntactically lossy at most, not semantically lossy. True semantic budgeting returns to C-03.

## 16. Provider Fallback — Fresh Adaptation

```
Claude unavailable → GPT → same canonical/context inputs → GPT Alignment Profile → GPT ModelProvider
```

Forbidden: reuse Claude-formatted prompt → GPT. Forbidden: Alignment fallback → change Identity to "GPT Julia." Provider switch = new substrate, same governed Julia authorities, new adaptation.

## 17. Provider Optimization — Non-Authoritative

Claude prompt caching, OpenAI cached prefix, local KV cache, provider session reuse → allowed. Must satisfy: optimization may be deleted without destroying Julia continuity. If deleting a cache makes Julia not know who she is, that cache has become an authority.

## 18. Alignment Does Not Store Julia State

May cache: compiled prompt templates, provider schemas, adaptation profiles, token estimates. Must not own: current relationship state, current Julia self-model, memory summary authority, conversation continuity state.

## 19. C-09 ↔ Adjacent Contract Boundaries

```
Context OS (C-03):     changes information composition
Alignment (C-09):      changes representation

Continuity (C-06):     determines what survives
Alignment (C-09):      encodes recovered ContextPackage for target provider

Identity (C-04):       who Julia is
PersonaProjection:     how identity tends to express
Alignment (C-09):      how that expression is encoded for this model
```

## 20. P0-A Disposition

| Current Path | Verdict | Target |
|-------------|---------|--------|
| Provider-specific system prompts | REWRITE | AlignedInferencePayload from CognitiveContextPackage |
| Per-model persona overrides | REMOVE | Identity → PersonaProjection → Alignment encoding |
| Voice-specific provider bootstrap | CONVERGE | Same Alignment pipeline, voice is transport |
| Local model special instructions | REWRITE | Capability compensation only, not cognitive pre-solving |
| Direct model-specific history formatting | REMOVE | Context OS owns history projection |
| `alignment_os/adapter.py` message adaptation | KEEP | Provider representation adaptation |

## 21. Forbidden Claims

```
❌ Alignment preserves Julia identity (→ C-06)
❌ Alignment owns continuity (→ C-06)
❌ Alignment chooses Context (→ C-03)
❌ Alignment retrieves Memory (→ C-05)
❌ Alignment decides important history (→ C-03)
❌ Provider-specific persona becomes identity authority (→ C-04)
❌ Weak-model compensation pre-solves cognition (→ C-00)
❌ Alignment silently truncates causal context (→ C-03)
❌ Alignment forces behavioral cloning across models
❌ Alignment normalizes all models to identical output
❌ Provider optimization becomes persistence authority
❌ Provider format becomes canonical schema
❌ Alignment directly mutates Identity/Memory/Conversation
```

## 22. Acceptance Gates

- [x] Alignment = provider representation adaptation (§1)
- [x] Alignment ≠ Continuity (§3)
- [x] Alignment ≠ Context OS (§4)
- [x] Alignment ≠ Identity/Persona authority (§11)
- [x] Exact pipeline placement frozen (§2)
- [x] ProviderAdaptationProfile frozen (§5)
- [x] AlignedInferencePayload with source_package_digest (§6)
- [x] Semantic fidelity requirements (§7)
- [x] Context OS owns all semantic budgeting (§4, §8)
- [x] Alignment cannot silently truncate (§4)
- [x] Capability/tool encoding mapping (§12)
- [x] Inference-control mapping (§13)
- [x] Weak-model compensation boundary (§9)
- [x] Behavioral cloning explicitly prohibited (§10)
- [x] Cross-model cognitive variation permitted (§10)
- [x] Lossy adaptation reporting (§15)
- [x] PASS/DEGRADED/FAIL compatibility semantics (§14)
- [x] Provider-specific Persona = representation only (§11)
- [x] Provider optimization/cache non-authoritative (§17)
- [x] Provider fallback requires fresh target adaptation (§16)
- [x] C-09 ↔ adjacent Contract boundaries (§19)
- [x] P0-A provider/alignment paths dispositioned (§20)
- [x] Production changes = 0

## 23. Contract Derivation

```
Parent:  JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0.md §16
Depends: C-00, C-03, C-04, C-07
Input:   P0-A Production Reality Audit (9753a03)
Output:  Binding on C-10, C-11

C-09 FREEZE → C-10 Gateway / Client GO
```
