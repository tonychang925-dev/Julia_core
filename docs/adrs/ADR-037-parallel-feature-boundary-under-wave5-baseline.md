# ADR-037 Parallel Feature Boundary Under Wave5 Baseline

## Status

APPROVED / FROZEN FOR PARALLEL DEVELOPMENT

## Scope

Wave5 parallel feature governance.

This ADR defines how multiple long-term feature tracks evolve on top of
the frozen Wave5 Authority Baseline without creating cross-domain
coupling.

## Authority

This ADR is subordinate to:

-   JULIA_CORE_UNIFIED_ARCHITECTURE_v1.0
-   Frozen C-series contracts
-   ARCHITECTURE_DOCUMENT_REGISTRY

This ADR does not modify:

-   ARCHITECTURE_FREEZE_RECORD
-   C-00
-   C-03
-   C-08
-   C-12

Purpose:

Define parallel feature isolation and integration governance.

---

## Frozen Baselines

Wave5 Authority Anchor

```text
4d48381c8e11dad394fa8873d142ca9bba2d0ca7
```

resolved from annotated tag `wave5-rc1-authority-baseline-20260825`.

Parallel Development Base

```text
698b811dfb9c7aae3529ba354cb6baa20b65e9b6
```

directly parents `4d48381`; the only intervening commit is one
governance document (`docs/authority/WAVE5_RC1_D1_EXECUTION_RECORD.md`,
+37/-0, runtime mutation: NO).

Governance Head

```text
latest canonical governance-only descendant of 698b811
```

Invariant: advancing main or Governance Head MUST NOT implicitly
redefine Parallel Development Base.

---

# Decision 1 — Bounded Context Separation

## Capability Domain

Responsible for External Capability Invocation.

Includes:

-   capability execution
-   tool invocation
-   provider interaction
-   authorization
-   execution trace
-   evidence generation

## Identity Continuity Domain

Responsible for Personality Migration and continuity preservation.

Includes:

-   identity artifacts
-   lineage
-   migration protocol
-   continuity validation
-   reconstruction process

The two domains:

-   do not share authority
-   do not share semantic models
-   do not directly write each other's state

---

# Decision 2 — Context OS Shared Boundary

The only controlled shared boundary is:

```text
julia_core/context_os/
```

Context OS is Context Assembly Runtime. It is NOT Identity Authority,
Capability Authority, or Memory Authority.

## Forbidden Capability Flow

```text
Capability Result → Context OS → Persona Mutation
```

## Forbidden Identity Flow

```text
Migration Artifact → Context OS → Capability Authorization
```

## Correct Flows

Identity:

```text
Identity Authority → Identity Projection → Context OS
```

Capability:

```text
Capability Authority → Evidence Projection → Context OS
```

---

# Decision 3 — Repository Ownership Matrix

```text
  Path                Capability Track   Migration Track
  ------------------- ------------------ -----------------
  capability/         OWN                forbidden
  providers/          OWN                forbidden
  tools/              OWN                forbidden
  runtime/execution   OWN                forbidden
  identity/           forbidden          OWN
  continuity/         forbidden          OWN
  migration/          forbidden          OWN
  memory authority    forbidden          OWN
  context_os/         governed           governed
```

Classification is by SEMANTIC, not by directory name. A file whose
semantic content is Identity/Continuity readiness belongs to the
Migration Track regardless of its physical path.

---

# Decision 4 — Context OS Change Gate

Any modification under `julia_core/context_os/*` requires:

1.  Independent commit.

2.  Impact declaration:

```text
impact: capability: yes/no identity: yes/no runtime: yes/no
```

3.  Contract verification.

Capability changes must prove: no identity leakage.
Migration changes must prove: no capability privilege escalation.

---

# Decision 5 — Branch Laws

BL-01 — Stable Fork Law

```text
Every active feature track MUST branch from the frozen Parallel
Development Base, or advance only on its own canonical lineage.
```

BL-02 — No Sibling Dependency Law

```text
Active sibling feature branches MUST NOT be stacked, rebased onto each
other, directly merged, or cherry-picked as development dependencies.
A sibling feature HEAD MUST NOT be used as build/test/runtime/PYTHONPATH/
dependency/implementation baseline.
```

BL-03 — Integration Candidate Law

```text
Cross-domain integration occurs only through an explicitly declared
Integration Candidate, after contributing tracks independently satisfy
their required acceptance gates.
```

BL-04 — Historical Mixed Lineage Law

```text
Mixed historical branches may be inspected and used as implementation
evidence/source material. They MUST NOT become authority bases, feature
development bases, test/runtime baselines, or dependency baselines.
```

BL-05 — Knowledge ≠ Authority Law

```text
Cross-track knowledge sharing is allowed.
Cross-track authority inheritance is forbidden.
```

---

# Decision 6 — Historical Mixed Lineage Classification

```text
00749a1c4cbbc1bbdf1367e883b5c852ba4ff528
```

classification:

```text
PRESERVED HISTORICAL MIXED LINEAGE
```

state:

```text
QUARANTINED
READ ONLY
NO NEW DEVELOPMENT
```

It is not a canonical Capability Track head, a canonical Identity Track
head, or an Integration Candidate. No force rewrite, delete, rebase, or
continuation is authorized.

---

# Decision 7 — Track State

```text
CAP-LR0                     PASS / CLOSED
CAP-LR1                     GO
CRB-PRE-P1                  HOLD
CRB-P1                      HOLD

Identity / Persona / Phase8 Track
                            GO
                            BASE = 698b811
                            OWN LINEAGE ONLY

Context OS Integration      HOLD
                            until accepted track-level candidates exist
```

Capability canonical clean root: `feature/julia-external-capability-c1-contract-tests`
(branch HEAD == 698b811). CAP-LR1 must use source-state extraction from
quarantined history; blind 55-commit cherry-pick is forbidden.

Persona / Phase8 Track may proceed independently from 698b811. Forbidden:
base = 00749a1, base = CAP-LR1 HEAD, merge/rebase/cherry-pick Capability
feature, or use a Capability worktree as build/test/runtime source.

---

# Decision 8 — Integration Order

```text
Wave5 Authority Baseline (4d48381)
        ↓
Parallel Development Base (698b811)
        ↓
Capability + Migration parallel development (own lineages)
        ↓
Context OS Integration Review (declared Integration Candidate)
        ↓
Phase 8 Runtime Boundary
        ↓
main candidate
```

---

# Non-Goals

This ADR does not define:

-   Persona model
-   Memory schema
-   Capability protocol
-   MCP protocol
-   Context OS internal implementation
-   C-series contract changes

This ADR only defines parallel feature isolation and integration governance.

---

# Final State

```text
Wave5 Authority Baseline        FROZEN
Parallel Development Base       FROZEN
ADR-037 Parallel Feature Boundary
                                APPROVED / FROZEN
External Capability Track       APPROVED FOR PARALLEL DEVELOPMENT
Personality Migration Track     APPROVED FOR PARALLEL DEVELOPMENT
Context OS                      CONTROLLED SHARED BOUNDARY
```
