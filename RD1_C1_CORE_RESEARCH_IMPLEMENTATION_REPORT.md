# RD1-C1 — Core Research Contract / Adapter Implementation Report

## Canonical base

```text
Repository: tonychchang925-dev/Julia_core
Canonical base: e2edba9dfff460e3769f93b58491afaf644e6da5
Capability: research.event.enrich
Scope: Core contract and governed adapter seam only
```

## Implementation summary

C1 adds a Core-owned Market-event research seam without implementing C2 final
synthesis:

```text
frozen market.event.read.v1 payload
  → MarketEventResearchAdapter.build_request()
  → CapabilityRequest(research.event.enrich)
  → governed provider boundary
  → ProviderExecutionOutcome
  → ResearchEvidenceNormalizer
  → NormalizedResearchEnrichment
```

The normalized output deliberately carries two different objects:

```text
ResearchSemanticResult
  != SourceObservationEvidence
```

Provider semantics remain claims and research material. Runtime source
observation evidence remains a separately minted `Evidence` collection with
Core-owned verification state.

## Files

- `julia_core/research/contracts.py`
  - Defines the exact frozen Market event context, semantic result, claim,
    source record, content binding, failure, and observation contracts.
- `julia_core/research/adapter.py`
  - Validates the frozen M0 fields and projects them into a canonical
    `CapabilityRequest`.
- `julia_core/research/registration.py`
  - Registers `research.event.enrich` as an intelligence capability with the
    `research.enrich` permission scope.
  - Binds no provider and installs no routing.
- `julia_core/research/normalizer.py`
  - Implements `ResearchEvidenceNormalizer`, provider-output parsing, truth-plane
    separation, canonical `Evidence` minting, and `ToolResult` linkage.
- `julia_core/research/__init__.py`
  - Exports the C1 public surface.
- `tests/research/test_c1_research_event_enrichment.py`
  - Covers request projection, frozen-contract rejection, positive verification,
    and all required negative matrices.

## Existing primitives reused

The implementation creates no parallel capability framework. It reuses:

- `CapabilityRequest`;
- `CapabilityCall`;
- `ProviderExecutionOutcome`;
- `ToolResult`;
- `Evidence`;
- `CapabilityDefinition`;
- `CapabilityRegistry`;
- `PermissionPolicy`.

The only new result carrier is the C1-specific
`NormalizedResearchEnrichment`, which composes the existing primitives and the
two required truth-plane objects. No generic `ResultV1` or generic evidence
family was added.

## Frozen Market event consumption

The adapter accepts only the M0-frozen `market.event.read.v1` shape:

- exact `event` fields documented by M0;
- exact `theme_relations` fields documented by M0;
- nullable M0 fields remain explicitly nullable;
- unknown context, event, or relation fields fail closed.

In particular, the adapter does not admit:

- `related_symbols`;
- generic entities;
- causal-claim fields;
- severity;
- source weight;
- lifecycle status;
- market heat/theme state;
- analyst claims.

The request contains only `event` and `theme_relations`, plus canonical C-08
metadata and provenance. It carries no provider, transport, browser, Claude, or
Assistant authority.

## Semantic plane

`ResearchSemanticResult` requires:

- `factual_summary`;
- `claims`;
- `contradictions`;
- `unknowns`;
- `timeline`;
- `related_entities`.

Every `ResearchClaim` carries stable `source_record_ids`. A provider
verification string is preserved only as non-authoritative
`provider_verification_state`; it is never copied into Core verification
authority.

This type contains no buy, sell, trading, execution, or final Julia judgment
semantics.

## Source observation plane

`SourceObservationEvidence` preserves:

- `source_records`;
- raw response references;
- content references;
- content/extract bindings;
- immutable SHA-256 digests;
- capture/fetch status;
- `observed_at`;
- provenance;
- `correlation_id`;
- exact failure truth;
- canonical `Evidence` objects.

The normalizer links each minted `Evidence` to the normalized `ToolResult`
through `ToolResult.evidence_refs`. Semantic claims never become the source of
those observation objects.

## Verification authority

`ResearchEvidenceNormalizer` is the only C1 implementation path that writes:

```text
Evidence.integrity_metadata["verification_state"]
```

Allowed values are exactly:

```text
SOURCE_VERIFIED
REPORT_ONLY
NOT_PROVEN
BLOCKED
```

Provider labels have no authority.

### E3 SOURCE_VERIFIED law

`SOURCE_VERIFIED` is possible only when all of the following hold:

1. provider execution succeeded;
2. source observation is available;
3. the claim references a known `SourceRecord`;
4. the source is not WebSearch-only material;
5. capture and fetch status represent retained/observed runtime material;
6. a content or extract reference exists;
7. the binding has a valid 64-character SHA-256 digest;
8. source-record and binding digests agree when both are present;
9. source and binding observation timestamps/provenance are present;
10. the binding is bound to the exact `CapabilityRequest` and `CapabilityCall`;
11. the binding’s runtime observation reference occurs in the provider
    execution’s observed raw-response references.

A URL by itself never satisfies this chain.

## Failure semantics

- WebSearch-only source records normalize to `REPORT_ONLY`.
- Fetched URL material without a content/extract binding normalizes to
  `NOT_PROVEN`.
- Missing source records, digests, or runtime provenance normalize to
  `NOT_PROVEN`.
- A blocked observation/provider failure normalizes to `BLOCKED`.
- Other provider failures normalize to `NOT_PROVEN`.
- Semantic material may be preserved on failure, but observation availability is
  false and no synthetic observation is created.

## Boundary compliance

The implementation does not:

- implement final Julia research judgment;
- invoke a live Claude provider;
- modify Assistant;
- modify the Market repository;
- add buy/sell/trading semantics;
- add automatic multi-event routing;
- bind a live provider;
- create a parallel generic capability/result/evidence framework.

## Regression evidence

Focused C1 suite:

```text
/opt/miniconda3/bin/pytest -q \
  tests/research/test_c1_research_event_enrichment.py

12 passed in 0.08s
```

Focused primitive/governance regression:

```text
/opt/miniconda3/bin/pytest -q \
  tests/research/test_c1_research_event_enrichment.py \
  tests/capability/test_m0_acceptance.py \
  tests/review/test_review_invocation.py

54 passed in 0.22s
```

Static checks:

```text
python -m compileall -q julia_core/research tests/research
git diff --check
```

Both completed successfully.

## C1 verdict

C1 = PASS
