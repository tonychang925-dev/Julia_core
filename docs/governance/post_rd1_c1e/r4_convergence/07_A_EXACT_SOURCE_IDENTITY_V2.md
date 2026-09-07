# 07 — A EXACT SOURCE IDENTITY V2 (normative; supersedes V1)

identity_version: market.identity.v2
Primary A identity. 07_EXACT_SOURCE_IDENTITY_V1 (constituents NOT_FOUND / A=HOLD) is SUPERSEDED.

## market.stock.history (exact; ai_theme_app f1bc3def72e0c4184799201aaf1ac5d02d6084d6)
| path | blob SHA | role |
|------|----------|------|
| check_stock_history.py | 34498cc487f0b734d6b3df810d5bf974b37c7908 | historical/donor |
| collect_jyhf_history_incremental.py | 762863970efabb2f8d4fc12676aace2bc8a1b138 | historical/donor |
| import_shenjian_history.py | 134ddfd08fbc4dfbba6c5e7d3d7e00446c6e9c98 | historical/donor |
| database_service/scripts/import_jyhf_history_incremental.py | 7153489ccfd8474397f06940337577399e89b673 | historical/donor |
| database_service/scripts/load_subject_history_staging.py | ee1bd3446716b756a34e91139f60bfee2533abe4 | historical/donor |

## market.theme.constituents (exact; FOUND_EXACT supersedes NOT_FOUND)
| path | blob SHA | role |
|------|----------|------|
| stock_processing_service/application/jobs/subject_stock_snapshot/base.py | 609ece34609f1eaaed1a2e73849e3f4d014cd7be | donor |
| .../config.py | ca56b477c8cb5fdc27a8a0fcc0ad39b919159160 | donor |
| .../jyhf_producer.py | 719695eb5c8a23d065429f4d94076907d7804ca5 | donor |
| database_service/scripts/detect_jyhf_changed_subjects.py | ea2e517e8c80fc783d7be331cba69eea905792fc | donor |
| database_service/scripts/import_jyhf_stock_daily_incremental.py | 49e157320fd180a743c4a93c73dfc2567da828ec | importer |
materialized dated membership authority: subject_stock_daily_snapshot (per trade_date full snapshot;
delete+rebuild per date; point-in-time capable).

Not inferred from branch names; untracked/local files are not donor authority. Donor classification is
historical/donor; authoritative status is established at implementation acceptance via GC fixtures.
