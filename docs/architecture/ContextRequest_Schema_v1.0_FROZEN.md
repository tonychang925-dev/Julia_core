# ContextRequest Schema v1.0 — FROZEN

> **Status**: FROZEN — A5.1.1 Binding Hardening  
> **Date**: 2026-07-31  
> **Contract**: Workspace → Julia Context OS protocol

---

## 1. Schema Definition

```typescript
interface ContextRequest {
  /** Action type — determines which Provider capabilities are invoked */
  action: "why" | "risk" | "compare";

  /** Target identification — intent pointer, not a payload dump */
  object_type: "theme" | "group";
  object_id: string;
  object_name: string;

  /** Minimal workspace snapshot — only what Julia needs for this action */
  workspace_snapshot: {
    stage_judgement: string;
    attention_level?: string;
    yesterday_view: string;
    today_actual: string;
    intraday_understanding?: string;
    trader_sentiment?: string;
    index_resonance?: string;
    event_stimuli: string[];
    analyst_notes: string;
    old_leaders?: string;
    trading_style?: string;
    long_identifiability?: number;
    short_identifiability?: number;
  };

  /** Human override evidence — what Tony changed from AI drafts */
  field_overrides_summary: Array<{
    field: string;
    ai_value: string;
    analyst_value: string;
  }>;

  /** Source marker — always "analyst_workspace" */
  source: "analyst_workspace";
}
```

---

## 2. Allowed Content (✅)

| Category | Allowed | Example |
|----------|---------|---------|
| Action intent | `why` / `risk` / `compare` | `"why"` |
| Object pointer | type + id | `{type: "theme", id: "CPO_001"}` |
| Workspace cognitive state | stage, sentiment, resonance, views, stimuli | `stage_judgement: "DIFFUSION"` |
| Analyst override history | field + ai_value + analyst_value | `{field: "stage_judgement", ai_value: "...", analyst_value: "..."}` |

---

## 3. FORBIDDEN Content (❌)

| Category | Forbidden | Reason |
|----------|-----------|--------|
| Full stock pools | `stocks[]`, `leaders[]`, `bull_pool[]`, `bear_pool[]` | Would pollute Context OS with raw data |
| Full workspace dump | All themes, all watch groups, all fields | Violates Intent-first Context-second principle |
| News/articles | `news[]`, `articles[]`, external URLs | Provider must fetch evidence, not workspace |
| Raw market data | OHLCV, bid/ask, volume | ai_theme_app owns data; Julia only receives evidence |
| Full theme list | All 50+ themes | Each action targets ONE object |
| AI draft content | `ai_draft: {...}` | Only field_overrides_summary captures the diff |

---

## 4. Action Context Mapping

| Action | Required workspace_snapshot fields | Provider invoked |
|--------|-----------------------------------|------------------|
| `why` | stage_judgement, event_stimuli, analyst_notes | Theme Evidence Provider |
| `risk` | stage_judgement, trader_sentiment, index_resonance | Risk Context Provider |
| `compare` | yesterday_view, today_actual | Historical Context Provider |

---

## 5. Evolution Rules

1. **Adding a field** to `workspace_snapshot` requires: (a) documented need, (b) matching Provider capability, (c) ADR approval.
2. **Adding a new action** (e.g., `suggest`) requires: new ADR + schema version bump.
3. **Adding a new object_type** requires: Domain Provider registration + context adapter for that type.
4. **Never** expand `workspace_snapshot` to a full object dump. The snapshot is a cognitive summary, not a data payload.

---

## 6. Version History

| Version | Date | Change |
|---------|------|--------|
| v1.0 | 2026-07-31 | Initial freeze — A5.1.1 Binding Hardening |
