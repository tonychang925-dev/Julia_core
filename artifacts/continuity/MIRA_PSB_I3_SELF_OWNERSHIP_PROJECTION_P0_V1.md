# MIRA PSB-I3 Self-Ownership Projection Evidence

## Provenance

- `TASK_ID=MIRA-PSB-I3-PROJECTION-MODEL-VISIBLE-SELF-OWNERSHIP-P0`
- `EXECUTION_AGENT=LOCAL_CODEX_ONLY`
- `DESIGN_SHA=73d5ecb1c2fc0e6dd70bccfe423c79a3370c0fa5`
- `PSB_I1_IMPLEMENTATION_SHA=a31c4576d79b916cdfcaf035558b73ffc61e3da7`
- `PSB_I2_FINAL_SHA=5992f75a66a88588c5df9dc1c9bc262c34456b68`
- `IMPLEMENTATION_BASE_SHA=5992f75a66a88588c5df9dc1c9bc262c34456b68`
- `IMPLEMENTATION_PARENT_SHA=5992f75a66a88588c5df9dc1c9bc262c34456b68`
- `IMPLEMENTATION_CANDIDATE_SHA=5a8be1ca29d1f2cfd4cb9534c45221f1a379b794`
- `BRANCH=mira/psb-i3-self-ownership-projection-p0`

The final evidence delivery SHA is not embedded in this artifact. Commit, push, remote HEAD read-back, and the Issue #139 completion comment prove it externally.

## Projection Contract

- The projector accepts only an exact validated `ADMITTED_ACTIVE` PersonaSelfBinding and optional typed identity assertion.
- Identity and experience project current-self ownership references without duplicating child semantic facts.
- Relationship projection preserves `ABSENT`, `EXPLICITLY_EMPTY`, and `ADMITTED_BOUND` as distinct states; bound output contains authority metadata only.
- Execution substrate is structurally separate from persona self and contains no concrete provider/model fields.
- Typed authority precedence records governed binding authority while current task content and provider identity have no persona identity authority.
- Resolved contradiction evidence projects typed metadata only; unresolved override fails closed.
- Canonical JSON and SHA-256 projection digests are deterministic; lifecycle/provenance-only changes do not drift visible ownership semantics.

## Adversarial Fixtures

The four owner-provided Chinese/DeepSeek/Mira contradiction fixtures are tested as non-authoritative task text. They do not enter projection bytes or alter the projection digest, and no real provider is called.

## Verification

- Focused tests: `54 passed`.
- Effective regression set: `63 passed, 1 inherited pre-existing assertion deselected`.
- Changed-file NCF gate: `PASS` with zero new violations.
- `git diff --check=PASS`.

No runtime wiring, C03, provider transport, durable store, RelationshipFrame, provider descriptor, dispatch receipt, RD1, classifier, prompt patch, response rewrite, or real provider execution changed.

## Result

`PASS_PSB_I3_SELF_OWNERSHIP_PROJECTION_READY_FOR_OWNER_REVIEW`
