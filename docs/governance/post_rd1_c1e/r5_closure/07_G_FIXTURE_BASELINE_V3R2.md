# 07 - G FIXTURE BASELINE V3R2

fixture_contract_version: `market.fixture.v3r2`
status: FROZEN_AS_GOVERNANCE
supersedes: `market.fixture.v3`

Implementation acceptance is NOT_EXECUTED. Every fixture records input, expected state, output, failure,
forbidden state, and provenance mechanically.

| case | source condition | expected canonical/typed | published state | oracle |
|---|---|---|---|---|
| GC-01 | full subject success | success canonical | canonical generation | requested equals completed and failed is empty |
| GC-02 | one subject fetch fails | INCOMPLETE_GENERATION with nested source cause SOURCE_UNAVAILABLE | no new canonical | any canonical with failed non-empty fails |
| GC-03 | many subject fetches fail | INCOMPLETE_GENERATION | no new canonical | any canonical with failed non-empty fails |
| GC-04 | membership >= 1200 or truncation risk | SOURCE_INCOMPLETE unless mechanical completeness proof exists | per type | canonical without proof fails |
| GC-05 | replace plus partial failure | INCOMPLETE_GENERATION; prior intact | old authoritative | partial replacement of canonical fails |
| GC-06 | duplicate triple | dedup counted or SOURCE_PARSE_FAILED | clean canonical or typed | duplicate triple in canonical fails |
| GC-07 | membership across dates | per-date canonical | per-date snapshots | mixed date publication fails |
| GC-08 | subject absent for date | NO_DATA | typed | later/current map answer fails |
| GC-09 | legitimate empty versus failure empty | empty data_state or SOURCE_UNAVAILABLE | distinct | failure represented as empty success fails |
| GC-10 | malformed row | SOURCE_PARSE_FAILED or canonical with row accounting | typed or provable canonical | silent drop plus canonical without accounting fails |
| GC-11 | as_of between snapshots | canonical snapshot = MAX(snapshot_date) <= as_of | selected snapshot | future snapshot fails |
| GC-12 | no snapshot <= as_of | NO_DATA | none | current-map answer fails |
| GC-13 | invalid provider config | INVALID_CONFIGURATION | none | silent conversion to jyhf fails |
| GC-14 | invalid on_existing config | INVALID_CONFIGURATION | none | silent conversion to skip fails |
| GC-15 | mixed generation | MIXED_GENERATION_REJECTED | single generation only | mixed canonical publication fails |

Hardening invariants remain:

- SOURCE_RESPONDED != SUBJECT_COMPLETE != GENERATION_COMPLETE != CANONICAL_PUBLISHED.
- count > 0 is not completeness proof.
- partial generation is not canonical generation.
- mixed generation publication is forbidden.
- sequencing is BUILD -> VERIFY COMPLETENESS -> PUBLISH.
