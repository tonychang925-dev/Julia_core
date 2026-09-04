# RD1-L0B-F2 Core / Assistant Conversation Bootstrap Compatibility Report

## 1. Exact bases

- Core base: `a64d3ebec084f85e038048248a57ea60f7d5d78c`
- Assistant frozen: `03de982a3ad60cdbe067fe68e1be1db8a4202de4`
- Market frozen: `d6889f4f39fc4f8adf404ea7c51eee3ad22d7fa7`
- D1 frozen: `b8ae48a9972ba5bf2f0e4b1db5a1025e38e97e82`
- Client frozen: `a13541e923d7c8d00f5c13851dfa9984da5a6bd3`

## 2. Source-proved Assistant chain

Frozen Assistant startup requires:

```text
voice_api/server.py main()
→ private_data.wiring.wire_legacy_composition(legacy_repo_path)
→ LegacyJsonConversationRepository(legacy_repo_path)
→ julia_core.runtime.conversation_runtime.configure_conversation_runtime
→ configure_conversation_runtime(legacy_repo)
→ canonical process ConversationRuntime
```

The function receives one explicit repository object and does not depend on a return value. `wire_legacy_composition()` then returns the composition root, binding report, and repository. At turn time, `voice_api/conversation_routes.py` imports `get_conversation_runtime()` and invokes the canonical begin/commit/cancel lifecycle.

At Core base `a64d3eb...`, `julia_core/runtime/conversation_runtime.py` exposed only:

```text
get_conversation_runtime()
```

It lazily constructed a default `ConversationRuntime()` and had no Assistant-required explicit configuration API.

## 3. Narrow Core repair

`julia_core/runtime/conversation_runtime.py` now adds:

```text
configure_conversation_runtime(repository)
```

Semantics:

- validates that an explicit repository object is supplied;
- creates one process-local canonical `ConversationRuntime` on first call;
- returns that exact instance;
- is idempotent when called again with the exact bound repository object;
- raises `ConversationCutoverRequired` for a different repository;
- guards singleton construction/configuration with the existing threading module lock;
- does not alter `ConversationRuntime`, repository persistence, Context OS, or turn lifecycle code.

`get_conversation_runtime()` now uses the same lock and returns the configured instance. No second singleton or persistence family is introduced.

## 4. Preserved authority

| Concern | Owner |
| --- | --- |
| canonical conversation lifecycle | Core `ConversationRuntime` |
| durable transcript | Core `ConversationRepository` |
| model-visible context | Context OS |
| startup composition | thin Assistant composition root |
| client transport/display | Electron/Voice clients |

Assistant does not gain transcript authority. Core does not gain a second runtime or repository implementation. Persisted conversation schema is unchanged.

## 5. Focused proof

- F01 frozen Assistant `private_data.wiring` imports successfully: PASS
- F02 explicit configuration installs canonical runtime: PASS
- F03 `get_conversation_runtime()` returns the exact object: PASS
- F04 exact same repository is idempotent: PASS
- F05 different repository fails closed: PASS
- F06 repeated configuration/get does not create a second authority: PASS
- F07 distinct controlled roots remain isolated: PASS
- F08 streaming commit settles exactly once: PASS
- F09 cancel retains accepted completed user turn and rejects late commit: PASS
- F10 frozen Assistant canonical conversation route imports: PASS
- F11 I1/I4 regressions remain green: PASS
- F12 L0A-F1 D1 binding remains green: PASS
- F13 L0B-F1 Market composition remains green: PASS
- F14 no live Market/D1/provider/Voice/user execution: PASS

## 6. Tests

Focused:

```text
/opt/miniconda3/bin/pytest -q tests/runtime/test_l0b_f2_conversation_bootstrap_compatibility.py
10 passed
```

Conversation/context:

```text
/opt/miniconda3/bin/pytest -q tests/test_conversation_authority.py tests/test_baseline_e2e_conversation.py tests/test_context_reconstruction.py tests/test_context_continuity_boundary.py tests/wave5/test_at03_text_voice_text.py
43 passed

/opt/miniconda3/bin/pytest -q tests/runtime/test_c1_rev2_context_os_projection.py tests/test_context_reconstruction.py tests/test_context_continuity_boundary.py
12 passed, 1 xfailed
```

Research and controlled bindings:

```text
/opt/miniconda3/bin/pytest -q tests/runtime/test_i1_streaming_capability_continuation.py tests/runtime/test_i4_same_turn_research_orchestration.py tests/research/test_c1_research_event_enrichment.py tests/research/test_c2_preliminary_research_judgment.py tests/research/test_l0a_f1_core_d1_provider_binding.py tests/capability/test_l0b_f1_market_frozen_composition.py
91 passed
```

Static:

```text
/opt/miniconda3/bin/python -m compileall -q julia_core/runtime/conversation_runtime.py tests/runtime/test_l0b_f2_conversation_bootstrap_compatibility.py
PASS

git diff --check
PASS
```

An exploratory broader historical context/chat suite contains pre-existing failures at this base (`JuliaSession.context_os` initialization and an obsolete Context OS source-purity expectation). They are unrelated to the two-file bootstrap diff and were not altered.

## 7. Execution boundary

- Production edits: Core only
- Assistant production edits: 0
- Market production edits: 0
- D1 production edits: 0
- Client production edits: 0
- Live execution: 0
- Market executions: 0
- D1 executions: 0
- Provider calls: 0
- Voice executions: 0
- User traffic: 0
- Port 18090 binding: none

## 8. Verdict

```text
RD1-L0B-F2 = PASS
```
