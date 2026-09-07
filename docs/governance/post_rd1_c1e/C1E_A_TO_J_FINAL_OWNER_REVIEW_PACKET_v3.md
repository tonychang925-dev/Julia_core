# C1E A-J FINAL OWNER REVIEW PACKET v3 (normative convergence; verbatim)

Superseded (not primary, listed only): binding v1, failure v1, request v1, response v1, derived v1,
provenance v1, source identity v1 (constituents NOT_FOUND), G baseline pre-V3R (INCOMPLETE-equivalent wording).

## [A] 07_A_EXACT_SOURCE_IDENTITY_V2.md
- source_path: /tmp/post_rd1_c1e_r4/07_A_EXACT_SOURCE_IDENTITY_V2.md
- sha256: `0dd10193dc54ca7dbcee7646ea91a925eefed8d5d98db036a00ff442ef55336b`
- status: PASS-ELIGIBLE

```markdown
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

```

## [B] 01_CAPABILITY_BINDING_V2.md
- source_path: /tmp/post_rd1_c1e_r4/01_CAPABILITY_BINDING_V2.md
- sha256: `863bc2b6003a38f2872e70434798f40f7d3250588e0b730886d5eddf303750ee`
- status: PASS-ELIGIBLE / REVIEW-PENDING

```markdown
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

```

## [C] 03_REQUEST_CONTRACT_V2.md
- source_path: /tmp/post_rd1_c1e_r4/03_REQUEST_CONTRACT_V2.md
- sha256: `f78b3f4f66f9a93afb1685f3dd438dea58d6757d847b3bf5fd6f4cebe6783e66`
- status: PASS-ELIGIBLE / REVIEW-PENDING

```markdown
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

```

## [D] 04_RESPONSE_CONTRACT_V2.md
- source_path: /tmp/post_rd1_c1e_r4/04_RESPONSE_CONTRACT_V2.md
- sha256: `9bcae136306bcd87b04694287705b711c3738c83a3a811348d2cea4bf31e0d02`
- status: PASS-ELIGIBLE / REVIEW-PENDING

```markdown
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

```

## [E] 05_DERIVED_METRIC_OWNERSHIP_V2.md
- source_path: /tmp/post_rd1_c1e_r4/05_DERIVED_METRIC_OWNERSHIP_V2.md
- sha256: `a9606695ad07e4e95f13279b787ce4bf78e495131f35a8bf59a6afb5ba80313a`
- status: PASS-ELIGIBLE / REVIEW-PENDING

```markdown
# 05 — DERIVED METRIC OWNERSHIP V2 (normative; no OPEN/TBD)

derived-ownership_version: market.derived-ownership.v2
Every value below is frozen as IN_WAVE1 (with formula) or NOT_IN_WAVE1. No "CAPABILITY_DERIVED + TBD".

## market.stock.history
IN_WAVE1 (normalization-derived; owner ai_theme_app; formulas fixed):
- pct_change = close_t/close_{t-1} - 1 (adjusted series when adjustment_mode != NONE); decimal precision per
  source policy recorded at implementation acceptance.
- amplitude = (high-low)/prev_close where prev_close>0 else row omitted from amplitude computation (field
  not emitted) — i.e., amplitude computed only when defined.
NOT_IN_WAVE1 (explicit): turnover-related values, moving averages, log/simple returns (only pct_change is
canonical), volume ratios / intraday_volume_vs_prev, total_return, max_drawdown_from_peak,
open_gap_vs_prev_close, key_level_status, limit_up_seal. These remain ai_theme_app domain-owned future
derived metrics; Wave-1 response does not contain them.

## market.theme.constituents
IN_WAVE1: none beyond the canonical membership rows (04). NOT_IN_WAVE1 (explicit): relative_strength_rank,
breadth_change, emerging_leaders, peer_limit_up_ratio, coverage — theme ranking/breadth/peer rules are not
Wave-1; their rule versions freeze when added as future derived capabilities.

Consumer (Julia/Strategy) never ad-hoc computes a NOT_IN_WAVE1 metric and labels it canonical; any future
addition requires its own contract addendum + owner approval.

```

## [F] 06_PROVENANCE_FRESHNESS_V2.md
- source_path: /tmp/post_rd1_c1e_r4/06_PROVENANCE_FRESHNESS_V2.md
- sha256: `c61fc8b59601931858d5cbeb55215bb6dd6122d72aa654861217723b578b08fe`
- status: PASS-ELIGIBLE / REVIEW-PENDING

```markdown
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

```

## [G] 08_G_FIXTURE_BASELINE_V3R.md
- source_path: /tmp/post_rd1_c1e_r4/08_G_FIXTURE_BASELINE_V3R.md
- sha256: `44df213643080d0b6ec40d4cf436f1134b5bc14fec62ca03d3ebdd54095c414e`
- status: PASS-ELIGIBLE

```markdown
# 08 — G FIXTURE BASELINE V3R (normative; exact failure codes)

fixture_contract_version: market.fixture.v3
G normative = this REV (supersedes prior G baseline wording "INCOMPLETE-equivalent"). FIXTURE_SPEC_ACCEPTED
= YES; IMPLEMENTATION_ACCEPTANCE = NOT_EXECUTED. Deterministic SOURCE/EXPECTED/PUBLISHED/ORACLE per case;
exact failure code from market.failure.v2 for every non-success.

| CASE | source condition | expected canonical/typed | published state | oracle (PASS/FAIL) |
|------|------------------|---------------------------|-----------------|--------------------|
| GC-01 | full subject success | success canonical | canonical generation | requested==completed∧failed=∅ else FAIL |
| GC-02 | one subject fetch fails | INCOMPLETE_GENERATION (or SOURCE_UNAVAILABLE pinned by fixture, exactly one) | no new canonical | any canonical with failed≠∅ ⇒ FAIL |
| GC-03 | many subject fetches fail | INCOMPLETE_GENERATION | no new canonical | canonical with failed≠∅ ⇒ FAIL |
| GC-04 | membership≥1200/truncation | SOURCE_INCOMPLETE (no proof path) or canonical with mechanical completeness proof | per type | canonical w/o proof ⇒ FAIL |
| GC-05 | replace+partial fail | INCOMPLETE_GENERATION; prior intact | old authoritative | canonical replaced by partial ⇒ FAIL |
| GC-06 | duplicate triple | dedup counted or SOURCE_PARSE_FAILED | clean canonical | dup triple in canonical ⇒ FAIL |
| GC-07 | membership across dates | per-date canonical | per-date snapshots | any mixed date ⇒ FAIL |
| GC-08 | subject absent for date | NO_DATA | typed | answered from later map ⇒ FAIL |
| GC-09 | legitimate empty vs failure empty | empty(data_state=empty) vs SOURCE_UNAVAILABLE | distinct | failure as empty success ⇒ FAIL |
| GC-10 | malformed row | SOURCE_PARSE_FAILED or canonical w/ row accounting | typed/provable | silent drop+canonical w/o accounting ⇒ FAIL |
| GC-11 | as_of between snapshots | canonical snapshot = MAX(trade_date)<=as_of | selected snapshot | future snapshot ⇒ FAIL |
| GC-12 | no snapshot<=as_of | NO_DATA | none | current-map answer ⇒ FAIL |
| GC-13 | invalid provider config | INVALID_CONFIGURATION | none | silent→jyhf ⇒ FAIL |
| GC-14 | invalid on_existing config | INVALID_CONFIGURATION | none | silent→skip ⇒ FAIL |
| GC-15 | mixed-generation | MIXED_GENERATION_REJECTED (outcome A/B typed) | single-generation | mixed canonical ⇒ FAIL |

Each fixture records input/expected state/output/failure/forbidden state/provenance mechanically.

```

## [G] 09_CONSTITUENTS_HARDENING_CONTRACT_V2R.md
- source_path: /tmp/post_rd1_c1e_r4/09_CONSTITUENTS_HARDENING_CONTRACT_V2R.md
- sha256: `bda67b54b967cc1dacafbaf03c6babda51016f94bba3be9ff82d3dbdfda72afd`
- status: PASS-ELIGIBLE

```markdown
# 09 — CONSTITUENTS HARDENING CONTRACT V2R (normative; no "equivalent")

version: market.constituents-hardening.v2
Normative supersedes prior hardening wording ("INCOMPLETE-equivalent added where taxonomy permits").

1. Completeness ladder (unchanged, frozen):
   SOURCE_RESPONDED != SUBJECT_COMPLETE != GENERATION_COMPLETE != CANONICAL_PUBLISHED.
   count>0 is never completeness proof; unknown completeness fails closed.
2. Completeness identities now map to market.failure.v2 exact codes:
   - subject-level truncation/unproven completeness → SOURCE_INCOMPLETE
   - generation-level completeness failure → INCOMPLETE_GENERATION
   - publication prevented (incl. mixed-generation attempt) → MIXED_GENERATION_REJECTED
   No "equivalent"; no implementer-chosen mapping.
3. Malformed-row semantics (unchanged): row rejected + completeness still provable ⇒ canonical with row
   accounting; row rejected + completeness unprovable ⇒ no canonical success (SOURCE_PARSE_FAILED /
   INCOMPLETE_GENERATION). Silent skip + success without accounting forbidden.
4. Snapshot vs serving layer (unchanged): dated snapshot = point-in-time authority; current maps
   (subject_stock_map/subject_stock_staging/theme_stock_map) never historical truth; no hindsight, no
   current-map fallback.
5. Fail-loud configuration: invalid provider → INVALID_CONFIGURATION (never jyhf); invalid on_existing →
   INVALID_CONFIGURATION (never skip).
6. Publication atomicity: HARDENING-PUBLISH-01 (BUILD→VERIFY COMPLETENESS→PUBLISH) with generation
   identity fields; partial generation != canonical; GC-15 outcome A/B both terminal MIXED_GENERATION_REJECTED.

```

## [G] 03_GENERATION_PUBLICATION_INVARIANTS_V1.md
- source_path: /tmp/post_rd1_c1e_g2_acceptance/03_GENERATION_PUBLICATION_INVARIANTS_V1.md
- sha256: `22c8bcfad9e3a5eecd3f6e736efd746aad444d17b69cf397aecc0a0b227a9321`
- status: PASS-ELIGIBLE

```markdown
# 03 — GENERATION PUBLICATION INVARIANTS V1

version: market.generation-publish.v1

## HARDENING-PUBLISH-01 (frozen)
A constituents snapshot generation MUST NOT become canonical/published unless completeness acceptance
for the requested generation has succeeded. Partial subject acquisition MUST NOT publish a mixed
generation.

Generation identity (conceptual minimum; exact implementation NOT designed here):
```text
trade_date
provider
batch_id/generation_id
requested_subject_set
completed_subject_set
failed_subject_set
completeness_status
```

Required sequencing:
```text
BUILD → VERIFY COMPLETENESS → PUBLISH
```
Forbidden sequencing:
```text
DELETE PUBLISHED → FETCH PARTIAL → PUBLISH WHATEVER SUCCEEDED
```

## Invariants
- I1: no canonical publication without generation completeness acceptance.
- I2: prior valid published data remains distinguishable from a failed replacement attempt (authoritative
  generation pointer untouched until verified replacement).
- I3: destructive replacement may never be considered successful before generation verification.
- I4: PARTIAL GENERATION != CANONICAL GENERATION.
- I5: mixed-generation publication is prohibited (GC-15): allowed contract outcomes are
  (A) new generation rejected and previous complete generation remains authoritative, or
  (B) new generation stored only as explicit incomplete/noncanonical and never returned as canonical.
  Neither A nor B is chosen here as implementation architecture; both preserve the invariant.
- I6: every non-success terminal state is typed; no silent success, no silent stale/current mixture,
  no semantic fallback.

```

## [G] GC_FIXTURE_MANIFEST_v2.json
- source_path: /tmp/post_rd1_c1e_r4/GC_FIXTURE_MANIFEST_v2.json
- sha256: `c380c1fef043c9bc35a2ca6319c852e97ac5381951de31d2d2bc389eb9d54ded`
- status: PASS-ELIGIBLE

```json
{
  "manifest_version": "market.gc-manifest.v2",
  "contract_version": "market.fixture.v3",
  "failure_taxonomy_version": "market.failure.v2",
  "fixture_spec_accepted": true,
  "implementation_acceptance": "NOT_EXECUTED",
  "donor": {
    "repo": "tonychang925-dev/ai_theme_app",
    "commit": "f1bc3def72e0c4184799201aaf1ac5d02d6084d6",
    "constituents": {
      "base_blob": "609ece34609f1eaaed1a2e73849e3f4d014cd7be",
      "config_blob": "ca56b477c8cb5fdc27a8a0fcc0ad39b919159160",
      "jyhf_producer_blob": "719695eb5c8a23d065429f4d94076907d7804ca5",
      "detect_changed_blob": "ea2e517e8c80fc783d7be331cba69eea905792fc",
      "importer_blob": "49e157320fd180a743c4a93c73dfc2567da828ec"
    }
  },
  "cases": [
    {"case_id": "GC-01", "canonical": "success", "failure_code": null},
    {"case_id": "GC-02", "canonical": null, "failure_code": "INCOMPLETE_GENERATION"},
    {"case_id": "GC-03", "canonical": null, "failure_code": "INCOMPLETE_GENERATION"},
    {"case_id": "GC-04", "canonical": "completeness_proof_required", "failure_code": "SOURCE_INCOMPLETE"},
    {"case_id": "GC-05", "canonical": null, "failure_code": "INCOMPLETE_GENERATION"},
    {"case_id": "GC-06", "canonical": "dedup_counted", "failure_code": "SOURCE_PARSE_FAILED"},
    {"case_id": "GC-07", "canonical": "per_date_membership", "failure_code": null},
    {"case_id": "GC-08", "canonical": null, "failure_code": "NO_DATA"},
    {"case_id": "GC-09", "canonical": "empty_data_state", "failure_code": "SOURCE_UNAVAILABLE"},
    {"case_id": "GC-10", "canonical": "row_accounted_provable", "failure_code": "SOURCE_PARSE_FAILED"},
    {"case_id": "GC-11", "canonical": "max_snapshot_le_as_of", "failure_code": null},
    {"case_id": "GC-12", "canonical": null, "failure_code": "NO_DATA"},
    {"case_id": "GC-13", "canonical": null, "failure_code": "INVALID_CONFIGURATION"},
    {"case_id": "GC-14", "canonical": null, "failure_code": "INVALID_CONFIGURATION"},
    {"case_id": "GC-15", "canonical": null, "failure_code": "MIXED_GENERATION_REJECTED"}
  ],
  "forbidden_path_counters": {
    "PARTIAL_GENERATION_CANONICAL_SUCCESS_FORBIDDEN_PATH_COUNT": 0,
    "MIXED_GENERATION_PUBLICATION_FORBIDDEN_PATH_COUNT": 0,
    "FUTURE_SNAPSHOT_FORBIDDEN_PATH_COUNT": 0,
    "CURRENT_MAP_AS_HISTORY_FORBIDDEN_PATH_COUNT": 0,
    "UNKNOWN_COMPLETENESS_SUCCESS_FORBIDDEN_PATH_COUNT": 0,
    "INVALID_PROVIDER_FALLBACK_FORBIDDEN_PATH_COUNT": 0,
    "INVALID_ON_EXISTING_FALLBACK_FORBIDDEN_PATH_COUNT": 0,
    "UPSTREAM_FAILURE_AS_EMPTY_FORBIDDEN_PATH_COUNT": 0
  }
}

```

## [H] 02_FAILURE_TAXONOMY_V2.md
- source_path: /tmp/post_rd1_c1e_r4/02_FAILURE_TAXONOMY_V2.md
- sha256: `2f54780a3c45b688db6b36549b682b108e666d315ca4c8e7851322ea5521bd50`
- status: PASS-ELIGIBLE / REVIEW-PENDING

```markdown
# 02 — FAILURE TAXONOMY V2 (normative, supersedes V1)

failure_contract_version: `market.failure.v2`
status: FROZEN_AS_GOVERNANCE. Supersedes V1; V2 adds formal identities that V1 referred to only as
"equivalent". No "equivalent", no implementation-time guessing.

## Formal failure identities
Request layer:
- INVALID_REQUEST
- MISSING_REQUIRED_ARGUMENT
- INVALID_STOCK_CODE
- INVALID_DATE_RANGE
- INVALID_CONFIGURATION   (NEW: config-provider / config-mode invalid; GC-13/14)

Capability layer:
- CAPABILITY_NOT_BOUND
- CAPABILITY_NOT_IMPLEMENTED
- SOURCE_UNAVAILABLE
- SOURCE_TIMEOUT

Data layer:
- NO_DATA
- STALE_DATA            (only when a frozen threshold exists; Wave-1 never emits — see F)
- PROVENANCE_UNVERIFIED
- SOURCE_INCOMPLETE     (NEW: source responded but membership completeness not proven/truncated; GC-04)
- INCOMPLETE_GENERATION (NEW: generation completeness not achieved; publication prevented; GC-02/03/05)
- MIXED_GENERATION_REJECTED (NEW: attempted mixed-generation canonical publication rejected; GC-15
  outcome-A/B terminal state)

Source-contract layer:
- SOURCE_SCHEMA_CHANGED
- SOURCE_PARSE_FAILED
- INTERNAL_PROVIDER_ERROR

## Exact GC-01..15 mapping (no "equivalent")
| case | canonical result | exact identity |
|------|------------------|----------------|
| GC-01 | success | canonical generation (no failure) |
| GC-02 | typed failure | SOURCE_UNAVAILABLE OR INCOMPLETE_GENERATION (per determinism of fixture, exactly one asserted) |
| GC-03 | typed failure | INCOMPLETE_GENERATION |
| GC-04 | proof OR typed | SOURCE_INCOMPLETE (when completeness unproven) |
| GC-05 | typed failure; old intact | INCOMPLETE_GENERATION |
| GC-06 | dedup+counted OR typed | SOURCE_PARSE_FAILED (only when dedup rule cannot resolve) |
| GC-07 | success per-date | canonical per-date membership |
| GC-08 | typed per-date absence | NO_DATA (subject absent for date) |
| GC-09 | distinct states | legitimate empty=data_state=empty; failure empty=SOURCE_UNAVAILABLE |
| GC-10 | typed failure | SOURCE_PARSE_FAILED |
| GC-11 | success | canonical snapshot <= as_of |
| GC-12 | typed failure | NO_DATA |
| GC-13 | typed config failure | INVALID_CONFIGURATION |
| GC-14 | typed config failure | INVALID_CONFIGURATION |
| GC-15 | outcome A/B typed | MIXED_GENERATION_REJECTED |

## Rules (unchanged)
failure→typed failure; failure != empty success; != synthetic success; != semantic alias; != fallback.
GC-02 fixture pins which of SOURCE_UNAVAILABLE/INCOMPLETE_GENERATION applies for its specific source
condition (each fixture asserts exactly one).

```

## [I] 03_CROSS_REPO_AUTHORITY_MATRIX_V1.md
- source_path: /tmp/post_rd1_c1e_unblock/03_CROSS_REPO_AUTHORITY_MATRIX_V1.md
- sha256: `764089ed6e166ac1343fb92cebfbc40414a4616b37a60aed4303fd26e5b70153`
- status: PASS-ELIGIBLE / REVIEW-PENDING

```markdown
# 03 — CROSS-REPO AUTHORITY / ISOLATION MATRIX V1

Matrix version: market.authority.v1
Rows: semantic concern. Columns: Julia_core / Julia-AI-Assistant / ai_theme_app.
Cell values: OWNER / CONSUMER / ADAPTER / NON_AUTHORITY / NOT_APPLICABLE.

| Semantic concern                  | Julia_core            | Julia-AI-Assistant              | ai_theme_app                 |
|-----------------------------------|-----------------------|---------------------------------|------------------------------|
| semantic capability definition    | OWNER                 | CONSUMER                        | NON_AUTHORITY                |
| request/response contract         | OWNER (authority)     | CONSUMER/ADAPTER                | CONSUMER (data provider side)|
| failure taxonomy                  | OWNER                 | ADAPTER (maps to transport)     | CONSUMER                     |
| source acquisition                | NOT_APPLICABLE        | NON_AUTHORITY                   | OWNER                        |
| normalization                     | NON_AUTHORITY         | NON_AUTHORITY                   | OWNER                        |
| derived metrics                   | NON_AUTHORITY         | NON_AUTHORITY                   | OWNER (domain owner; Julia/Strategy never compute ad hoc) |
| runtime routing                   | NOT_APPLICABLE        | OWNER (production composition)  | NON_AUTHORITY                |
| production registration           | NOT_APPLICABLE        | OWNER (explicit cutover gate only)| NON_AUTHORITY               |
| deployment/composition            | NOT_APPLICABLE        | OWNER                           | CONSUMER                     |
| rollback                          | NOT_APPLICABLE        | ADAPTER (per-capability)        | OWNER (per-provider)         |

Rules:
- No ambiguous/shared OWNER for one semantic concern.
- Julia_core stays semantic authority; the existence of capability strings in an implementation repo
  (router/source) does NOT confer semantic authority (normative separation).
- This matrix is the governing reference; repository evidence below is descriptive, not authority.

AUTHORITY_COLLISION = NO (model matches observed repository split; no silent semantic-authority transfer).

```

## [I] 04_PRODUCTION_ISOLATION_INVARIANTS_V1.md
- source_path: /tmp/post_rd1_c1e_unblock/04_PRODUCTION_ISOLATION_INVARIANTS_V1.md
- sha256: `77bafe9328f4a61d883fcd52d085446e5ee92a4be0e5b138918863ff3d50d169`
- status: PASS-ELIGIBLE / REVIEW-PENDING

```markdown
# 04 — PRODUCTION ISOLATION INVARIANTS V1

invariant_version: market.isolation.v1
status: FROZEN_AS_GOVERNANCE + spot source inspection (2026-09-07)

1. ai_theme_app source implementation does NOT auto-register itself into Julia production runtime.
   - Spot evidence: no import-time registration call site observed linking ai_theme_app modules into
     Julia-AI-Assistant runtime roots (ai_theme_app is a separate repo; Julia-AI-Assistant main has no import
     of ai_theme_app). Full-import-graph proof deferred to fixture/CI gate.
2. Julia-AI-Assistant MarketToolRouter capability strings are NOT semantic authority merely by presence.
   - Separation frozen in 03 (descriptive evidence != normative authority).
3. New Wave-1 source work cannot resurrect old fallback semantics.
   - Binding v1 (01) forbids alias/fallback; failure taxonomy v1 (02) forbids fallback-as-result.
4. No dual-authority path: old market router + new source adapter must not both claim canonical
   market.stock.history authority.
   - DUAL_AUTHORITY_PATH_COUNT = 0 (no new adapter exists; adapter activation requires cutover gate).
5. No import-time registration side effect in Wave-1 commits. (Hard requirement on future source edits.)
6. No production cutover in any Wave-1 source-implementation commit.
7. Production adapter activation requires a separate explicit cutover gate (owner decision, outside Wave-1).

These are commitments + spot-inspection results; they are enforced prospectively at the source-edit gate and
by CI (no registration/import side effects) when Wave-1 source edits are later authorized.

```

## [I] 05_EXISTING_ROUTER_DISPOSITION.md
- source_path: /tmp/post_rd1_c1e_unblock/05_EXISTING_ROUTER_DISPOSITION.md
- sha256: `47800a824ce666cfd16f7a10d48639a2f3071bfd2326bbc4d3b98b1888d30d30`
- status: PASS-ELIGIBLE / REVIEW-PENDING

```markdown
# 05 — EXISTING ROUTER DISPOSITION (descriptive, non-editing)

Target (NOT edited): Julia-AI-Assistant `server_v2_1_market_router.py` @ main 05e4e1fbe402ce38a6a4084bc338b549eb0ba427.

Wave-1 relevant behaviors and disposition:

| Behavior | Evidence (main@05e4e1f) | Disposition for Wave-1 binding |
|----------|-------------------------|--------------------------------|
| capability="market.stock.history" with fallback_capability="market.snapshot.read" | lines ~61-63 | FORBIDDEN_FOR_NEW_BINDING (alias/fallback banned) |
| capability="market.theme.constituents" with fallback_capability="market.intelligence.observe" | lines ~69-72 | FORBIDDEN_FOR_NEW_BINDING |
| capability="market.stock.auction" fallback "market.intelligence.observe" | ~55-57 | NOT_APPLICABLE_TO_WAVE1 (auction deferred); FORBIDDEN_FOR_NEW_BINDING as alias pattern |
| capability="market.theme.capital" fallback "market.intelligence.observe" | ~76-77 | NOT_APPLICABLE_TO_WAVE1 (capital deferred); FORBIDDEN alias pattern |
| generic hint → snapshot mapping (10-word locked hints, no names) | comments ~3-25 | KEEP_COMPATIBILITY_ONLY (existing production behavior, unchanged; not part of Wave-1 binding) |
| generic stock code → stock.history | ~61-63 | KEEP_COMPATIBILITY_ONLY for existing path; NOT normative for new binding |
| best-effort argument attachment | router argument attach logic | DEPRECATE_BEFORE_CUTOVER (must not become adapter semantics) |

Classification summary:
- REPLACE_AT_CUTOVER: none in Wave-1 (no adapter activated yet).
- FORBIDDEN_FOR_NEW_BINDING: fallback_capability edges for history & constituents (and the alias pattern in
  general).
- KEEP_COMPATIBILITY_ONLY: existing production hint/snapshot behavior remains untouched this task.
- DEPRECATE_BEFORE_CUTOVER: best-effort argument attachment.

Note: documenting historical behavior is descriptive evidence; it does NOT confer normative authority on it.

```

## [J] 06_ROLLBACK_BOUNDARY_V1.md
- source_path: /tmp/post_rd1_c1e_freeze2/06_ROLLBACK_BOUNDARY_V1.md
- sha256: `c33e8a2da4456aa220ed05ad8129e6128afc0794053eeb4a2b9904e5c93bdd94`
- status: PASS-ELIGIBLE / REVIEW-PENDING

```markdown
# 06 — ROLLBACK BOUNDARY V1

version: market.rollback.v1

Rollback is BINDING/CUTOVER rollback, never source-history rewriting, never semantic fallback.

## Per-capability rollback (history independent from constituents)
- what can be disabled: the Wave-1 capability adapter/binding for one capability only (binding rollback)
- what becomes inactive: the newly activated adapter (if cutover ever occurred); in Wave-1 (no cutover)
  nothing is active — rollback = no-op for production
- what authority remains unchanged: Julia_core semantic authority; ai_theme_app source ownership;
  Julia-AI-Assistant production composition until an explicit cutover gate
- data/schema mutations requiring rollback handling: none in Wave-1 source implementation (no DB migration
  authorized); if a later cutover introduced schema/data changes, rollback must handle them explicitly

## Forbidden rollback semantics
- history → snapshot.read (FORBIDDEN)
- constituents → intelligence.observe (FORBIDDEN)
- rollback to any semantically different capability (FORBIDDEN)

Rollback returns to the previous production BINDING state, not another semantic operation.

## Record-keeping
Each capability keeps separate commit lineage / tests / fixture acceptance / registration gate so that a
history failure never requires constituents rollback and vice versa.

```

# APPENDIX — Explicit unresolved facts

- DONOR_PAGINATION_COMPLETENESS = NOT_PROVEN
- IMPLEMENTATION_ACCEPTANCE = NOT_EXECUTED
- SOURCE_EDIT_AUTH = NOT_GRANTED
# APPENDIX — Invariant index (navigational)

- semantic alias = forbidden
- semantic fallback = forbidden
- synthetic success = forbidden
- failure -> typed failure
- unknown completeness -> fail closed
- future snapshot -> forbidden
- current-map-as-history -> forbidden
- partial generation -> noncanonical
- mixed generation publication -> forbidden
- BUILD -> VERIFY -> PUBLISH
- rollback != semantic fallback
- source implementation != production activation
- semantic authority = Julia_core
- source owner = ai_theme_app
- production adapter activation = separate cutover gate
