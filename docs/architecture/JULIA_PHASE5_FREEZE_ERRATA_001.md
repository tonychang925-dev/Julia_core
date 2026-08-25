# Julia Phase 5 — FREEZE-ERRATA-001

**Status:** ACTIVE ERRATA / CODE MUTATION STOP
**Date:** 2026-08-11
**Scope:** RMD-3A deployed S2S handler patch map only

## 1. What remains valid

The following frozen decisions remain valid and are NOT revoked:

- Conversation Management Unified Architecture v1.1
- Phase 5 Four-Repository Development Plan v1.2 at architecture/dependency level
- Wave B GO
- RMD-3A ONLY release
- RMD-3B / RMD-3G / RMD-4+ HOLD
- RMD-3A target: `conversation_id` must propagate Voice session → S2S chat-completions request → Brain native CRT branch
- Electron production mutation for RMD-3A remains `0 expected`
- No semantic history transfer

## 2. New provenance mismatch

Before the first RMD-3A source mutation, repository source was cross-checked against WB-JA-08.

WB-JA-08 reported the deployed `ChatCompletionsApiModelHandler` patch locus as:

```text
chat_completions_language_model.py
ChatCompletionsApiModelHandler._generate()
+ _request_chat_completions()
```

However both the historical imported Golden commit `b2c7567` and current Voice source generation `49ef5ba` show:

```text
ChatCompletionsApiModelHandler
  implements _serialize(), _build_optional_kwargs(), _request(), event hooks

BaseOpenAICompatibleHandler
  owns _generate(..., turn, optional_kwargs, ...)
```

Therefore the statement "modify subclass `_generate()`" is not yet a source-safe implementation instruction.

## 3. Gate consequence

```text
RMD-3A architecture GO                    ✅ remains valid
RMD-3A development branch creation        ✅ allowed
RMD-3A frontend design                    ✅ remains valid
RMD-3A deployed handler mutation          ⛔ STOP
RMD-3A source commit                      ⛔ STOP until reconciliation
Deployment/service/package mutation       ⛔ HOLD
```

No opportunistic partial source patch is permitted after this mismatch.

## 4. Required reconciliation

Attest exact LIVE deployed source snippets for:

1. `ChatCompletionsApiModelHandler` class definition and methods;
2. the actual `_generate()` owner;
3. `_request()` and `_request_chat_completions()`;
4. the exact path by which `turn.runtime_config.session.metadata` can reach the outbound request;
5. SHA256 of every live file involved;
6. compare live file bytes/hash against repo `b2c7567` / `49ef5ba` imported files.

Final classification must be one of:

```text
A. WB-JA-08 function attribution error; live bytes match repo architecture
B. LIVE site-packages drift; live bytes differ from imported repo source
C. other, with exact evidence
```

Only after this correction may the Exact Patch Map be amended and source mutation resume.
