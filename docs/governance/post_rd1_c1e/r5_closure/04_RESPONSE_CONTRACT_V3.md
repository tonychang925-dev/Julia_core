# 04 - RESPONSE CONTRACT V3

response_contract_version: `market.response.v3`
status: FROZEN_AS_GOVERNANCE
supersedes: `market.response.v2`

Shared envelope fields are `capability_id`, `contract_version`, `status`, `data_state`, `as_of`,
`payload`, `source_records`, `failures[]`, `observed_at`, `schema_version`, and `provenance`.

## market.stock.history rows[]

Canonical row:

| field | type | nullability | semantics |
|---|---|---|---|
| trade_date | string | non-null | `YYYY-MM-DD` source trading date |
| open | decimal | non-null unless row-level source parse failure | source-normalized open |
| high | decimal | non-null unless row-level source parse failure | source-normalized high |
| low | decimal | non-null unless row-level source parse failure | source-normalized low |
| close | decimal | non-null unless row-level source parse failure | source-normalized close |
| volume | numeric | nullable only if source row lacks volume and row accounting remains provable | source-normalized volume |
| amount | numeric | nullable only if source row lacks amount and row accounting remains provable | source-normalized amount |
| adjustment_mode | enum | non-null | echo of request/default adjustment mode |
| adjusted | boolean | non-null | whether OHLC values are adjusted |

Order is ascending by `trade_date`. Duplicate `trade_date` rows, malformed rows, or out-of-order canonical
publication produce typed failure unless row accounting and completeness remain mechanically provable.

`pct_change` and `amplitude` are NOT_IN_WAVE1 and are not canonical response fields. Any additional
canonical field requires a response contract version change.

## market.theme.constituents rows[]

Canonical row:

| field | type | nullability | semantics |
|---|---|---|---|
| trade_date | string | non-null | selected snapshot date, `MAX(snapshot_date) <= as_of` |
| subject_key | string | non-null | canonical theme identity |
| stock_code | string | non-null | canonical stock identity |

Identity is `(trade_date, subject_key, stock_code)`. Order is ascending by `stock_code`. A null identity
field produces `SOURCE_PARSE_FAILED`. `stock_name`, `rank`, and best-effort fields are not canonical
Wave-1 response fields.

If no snapshot exists with `snapshot_date <= as_of`, response is typed `NO_DATA`. Future snapshot use and
current-map-as-history use are forbidden.
