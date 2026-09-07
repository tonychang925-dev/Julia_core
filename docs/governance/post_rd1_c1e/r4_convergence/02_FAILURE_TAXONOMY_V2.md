# 02 — FAILURE TAXONOMY V2 (normative, supersedes V1)

failure_contract_version: `market.failure.v2`
status: FROZEN_AS_GOVERNANCE. Supersedes V1; V2 adds formal identities that V1 referred to only as
"equivalent". No "equivalent", no implementation-time guessing.

## Formal failure identities
Request layer:
- INVALID_REQUEST
- MISSING_REQUIRED_ARGUMENT
- INVALID_STOCK_CODE
- INVALID_DATE_RANGE
- INVALID_CONFIGURATION   (NEW: config-provider / config-mode invalid; GC-13/14)

Capability layer:
- CAPABILITY_NOT_BOUND
- CAPABILITY_NOT_IMPLEMENTED
- SOURCE_UNAVAILABLE
- SOURCE_TIMEOUT

Data layer:
- NO_DATA
- STALE_DATA            (only when a frozen threshold exists; Wave-1 never emits — see F)
- PROVENANCE_UNVERIFIED
- SOURCE_INCOMPLETE     (NEW: source responded but membership completeness not proven/truncated; GC-04)
- INCOMPLETE_GENERATION (NEW: generation completeness not achieved; publication prevented; GC-02/03/05)
- MIXED_GENERATION_REJECTED (NEW: attempted mixed-generation canonical publication rejected; GC-15
  outcome-A/B terminal state)

Source-contract layer:
- SOURCE_SCHEMA_CHANGED
- SOURCE_PARSE_FAILED
- INTERNAL_PROVIDER_ERROR

## Exact GC-01..15 mapping (no "equivalent")
| case | canonical result | exact identity |
|------|------------------|----------------|
| GC-01 | success | canonical generation (no failure) |
| GC-02 | typed failure | SOURCE_UNAVAILABLE OR INCOMPLETE_GENERATION (per determinism of fixture, exactly one asserted) |
| GC-03 | typed failure | INCOMPLETE_GENERATION |
| GC-04 | proof OR typed | SOURCE_INCOMPLETE (when completeness unproven) |
| GC-05 | typed failure; old intact | INCOMPLETE_GENERATION |
| GC-06 | dedup+counted OR typed | SOURCE_PARSE_FAILED (only when dedup rule cannot resolve) |
| GC-07 | success per-date | canonical per-date membership |
| GC-08 | typed per-date absence | NO_DATA (subject absent for date) |
| GC-09 | distinct states | legitimate empty=data_state=empty; failure empty=SOURCE_UNAVAILABLE |
| GC-10 | typed failure | SOURCE_PARSE_FAILED |
| GC-11 | success | canonical snapshot <= as_of |
| GC-12 | typed failure | NO_DATA |
| GC-13 | typed config failure | INVALID_CONFIGURATION |
| GC-14 | typed config failure | INVALID_CONFIGURATION |
| GC-15 | outcome A/B typed | MIXED_GENERATION_REJECTED |

## Rules (unchanged)
failure→typed failure; failure != empty success; != synthetic success; != semantic alias; != fallback.
GC-02 fixture pins which of SOURCE_UNAVAILABLE/INCOMPLETE_GENERATION applies for its specific source
condition (each fixture asserts exactly one).
