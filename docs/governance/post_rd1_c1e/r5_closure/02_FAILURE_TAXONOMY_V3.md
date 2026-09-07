# 02 - FAILURE TAXONOMY V3

failure_contract_version: `market.failure.v3`
status: FROZEN_AS_GOVERNANCE
supersedes: `market.failure.v2`

Failure always produces a typed failure. Failure is not empty success, synthetic success, semantic alias, or
fallback. Retry means retrying the same semantic capability only; retry never means routing to another
capability. Any retry must be bounded by the caller/runtime policy.

## Formal Failure Identities

| identity | layer | retryability |
|---|---|---|
| INVALID_REQUEST | request | TERMINAL |
| MISSING_REQUIRED_ARGUMENT | request | TERMINAL |
| INVALID_STOCK_CODE | request | TERMINAL |
| INVALID_DATE_RANGE | request | TERMINAL |
| INVALID_CONFIGURATION | request/config | TERMINAL |
| CAPABILITY_NOT_BOUND | capability | TERMINAL |
| CAPABILITY_NOT_IMPLEMENTED | capability | TERMINAL |
| SOURCE_UNAVAILABLE | capability/source | RETRYABLE |
| SOURCE_TIMEOUT | capability/source | RETRYABLE |
| NO_DATA | data | TERMINAL |
| STALE_DATA | data | TERMINAL |
| PROVENANCE_UNVERIFIED | data | TERMINAL |
| SOURCE_INCOMPLETE | data/source | RETRYABLE |
| INCOMPLETE_GENERATION | data/generation | RETRYABLE |
| MIXED_GENERATION_REJECTED | data/generation | TERMINAL |
| SOURCE_SCHEMA_CHANGED | source-contract | TERMINAL |
| SOURCE_PARSE_FAILED | source-contract | TERMINAL |
| INTERNAL_PROVIDER_ERROR | source-contract | RETRYABLE |

`STALE_DATA` is defined for future contracts with a frozen threshold. Wave-1 never emits `STALE_DATA`
because Wave-1 freshness is `UNKNOWN` only.

## Exact GC-01..15 Mapping

| case | canonical result | exact top-level identity | nested/source cause |
|---|---|---|---|
| GC-01 | success | none | none |
| GC-02 | typed failure; no new canonical | INCOMPLETE_GENERATION | SOURCE_UNAVAILABLE |
| GC-03 | typed failure; no new canonical | INCOMPLETE_GENERATION | SOURCE_UNAVAILABLE |
| GC-04 | proof required or typed failure | SOURCE_INCOMPLETE | none |
| GC-05 | typed failure; prior canonical intact | INCOMPLETE_GENERATION | SOURCE_UNAVAILABLE |
| GC-06 | dedup counted or typed failure | SOURCE_PARSE_FAILED | none |
| GC-07 | success per date | none | none |
| GC-08 | typed per-date absence | NO_DATA | none |
| GC-09 | empty success or source failure | SOURCE_UNAVAILABLE when source failed | none |
| GC-10 | typed failure or row-accounted canonical | SOURCE_PARSE_FAILED when unprovable | none |
| GC-11 | success | none | none |
| GC-12 | typed failure | NO_DATA | none |
| GC-13 | typed config failure | INVALID_CONFIGURATION | none |
| GC-14 | typed config failure | INVALID_CONFIGURATION | none |
| GC-15 | typed failure | MIXED_GENERATION_REJECTED | none |

GC-02 top-level semantic result is `INCOMPLETE_GENERATION`. `SOURCE_UNAVAILABLE` may appear only as nested
source cause for that case.
