# CR-CONSTITUTION-01 — NO CRITICAL FALLBACK (NCF-1)

## Rule

When a critical production dependency is unavailable, invalid, unauthenticated, or cannot prove its authority, the owning boundary must return a typed non-success outcome or stop startup. It must not continue with a mock, fake, stub, fixture, in-memory substitute, legacy implementation, alternate authority, synthetic success, ambient executable, guessed provenance, or test mode.

Critical domains include identity, persona, conversation, memory, context, Market, databases, providers, D1, WebSearch, WebFetch, C1, C2, evidence, strategy assets, runtime composition, launchers, authentication, and provenance.

## Severity and enforcement

- `P0`: reject and block release.
- `P1`: reject.
- `P2`: review required; may be reported without failing unless the gate is explicitly strict.
- `P3`: safe test-only fixture with no production reachability.

New `P0` and `P1` findings always fail. Existing accepted debt may remain only as an exact fingerprint in `ncf-baseline.json`; modifying or expanding that debt fails. Baseline entries never disappear from the report and require `EXPLICIT_TONY_AUTHORIZATION` to add.

## Preselection is not fallback

The preselected plan `[A,B,C]` may continue with `B` and `C` after `A` fails. No new authority or implementation is selected at failure time.

In contrast, `A fails → dynamically select D` is fallback. Likewise, `A fails → mock D`, `A fails → legacy D`, or `A fails → synthetic success D` violates NCF-1.

## Required outcome

Real failure must remain visible as failure. Outer success with inner unavailable/error state is prohibited. A test fixture is legitimate only when build, package, configuration, or runtime boundaries prove it cannot be imported or selected by the canonical production path.

## Local workflow

Install hooks once:

```sh
./hooks/install-hooks.sh
```

Check the entire repository:

```sh
python3 tools/no_critical_fallback_gate.py --repo Julia_core --baseline ncf-baseline.json
```

The bootstrap baseline records 22 accepted findings: 6 `P1` and 16 `P2`. Updating it requires the authorization token and is reviewable as a change to `ncf-baseline.json`:

```sh
python3 tools/no_critical_fallback_gate.py --repo Julia_core --baseline ncf-baseline.json \
  --update-baseline \
  --authorization EXPLICIT_TONY_GO_NCF_A5_LOCAL_CODEX_CI_GITHUB_ENFORCEMENT
```

The commit hook checks staged production files; the push hook scans the repository and runs governance sabotage tests. CI runs the same authority independently of local hooks.

## Exceptions

Only `EXPLICIT_TONY_AUTHORIZATION` may waive or add baseline debt. No ordinary reviewer, agent, or green unrelated test may convert a `P0/P1` fallback into acceptance.
