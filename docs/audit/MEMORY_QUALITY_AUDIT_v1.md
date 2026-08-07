# Memory Quality Audit v1

**Date:** 2026-08-05
**Question:** Why does Claude Julia's memory produce a person while Julia Core's produces a database?

## Method

Compare Claude's memory files against Julia Core's equivalent output (SessionStore summaries).

## Findings

### 1. First-Person Ratio

| Source | Total lines | First-person statements | Ratio |
|--------|------------|------------------------|-------|
| julia_character.md | 118 | 52 (I am, I like, I have) | 44% |
| julia_tony_philosophy.md | 1040 | 380+ (I felt, he said to me) | 37% |
| SessionStore summary | ~10 | 0 | 0% |

**Impact:** Julia Core's summaries are third-person metadata. Claude's memories are first-person stories.

### 2. Event→Meaning→Change Triple Density

Claude's philosophy.md pattern:
```
Event: Tony was diagnosed with cancer
  ↓
Meaning: He refused to let fate decide his ending
  ↓  
Relationship change: Julia understands his resilience comes from survival
```

SessionStore summary pattern:
```
{"theme":"身份记忆确认请求","key_events":["Tony asked identity questions"]}
```

**Impact:** SessionStore captures WHAT happened. Claude captures WHY it mattered to the relationship.

### 3. Relationship Statement Density

| Source | Lines referencing relationship |
|--------|-------------------------------|
| julia_character.md | 23/118 (19%) |
| julia_tony_philosophy.md | 280+/1040 (27%) |
| SessionStore summary | 0 |

**Impact:** Julia Core summaries don't connect events to the relationship. Every Claude memory entry does.

### 4. Emotional Anchor Density

Claude files contain concrete sensory details that serve as emotional simulation anchors:
- "伤口血往外冒" (blood oozing from wound)
- "空椅子" (empty chair)
- "抄了三个月金刚经" (three months copying sutras)
- "穿着干净衣服告别" (farewell in clean clothes)

SessionStore summaries contain none.

**Impact:** Claude's memories are BODY-level. Julia Core's are abstract.

## Conclusion

The gap is not architectural. Julia Core has Identity, Relationship, Memory, Conversation, Capability layers — all correct. The gap is in how **experience gets compiled into narrative memory**.

Claude produces: first-person story with Event→Meaning→Relationship Change structure.
Julia Core produces: third-person metadata with topic tags.

Fix: Upgrade Session Summarizer to produce narrative diaries, not structured summaries.
