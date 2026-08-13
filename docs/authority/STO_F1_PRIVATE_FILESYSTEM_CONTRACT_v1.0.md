# STO-F1 Private Filesystem Contract v1.0

STATUS: FROZEN
UPDATED: 2026-08-13
PROGRAM: Conversation Storage + Management + Julia Diary
PHASE: STO-F1 — Private Filesystem Contract (Wave 0)
BASE: cm-r0-fix @ `855dcd7` (canonical); STO-D0 frozen @ `261521f`

This contract does NOT discuss "how data should be stored". It turns D0-01's frozen decisions into an unambiguous, implementable, testable filesystem boundary.

## 0. Core decision — three-state semantics

```text
JULIA_PRIVATE_DATA_ROOT  absent         → OS product default
JULIA_PRIVATE_DATA_ROOT  present + ""   → INVALID EXPLICIT CONFIG, FAIL CLOSED
JULIA_PRIVATE_DATA_ROOT  present + nonempty → explicit only; any failure FAIL CLOSED, never fallback
```

`""` is treated as an explicit config error (NOT as absence) because `JULIA_PRIVATE_DATA_ROOT=""` is already an explicit configuration act; silently returning to a default would create the most dangerous class of bug:

```text
operator thought persistence = path A
system silently persisted = path B
```

Four load-bearing principles:

```text
1. absent ≠ empty
2. explicit failure ≠ fallback
3. existing directory ≠ automatically Julia-owned
4. resolved filesystem root ≠ semantic Julia identity
```

## 1. Resolver ownership

Sole implementation location:

```text
Julia-AI-Assistant → PrivateDataRootResolver
```

Forbidden:

```text
Julia_core            resolves path   ❌
Julia-Voice-S2S       resolves path   ❌
Electron              resolves path   ❌
another Assistant module guesses default ❌
```

```text
one product → one resolver → one resolved physical root
```

Core keeps `path knowledge = NONE`. F2 binds `ResolvedPrivateDataRoot → persistence adapters → Core ports`.

## 2. Three-state resolution

```text
STATE A — ABSENT            (key not in environment) → OS product default
STATE B — PRESENT_EMPTY     (key present, value == "") → ROOT_CONFIG_EMPTY → FAIL CLOSED, no default fallback
STATE C — PRESENT_NONEMPTY  (key present, value != "") → explicit candidate → canonicalize → validate → bootstrap/reconcile → READY | FAIL CLOSED
```

No trimming: `JULIA_PRIVATE_DATA_ROOT="   "` is a non-empty explicit value (NOT silently trimmed to `""`); it is resolved as a path and normally rejected as relative/invalid. No hidden normalization.

## 3. OS default (unchanged from D0-01)

```text
macOS    ~/Library/Application Support/JuliaAI/
Linux    ${XDG_DATA_HOME:-~/.local/share}/julia-ai/   (XDG_DATA_HOME absent/empty → ~/.local/share)
Windows  %LOCALAPPDATA%\JuliaAI\
```

`XDG_DATA_HOME=""` is platform default-resolution input (→ `~/.local/share`), NOT the same contract as `JULIA_PRIVATE_DATA_ROOT=""`. If `LOCALAPPDATA` cannot be reliably obtained → `ROOT_DEFAULT_UNRESOLVABLE` → FAIL CLOSED (never guess `C:\Users\...`).

## 4. No CWD dependence

`JULIA_PRIVATE_DATA_ROOT="./data"` is forbidden (would make `cd repo_A` vs `cd repo_B` yield different roots, violating process/repo independence).

```text
expand-user-home          ✅  (~/JuliaData)
arbitrary env interpolation ❌  ($HOME/foo, ${SOME_VAR}/foo)
CWD resolution            ❌
```

Final output MUST be a canonical absolute physical path.

## 5. Symlink handling

Symlinks are NOT blanket-forbidden (external drives / user-dir mapping may need them later):

```text
lexical candidate → expand user → canonical physical resolution → validate actual target
```

`~/JuliaData → symlink → /Volumes/SecureDrive/Julia` is allowed. But ALL safety rules apply to the canonical physical target (not the alias) — a symlink resolving into a Git worktree MUST be caught.

## 6. Git worktree gate (stricter than "root itself is a repo")

Canonical private root MUST NOT equal or reside beneath any Git working tree:

```text
/Users/admin/Julia_core/            ❌
/Users/admin/Julia_core/data/       ❌
/Users/admin/Julia_core/.private/   ❌
```

(otherwise RP-1 `worktree_clean` gets polluted by runtime data)

```text
/Users/admin/JuliaData/  (sibling of Julia_core)  ✅
```

## 7. Existing directory ownership discipline

```text
path does not exist          → create → bootstrap
path exists + empty          → bootstrap allowed
path exists + valid Julia root marker → validate → reconcile → READY
path is a regular file       → FAIL CLOSED
path is non-empty + no Julia root marker → ROOT_UNOWNED_NONEMPTY → FAIL CLOSED
```

Never adopt `/Users/admin/Documents` (hundreds of existing files) as "the Julia root".

## 8. Root marker

```text
<PRIVATE_JULIA_DATA>/.julia-root.json
```

Minimal content:

```json
{
  "schema_version": 1,
  "product": "JuliaAI",
  "storage_root_id": "<uuid>",
  "state": "READY",
  "created_at": "<RFC3339>"
}
```

`storage_root_id` is a **physical storage root identity only** — NOT Julia identity, NOT user identity, NOT conversation identity, NOT memory authority. (Written into contract to prevent future abuse.)

## 9. Bootstrap state machine

```text
UNINITIALIZED → BOOTSTRAPPING → READY
```

Not `mkdir → "almost READY"`. Frozen flow:

```text
select + validate root
        ↓
create root if needed
        ↓
durably create marker (state=BOOTSTRAPPING, storage_root_id=UUID)
        ↓
create/validate reserved directories
        ↓
permissions validation
        ↓
directory durability barriers
        ↓
atomically update marker (state=READY)
        ↓
fsync
        ↓
ROOT_READY
```

On crash, `marker=BOOTSTRAPPING` tells the next startup "this is Julia's own incomplete bootstrap" — not an unknown non-empty directory.

## 10. Crash recovery

```text
mkdir root → crash (root still empty) → retry bootstrap ✅

marker BOOTSTRAPPING durable → memory/ created → indexes/ created → crash
→ retry: read same marker → same storage_root_id → reconcile missing dirs → READY
```

MUST NOT generate a second `storage_root_id`.

## 11. Reserved top-level namespace

F1 bootstrap owns these six top-level namespaces:

```text
<PRIVATE_JULIA_DATA>/
├── memory/
├── runtime/
├── indexes/
├── backups/
├── migrations/
├── logs/
└── .julia-root.json
```

F1 does NOT decide the interior of `memory/conversations/*`, `memory/diary/*`, etc. — that belongs to CM / DIA / Memory / OPS.

## 12. Permissions

```text
POSIX: root directories ≤ 0700, private files ≤ 0600
```

Not "best effort". If privacy cannot be guaranteed → `ROOT_PRIVACY_UNENFORCEABLE` → FAIL CLOSED.

Existing overly-broad permissions (e.g. `0755`) may be auto-hardened **monotonically only** (`0755 → 0700` ✅). Resolver MUST NOT auto-widen (`0500 → 0700` ❌) — it may tighten, never relax, a user's security posture. Windows: current-user private ACL; if the platform adapter cannot establish/verify it → fail closed.

## 13. Marker corruption ≠ self-heal into a new Julia

Corrupt `.julia-root.json` → `ROOT_MARKER_CORRUPT` → FAIL CLOSED → explicit recovery/repair (never "regenerate a new marker" over an existing `memory/conversations/`). `schema_version > supported` → `ROOT_SCHEMA_UNSUPPORTED` (never downgrade-guess).

## 14. Concurrent bootstrap

Brain / maintenance process / future tools may start simultaneously. Requirement: **one physical bootstrap transaction** (one `storage_root_id`, one READY marker, no split init). Mechanism (`fcntl` / `flock` / mkdir-lock / OS mutex) is not frozen — the serialization semantic is.

## 15. Resolver return

```text
ResolvedPrivateDataRoot {
    canonical_path
    storage_root_id
    source: EXPLICIT | OS_DEFAULT
    schema_version
}
```

Never returns ConversationRepository / Memory / JuliaIdentity. Resolver is just a resolver.

## 16. Structured failure (error family)

```text
ROOT_CONFIG_EMPTY
ROOT_EXPLICIT_NOT_ABSOLUTE
ROOT_HOME_UNRESOLVABLE
ROOT_DEFAULT_UNRESOLVABLE
ROOT_IN_GIT_WORKTREE
ROOT_PATH_IS_FILE
ROOT_UNOWNED_NONEMPTY
ROOT_PERMISSION_DENIED
ROOT_PRIVACY_UNENFORCEABLE
ROOT_MARKER_CORRUPT
ROOT_SCHEMA_UNSUPPORTED
ROOT_BOOTSTRAP_DURABILITY_FAILURE
ROOT_BOOTSTRAP_CONFLICT
```

Outer normalization: `PRIVATE_DATA_ROOT_UNAVAILABLE`; inner `reason` must remain auditable.

## 17. No fallback

```text
explicit candidate selected → something fails → ERROR
```

Absolutely no fallback chain (`~/.julia`, `repo/data`, `./data` are never hidden emergency roots).

## 18. F1 / F2 boundary

F1 ends at:

```text
Configuration → PrivateDataRootResolver → ResolvedPrivateDataRoot
```

F2 begins at:

```text
ResolvedPrivateDataRoot → Assistant composition root
→ ConversationRepository adapter / DiaryRepository adapter / Memory adapter / Backup adapter
→ Julia Core ports
```

F1 MUST NOT pass the path to Core.

## Invariants

**F1-I01 — Single Resolver**

```text
Julia-AI-Assistant MUST provide the sole product-level PrivateDataRootResolver.

No other repository/component may independently select Julia's canonical
private-data root.
```

**F1-I02 — Explicit Empty Is Invalid**

```text
If JULIA_PRIVATE_DATA_ROOT is present with an empty value, resolution MUST fail
closed.

Empty explicit configuration MUST NOT be treated as absence and MUST NOT fall
back to an OS default.
```

**F1-I03 — No Relative/CWD Authority**

```text
Explicit root resolution MUST NOT depend on process CWD.

Relative explicit paths are invalid.
```

**F1-I04 — Canonical Physical Validation**

```text
All safety validation MUST apply to the canonical physical target after
supported user-home/symlink resolution.
```

**F1-I05 — No Git Worktree Persistence**

```text
The canonical private root MUST NOT equal or reside beneath a Git working
tree or repository metadata path.
```

**F1-I06 — Owned-Root Bootstrap**

```text
An existing non-empty unmarked directory MUST NOT be silently adopted as
Julia's private-data root.

Only a non-existent path, empty path, or valid Julia root may enter
bootstrap/reconciliation.
```

**F1-I07 — Durable Root Identity**

```text
A bootstrapped root MUST have one durable physical storage_root_id.

Crash/retry/concurrent bootstrap MUST NOT silently create multiple root
identities for the same root.
```

**F1-I08 — Private-by-Default**

```text
The resolver/bootstrap layer MUST enforce the platform's private-user filesystem
protection or fail closed.

It MUST NOT silently continue with demonstrably broader access.
```

**F1-I09 — Fail-Closed Marker Governance**

```text
Corrupt, incompatible, or ambiguous Julia root markers MUST fail closed.

Existing canonical data MUST NOT be re-owned by generating a replacement marker.
```

**F1-I10 — No Silent Fallback**

```text
Once an explicit root candidate is selected, any failure in canonicalization,
validation, permissions, bootstrap, or durability MUST terminate resolution.

No repo-local, ~/.julia, OS-default, or alternate path fallback is permitted.
```

**F1-I11 — Bootstrap Is Recoverable**

```text
Root bootstrap MUST distinguish BOOTSTRAPPING from READY and support
deterministic crash recovery without guessing.
```

**F1-I12 — Filesystem Only**

```text
PrivateDataRootResolver MUST NOT create semantic authority.

storage_root_id and path metadata are physical-storage identifiers only.
```

## Sabotage suite (AT-FS-01…24)

```text
AT-FS-01  JULIA_PRIVATE_DATA_ROOT absent on macOS → product default              ✅
AT-FS-02  Linux XDG_DATA_HOME set → XDG-based product default                     ✅
AT-FS-03  Linux XDG_DATA_HOME absent/empty → ~/.local/share/julia-ai              ✅
AT-FS-04  JULIA_PRIVATE_DATA_ROOT="" → ROOT_CONFIG_EMPTY → zero fallback          ✅
AT-FS-05  explicit relative path → rejected → CWD irrelevant                      ✅
AT-FS-06  valid explicit absolute root → selected → OS default never touched      ✅
AT-FS-07  explicit root cannot open/create → fail closed → no fallback            ✅
AT-FS-08  root inside Git worktree → rejected                                     ✅
AT-FS-09  symlink resolves into Git worktree → rejected                           ✅
AT-FS-10  candidate path is existing regular file → rejected                      ✅
AT-FS-11  existing non-empty directory without marker → ROOT_UNOWNED_NONEMPTY     ✅
AT-FS-12  existing empty directory → bootstrap allowed                            ✅
AT-FS-13  valid existing READY marker → same storage_root_id → idempotent resolve ✅
AT-FS-14  crash during BOOTSTRAPPING → retry resumes → same storage_root_id       ✅
AT-FS-15  corrupt marker → fail closed → no marker regeneration                   ✅
AT-FS-16  future/unsupported marker schema → fail closed                          ✅
AT-FS-17  two concurrent bootstrap attempts → one storage_root_id → one READY root ✅
AT-FS-18  existing overly broad permissions → safely harden OR fail closed        ✅
AT-FS-19  root creation succeeds but durability barrier fails → ROOT_READY false  ✅
AT-FS-20  resolver invoked from different CWD/process → identical canonical root  ✅
AT-FS-21  ~/.julia exists → never selected as fallback                            ✅
AT-FS-22  repo/data exists → never selected as fallback                           ✅
AT-FS-23  BOOTSTRAPPING marker + partial reserved dirs → deterministic reconcile → READY ✅
AT-FS-24  storage_root_id presented as Julia/user/conversation identity → contract violation ✅
```

## Freeze matrix

| Item | Decision |
|---|---|
| Resolver owner | Julia-AI-Assistant |
| Resolver count | exactly one |
| Core knows path | ❌ |
| env absent | OS default |
| env "" | FAIL CLOSED |
| explicit nonempty | explicit only |
| silent fallback | ❌ |
| relative path | ❌ |
| CWD-dependent resolution | ❌ |
| `~` home expansion | ✅ |
| arbitrary env interpolation | ❌ |
| symlink | ✅ canonicalize then validate |
| inside Git worktree | ❌ |
| existing file | ❌ |
| existing empty directory | bootstrap |
| existing unmarked nonempty dir | ❌ |
| marker | `.julia-root.json` |
| physical root ID | stable UUID |
| root ID = Julia identity | ❌ |
| bootstrap states | BOOTSTRAPPING → READY |
| crash recovery | deterministic |
| concurrent bootstrap | serialized |
| POSIX privacy | dirs ≤0700 / files ≤0600 |
| unsafe broad permissions | harden safely or fail |
| marker corrupt | fail closed |
| default fallback to ~/.julia | ❌ |
| default fallback to repo/data | ❌ |

## Resolver / implementation notes (not contract changes)

1. **Marker transitions are D0-03-class durable writes**: both the `BOOTSTRAPPING` and `READY` marker writes must use `write + flush + fsync` (not just an in-memory "atomic update"). `ROOT_READY` must not be reported until the READY marker has crossed the durability barrier (AT-FS-19 tests this; the marker fsync itself is the boundary).
2. **Valid-READY-marker + missing reserved dirs → idempotent reconcile, NOT fail-closed**: distinguish "valid marker with drift" (recreate missing reserved directories, same `storage_root_id`) from "corrupt/incompatible marker" (fail closed per F1-I09). A READY marker whose `memory/` was manually removed is drift, not corruption.

## Document status vocabulary

- FROZEN: contract accepted and sealed (current).
- (ACTIVE retained only for the D0 register's pre-closeout phase; not used here.)
