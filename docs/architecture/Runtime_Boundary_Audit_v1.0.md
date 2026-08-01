# Runtime Boundary Audit v1.0

> Phase: A1 — Runtime Boundary Audit & Architecture Inventory  
> Source Branch: `codex/full-agent-architecture-migration`  
> Date: 2026-07-31  
> Status: Draft Audit

## 1. Audit Scope

This audit reviews the architecture evaluation branch:

```text
codex/full-agent-architecture-migration
```

Purpose:

```text
Architecture evaluation only.
Do not merge as-is.
```

A1 is not a migration phase.

A1 does not:

- refactor code;
- delete code;
- move files;
- change imports;
- merge the evaluation branch;
- modify runtime behavior.

A1 only classifies existing assets and recommends future migration order.

## 2. Classification Model

### Category 1 — Julia Core

Definition:

Domain-independent runtime components that can serve all future Julia instances.

Examples:

- Identity OS engine/schema;
- Context OS;
- Memory OS engine;
- Action Governance;
- Capability Router;
- Provider Adaptation;
- Runtime Orchestration;
- Evidence/provenance primitives.

### Category 2 — Domain Provider

Definition:

Domain-specific facts, evidence, tools, and capability results.

Examples:

- Financial provider;
- future healthcare provider;
- future coding provider.

A Domain Provider must not own Context OS, Memory OS, prompt assembly, token budgeting, identity, or Julia action governance.

### Category 3 — Application Surface

Definition:

User-facing or system-facing interfaces.

Examples:

- Analyst Workbench;
- JuliaCopilot;
- voice UI;
- mobile UI.

### Category 4 — Runtime Artifact

Definition:

Generated runtime output and cache data.

Examples:

- `tmp/`;
- logs;
- cache;
- generated audio;
- runtime traces;
- conversation archives.

Runtime artifacts do not enter core migration.

### Category 5 — Private / Local Data

Definition:

Personal identity, private memory, local user data, private relationship material, and non-public conversation content.

Private/local data does not enter the public repository.

## 3. Julia Core Inventory

| Path | Classification | Confidence | Recommendation | Notes |
|---|---|---:|---|---|
| `runtime/context_os/` | Julia Core | High | A2 migration candidate | Single Context OS authority: planner, budget, projection, provenance, execution, mutation, cache, resurrection. |
| `runtime/action/` | Julia Core | High | Core governance migration candidate | Action OS / action governance shared by all domains. |
| `runtime/capability/` excluding `financial/` | Julia Core | High | Split router/provider contracts from domain providers | Capability router/provider/invocation runtime are core. |
| `runtime/cognitive/` | Julia Core | Medium | Review before migration | Cognitive arbitration, provider adaptation, rendering, benchmark. |
| `runtime/evidence/` | Julia Core | High | Core evidence subsystem migration candidate | Generic semantic evidence/chunk/ranker/retriever primitives. |
| `runtime/reflection/` | Julia Core | Medium | Review memory write gates | Reflection produces candidates; formal memory writes must remain governed. |
| `runtime/persona/` | Julia Core schema/engine | Medium | Migrate engine only | Persona compiler/policies are core; private identity content is not. |
| `runtime/relationship/` | Julia Core schema/engine | Medium | Migrate engine only | Relationship runtime/store abstractions; private relationship data excluded. |
| `runtime/situation/` | Julia Core | Medium | Core support candidate | Generic situation context support. |
| `runtime/runtime_trace/` | Julia Core observability | High | Migrate code only | Runtime trace abstractions; generated traces excluded. |
| `schemas/` | Public contract | High | Migrate with corresponding modules | Runtime schemas. |

## 4. Legacy / Transitional Core Candidates

| Path | Classification | Confidence | Recommendation | Notes |
|---|---|---:|---|---|
| `runtime/context_assembly/` | Legacy Core Candidate | Medium | Review for replacement by `context_os/` | Earlier context assembly layer. Do not expand before Context OS migration plan. |
| `runtime/context_builder.py` | Legacy Core Candidate | Medium | Review after Context OS migration | Older builder path. Must not compete with Context OS. |
| `runtime/conversation_state/` | Core Support Candidate | Medium | Review lifecycle overlap with Context OS state | Conversation continuity/session state. |
| `runtime/memory_loader.py` | Core Support Candidate | Medium | Review private data boundary | Loader code may be core; memory content remains private. |

## 5. Domain Provider Inventory

| Path | Classification | Confidence | Recommendation | Notes |
|---|---|---:|---|---|
| `runtime/capability/financial/` | Domain Provider | High | Keep isolated as first production domain | Financial typed contracts, read-only client, deterministic workflows, governance, rendering, analyst chat surface. |
| `docs/Julia_Financial_Analyst_Integration_Design_v1.0.md` | Domain architecture contract | High | Keep as financial domain contract | Must reference Context OS Domain Binding principles. |
| `docs/project_control/PHASE_CONTRACT_F0-F4.*` | Domain phase contracts | High | Keep as financial domain governance history | F0-F4.2.1 remain approved production route. |

Boundary note:

`runtime/capability/financial/interface/analyst_chat/context.py` is explicitly classified as a Legacy V0.1 adapter, not a Context OS implementation.

## 6. Application Surface Inventory

| Path | Classification | Confidence | Recommendation | Notes |
|---|---|---:|---|---|
| `frontend/` | Application Surface | High | Already approved through F4.2.1 | JuliaCopilot workbench entry. Future actions must carry intent pointers only. |
| `runtime/capability/financial/interface/analyst_chat/api.py` | Interaction transport | High | Keep as surface/runtime boundary | WebSocket transport shell. |
| `runtime/conversation_runtime/` | Conversation runtime / application runtime | Medium | Migrate after Context OS boundary | Includes CLI/bridge/latency/state machine. Not a domain provider. |
| `stt/` | Application Extension | Medium | Defer to A6 Voice Adapter | Speech-to-text adapters. |
| `tts/` | Application Extension | Medium | Defer to A6 Voice Adapter | Text-to-speech adapters; use env vars, no embedded secrets found. |
| `runtime/voice_validation/` | Extension validation | Medium | Defer to A6 Voice Adapter | Voice/runtime validation code. |

## 7. Runtime Artifact Inventory

| Path | Classification | Recommendation | Notes |
|---|---|---|---|
| `tmp/` | Runtime Artifact | Do not publish / do not migrate | Temporary reports, scan payloads, phase artifacts. |
| `data/` | Runtime Artifact | Do not publish / do not migrate | Runtime traces, archive data, governance artifacts. |
| `audio/` | Runtime Artifact / Private Asset | Do not publish / do not migrate | Generated/local audio. |
| `*.log` | Runtime Artifact | Excluded by `.gitignore` | Logs stay local. |
| `__pycache__/` | Generated cache | Excluded by `.gitignore` | Python cache only. |

## 8. Private Data Inventory

| Path | Classification | Recommendation | Notes |
|---|---|---|---|
| `identity/` | Private identity data | Do not publish | Real Julia/Tony identity/persona content. Core schema/engine may migrate separately. |
| `memory/` | Private memory content | Do not publish | Memory content and private relationship/episodic material. |
| `data/conversation_archive/` | Private/runtime data | Do not publish | Conversation transcripts and archive data. |
| `memory/claude_diary/` | Private/reference memory | Do not publish | Personal/reference content, not public core architecture. |

## 9. Boundary Findings

### 9.1 Core Contamination Scan

A scan for financial/stock/market/theme references inside likely core directories found no material domain dependency.

Only one textual false-positive was observed in `runtime/context_assembly/conflict_resolver.py` using the generic English word `themes`.

Assessment:

```text
No clear financial contamination in Julia Core candidates.
```

### 9.2 Financial Domain Dependency Scan

Financial F4/F4.2 docs intentionally mention Memory/DB/trading prohibitions.

Frontend static boundary check already prevents memory/database/trading API usage.

Assessment:

```text
Financial domain is currently isolated enough for staged provider binding.
```

### 9.3 Private Data Risk

Local private directories exist and must remain excluded:

```text
identity/
memory/
data/
tmp/
audio/
```

Assessment:

```text
Public migration must continue to separate code/schema from private content.
```

## 10. Migration Recommendation

Recommended next route:

```text
A2 Context OS Core Migration
  - migrate `runtime/context_os/` with targeted tests;
  - keep Context OS independent of financial domain;
  - include only required public schemas/contracts;
  - do not migrate private memory/identity content.

A3 Domain Provider Interface
  - formalize DomainContextRequest / DomainContextProvider;
  - define ContextBlock return contract;
  - add provider registry/binding layer.

A4 Financial Provider Binding
  - adapt financial capability client to provider contract;
  - return ContextBlock candidates with EvidenceRef mapping;
  - retire expansion path for analyst_chat/context.py.

A5 Workbench Context Actions
  - implement Ask Julia actions using intent pointer contract;
  - no context payloads from UI.

A6 Voice Adapter
  - migrate voice/STT/TTS after runtime boundaries are stable.
```

## 11. Non-Goals

A1 does not:

- merge `codex/full-agent-architecture-migration`;
- migrate code;
- delete legacy modules;
- move files;
- change imports;
- alter runtime behavior;
- publish private data;
- implement F4.4/F4.5 features.

## 12. Machine Inventory

A machine-readable audit artifact was generated at:

```text
tmp/runtime_boundary_inventory.json
```

It is intentionally not committed to `main` because it is an audit working artifact.

## 13. Approval Notes

Decision:

```text
APPROVED WITH NOTES
```

Approved:

- Runtime classification model;
- Julia Core boundary;
- Domain Provider boundary;
- Application Surface boundary;
- Runtime Artifact boundary;
- Private data isolation;
- `main` as Frozen Production Baseline;
- `codex/full-agent-architecture-migration` as evaluation-only branch.

Constraints:

- Audit does not imply migration;
- no code migration happened in A1;
- no runtime behavior changed in A1;
- full runtime migration branch remains `DO NOT MERGE`;
- future migration requires A2-A4 contracts;
- `tmp/runtime_boundary_inventory.json` remains a local audit artifact and is not source of truth.

Recommended next phase:

```text
A2.0 — Context OS Core Migration Contract
```

A2.0 must be contract-first. It must define Context OS ownership, dependency direction, migration boundaries, and forbidden dependencies before moving any runtime code.
