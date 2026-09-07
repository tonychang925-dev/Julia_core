# 06 - PROVENANCE / FRESHNESS V3

provenance_version: `market.provenance.v3`
status: FROZEN_AS_GOVERNANCE
supersedes: `market.provenance.v2`

## Provenance Envelope

Required provenance fields:

| field | required | nullability | semantics |
|---|---|---|---|
| source_name | REQUIRED | non-null | source/provider name |
| source_kind | REQUIRED | non-null | source category |
| source_ref/version | REQUIRED | non-null | exact source reference and version or commit/blob identity |
| retrieved_at | REQUIRED | non-null | retrieval timestamp observed by the acquisition process |
| source_data_time | REQUIRED | nullable only when source contains no source timestamp | timestamp carried by the source data |
| query_as_of | REQUIRED | non-null | requested/as-resolved as-of date |
| selected_snapshot_date | REQUIRED for constituents | non-null for successful constituents response | `MAX(snapshot_date) <= as_of` |
| freshness_status | REQUIRED | non-null | Wave-1 value is always `UNKNOWN` |
| query_window | REQUIRED where applicable | non-null for history windows | request/resolved query window |
| rule_version | REQUIRED for derived fields | non-null only when a derived field exists | derived metric rule version |

`universe_version` is NOT_IN_WAVE1. Wave-1 does not emit or match on a standalone universe version field.
Constituents identity is supplied by `subject_key`, `query_as_of`, `selected_snapshot_date`, exact donor
refs, and `source_ref/version`.

## Freshness

Wave-1 freshness status is `UNKNOWN` for both history and constituents. `FRESH` and `STALE` are not emitted
in Wave-1 because no mechanical threshold is frozen.

`source_data_time` is required as a field. Its value is nullable only when the source contains no source
timestamp. If `source_data_time` is null, `freshness_status` remains `UNKNOWN`. Current wall-clock time must
not substitute for missing `source_data_time`.

`STALE_DATA` remains a failure identity for future thresholded contracts, but Wave-1 does not produce it.
