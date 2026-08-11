# CC-1 Conversation Convergence Delta Map

STATUS: CANONICAL CC-1 SOURCE REVIEW INPUT
UPDATED: 2026-08-11
OWNER: Codex
REVIEWER: Julia Agent
GOVERNANCE FLOOR: G0 FOUR-REPO AUTHORITY CLOSEOUT CLOSED, ambiguous authority count 0

## Objective

Establish one canonical conversation identity across Electron Text, Electron Voice, S2S, Brain, ConversationRuntime, Context OS, and Core durability.

Durable authority: ConversationRuntime/Core.

Non-authorities:

- Electron local cache is display/projection only.
- S2S carries `conversation_id` transparently and does not own conversation history.
- Brain OpenAI compatibility layer routes into ConversationRuntime and is not the durable store.
- `voice_trace_id` is observability only.
- `turn_id` is turn identity only.

## Targeted delta map

| Edge | Current finding | CC-1 classification | Required disposition |
| --- | --- | --- | --- |
| Core ConversationRuntime | `begin_turn_streaming()` accepts/creates canonical conversation, persists accepted user turn before cognition, commits/cancels assistant settlement under Core authority. | PASS | No Core code change required for CC-1. Keep RMD-1-SC floor `b463a3f702f9cfcb8db3cda870d8f570fc92483d` as production durability authority. |
| Brain OpenAI compatibility → ConversationRuntime | When `conversation_id` is supplied, Brain passes it unchanged into ConversationRuntime and emits CRT bind/settlement evidence. | PASS | No Brain code change required for CC-1 source package. Legacy no-`conversation_id` path remains non-authoritative/backcompat and must not be used by Electron/S2S production flows. |
| Voice/S2S → Brain | S2S C1 release carries `conversation_id` in request `extra_body` and keeps `voice_trace_id` separate from SDK kwargs and `turn_id`. | PASS | No Voice code change required for CC-1 source package. C1 source/artifact remain production Voice authority. |
| Electron Text → Brain | Text turns use Julia-native `/internal/v1/conversations/{conversation_id}/turns` path and treat local cache as disposable projection. | PASS | Retain existing native text path and canonical reconcile. |
| Electron Voice bind | Previous Voice workspace bootstrap copied canonical messages into Voice iframe, creating a shadow history/semantic authority risk. | FIX REQUIRED | Replace history snapshot bootstrap with pure `conversation_id` bind message. Do not send `messages` or `baseLastMessageId` to Voice. |
| Electron Voice flush | Previous Voice workspace flush uploaded copied Voice turns through `/external-turns`, creating a second write authority. | FIX REQUIRED | Retire external-turn upload from Electron. Keep rejecting safety fence only while historical callers are being removed. Voice turns must enter Core via S2S → Brain → ConversationRuntime. |
| Text ↔ Voice mode switch | Mode switch should attach another modality to the same canonical conversation, not copy/seed/flush history stores. | FIX REQUIRED | On switch, sync canonical projection for display only; do not use caller-owned history as model-visible authority. |
| Electron reconnect | Electron may retain the returned canonical `conversation_id` and rebind Voice to it. | PASS WITH RETIREMENT TARGETS | Future runtime tests must prove reconnect does not create replacement conversation authority. |
| Two-conversation isolation | No code-level new authority introduced in CC-1; isolation remains a required deployment/runtime test. | PASS WITH RUNTIME TEST REQUIRED | Runtime IV&V must verify no stale async event is rendered into the wrong conversation. |

## Identity separation rules

- `conversation_id`: canonical conversation identity; created/accepted by Core/ConversationRuntime authority.
- `turn_id`: turn identity; never a conversation substitute.
- `voice_trace_id`: ephemeral observability identity; never a durable conversation or turn authority.

## CC-1 implemented source delta

Electron/Julia_client is the only repository requiring immediate source changes for CC-1:

- Retire Voice message snapshot bootstrap.
- Retire Electron `/external-turns` write path by replacing it with a rejecting safety fence.
- Bind Voice by canonical `conversation_id` only.
- Update Voice UX copy so it no longer describes a Voice workspace as a semantic/history authority.

Core, Brain, and Voice/S2S require no CC-1 code change at this source gate because their current authoritative paths already satisfy transparent `conversation_id` propagation and Core durability requirements.

## Verification expectations

Automated source tests must prove at minimum:

- Electron no longer constructs the `/external-turns` endpoint.
- Any historical external-turn commit caller is rejected.
- Text Julia-native turn contract still carries canonical `conversation_id` without caller-owned history.
- Electron local conversation/cache remains projection-only.
- Voice UX state changes do not create cognition/history authority.

Runtime verification after deployment must prove:

- Text → Voice and Voice → Text continuity under the same `conversation_id`.
- Voice reconnect does not create a new durable conversation.
- Brain restart does not change canonical conversation authority.
- Two active conversations do not leak events/messages across IDs.
