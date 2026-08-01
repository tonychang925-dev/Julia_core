# Context OS Core Migration Plan v1.0

> Phase: A2.0 — Context OS Core Migration Contract  
> Status: Contract Draft  
> Date: 2026-07-31  
> Baseline: `phase-a1-runtime-boundary-audit-complete`  
> Source Evaluation Branch: `codex/full-agent-architecture-migration`

## 1. Purpose

A2.0 freezes the ownership, interfaces, dependency direction, and migration boundary for Julia Context OS as a formal Julia Core Runtime component.

A2.0 is not implementation.

A2.0 does not:

- move runtime code;
- refactor modules;
- change imports;
- delete files;
- merge `codex/full-agent-architecture-migration`;
- change runtime behavior.

A1 answered:

```text
Where are the existing code assets?
```

A2.0 answers:

```text
Where should Context OS belong,
how should it be used by all domains,
and what must be true before migration starts?
```

## 2. Architecture Position

Julia Agent is a general Agent OS.

```text
Julia Agent OS
├── Identity OS
├── Memory OS
├── Context OS
├── Governance OS
├── Runtime Kernel
└── Domain Provider Interface
        ├── Financial
        ├── Healthcare
        ├── Coding
        └── Personal
```

Context OS belongs to Julia Core.

It is not part of any domain.

Financial analysis is the first production domain provider, not the owner of context.

## 3. Context OS Ownership

### 3.1 Context OS Owns

Julia Context OS owns:

- context lifecycle;
- context planning;
- context selection;
- context composition;
- context budget;
- context projection;
- context expiration;
- evidence coordination;
- provenance enforcement;
- conflict resolution;
- model-facing context assembly.

In short:

```text
Context OS decides what Julia sees.
```

### 3.2 Context OS Does Not Own

Julia Context OS does not own:

- domain knowledge;
- financial reasoning;
- medical knowledge;
- stock analysis rules;
- coding rules;
- user private facts;
- memory content;
- identity definition;
- final answers;
- provider-specific prompt style.

In short:

```text
Context OS decides context eligibility,
not domain truth.
```

## 4. Dependency Direction

Correct dependency direction:

```text
Julia Core
  ↓
Context OS
  ↓
Provider Interface Layer
  ↓
Domain Providers
```

Expanded view:

```text
                Julia Core

              Context OS

                  │
                  ▼
        Provider Interface Layer

                  │
        ┌─────────┴─────────┐
        │                   │
 Financial Provider   Other Providers
```

Forbidden dependency direction:

```text
Context OS
  ↓
Financial Engine
```

Forbidden:

```text
Context OS
  ↓
stock database / market engine / theme engine
```

Forbidden:

```text
Context Planner
  ↓
private memory content / private identity data
```

Permitted:

```text
Context OS
  ↓
Domain Provider Interface
  ↓
ContextBlock candidates
```

## 5. Migration Scope

### 5.1 In Scope

A2 implementation may consider migrating the following from the evaluation branch after this contract is approved:

```text
runtime/context_os/
```

Submodules in scope:

- planner;
- budget;
- projection;
- provenance;
- conflict;
- execution;
- mutation;
- cache;
- compact;
- resurrection;
- transcript;
- state;
- quality;
- evidence coordination;
- worker lifecycle where domain-independent.

### 5.2 Conditional Scope

These modules may be reviewed as supporting dependencies but must not be blindly migrated:

```text
runtime/evidence/
runtime/context_assembly/
runtime/conversation_state/
runtime/memory_loader.py
runtime/cognitive/context_compiler/
schemas/
```

Rules:

- generic evidence primitives may be included;
- legacy context assembly must not compete with Context OS;
- memory loader code may be included only if separated from memory content;
- schemas may be migrated only when tied to public contracts.

### 5.3 Out of Scope

A2 must not migrate:

- `runtime/capability/financial/` as part of Context OS;
- market engine;
- stock database;
- theme engine;
- financial context builder;
- healthcare/coding domain implementations;
- identity private data;
- memory content;
- conversation transcripts;
- audio;
- runtime cache;
- `tmp/`;
- `data/`;
- generated artifacts.

## 6. Core API Contract

A2.0 freezes the conceptual API. Exact file/module placement may be finalized in A2 implementation contract, but behavior must preserve these semantics.

### 6.1 ContextRequest

`ContextRequest` expresses what Julia currently needs.

It is a demand signal, not data.

```python
@dataclass(frozen=True, slots=True)
class ContextRequest:
    request_id: str
    session_id: str | None
    task_intent: str                  # analysis / conversation / review / action_support
    cognitive_mode: str               # conversation / analytical / governance / ...
    domain: str | None                # financial / healthcare / coding / None
    domain_object_type: str | None    # theme / stock / event / patient_record / repo / ...
    domain_object_id: str | None
    required_capabilities: tuple[str, ...]
    evidence_intents: tuple[str, ...]
    required_blocks: tuple[str, ...]
    optional_blocks: tuple[str, ...]
    exclusions: tuple[str, ...]
    constraints: Mapping[str, object]
    target_budget_tokens: int
```

Examples:

```python
ContextRequest(
    task_intent="analysis",
    domain="financial",
    cognitive_mode="analytical",
    domain_object_type="theme",
    domain_object_id="9043089",
    required_capabilities=("theme_analysis", "risk_evidence"),
    evidence_intents=("theme_driver", "risk_signal"),
)
```

### 6.2 ContextBlock

`ContextBlock` is the standard candidate unit that may enter Julia model-facing context after planning, budget, provenance, and projection.

```python
@dataclass(frozen=True, slots=True)
class ContextBlock:
    block_id: str
    block_type: str
    source: str                       # context_os / memory_os / domain_provider / runtime
    domain: str | None
    content: object                   # structured or renderable content
    evidence_refs: tuple[str, ...]
    source_refs: tuple[str, ...]
    authority: str                    # user / system / domain_provider / memory / runtime
    authority_score: float
    created_at: str
    expires_at: str | None
    ttl_seconds: int | None
    required: bool
    estimated_tokens: int | None
    metadata: Mapping[str, object]
```

Important rule:

```text
Domain returns ContextBlock candidates.
Domain does not return Prompt.
Domain does not return Final Answer.
Domain does not return Memory Mutation.
```

### 6.3 ContextPlan

`ContextPlan` decides required blocks, optional blocks, evidence intents, exclusions, and budget.

It may be implemented using existing `runtime/context_os/planner/context_plan.py` semantics, but must remain domain-independent.

### 6.4 ContextResult

`ContextResult` is the output of Context OS before provider invocation.

```python
@dataclass(frozen=True, slots=True)
class ContextResult:
    request_id: str
    plan_id: str
    selected_blocks: tuple[ContextBlock, ...]
    excluded_blocks: tuple[ContextBlock, ...]
    provenance_records: tuple[object, ...]
    budget_trace: Mapping[str, object]
    quality: Mapping[str, object]
```

## 7. Domain Provider Contract

A domain provider is an evidence/fact/capability source.

It is not a context authority.

### 7.1 Domain Provider Owns

Domain providers may provide:

- facts;
- evidence;
- capability results;
- domain object references;
- domain governance metadata;
- candidate ContextBlocks.

### 7.2 Domain Provider Does Not Own

Domain providers must not provide:

- prompt text instructions for the model;
- final answer text as Julia;
- memory mutations;
- identity updates;
- token budget decisions;
- context lifecycle decisions;
- provider-specific prompt assembly.

### 7.3 Financial Example

Input pointer:

```text
theme_id = 9043089
action = ask_why
```

Financial provider may return:

```json
{
  "block_type": "financial_theme_context",
  "domain": "financial",
  "content": {
    "summary": "...",
    "events": [],
    "risks": []
  },
  "evidence_refs": ["theme-9043089-001"],
  "authority": "domain_provider"
}
```

Financial provider must not return:

```text
"Julia should tell Tony to..."
```

or:

```text
BUY / SELL / ORDER / EXECUTE
```

## 8. Why Not Financial Context OS

A financial context builder may look convenient in the short term, but it creates long-term architectural risk.

Rejected architecture:

```text
Financial Workbench
  ↓
Financial Context Builder
  ↓
Prompt Injection Rules
  ↓
Julia
```

Problems:

1. Multiple context authorities;
2. domain-controlled prompt construction;
3. duplicated Context OS for future domains;
4. no unified budget;
5. weaker provenance chain;
6. memory/learning governance bypass risk;
7. Julia splits into several domain agents instead of one Agent OS.

Accepted architecture:

```text
Julia Context OS
  ↓
Domain Provider Interface
  ↓
Financial Domain Provider
  ↓
ContextBlock candidates
  ↓
Julia Context OS budget/provenance/projection
```

Result:

```text
One Julia Context OS.
Many Domain Providers.
```

## 9. Migration Safety Rules

Any future A2 implementation PR must include automated or reviewable checks for the following.

### 9.1 Core Dependency Check

Context OS code must not import domain packages.

Forbidden examples:

```python
import runtime.capability.financial
import ai_theme_app
import stock_database
import market_engine
import theme_engine
```

### 9.2 Domain Leakage Check

Context OS source should not contain domain-specific rules such as:

- stock ranking;
- theme scoring;
- market risk gate;
- medical diagnosis;
- coding-specific repository heuristics.

### 9.3 Private Data Check

Context OS migration must not include:

- `identity/` private files;
- memory `.jsonl` content;
- conversation transcripts;
- runtime traces;
- audio data;
- `.env` files;
- generated cache.

### 9.4 Behavior Change Check

A2.0 has no runtime behavior change.

A2 implementation must be test-first and must preserve existing F0-F4.3-pre baselines.

## 10. Migration Order

Recommended post-contract sequence:

```text
A2.1 Context OS Interface Tests
A2.2 Context OS Core Package Import Migration
A2.3 Planner / Budget / ContextBlock Contract Verification
A2.4 Provenance / Quality / Conflict Verification
A2.5 Execution Runtime Smoke Test
A2.6 Boundary Static Checks
A2.7 Phase Report + Review
```

A2 must remain small enough to review.

If the full `runtime/context_os/` import is too large, split A2 into:

```text
A2a Context OS public contracts
A2b planner + budget
A2c projection + provenance
A2d execution + mutation
A2e cache/resurrection/worker
```

## 11. Rollback Strategy

If A2 implementation discovers that Context OS still depends on domain modules, private data, unstable legacy builders, or unclear API boundaries:

1. stop migration;
2. keep `main` at the latest architecture baseline;
3. retain A2.0 contract;
4. record blocker in phase report;
5. split migration into smaller A2a/A2b phases;
6. do not merge partial runtime code until boundary checks pass.

Rollback does not require reverting A2.0 because A2.0 is architecture contract only.

## 12. Acceptance Targets

- [ ] **A2.0-AT-01 Context OS single ownership defined**: Context OS owns lifecycle/planning/budget/projection, not domain truth.
- [ ] **A2.0-AT-02 Context OS module inventory defined**: candidate modules are listed and classified.
- [ ] **A2.0-AT-03 Migration scope frozen**: in-scope modules are documented.
- [ ] **A2.0-AT-04 Exclusion scope frozen**: financial/domain/private/artifact exclusions are documented.
- [ ] **A2.0-AT-05 ContextRequest schema defined**: request expresses demand, not data.
- [ ] **A2.0-AT-06 ContextBlock schema defined**: standard candidate unit includes evidence, source, authority, TTL, and metadata.
- [ ] **A2.0-AT-07 Domain Provider boundary defined**: provider returns facts/evidence/capability results, not prompt/final answer/memory mutation.
- [ ] **A2.0-AT-08 Dependency direction defined**: Context OS depends on provider interface, not domains.
- [ ] **A2.0-AT-09 No Financial Dependency rule defined**: Context OS must not import financial/market/stock/theme engines.
- [ ] **A2.0-AT-10 No Private Data Dependency rule defined**: private identity/memory/audio/data/tmp remain excluded.
- [ ] **A2.0-AT-11 Rollback strategy defined**: stop/split/no merge if boundary violations are found.
- [ ] **A2.0-AT-12 No runtime behavior change**: this phase introduces only architecture documentation.

## 13. Required Validation

A2.0 required validation is documentation-only:

```bash
git diff --name-only
```

Expected changed files:

```text
docs/architecture/Context_OS_Core_Migration_Plan_v1.0.md
```

No runtime file should be changed in A2.0.


## 14. Approval Notes

Decision:

```text
APPROVED WITH NOTES
```

Approved:

- Context OS single ownership;
- dependency direction from Julia Core to Domain Provider Interface;
- ContextRequest as demand signal;
- ContextBlock as facts/evidence/capability-result candidate;
- Domain Provider boundary;
- rejection of Financial Context OS;
- migration safety rules;
- rollback strategy;
- documentation-only scope.

Notes:

1. **ContextBlock must not become hidden Memory.**

   `ContextBlock` belongs to session/context lifecycle. It may expire, refresh, be excluded, or be re-projected. It is not long-term Memory and must not silently persist as Memory.

   ```text
   ContextBlock = session/model-facing context candidate
   Memory       = governed long-term persisted knowledge
   ```

2. **Context OS does not judge domain truth.**

   Context OS organizes, selects, budgets, projects, and traces context. It does not decide whether a financial, medical, or coding fact is domain-correct. Domain truth and evidence validity remain the responsibility of Domain Providers and their evidence authority mechanisms.

Recommended next phase:

```text
A2 — Context OS Core Migration
```

Implementation should remain test-first and should be split if the full `runtime/context_os/` migration is too large for one reviewable PR.
