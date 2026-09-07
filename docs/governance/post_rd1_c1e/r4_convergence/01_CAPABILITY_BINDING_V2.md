# 01 — CAPABILITY BINDING CONTRACT V2 (normative, supersedes V1)

binding_version: `market.binding.v2`
status: FROZEN_AS_GOVERNANCE (owner/Mira acceptance pending)
Supersedes: 01_CAPABILITY_BINDING_V1 (PENDING/NOT_FOUND entries removed).

semantic_owner: Julia_core
source_owner: ai_theme_app
production_adapter_owner: Julia-AI-Assistant (activates ONLY via separate cutover gate)

## market.stock.history
- canonical_name: market.stock.history
- binding_version: market.binding.v2
- request_contract_version: market.request.v2
- response_contract_version: market.response.v2
- failure_contract_version: market.failure.v2
- provider/donor exact refs (ai_theme_app f1bc3def72e0c4184799201aaf1ac5d02d6084d6):
  - check_stock_history.py blob 34498cc487f0b734d6b3df810d5bf974b37c7908 (historical/donor)
  - collect_jyhf_history_incremental.py blob 762863970efabb2f8d4fc12676aace2bc8a1b138
  - import_shenjian_history.py blob 134ddfd08fbc4dfbba6c5e7d3d7e00446c6e9c98
  - database_service/scripts/import_jyhf_history_incremental.py blob 7153489ccfd8474397f06940337577399e89b673
  - database_service/scripts/load_subject_history_staging.py blob ee1bd3446716b756a34e91139f60bfee2533abe4

## market.theme.constituents
- canonical_name: market.theme.constituents
- binding_version: market.binding.v2
- request_contract_version: market.request.v2
- response_contract_version: market.response.v2
- failure_contract_version: market.failure.v2
- provider/donor exact refs (ai_theme_app f1bc3def72e0c4184799201aaf1ac5d02d6084d6):
  - stock_processing_service/application/jobs/subject_stock_snapshot/base.py blob 609ece34609f1eaaed1a2e73849e3f4d014cd7be
  - .../config.py blob ca56b477c8cb5fdc27a8a0fcc0ad39b919159160
  - .../jyhf_producer.py blob 719695eb5c8a23d065429f4d94076907d7804ca5
  - database_service/scripts/detect_jyhf_changed_subjects.py blob ea2e517e8c80fc783d7be331cba69eea905792fc
  - database_service/scripts/import_jyhf_stock_daily_incremental.py blob 49e157320fd180a743c4a93c73dfc2567da828ec
  - materialized table: subject_stock_daily_snapshot (per-trade_date full membership snapshot)
  DEDICATED_TRACKED_DONOR_SOURCE = FOUND_EXACT (supersedes NOT_FOUND in V1)

## Binding rules (unchanged from V1, still binding)
- semantic alias = NONE; fallback alias = NONE; duplicate_operation_policy / replacement_policy /
  deprecation_policy / registration_policy (no registration in source commits) / rollback_binding
  (per-capability) all as V1.

No PENDING, no "NONE pinned", no deferred fields remain in this contract.
