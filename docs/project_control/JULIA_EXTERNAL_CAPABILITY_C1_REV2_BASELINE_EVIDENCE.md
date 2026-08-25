# Julia External Capability — C1 REV2 Baseline Evidence

**Status:** C1-R2.0 BASELINE ESTABLISHED  
**Feature:** Julia External Capability Invocation — REV2 Contract Tests  
**Branch:** `feature/julia-external-capability-c1-rev2-contract-tests`  
**Base / HEAD:** `698b811dfb9c7aae3529ba354cb6baa20b65e9b6`  
**Baseline delta:** EMPTY  
**Production code mutation:** NONE  
**Test code mutation:** NONE  

## Source of Truth

This baseline is governed by:

- `JULIA_EXTERNAL_CAPABILITY_INVOCATION_REFACTOR_DESIGN_REV2_FREEZE.md`
- `JULIA_EXTERNAL_CAPABILITY_C1_CONTRACT_TEST_DESIGN_REV2.md`
- Julia Core canonical architecture and frozen C-series contracts:
  - C-00 Cognitive Boundary
  - C-03 Context OS
  - C-08 Capability / Tool
  - C-12 Evidence / Action / Trace

## Baseline Decision

C1 REV2 starts from the clean authority baseline:

```text
698b811dfb9c7aae3529ba354cb6baa20b65e9b6
```

The prior local C1 attempt:

```text
773feb50a6e65af7b3e20230492ca0bb06f94e46
```

is preserved as historical evidence only:

```text
HOLD / DO NOT EXTEND / DO NOT TREAT AS REV2 CONTRACT TRUTH
```

## REV1 Contamination Check

The REV1 C1 test files are intentionally absent from this branch:

```text
tests/capability/test_c1_ai_theme_boundary.py                  ABSENT
tests/capability/test_c1_capability_contracts.py               ABSENT
tests/runtime/test_c1_capability_authority.py                  ABSENT
tests/runtime/test_c1_context_projection.py                    ABSENT
tests/runtime/test_c1_failure_non_fabrication.py               ABSENT
tests/runtime/test_c1_sync_stream_parity.py                    ABSENT
```

## C1-R2.0 Scope

Allowed in this commit:

- baseline evidence documentation only.

Not allowed in this commit:

- production code changes;
- test implementation;
- fixtures/mocks;
- reuse of REV1 C1 schemas;
- reset/revert/cherry-pick of `773feb5`.

## Next Step

After this baseline evidence commit is accepted, the next implementation step may be:

```text
C1-R2.1 Capability Contract Object Tests
```

Those tests must derive directly from C-00/C-03/C-08/C-12 and REV2 feature freeze, not from the superseded REV1 contract.
