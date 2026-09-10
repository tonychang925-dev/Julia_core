# ENG-01..ENG-06 Convergence Baseline V1

Date: 2026-09-10
Status: OWNER-AUTHORIZED CONVERGENCE EVIDENCE / BRANCH-ONLY
Authority scope: ENG-01..ENG-06 only

## 1. Owner authorization boundary

Authorized:
- exact baseline capture
- C0-03..C0-08 status/hash reconciliation
- isolated branch governance
- current semantic-authority inventory
- ghost-authority lane inventory
- retrofit constitutional conformance matrix
- documentation/scaffolding needed to bind the above evidence

Not authorized in this phase:
- C-04 canonical Identity implementation (ENG-07)
- C-05 MemoryExperience implementation/admission
- C-06 hydration implementation
- C-03 canonical model-visible package implementation
- runtime/provider semantic rebinding
- main mutation
- production cutover
- legacy retirement

## 2. Exact repository baselines

| Repository | Baseline / evidence ref | Purpose |
|---|---|---|
| `tonychang925-dev/Julia_core` | `e2edba9dfff460e3769f93b58491afaf644e6da5` | production/main baseline and base of `mira/persona-architecture-v1` |
| `tonychang925-dev/Julia-AI-Assistant` | `a29d999de52827da401eb8021f057656a468dcef` | current main baseline used for cross-repo authority inventory |
| `tonychang925-dev/julia-persona--extractor` | `13d252e9bb14f05fc8900094bcf2e0b3a904f0c8` | verified V2.6 remote evidence base of `mira/persona-migration-v1` |

Branch isolation policy:

```text
Julia_core main persona semantic mutation = FORBIDDEN
mira/persona-architecture-v1 = authorized ENG-01..06 working branch
mira/persona-migration-v1 = authorized migration preparation branch
main cutover = separate Tony Owner authorization required
```

## 3. C0 contract reconciliation

The exact local contract artifacts supplied for this convergence all state:

`CONTRACT DRAFT / NOT FROZEN / NO IMPLEMENTATION AUTHORITY`

They are binding here as audit/design inputs only; they are not silently promoted to frozen implementation contracts.

| Contract | Version | SHA-256 | Status |
|---|---|---|---|
| C0-03 Canonical Object & Authority Binding | v0.1 | `7b3cfb707ced45413f0ac5bcde8d9eff0a147d19ecdbca1dd8650bb389fab95e` | DRAFT / NOT FROZEN / NO IMPLEMENTATION AUTHORITY |
| C0-04 C-03 Exclusive Model-Visible Admission | v0.1 | `a1709bee5f476f9ff01ce6267b76467db26faacdc88f886b3ce7c3a75ca68c22` | DRAFT / NOT FROZEN / NO IMPLEMENTATION AUTHORITY |
| C0-05 MemoryExperience Ingestion | v0.1 | `817ba55762b5c28f45dfdbed67da424a12221b8273e95a33735d2c413414a92d` | DRAFT / NOT FROZEN / NO IMPLEMENTATION AUTHORITY |
| C0-06 Normal Resume / Continuity Recovery | v0.1 | `b2dc84316b78550bea7e82e0a32804448f829a0f53458cff31f98f8bcae0d7e8` | DRAFT / NOT FROZEN / NO IMPLEMENTATION AUTHORITY |
| C0-07 Semantic Authority Observability & Provenance | v0.1 | `f29ba5a3b0323fd11abbd9d3ed78620e15d3ba63a59e2053c105d970c2c53051` | DRAFT / NOT FROZEN / NO IMPLEMENTATION AUTHORITY |
| C0-08 Legacy Rebinding / Fence / Cutover | v0.1 | `c0a054396a14959d3c90cedf51b06300f1a7db14a5c699c8f0d8c50dd34fb0b3` | DRAFT / NOT FROZEN / NO IMPLEMENTATION AUTHORITY |

Governance namespaces remain distinct:

```text
ARCHITECTURE_DIRECTION_FROZEN
!= CONTRACT_FROZEN
!= ROADMAP_BASELINED
!= IMPLEMENTATION_AUTHORIZED
```

## 4. Current Julia Core implementation inventory at exact base

The current Core is not empty and must be converged rather than replaced. Exact implementation families verified at `e2edba9d...` include:

### Identity / persona
- `julia_core/persona/identity_kernel.yaml`
- `julia_core/persona/canonical_events.yaml`
- `julia_core/self_model/activation.py`
- `julia_core/self_model/archive_recall.py`
- `julia_core/self_model/relationship.py`
- `julia_core/self_model/self_model.py`
- `julia_core/persona/**`

`identity_kernel.yaml` currently mixes identity, biography, appearance, daily-life preferences, relationship data, voice and values. It therefore cannot be treated as the future C-04 canonical object without governed decomposition.

### Memory / experience
- `julia_core/memory/**`
- `julia_core/memory_runtime.py`
- `julia_core/experience/**`
- `julia_core/narrative/**`

### Continuity / recovery
- `julia_core/continuity/checkpoint.py`
- `julia_core/continuity/contracts.py`
- `julia_core/continuity/memory_binding.py`
- `julia_core/continuity/memory_governance_adapter.py`
- `julia_core/continuity/policy.py`
- `julia_core/continuity/recovery.py`
- `julia_core/continuity/trace.py`
- `julia_core/continuity/trigger.py`

These are KEEP / COMPLETE-HYDRATION candidates, not demolition targets.

### C-03 / context assembly
- `julia_core/context_os/block.py`
- `julia_core/context_os/planner.py`
- `julia_core/context_os/continuity_adapter.py`
- `julia_core/context_os/evidence_context.py`
- `julia_core/context_os/reconstruction.py`
- `julia_core/context_os/budget_model.py`
- `julia_core/context_os/priority_model.py`
- `julia_core/context_os/providers/**`
- `julia_core/context_assembly/**`

### Runtime / downstream
- `julia_core/runtime/**`
- `julia_core/providers/interface.py`
- `julia_core/providers/registry.py`
- `julia_core/providers/streaming.py`
- `julia_core/providers/voice_provider.py`
- `julia_core/alignment_os/**`
- `julia_core/voice/**`
- `julia_core/voice_os/**`

### Relationship semantic sources
- `julia_core/relationship/**`
- `julia_core/self_model/relationship.py`

## 5. Verified ghost-authority / bypass lanes

### GHOST-01 — mixed identity kernel
`julia_core/persona/identity_kernel.yaml`

Current file self-labels as an immutable constitutional identity kernel while containing biography, appearance, preferences, relationship and voice semantics. Disposition: `MIGRATE + DECOMPOSE + FENCE`; do not reinterpret it as the new C-04 schema.

### GHOST-02 — SelfModel family
`julia_core/self_model/**`

Mixed self/biography/relationship/archive activation semantics. Disposition: `REBIND`; retain useful reconstruction mechanics but remove independent durable semantic authority after canonical paths exist.

### GHOST-03 — Assistant self activation renderer
Cross-repo current main: `Julia-AI-Assistant/runtime/assistant_runtime.py::_self_activation_context_text()`.

Verified current implementation constructs model-visible self/relationship reconstruction text outside the future exclusive C-03 admission boundary. Disposition: `FENCE / REPLACE WITH TYPED FRAMES` in later authorized wave.

### GHOST-04 — Assistant semantic context renderer
Cross-repo current main: `Julia-AI-Assistant/runtime/assistant_runtime.py::_semantic_context_text()`.

Verified current implementation renders governed blocks into model-visible semantic text. Governed source is not equivalent to governed model-visible admission. Disposition: `FENCE / REPLACE WITH C-03 PACKAGE CONSUMPTION` in later authorized wave.

### GHOST-05 — provider/persona semantic capability
`julia_core/providers/**` and current provider-facing persona surfaces remain downstream audit targets. Disposition: runtime/provider may serialize representation but must not become canonical durable Identity/Memory semantic authority.

### GHOST-06 — Alignment / Voice semantic mutation surfaces
`julia_core/alignment_os/**`, `julia_core/voice/**`, `julia_core/voice_os/**` remain explicit later-wave bypass audit targets. Post-C03 representation-only transformation is allowed only when semantic fidelity is preserved.

## 6. Core Retrofit Constitutional Conformance Matrix

| Area | Current seam | Target ownership | ENG-01..06 disposition | Later implementation wave |
|---|---|---|---|---|
| Identity | `persona/identity_kernel.yaml`, `self_model/**` | C-04 governed Identity | CONFIRMED GAP; reuse/migrate, do not duplicate | ENG-07+ |
| Lived history | `memory/**`, `experience/**`, narrative/self archives | C-05 five-type MemoryExperience | CONFIRMED GAP; classify and bind provenance | ENG-09+ |
| Continuity | `continuity/**` | C-06 refs/recovery | SUBSTANTIAL KEEP; canonical hydration seam incomplete | ENG-11+ |
| Model-visible admission | `context_os/**` plus cross-repo renderers | C-03 exclusive semantic admission | PARTIAL INFRASTRUCTURE; exclusivity not proven | ENG-12+ |
| Runtime/provider | `runtime/**`, `providers/**` | consume admitted package; no durable semantic authority | REBIND TARGET | ENG-13+ |
| Alignment/voice | `alignment_os/**`, `voice/**`, `voice_os/**` | representation only after C-03 unless separately admitted | BYPASS WATCH | ENG-13/14+ |
| Observability | continuity/context traces and existing evidence infra | semantic authority provenance | KEEP + EXTEND | ENG-14+ |
| Legacy | persona/self/relationship/memory prompt-era sources | historical/migration evidence only after cutover | FENCE, DO NOT DELETE | ENG-20+ |

## 7. ENG-01..06 convergence conclusion

```text
ENG-01 BASELINES = CAPTURED
ENG-02 C0 STATUS/HASH = RECONCILED; ALL SIX CONTRACTS REMAIN DRAFT
ENG-03 JULIA CORE ISOLATED BRANCH = PRESENT
ENG-04 PERSONA EXTRACTOR MIGRATION BRANCH = PRESENT
ENG-05 BRANCH/TASK GOVERNANCE = BOUND BY THIS ARTIFACT; MAIN MUTATION FORBIDDEN
ENG-06 RETROFIT CONFORMANCE MATRIX = ESTABLISHED

ARCHITECTURE REDESIGN REQUIRED = NO
AUTHORITY CONVERGENCE REQUIRED = YES
SECOND PARALLEL CORE = FORBIDDEN
ENG-07 IMPLEMENTATION = NOT STARTED BY THIS COMMIT
```

Next gate: separate bounded authorization/task contract for ENG-07 canonical Identity minimal slice. Until that gate, this branch may carry convergence evidence/scaffolding only.