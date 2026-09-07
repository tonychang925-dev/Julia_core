# 04 — RESPONSE CONTRACT V2 (normative)

response_contract_version: market.response.v2
Supersedes response v1 (constituents exact canonical row schema now frozen; no "frozen at fixture acceptance").

Shared envelope: capability_id, contract_version, status (success|partial|unavailable|error),
data_state (normal|empty|stale), as_of, payload, source_records, failures[], observed_at, schema_version,
provenance.

## market.stock.history rows[]
Canonical row (frozen): trade_date (YYYY-MM-DD, non-null), open/high/low/close (decimal, non-null unless
source record null → then row-level typed SOURCE_PARSE_FAILED/partial-with-disclosure),
volume, amount (numeric; units per source owner doc), adjustment_mode echo + adjusted flag.
Order: ascending by trade_date. No duplicate (trade_date) rows; malformed/out-of-order → typed failure.
No best-effort fields; no provider raw field silently canonical (additions need version bump).

## market.theme.constituents — exact canonical row schema (frozen, new)
Canonical constituent row:
- trade_date: string YYYY-MM-DD, non-null — snapshot_date used (selected as MAX(snapshot_date) <= as_of)
- subject_key: string, non-null — canonical theme identity resolved
- stock_code: string, non-null — canonical stock identity
Identity semantics: canonical triple (trade_date, subject_key, stock_code) is unique; membership means
stock was a member of subject on that snapshot date.
Order: ascending by stock_code. Null semantics: any of the three identity fields null ⇒ row rejected as
SOURCE_PARSE_FAILED (row counted; completeness provability required for canonical publication).
No stock_name/rank/best-effort in canonical row (consumer-derived additions are separate contracts).
data_state: normal (members exist); empty (subject legitimately empty on snapshot → typed empty, distinct
from failure); stale: Wave-1 never emits stale (see F: UNKNOWN-only). as_of with no snapshot<=as_of →
NO_DATA typed failure (GC-12).
