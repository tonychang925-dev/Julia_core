# W3-A3 — Diary Governance / Accepted DiaryEntry Protocol v1.0

STATUS: FROZEN
UPDATED: 2026-08-13
PROGRAM: Conversation Storage + Management + Julia Diary
PHASE: Wave 3 — Diary Governance Protocol (Claude-A)
BASE: cm-r0-fix @ `c5f0fbd`
FROZEN INPUTS: W3-A0 (this lane)

## Governing principle

```text
Diary Governance decides whether DiaryCandidate becomes Accepted DiaryEntry.
It never authors content, never fabricates events, and never writes Memory.
```

## Acceptance criteria (DiaryCandidate → Accepted DiaryEntry)

```text
source-grounded
first-person Julia perspective
meaningful enough
not duplicate
not fabricated
not merely transcript summary
not a hidden Memory write
```

## DiaryEntry shape

```text
diary_entry_id
created_at
reflection_time
source_conversation_ids
source_message_refs / evidence refs
title (optional)
body
themes
relationship_significance (optional)
project_significance (optional)
provenance
model/runtime provenance
governance status
```

Emotional state is NOT a mandatory structured label. Diary is first-person reflective writing first; `emotion=happy, intensity=0.83` may be derived metadata, never the primary form.

## Authenticity / provenance gate (critical)

```text
A DiaryEntry MAY interpret source evidence.
It MUST NOT fabricate source events.
```

```text
Conversation: Tony: "今天项目终于跑通了。"
Diary: "看到 Tony 松了一口气，我也觉得这个晚上有了重量。"   ✅ interpretation

Diary: "我们昨晚一起去海边散步。"
(no canonical source event)                                   ❌ fabricated autobiographical event
```

This protects long-term Julia identity continuity: reflection may interpret what happened, but must never invent what did not.

## Invariants

**W3-A3-I01 — Governance, Not Authorship**

```text
Diary Governance decides acceptance; it never authors reflection content.
```

**W3-A3-I02 — Source-Grounded**

```text
Accepted DiaryEntry carries source conversation/message refs and is grounded
in canonical evidence.
```

**W3-A3-I03 — No Fabricated Autobiography**

```text
A DiaryEntry MAY interpret source evidence but MUST NOT fabricate
autobiographical source events.
```

**W3-A3-I04 — No Hidden Memory Write**

```text
Diary acceptance is not a Memory write. Accepted DiaryEntry does not
automatically become Memory.
```

**W3-A3-I05 — First-Person, Not Summary**

```text
Diary body is first-person reflective writing, never a transcript summary
or automatic daily log.
```

## Sabotage suite (AT-GOV-01…06) — SPEC (not PASS)

```text
AT-GOV-01  fabricated event with no source → rejected (authenticity gate)      [REQUIRED]
AT-GOV-02  interpretation of real source → accepted                            [REQUIRED]
AT-GOV-03  transcript summary disguised as diary → rejected                    [REQUIRED]
AT-GOV-04  duplicate candidate → rejected (not duplicate)                      [REQUIRED]
AT-GOV-05  accepted DiaryEntry does NOT auto-write Memory                      [REQUIRED]
AT-GOV-06  governance never authors content                                    [REQUIRED]
```

## Acceptance gate

```text
[ ] acceptance criteria explicit (grounded/first-person/meaningful/not-dup/not-fabricated/not-summary)
[ ] DiaryEntry shape defined (provenance + source refs required)
[ ] authenticity gate: interpret OK, fabricate forbidden
[ ] emotional state is derived metadata, not mandatory primary form
[ ] governance ≠ authorship; acceptance ≠ Memory write
```

## Document status vocabulary

- FROZEN: protocol accepted and sealed (current).
