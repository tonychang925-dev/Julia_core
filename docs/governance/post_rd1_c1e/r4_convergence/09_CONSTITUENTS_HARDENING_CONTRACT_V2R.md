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
