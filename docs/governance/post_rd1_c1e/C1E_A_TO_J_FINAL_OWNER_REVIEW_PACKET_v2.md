# C1E A–J FINAL OWNER REVIEW PACKET v2 (read-only, verbatim)

Status vocabulary: PASS-ELIGIBLE / HOLD / BLOCKING / REVIEW-PENDING only. No gate labeled PASS/APPROVED/CLOSED_PASS. Owner/Mira performs final approval.

Superseded references (older G fixture baseline market.fixture.v1 in freeze2/05) are NOT included in the primary section and must not override market.fixture.v3.

## [A] 00_A1_QUALIFICATION.md

- logical_gate: A
- source_path: /tmp/post_rd1_c1e_a1/00_A1_QUALIFICATION.md
- filename: 00_A1_QUALIFICATION.md
- sha256: `43416d0a705dbd85e60cec9ea00a420859a15210d43e16fb32cdc3dce6eea143`
- status: PASS-ELIGIBLE

```markdown
# C1E-A1 — market.theme.constituents source qualification

Decision: FOUND_EXACT

## Qualified mechanism set (tracked, exact refs; ai_theme_app HEAD f1bc3def72e0c4184799201aaf1ac5d02d6084d6)
- Mechanism: per-`trade_date` full subject→stock membership snapshot
  `subject_stock_daily_snapshot` (delete-then-rebuild for the trade date),
  produced by the tracked JYHF subject-stock daily snapshot job, consumed via
  subject stock pool gateway; membership-change detection exists separately.
- Qualified files (role=DONOR; authoritative status pending fixture-time
  verification of complete-member semantics + no-hindsight consumption):
  | path | blob SHA |
  |------|----------|
  | stock_processing_service/application/jobs/subject_stock_snapshot/base.py | 609ece34609f1eaaed1a2e73849e3f4d014cd7be |
  | stock_processing_service/application/jobs/subject_stock_snapshot/config.py | ca56b477c8cb5fdc27a8a0fcc0ad39b919159160 |
  | stock_processing_service/application/jobs/subject_stock_snapshot/jyhf_producer.py | 719695eb5c8a23d065429f4d94076907d7804ca5 |
  | database_service/scripts/detect_jyhf_changed_subjects.py | ea2e517e8c80fc783d7be331cba69eea905792fc |

## Semantic check
- Answers "given canonical theme identity + cutoff, which stocks were members":
  YES via date-keyed snapshot rows (subject_key + trade_date). Not merely ranking/
  heat/leader/event/intelligence. Semantic alias: NO.
- source_name: JYHF (九盈衡丰) subject detail DOM capture, materialized to daily
  subject→stock snapshot table.
- input identity: subject_key (canonical); output identity: stock members per day.
- membership semantics: full-list snapshot per trade_date (delete+rebuild),
  verified at fixture acceptance; membership effective timestamp = trade_date.
- temporal: POINT_IN_TIME_CAPABLE (date-keyed; no-hindsight rule = consumer must
  use snapshot date <= as_of; never future membership). CURRENT_ONLY not claimed.

## Exclusion checks
- branch name as identity: NO; untracked source accepted: NO.
- Other repos (Julia-AI-Assistant router = capability vocabulary only;
  julia_core / market lanes = no tracked membership source) do not hold a second
  qualified source → single qualified source, no MULTIPLE decision.

## Open qualification item (recorded, not blocking FOUND_EXACT)
- Fixture-time must prove the JYHF detail page parser yields the COMPLETE member
  set (not partial/leader-only) and define pagination/completeness + delisted/
  suspended treatment before fixture acceptance closes.

```

## [A] 07_EXACT_SOURCE_IDENTITY_V1.md

- logical_gate: A
- source_path: /tmp/post_rd1_c1e_freeze2/07_EXACT_SOURCE_IDENTITY_V1.md
- filename: 07_EXACT_SOURCE_IDENTITY_V1.md
- sha256: `901ad43fc031f3be79884eaedecc66ddf17b6a48b6ef38d2905b1ed241a6181e`
- status: PASS-ELIGIBLE

```markdown
# 07 — EXACT SOURCE IDENTITY REVALIDATION V1 (Gate A)

Rule: source identity must be exact (repo + commit + path + blob SHA). Branch names are invalid identity;
untracked/local-only files cannot be authoritative donor source.

## market.stock.history — revalidated inventory (observed 2026-09-07)
| repo | commit | path | blob SHA | role | classification |
|------|--------|------|----------|------|----------------|
| tonychang925-dev/ai_theme_app | f1bc3def72e0c4184799201aaf1ac5d02d6084d6 | check_stock_history.py | 34498cc487f0b734d6b3df810d5bf974b37c7908 | collector | historical/donor |
| tonychang925-dev/ai_theme_app | f1bc3def72e0c4184799201aaf1ac5d02d6084d6 | collect_jyhf_history_incremental.py | 762863970efabb2f8d4fc12676aace2bc8a1b138 | provider collector | historical/donor |
| tonychang925-dev/ai_theme_app | f1bc3def72e0c4184799201aaf1ac5d02d6084d6 | import_shenjian_history.py | 134ddfd08fbc4dfbba6c5e7d3d7e00446c6e9c98 | provider collector | historical/donor |
| tonychang925-dev/ai_theme_app | f1bc3def72e0c4184799201aaf1ac5d02d6084d6 | database_service/scripts/import_jyhf_history_incremental.py | 7153489ccfd8474397f06940337577399e89b673 | import | historical/donor |
| tonychang925-dev/ai_theme_app | f1bc3def72e0c4184799201aaf1ac5d02d6084d6 | database_service/scripts/load_subject_history_staging.py | ee1bd3446716b756a34e91139f60bfee2533abe4 | staging load | historical/donor |

All blobs were re-read from ai_theme_app HEAD f1bc3def72e0c4184799201aaf1ac5d02d6084d6. Worktree dirty (99
untracked files) — none of the untracked files is used as donor authority here.

## market.theme.constituents
DEDICATED_TRACKED_DONOR_SOURCE = NOT_FOUND
(Theme membership is represented only through theme_master DB artifacts
[database_service/theme_master_data.sql, docs/architecture/theme_master_schema.sql,
evaluate_service/core/virtual_theme_database.py] — production/data artifacts, not a pinned dedicated
donor source.)

Consequence: A = HOLD until constituents donor identity is resolved exactly. No donor is invented to close
the gate.

```

## [B] 01_CAPABILITY_BINDING_V1.md

- logical_gate: B
- source_path: /tmp/post_rd1_c1e_unblock/01_CAPABILITY_BINDING_V1.md
- filename: 01_CAPABILITY_BINDING_V1.md
- sha256: `31eb5ec898d526b8b3b5b432be49c3b7a7f33429899a2e123648b2efd21ea53f`
- status: PASS-ELIGIBLE / REVIEW-PENDING

```markdown
# 01 — CAPABILITY BINDING CONTRACT V1

binding_version: `market.binding.v1`
status: FROZEN_AS_GOVERNANCE (owner/Mira acceptance pending)
semantic_owner: Julia_core (semantic capability authority — NOT transferred to any implementation repo)
source_owner: ai_theme_app (market source/data/provider owner)
production_adapter_owner: Julia-AI-Assistant (Brain / production composition + adapter — ONLY after an explicit cutover gate; no cutover in Wave-1)

## market.stock.history
- canonical_name: `market.stock.history`
- binding_version: market.binding.v1
- request_contract_version: PENDING (held open; not frozen in this task)
- response_contract_version: PENDING
- failure_contract_version: `market.failure.v1` (see 02)
- provider/donor exact refs: ai_theme_app HEAD f1bc3def72e0c4184799201aaf1ac5d02d6084d6 —
  - check_stock_history.py blob 34498cc487f0b734d6b3df810d5bf974b37c7908 (historical/donor REFERENCE)
  - collect_jyhf_history_incremental.py blob 762863970efabb2f8d4fc12676aace2bc8a1b138
  - import_shenjian_history.py blob 134ddfd08fbc4dfbba6c5e7d3d7e00446c6e9c98
  - database_service/scripts/import_jyhf_history_incremental.py blob 7153489ccfd8474397f06940337577399e89b673
  - database_service/scripts/load_subject_history_staging.py blob ee1bd3446716b756a34e91139f60bfee2533abe4
  classification: donor/historical (authoritative only if independently re-verified)

## market.theme.constituents
- canonical_name: `market.theme.constituents`
- binding_version: market.binding.v1
- request_contract_version: PENDING
- response_contract_version: PENDING
- failure_contract_version: market.failure.v1
- provider/donor exact refs: NONE pinned — constituents membership currently lives in theme_master DB
  schema/data (database_service/theme_master_data.sql, docs/architecture/theme_master_schema.sql,
  evaluate_service/core/virtual_theme_database.py). DEDICATED_TRACKED_DONOR_SOURCE = NOT_FOUND.

## Shared binding rules (Wave-1)
- semantic alias = NONE; fallback alias = NONE.
- Forbidden mappings (different semantic operations; missing required input is a typed failure):
  market.stock.history → market.snapshot.read
  market.theme.constituents → market.intelligence.observe
- duplicate_operation_policy: if an existing production router exposes the same canonical capability, do NOT
  auto-register a second authority, do NOT silently replace, do NOT run dual semantic owners. The binding
  identifies exactly which implementation may become production adapter AFTER a separate cutover gate.
- replacement_policy: adapter replacement requires owner decision + cutover gate; capability contract
  (binding/request/response/failure versions) is the cutover checklist anchor.
- deprecation_policy: any deprecated alias/fallback must be removed before the new adapter activates.
- registration_policy: NO registration in any Wave-1 source-implementation commit.
- rollback_binding: rollback is per-capability; never requires a whole-donor rollback.

```

## [C] 01_REQUEST_CONTRACT_V1.md

- logical_gate: C
- source_path: /tmp/post_rd1_c1e_freeze2/01_REQUEST_CONTRACT_V1.md
- filename: 01_REQUEST_CONTRACT_V1.md
- sha256: `4dcb0acf35b7f562e67615c160e9d3776e31b54dcfcdbb1fcd042623d5da196c`
- status: PASS-ELIGIBLE / REVIEW-PENDING

```markdown
# 01 — WAVE-1 REQUEST CONTRACT V1

request_contract_version: `market.request.v1`
status: FROZEN_AS_GOVERNANCE (independent owner/Mira review pending → PASS-ELIGIBLE)
Shared fields (both capabilities): request_id (string, required), correlation_id (string, required),
schema_version (fixed market.request.v1, required), requested_at (ISO-8601 UTC, required),
idempotency_key (string, required).

## market.stock.history
| field | required | type | format | normalization owner | validation owner | default allowed |
|-------|----------|------|--------|---------------------|------------------|-----------------|
| stock_code | REQUIRED | string | canonical exchange symbol (e.g. 600000.SH); normalized by source owner | ai_theme_app | Julia_core (semantic) | NO |
| start_date | REQUIRED | string | YYYY-MM-DD | ai_theme_app | Julia_core | NO |
| end_date | REQUIRED | string | YYYY-MM-DD (>= start_date) | ai_theme_app | Julia_core | NO |
| as_of | OPTIONAL | string | YYYY-MM-DD evaluation cutoff; default = end_date | Julia_core | Julia_core | YES (end_date) |
| adjustment_mode | OPTIONAL | enum | NONE / FORWARD / BACKWARD | ai_theme_app | Julia_core | YES (NONE) |
| market/exchange | OPTIONAL | string | exchange tag embedded in canonical symbol; direct override only when required | ai_theme_app | Julia_core | YES (derived from symbol) |

Calendar semantics: trading sessions; weekend/holiday excluded per source trading calendar; T0 = end_date
session; no future rows; lookback window is inclusive trading-session range. Missing required argument →
typed failure per market.failure.v1 (MISSING_REQUIRED_ARGUMENT); invalid stock code → INVALID_STOCK_CODE;
invalid range → INVALID_DATE_RANGE.

## market.theme.constituents
Canonical theme identity input (REQUIRED): subject_key (string) resolving to a single theme identity via an
explicit universe mapping owned by ai_theme_app. Optional: as_of, universe_version (validated against pinned
universe). Fuzzy theme-name guessing is NOT part of this contract (a separate semantic capability would be
required). Optional fields with explicit defaults documented per capability binding.

```

## [D] 02_RESPONSE_CONTRACT_V1.md

- logical_gate: D
- source_path: /tmp/post_rd1_c1e_freeze2/02_RESPONSE_CONTRACT_V1.md
- filename: 02_RESPONSE_CONTRACT_V1.md
- sha256: `b321c978f4fc463d9e087899dca945016cbf4666dda23f707219c660e003a57f`
- status: PASS-ELIGIBLE / REVIEW-PENDING

```markdown
# 02 — WAVE-1 RESPONSE CONTRACT V1

response_contract_version: `market.response.v1`
status: FROZEN_AS_GOVERNANCE (independent review pending → PASS-ELIGIBLE)

Shared envelope (both capabilities):
capability_id, contract_version, status (success|partial|unavailable|error), data_state
(normal|empty|stale), as_of, payload, source_records (evidence summary), failures[], observed_at,
schema_version, provenance (per F).

## market.stock.history payload rows[]
Row canonical fields:
- trade_date (YYYY-MM-DD, non-null; normalized date identity)
- open / high / low / close (non-null decimal; null only if the SOURCE record itself is null for that
  field, in which case failure PARTIAL/SOURCE_PARSE_FAILED rules apply — see below)
- volume, amount (numeric; source units as documented by source owner)
- adjustment semantics: each row carries an `adjustment_mode` echo + per-field adjusted flag produced by
  the normalization owner (ai_theme_app)

Row rules: deterministic ordering by trade_date ascending; duplicate/out-of-order dates and malformed
numeric fields are source-contract violations → typed failure (SOURCE_PARSE_FAILED / NO_DATA per
market.failure.v1), never silently dropped. No “best effort” fields with undefined meaning. No
provider-specific raw field may silently become a canonical field; any additional canonical field requires
a contract version bump.

## market.theme.constituents payload
Deterministic list of constituents for the resolved theme subject with membership cutoff identity; exact
row fields frozen with the capability response contract addendum at fixture-acceptance time.

## data_state semantics
- normal: payload reflects requested as_of within freshness
- empty: NO rows exist for the valid requested window (typed NO_DATA-style empty success is NOT allowed;
  empty → data_state=empty only when contract defines empty as a valid outcome, never as UNAVAILABLE)
- stale: source data older than threshold (typed STALE_DATA result per frozen contract; never silently
  relabeled current)

```

## [E] 03_DERIVED_METRIC_OWNERSHIP_V1.md

- logical_gate: E
- source_path: /tmp/post_rd1_c1e_freeze2/03_DERIVED_METRIC_OWNERSHIP_V1.md
- filename: 03_DERIVED_METRIC_OWNERSHIP_V1.md
- sha256: `198ff7a3a97f335660bbd19ce8ca07801b2bffd0eaa7299b20255dff91399cd5`
- status: PASS-ELIGIBLE / REVIEW-PENDING

```markdown
# 03 — DERIVED METRIC OWNERSHIP V1

version: market.derived-ownership.v1
Classification vocabulary: SOURCE_NATIVE / NORMALIZATION_DERIVED / CAPABILITY_DERIVED /
CONSUMER_DERIVED / NOT_IN_WAVE1. One semantic owner only; no metric recomputed in multiple repos with
different formulas.

| derived value | owner | class | formula/precision policy (Wave-1) |
|---------------|-------|-------|-----------------------------------|
| pct_change (close-to-close) | ai_theme_app | NORMALIZATION_DERIVED | (close_t/close_{t-1} - 1); decimals per source policy; based on adjusted series when adjustment_mode != NONE |
| amplitude (high-low range %) | ai_theme_app | NORMALIZATION_DERIVED | (high-low)/prev_close, defined where prev_close present and >0; precision policy documented |
| turnover-related values | ai_theme_app | NORMALIZATION_DERIVED | formula defined against source volume/amount units; NOT_IN_WAVE1 unless source provides float shares |
| moving averages | ai_theme_app | CAPABILITY_DERIVED | exact window definition at capability contract addendum; NOT computed ad hoc by consumer |
| returns | ai_theme_app | NORMALIZATION_DERIVED | log/simple choice fixed at fixture acceptance |
| volume ratios / intraday_volume_vs_prev | ai_theme_app | CAPABILITY_DERIVED | implementation MISSING — open; formula frozen only after implementation + fixture |
| total_return / max_drawdown_from_peak / key_level_status / open_gap_vs_prev_close / limit_up_seal | ai_theme_app | CAPABILITY_DERIVED | domain owner = ai_theme_app; key_level_status prior-limit-up support incomplete (open); limit_up_seal implementation MISSING (open) |
| theme relative_strength_rank / breadth_change / emerging_leaders / peer_limit_up_ratio / coverage | ai_theme_app | CAPABILITY_DERIVED | universe_version/source completeness/ranking rule version/breadth rule version/peer-follow-through rule version to be frozen at constituents fixture acceptance |

Rule: Julia / Strategy layer NEVER ad-hoc recomputes a metric owned above; consumer-visible derived fields
require provenance back to the owning repo's rule version (see F).

```

## [F] 04_PROVENANCE_FRESHNESS_V1.md

- logical_gate: F
- source_path: /tmp/post_rd1_c1e_freeze2/04_PROVENANCE_FRESHNESS_V1.md
- filename: 04_PROVENANCE_FRESHNESS_V1.md
- sha256: `8fb196fd839fae0e7f92e714d70fd9e21e64379c4862f4b692eb8b7ff9002323`
- status: PASS-ELIGIBLE / REVIEW-PENDING

```markdown
# 04 — PROVENANCE / FRESHNESS V1

version: market.provenance.v1

## Provenance envelope (per response, and per material derived field where required)
- source_name (provider/dataset name)
- source_kind (e.g. market_snapshot / history_endpoint / theme_universe)
- source_ref/version (pinned source schema/dataset version; blob/commit where vendored)
- retrieved_at (actual retrieval timestamp)
- source_data_time (timestamp carried IN the source payload; may be null if absent)
- query_as_of (requested cutoff)
- freshness_status (FRESH / STALE / UNKNOWN)
- query_window (effective trading-session range actually served)
- rule_version where derived (ranking/breadth/peer rule version; normalization/adjustment version)

## Freshness states (exact)
- FRESH: source_data_time within the frozen threshold of query_as_of (threshold + ownership:
  ai_theme_app defines per source-kind; recorded in fixture acceptance)
- STALE: source_data_time older than threshold → STALE_DATA typed failure or explicitly typed stale result
  (per frozen contract); never silently relabeled as current
- UNKNOWN: source timestamp absent → provenance.freshness_status = UNKNOWN; a current wall-clock timestamp
  must NEVER substitute for an unknown source timestamp

## Invariant
A derived field exists only if source_records/provenance explains how it was derived (formula + rule
version + source refs). MISSING EVIDENCE != NEGATIVE EVIDENCE.

```

## [G] 01_G_FIXTURE_BASELINE_V3.md

- logical_gate: G
- source_path: /tmp/post_rd1_c1e_g2_acceptance/01_G_FIXTURE_BASELINE_V3.md
- filename: 01_G_FIXTURE_BASELINE_V3.md
- sha256: `018d51a63a04e5c1d6120c143a4da2d0929c86322fd7cfa84ae16465074231ac`
- status: PASS-ELIGIBLE

```markdown
# 01 — G FIXTURE BASELINE V3 (constituents donor-specific, GC-01..GC-15)

fixture_contract_version: market.fixture.v3
FIXTURE_SPEC_ACCEPTED = YES (contract only)
IMPLEMENTATION_ACCEPTANCE = NOT_EXECUTED (SOURCE_EDIT_AUTH = NOT_GRANTED)
Donor authority: ai_theme_app @ f1bc3def72e0c4184799201aaf1ac5d02d6084d6; importer blob
import_jyhf_stock_daily_incremental.py = 49e157320fd180a743c4a93c73dfc2567da828ec.
GC spec oracle rule: PASS/FAIL oracles are deterministic state comparisons over the published
snapshot/generation ledger + typed outcome; they never execute the production implementation.

Each case below is a fixture CONTRACT: SOURCE_INPUT (deterministic source sample), PREEXISTING_STATE,
EXPECTED_* (canonical or typed failure), EXPECTED_PUBLISHED_STATE, FORBIDDEN_OUTPUT, DERIVATION_RULE,
PASS_ORACLE, FAIL_ORACLE.

## GC-01 complete membership success
- PURPOSE: full subject set acquisition publishes a canonical generation.
- SOURCE_INPUT: provider returns complete member sets for requested subjects (deterministic fixture).
- PREEXISTING_STATE: none / empty ledger.
- EXPECTED_CANONICAL_OUTPUT: canonical constituents generation; completeness_status=COMPLETE; status=success.
- EXPECTED_PUBLISHED_STATE: generation marked canonical (published) for trade_date; ledger complete.
- FORBIDDEN_OUTPUT: any incomplete flag absent; no partial.
- DERIVATION_RULE: BUILD→VERIFY COMPLETENESS (requested==completed, failed==∅)→PUBLISH.
- PASS_ORACLE: published generation.completeness==COMPLETE ∧ requested==completed ∧ failed==∅.
- FAIL_ORACLE: any of those false ⇒ fixture fails.

## GC-02 one subject upstream fetch failure
- PURPOSE: single failure must never be canonical success.
- EXPECTED: typed failure (SOURCE_UNAVAILABLE/partial-with-disclosure); NEVER canonical success.
- EXPECTED_PUBLISHED_STATE: no new canonical generation; prior canonical (if any) unchanged.
- FORBIDDEN_OUTPUT: status=ok with count>0; partial generation exposed as canonical.
- PASS_ORACLE: outcome is typed failure OR stored only as explicit incomplete(noncanonical) generation.
- FAIL_ORACLE: canonical published generation exists containing partial sets ⇒ fail.

## GC-03 multiple subject upstream failures
- PURPOSE: many failures must not be masked by success of others.
- EXPECTED: typed failure (SOURCE_UNAVAILABLE/PARTIAL_DATA per market.failure.v1).
- PASS_ORACLE: failed_subject_set non-empty ⇒ no canonical publication.
- FAIL_ORACLE: canonical publication with failed_subject_set non-empty ⇒ fail.

## GC-04 pagination / completeness boundary (donor start=0/end=1200)
- PURPOSE: donor default range is not completeness proof.
- SOURCE_INPUT: membership exceeding 1200 rows and/or server pages.
- EXPECTED: either mechanical completeness proof (requested==returned, no truncation, page loop exhausted)
  OR typed INCOMPLETE failure (SOURCE_INCOMPLETE-equivalent per frozen taxonomy).
- PASS_ORACLE: completeness_status ∈ {COMPLETE(proof), INCOMPLETE(typed failure)}; no silent truncation.
- FAIL_ORACLE: published canonical with unknown pagination completeness ⇒ fail.

## GC-05 replace attempt + partial upstream failure
- PURPOSE: old complete generation must not be silently destroyed and replaced by partial canonical.
- PREEXISTING_STATE: complete canonical generation G0 for trade_date.
- SOURCE_INPUT: replace run where some subjects fail.
- EXPECTED: G0 remains authoritative (or new stored as noncanonical incomplete); typed failure.
- FORBIDDEN_OUTPUT: DELETE-then-publish-partial-as-ok.
- PASS_ORACLE: after failed replace, authoritative generation == G0 (intact) or explicit incomplete only.
- FAIL_ORACLE: canonical membership changed to partial set ⇒ fail.

## GC-06 duplicate (trade_date, subject_key, stock_id) membership
- EXPECTED: deterministic dedup rule applied AND counted, or typed failure; never silent duplicate rows in
  canonical generation.
- PASS_ORACLE: canonical membership has no duplicate triple; duplicates reported in accounting.
- FAIL_ORACLE: duplicate triple present in canonical ⇒ fail.

## GC-07 stock membership changes across dates
- SOURCE_INPUT: T: 08-01 {A,B,C}; 08-02 {A,C,D}; 08-03 {C,D,E}.
- EXPECTED: point-in-time per-date membership selectable by snapshot_date <= as_of.
- PASS_ORACLE: as_of=08-02 ⇒ {A,C,D}; as_of=08-03 ⇒ {C,D,E}; no cross-date leakage.
- FAIL_ORACLE: any date answer mixes a later snapshot ⇒ fail.

## GC-08 subject disappears / inactive subject semantics
- EXPECTED: subject not present on date d (or delisted) is distinguishable: typed empty (legitimate) vs
  failure; per snapshot_date.
- PASS_ORACLE: missing subject yields typed empty/failure state, no current-universe hindsight.
- FAIL_ORACLE: missing subject answered from today's map ⇒ fail.

## GC-09 legitimate empty vs upstream-failure empty
- PURPOSE: EMPTY != FAILURE.
- EXPECTED: legitimate empty → data_state=empty (typed) with completeness evidence (provider responded
  empty); upstream-failure empty → typed failure; states distinct.
- PASS_ORACLE: two fixtures with identical empty payload but different provider outcome resolve to
  different typed states.
- FAIL_ORACLE: failure rendered as empty success ⇒ fail.

## GC-10 malformed JYHF row
- EXPECTED: rejected row counted; canonical completeness only if rejection does not break membership
  provability; otherwise no canonical success (SOURCE_PARSE_FAILED).
- PASS_ORACLE: accounting shows rejected rows; publication only when completeness still provable.
- FAIL_ORACLE: silent row drop then canonical success without completeness accounting ⇒ fail.

## GC-11 as_of between snapshot dates
- MECHANICAL RULE: selected_snapshot_date = MAX(snapshot_date) WHERE snapshot_date <= as_of.
- PASS_ORACLE: as_of between dates returns the ≤ snapshot, never the future one.
- FAIL_ORACLE: any future snapshot returned ⇒ fail.

## GC-12 no snapshot_date <= as_of
- EXPECTED: typed NO_DATA-equivalent failure; no current-universe hindsight.
- PASS_ORACLE: outcome typed NO_DATA; no canonical membership fabricated from today.
- FAIL_ORACLE: current map returned as history ⇒ fail.

## GC-13 invalid provider config
- PURPOSE: fail loud; forbidden invalid→jyhf.
- EXPECTED: explicit typed configuration failure at binding/validation.
- PASS_ORACLE: invalid provider raises typed CONFIGURATION/CONTRACT failure before any fetch.
- FAIL_ORACLE: silently resolves to jyhf ⇒ fail.

## GC-14 invalid on_existing config
- PURPOSE: fail loud; forbidden invalid→skip.
- EXPECTED: explicit typed configuration failure.
- PASS_ORACLE: invalid on_existing raises typed failure.
- FAIL_ORACLE: silently resolves to skip ⇒ fail.

## GC-15 mixed-generation publication
- PURPOSE: A/B/C new succeed, D fails → no mixed canonical universe.
- SOURCE_INPUT: prev generation P; new request A,B,C,D; A,B,C succeed; D fails; D not touched.
- EXPECTED: outcome A (new rejected; prev complete P remains authoritative) OR B (new stored only as
  explicit incomplete/noncanonical, never returned as canonical).
- EXPECTED_PUBLISHED_STATE: canonical universe == P (or explicitly noncanonical new).
- FORBIDDEN_OUTPUT: A/B/C=new + D=prev combined as one canonical constituents.
- DERIVATION_RULE: partial generation != canonical generation.
- PASS_ORACLE: canonical membership is single-generation (either full P, or explicitly noncanonical new);
  typed state emitted.
- FAIL_ORACLE: mixed-generation set exposed as canonical ⇒ fail.

```

## [G] 02_CONSTITUENTS_HARDENING_CONTRACT_V2.md

- logical_gate: G
- source_path: /tmp/post_rd1_c1e_g2_acceptance/02_CONSTITUENTS_HARDENING_CONTRACT_V2.md
- filename: 02_CONSTITUENTS_HARDENING_CONTRACT_V2.md
- sha256: `ec36a509d465508157c574ef3462327d96f4d534f45fc81b597dfaf84733f11e`
- status: PASS-ELIGIBLE

```markdown
# 02 — CONSTITUENTS HARDENING CONTRACT V2

version: market.constituents-hardening.v2
Donor = provenance only; donor behavior is descriptive, never normative for Wave-1 canonical behavior.

## 1. Completeness ladder (frozen)
```text
SOURCE_RESPONDED != SUBJECT_COMPLETE != GENERATION_COMPLETE != CANONICAL_PUBLISHED
```
- SOURCE_RESPONDED: provider returned bytes for a subject request.
- SUBJECT_COMPLETE: that subject's membership is proven complete for the date (pagination/truncation
  resolved or typed incomplete).
- GENERATION_COMPLETE: every requested subject resolved to SUBJECT_COMPLETE (or legitimate-empty with
  evidence); failed==∅; rejected-row accounting cannot break provability.
- CANONICAL_PUBLISHED: only after GENERATION_COMPLETE verification passes (HARDENING-PUBLISH-01).
- General completeness rule: count>0 is NEVER completeness proof. Unknown completeness fails closed.

## 2. Malformed-row semantics (frozen)
- row rejected but completeness still provable → row counted, canonical publication allowed with
  accounting.
- row rejected and completeness no longer provable → NO canonical success; typed failure
  (SOURCE_PARSE_FAILED / INCOMPLETE-equivalent).
- Silent skip of bad rows + success without completeness evidence is forbidden.

## 3. Snapshot vs serving-layer authority (frozen)
- subject_stock_daily_snapshot = dated source snapshot/provenance layer (point-in-time authority for
  market.theme.constituents).
- subject_stock_map / subject_stock_staging / theme_stock_map = current/derived serving layers.
- Historical membership MUST derive from the dated snapshot authority; current map is never historical
  truth. No hindsight. No current-map fallback.

## 4. Fail-loud configuration (frozen)
- invalid provider → explicit typed configuration failure; FORBIDDEN invalid→jyhf.
- invalid on_existing → explicit typed configuration failure; FORBIDDEN invalid→skip.

## 5. Failure taxonomy binding
Uses market.failure.v1 typed failures (SOURCE_UNAVAILABLE, SOURCE_TIMEOUT, NO_DATA, STALE_DATA,
PROVENANCE_UNVERIFIED, SOURCE_SCHEMA_CHANGED, SOURCE_PARSE_FAILED, INTERNAL_PROVIDER_ERROR,
INCOMPLETE-equivalent added where taxonomy permits). No alias/fallback/empty-as-success.

```

## [G] 03_GENERATION_PUBLICATION_INVARIANTS_V1.md

- logical_gate: G
- source_path: /tmp/post_rd1_c1e_g2_acceptance/03_GENERATION_PUBLICATION_INVARIANTS_V1.md
- filename: 03_GENERATION_PUBLICATION_INVARIANTS_V1.md
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

## [G] 04_G_ACCEPTANCE_MATRIX_V1.md

- logical_gate: G
- source_path: /tmp/post_rd1_c1e_g2_acceptance/04_G_ACCEPTANCE_MATRIX_V1.md
- filename: 04_G_ACCEPTANCE_MATRIX_V1.md
- sha256: `2bf5e21245fb4a318c9ed5cd4cb2a8b83b68dbdb3211ae494d33be5587e6eeec`
- status: PASS-ELIGIBLE

```markdown
# 04 — G ACCEPTANCE MATRIX V1 (spec-level)

matrix_version: market.g-acceptance.v1
FIXTURE_SPEC_ACCEPTED = YES; IMPLEMENTATION_ACCEPTANCE = NOT_EXECUTED.

| CASE | PURPOSE | expected | published state | oracle deterministic | consistency (request/response/failure/rollback) |
|------|---------|----------|-----------------|----------------------|-------------------------------------------------|
| GC-01 | complete success | canonical success | canonical generation | YES | YES |
| GC-02 | one subject fails | typed failure | prior intact | YES | YES |
| GC-03 | many subject fails | typed failure | no canonical | YES | YES |
| GC-04 | pagination 1200 boundary | completeness proof OR INCOMPLETE failure | per type | YES | YES |
| GC-05 | replace+partial failure | typed failure; old intact | old authoritative | YES | YES |
| GC-06 | duplicate triple | dedup+accounted or typed failure | clean canonical | YES | YES |
| GC-07 | membership changes across dates | point-in-time per date | per-date snapshots | YES | YES |
| GC-08 | subject disappears/inactive | typed empty/failure, no hindsight | per date | YES | YES |
| GC-09 | empty vs failure empty | distinct states | typed | YES | YES |
| GC-10 | malformed row | counted; completeness provable or failure | typed | YES | YES |
| GC-11 | as_of between dates | MAX(snapshot_date)<=as_of | deterministic snapshot | YES | YES |
| GC-12 | no snapshot<=as_of | typed NO_DATA | no hindsight | YES | YES |
| GC-13 | invalid provider config | typed config failure | none | YES | YES |
| GC-14 | invalid on_existing config | typed config failure | none | YES | YES |
| GC-15 | mixed generation | outcome A or B; never mixed canonical | single-generation | YES | YES |

All 15 cases specify: input, expected state/output/failure, forbidden state, PASS/FAIL mechanical oracle.
Hardening invariants (HARDENING-PUBLISH-01; completeness ladder; malformed-row; snapshot-vs-serving;
fail-loud config; GC-11/12 no-hindsight) are consistent with market.request.v1 / market.response.v1 /
market.failure.v1 / market.rollback.v1.
=> G_FIXTURE_BASELINE = PASS-ELIGIBLE (spec accepted; Owner approval still separate).

```

## [G] 05_C1E_GATE_MATRIX_SNAPSHOT_V4.md

- logical_gate: G
- source_path: /tmp/post_rd1_c1e_g2_acceptance/05_C1E_GATE_MATRIX_SNAPSHOT_V4.md
- filename: 05_C1E_GATE_MATRIX_SNAPSHOT_V4.md
- sha256: `426b510f4189a0f26330b66ee18a38ee6f413add3890ee935eb5d125a7e681fa`
- status: PASS-ELIGIBLE

```markdown
# 05 — C1E GATE MATRIX SNAPSHOT V4

| gate | state |
|------|-------|
| A Exact source identity | PASS-ELIGIBLE |
| B Capability binding | PASS-ELIGIBLE / REVIEW PENDING |
| C Request contract | PASS-ELIGIBLE / REVIEW PENDING |
| D Response contract | PASS-ELIGIBLE / REVIEW PENDING |
| E Derived metric ownership | PASS-ELIGIBLE / REVIEW PENDING |
| F Provenance/freshness | PASS-ELIGIBLE / REVIEW PENDING |
| G Fixture baseline | PASS-ELIGIBLE (spec accepted; IMPLEMENTATION_ACCEPTANCE=NOT_EXECUTED) |
| H Failure semantics | PASS-ELIGIBLE / REVIEW PENDING |
| I Production isolation | PASS-ELIGIBLE / REVIEW PENDING |
| J Rollback boundary | PASS-ELIGIBLE / REVIEW PENDING |

```
GC_CASES_DEFINED = 15 (GC-01..GC-15, all with mechanical oracles)
FIXTURE_SPEC_ACCEPTED = YES
IMPLEMENTATION_ACCEPTANCE = NOT_EXECUTED
C1E = OPEN
SOURCE_EDIT_AUTH = NOT_GRANTED
```

Note: PASS-ELIGIBLE is NOT Owner-approved PASS. C1E stays OPEN until Owner/Mira independently approve the
complete A–J packet.

```

## [G] GC_FIXTURE_MANIFEST_v1.json

- logical_gate: G
- source_path: /tmp/post_rd1_c1e_g2_acceptance/GC_FIXTURE_MANIFEST_v1.json
- filename: GC_FIXTURE_MANIFEST_v1.json
- sha256: `dd6674ff3f5327f2cf6ee089728f6241f3f8669802c6bc8a48b3602fbab39f86`
- status: PASS-ELIGIBLE

```json
{
  "manifest_version": "market.gc-manifest.v1",
  "contract_version": "market.fixture.v3",
  "fixture_spec_accepted": true,
  "implementation_acceptance": "NOT_EXECUTED",
  "donor": {
    "repo": "tonychang925-dev/ai_theme_app",
    "commit": "f1bc3def72e0c4184799201aaf1ac5d02d6084d6",
    "base_blob": "609ece34609f1eaaed1a2e73849e3f4d014cd7be",
    "config_blob": "ca56b477c8cb5fdc27a8a0fcc0ad39b919159160",
    "jyhf_producer_blob": "719695eb5c8a23d065429f4d94076907d7804ca5",
    "detect_changed_blob": "ea2e517e8c80fc783d7be331cba69eea905792fc",
    "importer_blob": "49e157320fd180a743c4a93c73dfc2567da828ec",
    "import_path": "database_service/scripts/import_jyhf_stock_daily_incremental.py"
  },
  "cases": [
    {"case_id": "GC-01", "purpose": "complete membership success", "oracle": "deterministic"},
    {"case_id": "GC-02", "purpose": "one subject upstream fetch failure never canonical", "oracle": "deterministic"},
    {"case_id": "GC-03", "purpose": "multiple subject failures never incomplete ok", "oracle": "deterministic"},
    {"case_id": "GC-04", "purpose": "pagination/completeness at 1200 boundary", "oracle": "deterministic"},
    {"case_id": "GC-05", "purpose": "replace + partial failure keeps old authoritative", "oracle": "deterministic"},
    {"case_id": "GC-06", "purpose": "duplicate membership triple", "oracle": "deterministic"},
    {"case_id": "GC-07", "purpose": "membership changes across dates point-in-time", "oracle": "deterministic"},
    {"case_id": "GC-08", "purpose": "subject disappears / inactive", "oracle": "deterministic"},
    {"case_id": "GC-09", "purpose": "legitimate empty != failure empty", "oracle": "deterministic"},
    {"case_id": "GC-10", "purpose": "malformed JYHF row", "oracle": "deterministic"},
    {"case_id": "GC-11", "purpose": "as_of between snapshot dates, no future", "oracle": "deterministic"},
    {"case_id": "GC-12", "purpose": "no snapshot <= as_of -> typed NO_DATA", "oracle": "deterministic"},
    {"case_id": "GC-13", "purpose": "invalid provider config fail-loud", "oracle": "deterministic"},
    {"case_id": "GC-14", "purpose": "invalid on_existing config fail-loud", "oracle": "deterministic"},
    {"case_id": "GC-15", "purpose": "mixed-generation publication prohibition", "oracle": "deterministic"}
  ],
  "counters": {
    "PARTIAL_GENERATION_CANONICAL_SUCCESS_ACCEPT_COUNT": 0,
    "MIXED_GENERATION_PUBLICATION_ACCEPT_COUNT": 0,
    "FUTURE_SNAPSHOT_ACCEPT_COUNT": 0,
    "CURRENT_MAP_AS_HISTORY_ACCEPT_COUNT": 0,
    "UNKNOWN_COMPLETENESS_SUCCESS_ACCEPT_COUNT": 0,
    "INVALID_PROVIDER_FALLBACK_ACCEPT_COUNT": 0,
    "INVALID_ON_EXISTING_FALLBACK_ACCEPT_COUNT": 0,
    "UPSTREAM_FAILURE_AS_EMPTY_ACCEPT_COUNT": 0
  }
}

```

## [H] 02_FAILURE_TAXONOMY_V1.md

- logical_gate: H
- source_path: /tmp/post_rd1_c1e_unblock/02_FAILURE_TAXONOMY_V1.md
- filename: 02_FAILURE_TAXONOMY_V1.md
- sha256: `d5d10171e71c642c49ff8296885e090af7a6fb18e64f94ca53e7722d926068ea`
- status: PASS-ELIGIBLE / REVIEW-PENDING

```markdown
# 02 — WAVE-1 FAILURE TAXONOMY V1

failure_contract_version: `market.failure.v1`
status: FROZEN_AS_GOVERNANCE

## Request-layer failures
- INVALID_REQUEST — malformed request envelope
- MISSING_REQUIRED_ARGUMENT — required argument absent (e.g. history stock_code)
- INVALID_STOCK_CODE — stock identity invalid for the target market
- INVALID_DATE_RANGE — date/cutoff/lookback invalid or out of supported range

## Capability-layer failures
- CAPABILITY_NOT_BOUND — canonical capability has no accepted binding
- CAPABILITY_NOT_IMPLEMENTED — bound but adapter not implemented
- SOURCE_UNAVAILABLE — provider/source unreachable
- SOURCE_TIMEOUT — provider/source timed out

## Data-layer failures
- NO_DATA — source reachable but no data for the requested identity/cutoff
- STALE_DATA — data older than freshness bound for the requested cutoff
- PROVENANCE_UNVERIFIED — requested provenance fields cannot be produced

## Source-contract failures
- SOURCE_SCHEMA_CHANGED — provider schema/dataset drifted from the pinned source contract
- SOURCE_PARSE_FAILED — source bytes/records failed deterministic parse
- INTERNAL_PROVIDER_ERROR — adapter/provider internal error (no partial synthetic result)

## Frozen rules
- failure → typed failure
- failure != empty success (NO_DATA is not `[]` success; UNAVAILABLE is not ZERO)
- failure != synthetic success
- failure != semantic alias
- failure != fallback capability

## Required-argument semantics
- market.stock.history missing stock_code → MISSING_REQUIRED_ARGUMENT (NOT market.snapshot.read)
- market.theme.constituents missing theme identity → typed request failure (NOT market.intelligence.observe)

## Retryability at adapter layer (frozen)
- Retryable: SOURCE_TIMEOUT, SOURCE_UNAVAILABLE (bounded, adapter-local, no semantic retry to another
  capability), INTERNAL_PROVIDER_ERROR only if provider contract defines transient semantics.
- Terminal (no retry): INVALID_REQUEST, MISSING_REQUIRED_ARGUMENT, INVALID_STOCK_CODE,
  INVALID_DATE_RANGE, CAPABILITY_NOT_BOUND, CAPABILITY_NOT_IMPLEMENTED, SOURCE_SCHEMA_CHANGED,
  SOURCE_PARSE_FAILED, STALE_DATA, PROVENANCE_UNVERIFIED, NO_DATA.
- NO automatic semantic retry to another capability anywhere in Wave-1.

```

## [I] 03_CROSS_REPO_AUTHORITY_MATRIX_V1.md

- logical_gate: I
- source_path: /tmp/post_rd1_c1e_unblock/03_CROSS_REPO_AUTHORITY_MATRIX_V1.md
- filename: 03_CROSS_REPO_AUTHORITY_MATRIX_V1.md
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

- logical_gate: I
- source_path: /tmp/post_rd1_c1e_unblock/04_PRODUCTION_ISOLATION_INVARIANTS_V1.md
- filename: 04_PRODUCTION_ISOLATION_INVARIANTS_V1.md
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

- logical_gate: I
- source_path: /tmp/post_rd1_c1e_unblock/05_EXISTING_ROUTER_DISPOSITION.md
- filename: 05_EXISTING_ROUTER_DISPOSITION.md
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

- logical_gate: J
- source_path: /tmp/post_rd1_c1e_freeze2/06_ROLLBACK_BOUNDARY_V1.md
- filename: 06_ROLLBACK_BOUNDARY_V1.md
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

# APPENDIX — Source identity (exact)

ai_theme_app commit f1bc3def72e0c4184799201aaf1ac5d02d6084d6

- base.py blob `609ece34609f1eaaed1a2e73849e3f4d014cd7be`
- config.py blob `ca56b477c8cb5fdc27a8a0fcc0ad39b919159160`
- jyhf_producer.py blob `719695eb5c8a23d065429f4d94076907d7804ca5`
- detect_jyhf_changed_subjects.py blob `ea2e517e8c80fc783d7be331cba69eea905792fc`
- import_jyhf_stock_daily_incremental.py blob `49e157320fd180a743c4a93c73dfc2567da828ec`

History donor/provider refs: see A artifact (freeze2/07 exact identity list).

# APPENDIX — Explicit unresolved facts

- DONOR_PAGINATION_COMPLETENESS = NOT_PROVEN
- start=0/end=1200 is donor behavior, not completeness proof
- IMPLEMENTATION_ACCEPTANCE = NOT_EXECUTED
- SOURCE_EDIT_AUTH = NOT_GRANTED
- Donor risks forbidden to inherit: partial subject failure may coexist with count>0; replace may delete before acquisition completion; invalid provider may silently map to jyhf; invalid on_existing may silently map to skip

# APPENDIX — Invariant index (navigational; full contracts authoritative)

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
