# MIRA PSB-I6 Provider-Name Heuristic Hardening Evidence

## Result

`PASS_PSB_I6_PROVIDER_NAME_HEURISTIC_HARDENING_READY_FOR_OWNER_REVIEW`

## Provenance

- Original implementation: `4a027d392a5dd667cb3399b965fe6f67088cb5fd`
- Original evidence remote HEAD: `1b1e7c616396bf39ee01a532f7bd2227fd722721`
- Hardening parent: `1b1e7c616396bf39ee01a532f7bd2227fd722721`
- Hardening candidate: `49ec43c27856b1763e6a02a8ab13576cc4493406`
- Review comment: `5775496935`
- Branch: `mira/psb-i6-provider-persona-runtime-separation-p0`

## Hardening

The production contract no longer compares provider/model strings to a persona label. Separation is enforced only by typed runtime provenance and structural projection boundaries:

- descriptor and receipt remain runtime-only metadata;
- persona authority remains the governed `PersonaSelfBinding`;
- injecting `provider_id`, `model_id`, or `runtime_instance_id` fields into the PSB projection fails closed;
- a provider/model string that lexically equals a persona label neither gains persona authority nor is rejected merely for matching that label.

The new reverse regression uses provider/model IDs both equal to `golden-mira`. The descriptor digest is `ced96108e9753e6a7cc6d8ad85d75a0ed3e90eaa4153691f26a61d904b42cdc5`, receipt digest is `773f93aaaf7dc14ef6fef3b66681eeaa598e48622cd0e195e199a2735ab478f0`, and the PSB projection digest remains `40909d4076d81853de2f727f5e6d3e4eff61e94f9ed7ff13efbe86a994862a3b`.

## Validation

- Focused I6 tests: `24 passed`
- Required regression set: `251 passed`
- Changed-file NCF gate: `PASS`, `P0=0`, `P1=0`, `P2=0`
- Changed-file `py_compile`: `PASS`
- `git diff --check`: `PASS`
- Provider transport changed: `NO`
- Real provider called: `NO`
- Persona semantics changed: `NO`
- Raw canonical fallback: `NO`
- Synthetic identity: `NO`
- RD1 changed files: `0`
