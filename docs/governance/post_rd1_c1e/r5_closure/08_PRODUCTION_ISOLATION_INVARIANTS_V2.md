# 08 - PRODUCTION ISOLATION INVARIANTS V2

invariant_version: `market.isolation.v2`
status: FROZEN_AS_GOVERNANCE
supersedes: `market.isolation.v1`

## Authority Matrix

| semantic concern | Julia_core | Julia-AI-Assistant | ai_theme_app |
|---|---|---|---|
| semantic capability definition | OWNER | CONSUMER | NON_AUTHORITY |
| request/response contract | OWNER | CONSUMER/ADAPTER | CONSUMER |
| failure taxonomy | OWNER | ADAPTER | CONSUMER |
| source acquisition | NOT_APPLICABLE | NON_AUTHORITY | OWNER |
| normalization | NON_AUTHORITY | NON_AUTHORITY | OWNER |
| derived metrics | NON_AUTHORITY | NON_AUTHORITY | OWNER |
| runtime routing | NOT_APPLICABLE | OWNER | NON_AUTHORITY |
| production registration | NOT_APPLICABLE | OWNER after explicit cutover gate | NON_AUTHORITY |
| deployment/composition | NOT_APPLICABLE | OWNER | CONSUMER |
| rollback | NOT_APPLICABLE | ADAPTER per capability | OWNER per provider |

## Isolation Rules

1. ai_theme_app source implementation does not auto-register itself into Julia production runtime.
2. Julia-AI-Assistant runtime capability strings are not semantic authority by presence.
3. Wave-1 source work cannot resurrect semantic alias or fallback semantics.
4. No dual-authority path is allowed for `market.stock.history` or `market.theme.constituents`.
5. No import-time registration side effect is allowed in Wave-1 source commits.
6. No production cutover is authorized by C1E R5.
7. Production adapter activation requires a separate explicit future cutover gate.
8. Rollback is a per-capability binding rollback, not semantic fallback and not another capability.

This R5 task changes governance documents only. Source, runtime, provider, DB, router, registration, and
production composition changes are not authorized.
