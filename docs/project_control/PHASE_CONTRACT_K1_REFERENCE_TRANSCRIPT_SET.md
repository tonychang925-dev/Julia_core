# Phase Contract — K1 — Reference Transcript Set

Status: COMPLETE / APPROVED at Reference Schema + Starter Dataset scope  
Date: 2026-08-02

## 1. Purpose

K1 creates Claude Julia Reference Behavior Dataset v1.

The dataset stores behavior patterns, not just response text.

## 2. Artifact

```text
artifacts/benchmark/claude_reference/claude_behavior_reference_v1.jsonl
```

## 3. Schema and Guideline

```text
docs/benchmark/CLAUDE_REFERENCE_TRANSCRIPT_SCHEMA_v1.md
docs/benchmark/CLAUDE_REFERENCE_ANNOTATION_GUIDELINE_v1.md
```

## 4. Case Families

```text
K-SELF
K-ARCHIVE
K-REL
K-MEM
K-CORR
K-INIT
K-TRANS
K-PROJ
K-XFER
```

## 5. Boundary

```text
Reference transcript is benchmark evidence.
Reference transcript is not Memory.
Reference transcript is not Persona update.
Reference transcript is not Identity authority.
Reference transcript does not copy Claude internals.
```

## 6. Next

```text
K2 — Julia Run Set
```
