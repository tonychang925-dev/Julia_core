# 06 — PROVENANCE / FRESHNESS V2 (normative; Wave-1 UNKNOWN-only)

provenance_version: market.provenance.v2
Supersedes provenance v1 deferral ("threshold recorded at fixture acceptance").

## Provenance envelope (frozen per response and per derived material field)
source_name, source_kind, source_ref/version, retrieved_at, source_data_time, query_as_of,
freshness_status, query_window, rule_version where derived.

## Freshness (frozen for Wave-1)
- Wave-1 freshness_status = UNKNOWN for every source kind (history and constituents daily snapshot).
- FRESH/STALE inference is NOT permitted in Wave-1 because no mechanical threshold has been frozen for any
  source kind. Thresholds are a separate future contract; until then the only honest state is UNKNOWN.
- source_data_time is still REQUIRED in provenance and recorded as-is; it is never used to claim
  FRESH/STALE.
- A current wall-clock timestamp never substitutes for unknown source timestamp.
- STALE_DATA (market.failure.v2) is defined but Wave-1 never emits it (would require a frozen threshold).
- Provenance always records query_as_of, source timestamp, and selected snapshot_date<=as_of so freshness
  can be decided later without rework.
