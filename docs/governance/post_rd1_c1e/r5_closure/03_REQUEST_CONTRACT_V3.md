# 03 - REQUEST CONTRACT V3

request_contract_version: `market.request.v3`
status: FROZEN_AS_GOVERNANCE
supersedes: `market.request.v2`

Shared fields are `request_id`, `correlation_id`, `schema_version`, `requested_at`, and
`idempotency_key`; each is a required string.

## market.stock.history

| field | required | type | format | normalization owner | validation owner | default |
|---|---|---|---|---|---|---|
| stock_code | REQUIRED | string | canonical symbol, e.g. `600000.SH` | ai_theme_app | Julia_core | NO |
| start_date | REQUIRED | string | `YYYY-MM-DD` | ai_theme_app | Julia_core | NO |
| end_date | REQUIRED | string | `YYYY-MM-DD`, `>= start_date` | ai_theme_app | Julia_core | NO |
| as_of | OPTIONAL | string | `YYYY-MM-DD`; defaults to `end_date` | Julia_core | Julia_core | YES, `end_date` |
| adjustment_mode | OPTIONAL | enum | `NONE`, `FORWARD`, `BACKWARD` | ai_theme_app | Julia_core | YES, `NONE` |
| market/exchange | OPTIONAL | string | derived from symbol unless override required | ai_theme_app | Julia_core | YES, derived |

## market.theme.constituents

| field | required | type | format | normalization owner | validation owner | default |
|---|---|---|---|---|---|---|
| subject_key | REQUIRED | string | canonical theme identity resolving to exactly one universe subject | ai_theme_app | Julia_core | NO |
| as_of | REQUIRED | string | `YYYY-MM-DD`; membership snapshot is `MAX(snapshot_date) <= as_of` | Julia_core | Julia_core | NO |
| request_id / correlation_id / schema_version / requested_at / idempotency_key | REQUIRED | string | per shared fields | Julia_core | Julia_core | NO |

`universe_version` is NOT_IN_WAVE1 and is not accepted as a Wave-1 request field. The Wave-1 identity is the
tuple of `subject_key`, `as_of`, exact donor refs, `selected_snapshot_date`, and provenance
`source_ref/version`.

No fuzzy theme-name guessing is permitted. Missing required fields produce `MISSING_REQUIRED_ARGUMENT`.
Invalid request shapes produce a typed request failure.
