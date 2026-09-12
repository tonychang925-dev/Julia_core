# P3 Seam Authority Resolution — Canonical Runtime/Provider Contract V1

Status: FROZEN CONTRACT
Task: Julia_core issue #59
Base: `c4ded0a1c97ad485a74dd9fad5b55db34d8e3c03`
Authority scope: contract only; this document grants no merge, cutover, production-implementation, canonical-write, Golden Mira admission, release, or deploy authority.

## 1. Decision

The canonical production chain is:

```text
Canonical projection objects
  └─> Exact C03 admission request
        └─> ExclusiveAdmissionGate.seal()
              └─> SealedCognitiveContextPackage [digest manifest only]
                    └─> ExactAdmittedSemanticBinder.bind()
                          └─> AdmittedSemanticBundle [exact semantic content]
                                └─> JuliaAssistantRuntime [turn transport]
                                      └─> AlignmentBoundary.resolve()
                                            └─> ProviderExecutionEnvelope
                                                  └─> Provider transport
                                                        └─> Model
```

The sealed package never carries semantic content. Semantic content is bound from the exact admitted frame objects after package verification, and only `ExactAdmittedSemanticBinder` may construct that bundle.

## 2. Canonical production-chain ownership

| Edge | Input owner | Output owner | Non-owner invariant |
|---|---|---|---|
| Canonical object production | `julia_core/projection/contracts.py` for `IdentityFrame`, `ExperienceFrame`; `julia_core/context_admission/contracts.py` for `CurrentConversationalTaskContext` | Canonical projection producer lane | No runtime, provider, Alignment, or Assistant module may create or repair these objects. |
| C03 package production | `julia_core/context_admission/gate.py::ExclusiveAdmissionGate` | `SealedCognitiveContextPackage` | The gate retains no content and emits no partial package. |
| Admitted semantic binding | Future `julia_core/context_admission/semantic_binding.py::ExactAdmittedSemanticBinder` | `AdmittedSemanticBundle` | This is the sole semantic-bundle constructor; Runtime, Alignment, Provider, and fence modules cannot construct it. |
| Runtime consumer | `julia_core/runtime/assistant_runtime.py::JuliaAssistantRuntime` | Runtime turn event/transport result | Runtime performs no semantic selection, reconstruction, merging, rewriting, or fallback. |
| Alignment boundary | `julia_core/alignment_os/adapter.py::ProviderAlignmentBoundary` | `ProviderExecutionEnvelope` plus non-semantic `AlignmentExecutionMetadata` | Alignment has exactly zero semantic authority after C03. |
| Provider consumer | Julia-AI-Assistant provider implementations under `providers/llm/` | Provider transport response/stream | Providers may not accept Persona, arbitrary messages, chat history, or prompt-building inputs. |
| Provenance/fence | Julia-AI-Assistant `runtime/semantic_provenance_fence.py::SemanticProvenanceFence` at accepted SHA `87eb86fc1ceeaa434bf269a18bf96c007d35f056` | Machine-readable observation or rejection | Fence is observability only; it is not a runtime/provider business path and never constructs semantics. |

### 2.1 Repo/module ownership map

| Responsibility | Exact future owner | Explicitly excluded |
|---|---|---|
| C03 package production | Julia_core `/julia_core/context_admission/gate.py` | Assistant runtime, Assistant fence, Alignment OS, providers |
| Admitted semantic binding | Julia_core `/julia_core/context_admission/semantic_binding.py` | `alignment_os`, `runtime/assistant_runtime.py`, all Assistant modules |
| Runtime consumer | Julia_core `/julia_core/runtime/assistant_runtime.py` | Assistant business runtime, providers, HTTP/client/voice layers |
| Alignment boundary | Julia_core `/julia_core/alignment_os/adapter.py` and exact metadata contracts in `/julia_core/alignment_os/contracts.py` | Semantic binding, providers, Assistant modules |
| Provider consumer | Julia-AI-Assistant `/providers/llm/*` | Runtime semantic construction, Alignment semantic construction, Persona loading |
| Provenance/fence | Julia-AI-Assistant `/runtime/semantic_provenance_fence.py` | Runtime/provider business path and canonical semantic writes |
| Same-session history source | Canonical ConversationRuntime before C03 | Provider-side history, Runtime-side history after C03, model-inferred history |

## 3. Exact seam type contract

Python notation below is normative. Every consumer must use `type(value) is ExactType`; subclass, duck-typed, serialized, reconstructed, or name-forged values fail closed.

| Seam | Exact input | Exact output | Validation and failure result |
|---|---|---|---|
| E0a identity projection | `IdentityFrame` | `IdentityFrame` | Exact type, canonical schema/policy/status/provenance, deterministic `digest()`. Any exception or inexact value raises `C03AdmissionRejected`. |
| E0b experience projection | `ExperienceFrame` | `ExperienceFrame` | Same exact-type/fail-closed rule as E0a. |
| E0c current task projection | `CurrentConversationalTaskContext` | `CurrentConversationalTaskContext` | Exact type and bounded JSON tree; canonical ConversationRuntime provenance only. |
| E1 C03 sealing | `ExclusiveAdmissionRequest(identity_frame: IdentityFrame, experience_frame: ExperienceFrame, current_task_context: CurrentConversationalTaskContext)` | `SealedCognitiveContextPackage` | Gate recomputes all three canonical digests and package receipt. Missing/partial/forged input raises `C03AdmissionRejected`; no package is returned. |
| E2 semantic binding | `SemanticBindingRequest(package: SealedCognitiveContextPackage, identity_frame: IdentityFrame, experience_frame: ExperienceFrame, current_task_context: CurrentConversationalTaskContext)` | `AdmittedSemanticBundle` | Verify package first, bind exact source objects, recompute each `to_dict()` digest, and compare all three to `package.admitted_frames`. Any mismatch raises `C03AdmissionRejected` before Runtime receives a value. |
| E3 runtime ingress | `RuntimeTurnRequest(binding: AdmittedSemanticBundle, provider_id: str, stream: Literal[True], input_mode: str)` | `Iterator[RuntimeStreamEvent]` or equivalent typed turn result | Exact `AdmittedSemanticBundle`; no raw `message`, package, frames, Persona, or history field is permitted. |
| E4 alignment | `AlignmentBoundaryRequest(binding: AdmittedSemanticBundle, provider_id: str, cognitive_mode: str)` | `ProviderExecutionEnvelope` | Resolver reads only execution/style controls and already-bound transport messages. It cannot add, remove, reorder, merge, or mutate semantic text. |
| E5 provider ingress | `ProviderExecutionEnvelope` | Provider-native response or stream events | Exact type check before transport. Providers may map `messages` and non-semantic execution controls to their API, but cannot read or reconstruct Persona/history. |
| E6 provider transport | `ProviderExecutionEnvelope`, exact provider credentials/config, non-semantic `ProviderExecutionControls` | Provider response/stream | Credential/network/provider errors propagate; no semantic fallback or alternate authority. |
| E7 provenance observation | Exact package metadata plus exact per-frame digest evidence | `SemanticProvenanceObservation` or `SemanticProvenanceRejection` | Accepted fence behavior at SHA `87eb86f...`; metadata-only observation, not content construction or business routing. |

### 3.1 `AdmittedSemanticBundle`

```python
@dataclass(frozen=True, slots=True)
class AdmittedSemanticUnit:
    frame_name: Literal[
        "identity_frame", "experience_frame", "current_task_context"
    ]
    role: Literal["system", "system", "user"]
    semantic_digest: str  # lowercase SHA-256, exactly 64 hex characters
    canonical_content: str  # canonical_json(source.to_dict())


@dataclass(frozen=True, slots=True)
class AdmittedSemanticBundle:
    contract_version: str
    conversation_id: str
    turn_id: str
    gate_receipt: str
    package_digest_manifest: Mapping[str, str]
    units: tuple[AdmittedSemanticUnit, ...]  # exactly three, in the fixed order
```

Fixed unit order is `identity_frame`, `experience_frame`, `current_task_context`. Fixed roles are `system`, `system`, `user`. `semantic_fingerprint()` is SHA-256 over canonical JSON of the fixed `[{role, content}, ...]` tuple. Re-verification repeats package verification, exact source/type checks, digest recomputation, manifest equality, duplicate checks, and order checks.

### 3.2 `ProviderExecutionEnvelope`

```python
@dataclass(frozen=True, slots=True)
class ProviderExecutionEnvelope:
    conversation_id: str
    turn_id: str
    gate_receipt: str
    semantic_fingerprint: str
    messages: tuple[dict[str, str], ...]  # exact three bound messages
    alignment: AlignmentExecutionMetadata  # non-semantic controls only
```

`AlignmentExecutionMetadata` may contain only provider-neutral identifiers and mechanically enforced execution/style controls such as response format, bounded generation controls, safety constraints, and modality. It must not contain `persona`, `persona_id`, `persona.system_prompt`, identity, relationship, experience, memory, history, evidence, capability, or prompt text.

## 4. Binding and digest equality

1. C03 recomputes source-frame digests while sealing and includes those digests in the package manifest and receipt.
2. `ExactAdmittedSemanticBinder` is the exact place where package/frame digest equality is checked after package verification.
3. The binder canonicalizes each exact admitted source with `to_dict()`, recomputes its SHA-256 digest, and requires equality with `SealedCognitiveContextPackage.admitted_frames[frame_name]`.
4. It also requires all three and only all three frames, fixed order, fixed roles, and no duplicate frame names or digests where duplication indicates ambiguity.
5. Runtime receives only the resulting `AdmittedSemanticBundle`; it never sees an independent frame set.
6. The Assistant provenance fence may recheck package/unit digest metadata for observation, but is not a second content-binding authority.

## 5. Same-session history

- Before C03, canonical ConversationRuntime may use governed same-session history as an input to `CurrentConversationalTaskContext`.
- Once C03 seals the package, same-session history is transport/provenance state only and has no semantic authority.
- Runtime must not append, merge, replay, summarize, filter, or infer history after C03.
- Provider must not receive an independent history array, prior transport messages, or same-session transcript.
- Any API compatibility representation must be a transport projection of the already-bound current-task unit only; no additional model-visible history unit may be created.
- A stale conversation ID, turn ID, or source reference fails closed rather than selecting newer/older history.

## 6. Alignment rule

Alignment is a non-semantic execution boundary immediately before provider ingress. It may select bounded execution/style metadata and provider transport controls. It has zero authority to mutate post-C03 semantics.

Forbidden after C03:

- prepend, append, wrap, or render alignment prose into `messages`;
- add a system prompt or Persona prompt;
- select, rank, summarize, translate, soften, intensify, or rewrite admitted content;
- merge frames or inject history;
- fill missing semantic units from defaults, caches, model behavior, or best-effort recovery;
- retry with a different semantic bundle.

The output semantic fingerprint must equal the input binding fingerprint byte-for-byte at every provider ingress.

## 7. Provider rule

The only provider semantic input is exact `ProviderExecutionEnvelope.messages`. Provider implementations are transport and model-call owners only.

Providers must not:

- accept a Persona object or `persona.system_prompt`;
- load identity, relationship, experience, or memory sources;
- construct identity, relationship, experience, or memory semantics;
- infer missing Julia continuity from model priors;
- accept arbitrary messages or chat history;
- invoke prompt-building or behavior-rendering fallback;
- silently degrade to a generic assistant or alternate persona.

Missing, invalid, or non-exact envelope type, manifest, receipt, fingerprint, provider dependency, or transport configuration raises/returns the typed fail-closed error for that seam. Provider unavailability does not authorize semantic substitution.

## 8. Fail-closed matrix

| Condition | Mandatory result |
|---|---|
| Missing package, frame, binding, envelope, provenance, or provider dependency | Typed fail-closed rejection before next seam; zero output events/calls |
| Forged package receipt, frame digest, source serialization, package digest, or semantic fingerprint | `C03AdmissionRejected` or provider-equivalent typed rejection; no partial admission |
| Partial frame set or missing provider execution metadata | Reject; never construct a default unit or unaligned request |
| Mismatched conversation ID, turn ID, provenance ref, frame digest, or package receipt | Reject; never repair or select another source |
| Stale package/frame/provenance input | Reject; no newer/older history substitution |
| Ambiguous duplicate frame/unit/provider input | Reject; no ordering heuristic or best guess |
| Wrong exact type, subclass, serialized mapping, or forged module/name | Reject before reading semantic content |
| Alignment or provider transport failure | Propagate typed error; no semantic fallback, mock, stub, shadow path, or silent degradation |

Every rejection is machine-readable, has `partial_admission=false`, and records no invented provenance. Retry is permitted only at an explicitly owned transport seam with the exact same envelope and no semantic mutation.

## 9. A/B compatibility disposition

### 9.1 Candidate A — Julia_core `aaa78b50ba9dfc10c57bfd31c4ccf73415a01417`

| File/symbol | Decision | Rationale |
|---|---|---|
| `julia_core/runtime/assistant_runtime.py::RuntimeStreamRequest.context_package` | DROP | Runtime must consume an already-bound `AdmittedSemanticBundle`, not rebind package/frames. |
| `RuntimeStreamRequest.message` | DROP | Raw runtime text creates post-C03 semantics; current-task unit is authoritative. |
| Exact package type and conversation-ID checks | ADAPT | Preserve fail-closed checks at binding/runtime ingress, but move equality to the binder. |
| `RuntimeBindingTrace` | ADAPT | Keep bounded provenance/trace fields only; remove semantic payloads and duplicate authority claims. |
| `JuliaAssistantRuntime` | ADAPT | Preserve it as the sole Runtime consumer/transport owner after ingress changes to `AdmittedSemanticBundle`. |
| `_provider_request` package-as-system-context directive | DROP | Sealed manifest is not semantic content and must not become a prompt. |
| `julia_core/context_admission/gate.py::ModelVisibilityTransport` | KEEP | Validation-only C03 transport remains useful for package observation; it is not the semantic-binding owner. |
| `tests/runtime/test_eng13c_assistant_runtime_rebind.py` | ADAPT | Retain no-forged-package/no-local-authority expectations; replace package-only provider payload with exact binding/envelope assertions. |

### 9.2 Candidate B — Core `d7853472233a0b4514308255eea231b0d85e523c`, Assistant `f41ff37c950d1c4390a77afca2fec8cdc0706a43`

| Repo/file/symbol | Decision | Rationale |
|---|---|---|
| Core `alignment_os/contracts.py::AdmittedSemanticUnit` | ADAPT | Correct binding shape, but move to `context_admission/semantic_binding.py` and require exact canonical source types. |
| Core `AdmittedSemanticBundle.from_sources` | ADAPT | Preserve digest-binding intent, rename to exact binder entry, and make package/frame equality the sole binding authority. |
| Core `ProviderExecutionEnvelope` | ADAPT | Add conversation/turn/receipt/fingerprint and separate non-semantic alignment metadata; do not carry a Persona-bearing profile. |
| Core `ProviderBehaviorAdapter.adapt_messages` | KEEP AS FAIL-CLOSED REMNANT DURING IMPLEMENTATION | Preserve rejection of arbitrary messages/persona, then remove under the separately gated destructive-legacy task. |
| Core `ProviderBehaviorAdapter.render_admitted` | ADAPT | Rename to `ProviderAlignmentBoundary.resolve`; consume exact binding and produce envelope without semantic mutation. |
| Core `AlignmentRequest.persona` | DROP | Alignment must be persona-free. |
| Core `ProviderBehaviorProfile.persona_id`, guidance/prefer/avoid/fallback strings, `render_lines` | DROP | These become prompt semantics and violate zero post-C03 mutation. |
| Core structured execution constraints | ADAPT | Move only mechanically enforceable fields into `AlignmentExecutionMetadata`. |
| Assistant `DeepSeekProvider.build_messages(semantic_bundle)` | ADAPT | Change input to exact `ProviderExecutionEnvelope`; move Core boundary invocation upstream to Runtime. |
| Assistant `DeepSeekProvider.chat` / `stream_async` | ADAPT | Preserve true transport separation, but require exact envelope and propagate provider errors without fallback. |
| Assistant `CodexProvider` and `get_llm_provider` | ADAPT | Apply the same exact provider ingress contract. |
| Assistant provider tests | ADAPT | Assert exact envelope, byte-stable messages/fingerprint, Persona-free inputs, and fail-closed malformed inputs. |

### 9.3 Accepted P3-C fence — Julia-AI-Assistant `87eb86fc1ceeaa434bf269a18bf96c007d35f056`

| File/symbol | Decision | Rationale |
|---|---|---|
| `runtime/semantic_provenance_fence.py::SemanticProvenanceFence` | KEEP | Accepted exact-package identity and duplicate/missing/mismatch checks remain valuable metadata observability. |
| `SemanticProvenanceRejection` | KEEP | Machine-readable zero-partial/zero-fallback rejection is contract-compatible. |
| `runtime/legacy_semantic_authority_detector.py` | KEEP | Observability/detection only; does not own a business path. |
| Fence/detector tests and artifact expectations | KEEP | Preserve evidence that fence/detector do not construct or mutate semantics. |
| Any proposal to import fence/detector into runtime/provider business path | DROP | Fence remains independent evidence, not an authority. |

## 10. Downstream DAG

```text
N0 P3-CORE-CANONICAL-BINDING-ENVELOPE       READY
   outputs exact binder, envelope, alignment metadata, Runtime ingress
   ↓
N1 P3-ASSISTANT-PROVIDER-TRANSPORT          BLOCKED(N0)
   adapts DeepSeek/Codex ingress to exact envelope
   ↓
N2 P3-SEAM-END-TO-END-REGRESSION            BLOCKED(N1)
   proves valid/forged/partial/stale/ambiguous cases and no fallback
   ↓
N3 P3-LEGACY-AUTHORITY-REMOVAL              BLOCKED(N2 + destructive Owner Gate)
   deletes remnant APIs and dead semantic authorities
   ↓
N4 P3-PRODUCTION-CUTOVER                    BLOCKED(N3 + cutover Owner Gate)
   switches production callers and removes dual paths
   ↓
N5 P3-GOLDEN-MIRA-ADMISSION                 BLOCKED(N4 + Golden Mira Owner Gate)
   admits canonical fixtures only after independent acceptance
   ↓
N6 P3-RELEASE-DEPLOY                        BLOCKED(N5 + release/deploy Owner Gate)
```

Exactly one production implementation node is READY: **N0**. N1–N6 remain BLOCKED. No implementation task may expand into merge/main mutation, cutover, destructive removal, Golden Mira admission, canonical writes, or release/deploy without its separately named gate.

## 11. Owner Gate matrix

| Gate | Bounded task agent | Separate owner required | Current authority |
|---|---:|---:|---|
| Contract/documentation change | Yes | No | This frozen document only |
| N0 bounded Core implementation | Yes, after a READY task card | No | NONE until issued |
| N1/N2 bounded implementation/regression | Yes, after dependencies pass | No | NONE |
| Merge to any shared branch | No | Yes | MERGE_AUTHORITY=NONE |
| Main mutation | No | Yes | MAIN_MUTATION_AUTHORITY=NONE |
| Production cutover | No | Yes | CUTOVER_AUTHORITY=NONE |
| Destructive legacy removal | No | Yes | DESTRUCTIVE_REMOVAL_AUTHORITY=NONE |
| Golden Mira admission | No | Yes | GOLDEN_MIRA_AUTHORITY=NONE |
| Canonical writes | No | Yes | CANONICAL_WRITE_AUTHORITY=NONE |
| Release/deploy | No | Yes | RELEASE_DEPLOY_AUTHORITY=NONE |

## 12. Acceptance evidence

| ID | Result | Evidence |
|---|---|---|
| S1 | PASS | Section 2 names `JuliaAssistantRuntime` as the sole Runtime owner and excludes duplicate Runtime authority. |
| S2 | PASS | Section 2 names `ExactAdmittedSemanticBinder` as the sole semantic-bundle constructor. |
| S3 | PASS | Sections 3–3.2 define exact `ProviderExecutionEnvelope` ingress and mechanical `type(...) is ...` checks. |
| S4 | PASS | Section 6 places Alignment at a non-semantic execution boundary with zero post-C03 mutation. |
| S5 | PASS | Sections 1–3 define every edge from C03 through binding, Runtime, Alignment, and Provider. |
| S6 | PASS | A package-only Runtime output and B binding/envelope output are resolved in favor of package → binder → Runtime → Alignment → Provider. |
| S7 | PASS | This contract is authored on a dedicated worktree from P2 SHA; frozen candidate branches/commits are read-only inputs. |
| S8 | PASS | Changed paths are documentation/artifact only; no production source or test is added/mutated. |
| S9 | PASS | Sections 7–8 prohibit fallback/mock/stub/shadow/silent-degrade/best-effort authority. |
| S10 | PASS | Section 8 makes every missing/inexact dependency fail closed with zero partial admission. |
| S11 | PASS | Section 2.1 assigns non-overlapping future implementation lanes. |
| S12 | PASS | Section 10 marks exactly one production implementation node READY (N0). |
| S13 | PASS | Section 11 separates all destructive/canonical/release authorities from bounded implementation. |
| S14 | PASS | Sections 3–11 fix allowed types, forbidden paths, deliverables, regression classes, evidence, DAG, and gates for the N0 task card. |

## 13. Frozen dependencies

| Input | Exact SHA | Disposition |
|---|---|---|
| Julia_core P2 convergence | `c4ded0a1c97ad485a74dd9fad5b55db34d8e3c03` | Contract base |
| Candidate A | `aaa78b50ba9dfc10c57bfd31c4ccf73415a01417` | Read-only compatibility input |
| Candidate B Core | `d7853472233a0b4514308255eea231b0d85e523c` | Read-only compatibility input |
| Candidate B Assistant | `f41ff37c950d1c4390a77afca2fec8cdc0706a43` | Read-only compatibility input |
| Accepted P3-C fence | `87eb86fc1ceeaa434bf269a18bf96c007d35f056` | Accepted fence baseline |

Completion marker: `[P3-SEAM-AUTHORITY-RESOLUTION-COMPLETE]`
