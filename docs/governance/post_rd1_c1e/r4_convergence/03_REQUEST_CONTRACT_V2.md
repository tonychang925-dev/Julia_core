# 03 — REQUEST CONTRACT V2 (normative)

request_contract_version: market.request.v2
Supersedes request v1 (constituents fields now fully frozen; no "documented per capability binding" deferral).
Shared: request_id/correlation_id/schema_version/requested_at/idempotency_key (string, required).

## market.stock.history (unchanged from v1, restated)
| field | required | type | format | normalization owner | validation owner | default |
|-------|----------|------|--------|--------------------|------------------|---------|
| stock_code | REQUIRED | string | canonical symbol (600000.SH) | ai_theme_app | Julia_core | NO |
| start_date | REQUIRED | string | YYYY-MM-DD | ai_theme_app | Julia_core | NO |
| end_date | REQUIRED | string | YYYY-MM-DD >= start | ai_theme_app | Julia_core | NO |
| as_of | OPTIONAL | string | YYYY-MM-DD; default end_date | Julia_core | Julia_core | YES(end_date) |
| adjustment_mode | OPTIONAL | enum | NONE/FORWARD/BACKWARD | ai_theme_app | Julia_core | YES(NONE) |
| market/exchange | OPTIONAL | string | derived from symbol unless override required | ai_theme_app | Julia_core | YES(derived) |

## market.theme.constituents (fully frozen)
| field | required | type | format | normalization owner | validation owner | default |
|-------|----------|------|--------|--------------------|------------------|---------|
| subject_key | REQUIRED | string | canonical theme identity (must resolve to exactly one universe subject) | ai_theme_app | Julia_core | NO |
| as_of | REQUIRED | string | YYYY-MM-DD cutoff; membership = snapshot with MAX(trade_date)<=as_of | Julia_core | Julia_core | NO |
| universe_version | OPTIONAL | string | pinned universe/source version; if provided must match pinned snapshot universe_version, else NO_DATA/PROVENANCE_UNVERIFIED typed; if absent response still carries resolved universe_version in provenance | ai_theme_app | Julia_core | YES(absent→resolved+recorded) |
| request_id / correlation_id / schema_version / requested_at / idempotency_key | REQUIRED | string | per shared | Julia_core | Julia_core | NO |

Unknown universe_version behavior: mismatch → PROVENANCE_UNVERIFIED (typed). No fuzzy theme-name guessing.
Missing required → MISSING_REQUIRED_ARGUMENT. as_of required (no ambient default).
