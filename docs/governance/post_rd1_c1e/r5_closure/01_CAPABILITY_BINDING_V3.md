# 01 - CAPABILITY BINDING CONTRACT V3

binding_version: `market.binding.v3`
status: FROZEN_AS_GOVERNANCE
supersedes: `market.binding.v2`

Julia_core is the semantic capability authority. ai_theme_app is the market source/data/provider owner.
Julia-AI-Assistant is the production adapter/runtime composition owner only after a separate explicit future
cutover gate.

## market.stock.history

- canonical_name: `market.stock.history`
- binding_version: `market.binding.v3`
- request_contract_version: `market.request.v3`
- response_contract_version: `market.response.v3`
- failure_contract_version: `market.failure.v3`
- donor repo: `tonychang925-dev/ai_theme_app`
- donor commit: `f1bc3def72e0c4184799201aaf1ac5d02d6084d6`
- donor refs:
  - `check_stock_history.py` blob `34498cc487f0b734d6b3df810d5bf974b37c7908`
  - `collect_jyhf_history_incremental.py` blob `762863970efabb2f8d4fc12676aace2bc8a1b138`
  - `import_shenjian_history.py` blob `134ddfd08fbc4dfbba6c5e7d3d7e00446c6e9c98`
  - `database_service/scripts/import_jyhf_history_incremental.py` blob `7153489ccfd8474397f06940337577399e89b673`
  - `database_service/scripts/load_subject_history_staging.py` blob `ee1bd3446716b756a34e91139f60bfee2533abe4`

## market.theme.constituents

- canonical_name: `market.theme.constituents`
- binding_version: `market.binding.v3`
- request_contract_version: `market.request.v3`
- response_contract_version: `market.response.v3`
- failure_contract_version: `market.failure.v3`
- donor repo: `tonychang925-dev/ai_theme_app`
- donor commit: `f1bc3def72e0c4184799201aaf1ac5d02d6084d6`
- donor refs:
  - `stock_processing_service/application/jobs/subject_stock_snapshot/base.py` blob `609ece34609f1eaaed1a2e73849e3f4d014cd7be`
  - `stock_processing_service/application/jobs/subject_stock_snapshot/config.py` blob `ca56b477c8cb5fdc27a8a0fcc0ad39b919159160`
  - `stock_processing_service/application/jobs/subject_stock_snapshot/jyhf_producer.py` blob `719695eb5c8a23d065429f4d94076907d7804ca5`
  - `database_service/scripts/detect_jyhf_changed_subjects.py` blob `ea2e517e8c80fc783d7be331cba69eea905792fc`
  - `database_service/scripts/import_jyhf_stock_daily_incremental.py` blob `49e157320fd180a743c4a93c73dfc2567da828ec`
- materialized dated source authority: `subject_stock_daily_snapshot`
- point-in-time selection rule: `selected_snapshot_date = MAX(snapshot_date) WHERE snapshot_date <= as_of`

## Binding Policies

- semantic alias policy: FORBIDDEN. A canonical capability name cannot be treated as another capability.
- fallback policy: FORBIDDEN. A failure in one semantic capability cannot be answered by another capability.
- duplicate_operation_policy: one semantic capability has one canonical binding at a time. Duplicate runtime
  operations may exist only as descriptive implementation details and cannot both claim canonical semantic
  authority.
- replacement_policy: replacement requires owner-approved contract versioning, fixture acceptance, and a
  separate cutover gate. Replacement cannot silently change request, response, provenance, failure, or source
  identity semantics.
- deprecation_policy: deprecated or historical capability paths can remain for compatibility only. They are
  not normative sources for Wave-1 behavior and cannot be used to justify alias or fallback behavior.
- registration_policy: source implementation does not register itself into production. Production activation
  is owned by Julia-AI-Assistant and requires a separate explicit future cutover gate.
- rollback_binding: rollback disables or restores a per-capability binding state. Rollback is never semantic
  fallback, never source-history rewriting, and never substitution with a different capability.

Forbidden bindings include `market.stock.history -> market.snapshot.read` and
`market.theme.constituents -> market.intelligence.observe`.
