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
