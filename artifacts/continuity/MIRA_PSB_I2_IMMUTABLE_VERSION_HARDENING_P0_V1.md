# PSB-I2 Immutable Version Hardening Evidence

## Provenance

- `IMPLEMENTATION_BASE_SHA=69ba027d354f6bfe2e65f8edeb699341376a154b`
- `IMPLEMENTATION_PARENT_SHA=69ba027d354f6bfe2e65f8edeb699341376a154b`
- `IMPLEMENTATION_CANDIDATE_SHA=012b1ebb0725164b8117d5580c73c2371638a57f`
- `BRANCH=mira/psb-i2-durable-governance-p0`

The final hardening delivery SHA is not embedded in this artifact. Commit, push, remote HEAD read-back, and the Issue #137 completion comment establish it externally.

## Hardening

Repeated records with the same `binding_version` now require an identical immutable semantic payload. Only `lifecycle_status`, `governance_provenance`, and governed `supersession` may evolve. A mutation raises the explicit `PSB_IMMUTABLE_VERSION_MUTATION` error.

Sabotage coverage rejects same-version mutation of identity authority, `persona_self_id`, relationship authority, execution substrate policy, and predecessor metadata, while proving legitimate lifecycle/provenance append remains valid.

## Verification

- Focused tests: `41 passed`.
- Effective regression set: `63 passed, 1 inherited pre-existing assertion deselected`.
- Changed-file NCF gate: `PASS` with zero new violations.
- `git diff --check=PASS`.

No runtime, C03, projection, provider, RelationshipFrame, dispatch receipt, or RD1 scope changed.

## Result

`PASS_PSB_I2_IMMUTABLE_VERSION_HARDENING_READY_FOR_OWNER_REVIEW`
