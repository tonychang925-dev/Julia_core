# Julia Core Current Authority

STATUS: CANONICAL
UPDATED: 2026-08-11
REPOSITORY: Julia_core
ROLE: Core runtime, ConversationRuntime, Context OS, canonical architecture authority
AUTHORITATIVE BRANCH: main
CURRENT REPOSITORY / DOCUMENTATION AUTHORITY AT CLOSEOUT: 7d29fb9dcb2719c406ac2cd66cd32ddc1e663662
HISTORICAL MAIN SNAPSHOT MENTIONED BY EARLIER G0: 0d72b05534c79c22e58b2e4e95dca97171d8489a
PRODUCTION CONVERSATION RUNTIME FLOOR: b463a3f702f9cfcb8db3cda870d8f570fc92483d
RMD-1-SC PRODUCTION AUTHORITY: b463a3f702f9cfcb8db3cda870d8f570fc92483d

IMPORTANT: `0d72b05534c79c22e58b2e4e95dca97171d8489a` MUST NOT be interpreted as production ConversationRuntime authority. It is not a supersession of the RMD-1-SC floor unless a later manifest explicitly proves ancestry/content inclusion of `b463a3f...`.

## Production/development status

- RMD-3G source/artifact/staging/live recovery work has superseded earlier Aug-11 freeze status language.
- This file is the current per-repository authority entry point.
- The cross-repository authority entry point is `docs/authority/JULIA_FOUR_REPO_AUTHORITY_MANIFEST.md`.

## Authoritative architecture docs

CANONICAL:

- `docs/architecture/JULIA_CONVERSATION_MANAGEMENT_UNIFIED_ARCHITECTURE_v1.1_FINAL_FREEZE_CANDIDATE.md`
- `docs/architecture/JULIA_PHASE5_FOUR_REPO_DEVELOPMENT_PLAN_v1.2_FINAL_FREEZE_CANDIDATE.md`
- `docs/architecture/CM_CORE_CONVERSATION_RUNTIME_CONTRACT_v1.0.md`
- `docs/architecture/C-02_CONVERSATION_AUTHORITY_CONTRACT.md`
- `docs/adrs/ADR-020-production-context-authority-reconciliation.md`

DERIVED / SUPPORTING:

- `docs/architecture/JULIA_PHASE5_AUTHORITY_RECONCILIATION_REGISTER_v1.0_FINAL_REVIEW.md`
- `docs/architecture/JULIA_WAVE_B_EXACT_PATCH_MAP_v1.0_FINAL_REVIEW.md`
- `docs/architecture/ARCHITECTURE_INDEX.md`
- `docs/architecture/ARCHITECTURE_DOCUMENT_REGISTRY.md`

HISTORICAL / SUPERSEDED:

- `docs/architecture/PHASE5_ARCHITECTURE_TASK_FREEZE_MANIFEST_2026-08-11.md` at commit `836b252...` is historical freeze evidence only.
- Earlier non-final drafts named `*_DRAFT*`, non-final `*_FREEZE_CANDIDATE*`, or duplicate `(1)` files are not implementation authority.
- Earlier workspace/live-turn proposal documents are historical unless referenced by this manifest or the cross-repo manifest as CANONICAL.

## Current production code authority

Authority roles are deliberately separate:

- REPOSITORY / DOCUMENTATION HEAD: current `main` authority manifest head.
- PRODUCTION CONVERSATION RUNTIME FLOOR: `b463a3f702f9cfcb8db3cda870d8f570fc92483d`.
- RMD-1-SC AUTHORITY: `b463a3f702f9cfcb8db3cda870d8f570fc92483d`.

Do not derive live production runtime bytes from repository HEAD alone. Runtime binding must prove loaded file paths and hashes.

ACTIVE:

- `julia_core/runtime/conversation_runtime.py`
- `julia_core/runtime/context_execution_runtime.py`
- `julia_core/runtime/julia_session.py`
- `julia_core/storage_v2/` where present
- `julia_core/context_assembly/` where present

LEGACY / DO-NOT-USE FOR NEW WORK:

- old workspace/bootstrap semantic authority paths
- abandoned live-turn shadow authority paths
- local runtime/data mutations not committed to Git

## Current open remediation items

- CC-1 Canonical Conversation Convergence remains next permitted feature/convergence package after G0 closeout.
- Existing uncommitted runtime data and experimental worktree dirt are not source authority.

## Precedence

If documents conflict, authority order is:

1. `docs/authority/JULIA_FOUR_REPO_AUTHORITY_MANIFEST.md`
2. this `docs/authority/CURRENT_AUTHORITY.md`
3. frozen canonical architecture/contracts listed above
4. compatible ADRs
5. implementation code
6. historical/archive documents
