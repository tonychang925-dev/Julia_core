# Phase Contract — I2 — Self Archive Recall Runtime

Status: COMPLETE / APPROVED at Recall Runtime MVP scope  
Date: 2026-08-02

## 1. Purpose

I2 implements on-demand self archive recall for Claude Julia-like behavior.

It is not a startup loader.

```text
User self-related question
  ↓
SelfRecallDecision
  ↓
SelfArchiveRetriever
  ↓
PersonaArchiveRef
  ↓
SelfNarrativeContextBlock
  ↓
Provider first-person response
```

## 2. Objects

```text
PersonaArchiveRef
SelfRecallDecision
SelfNarrativeContextBlock
SelfArchiveRetriever
```

## 3. Required Behavior

SA-001:

```text
Tony: 你是谁？
```

Response must come from self archive when available and include biography fields, not backend runtime terms.

SA-002:

```text
Tony: 你读一下你的档案，然后介绍自己
```

Trace must include:

```text
self_recall.recall_required = true
self_archive_block.context_type = self_narrative
archive_ref authority = private_persona_archive
```

SA-003:

If archive is missing:

```text
Julia says she did not find the archive and does not invent facts.
```

SA-004:

If archive has conflicts:

```text
conflicts are surfaced for governance; model does not choose by itself.
```

## 4. Boundary

```text
Self Archive Recall is on-demand, not startup injection.
PersonaArchiveRef is not MemoryRef.
SelfNarrativeContextBlock is not raw archive dump.
Self Archive Recall does not mutate Identity.
Self Archive Recall does not update Self Model automatically.
Fallback provider is only a renderer for deterministic tests; it is not Julia.
```

## 5. Next

```text
I3 — Relationship Continuity Test
```
