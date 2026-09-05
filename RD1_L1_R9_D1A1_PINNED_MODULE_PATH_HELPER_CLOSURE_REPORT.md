# RD1-L1-R9-D1A.1 Pinned Module Path Helper Closure

## Source state

- Base SHA: `abcff9e60dd11f02e8fe95b9e07ec12f2b09da22`
- Source closure SHA: `ce2455f52207db4c116b48a11bb838e1236a0947`
- Branch: `glm-d/rd1-l1-r9-d1a1-pinned-module-path-fix`

## Defect and fix

The nested controlled-runtime helper built `package_path` as:

```text
<root>/<package>/__init__.py
```

but then incorrectly tested and returned:

```text
<root>/<package>/__init__.py/__init__.py
```

The fix changes the fallback to test `package_path.is_file()` and return `package_path.resolve()`.

Normal module resolution remains:

```text
package.submodule → <root>/package/submodule.py
```

Package resolution now correctly returns:

```text
package.subpackage → <root>/package/subpackage/__init__.py
```

Missing modules continue to raise `RuntimeError`; no fuzzy lookup was added.

## Functional proof

The focused test extracts the exact nested production helper and executes it against a temporary root containing:

```text
example_pkg/__init__.py
example_pkg/module.py
example_pkg/child/__init__.py
```

It proves:

```text
MODULE_FILE_RESOLUTION = PASS
PACKAGE_INIT_RESOLUTION = PASS
MISSING_MODULE_FAILS_CLOSED = YES
```

## Changed files

```text
julia_core/runtime/capability_bridge.py
tests/runtime/test_r9_d1a_market_db_source_identity.py
```

Only one Core production file changed. No Market source, frozen identity, DB runtime identity, SQL, runtime architecture, or composition behavior changed.

## Verification

```text
/opt/miniconda3/bin/pytest -q tests/runtime/test_r9_d1a_market_db_source_identity.py tests/runtime/test_r9_d1_canonical_market_provider_composition.py
11 passed in 57.63s

/opt/miniconda3/bin/python -m compileall -q julia_core/runtime/capability_bridge.py tests/runtime/test_r9_d1a_market_db_source_identity.py
PASS

git diff --check
PASS
```

Execution counts:

```text
USER_TURNS = 0
REAL_RESOLVER_EXECUTIONS = 0
MARKET_EVENT_READ_EXECUTIONS = 0
D1_EXECUTIONS = 0
DB_WRITES = 0
```

## Gate

```text
SOURCE_SCOPE = PASS
PACKAGE_INIT_PATH_BUG_FIXED = YES
FOCUSED_TESTS = PASS
R9_D1A_1_READY_TO_CLOSE = YES
R9_D2_READY = YES
R9_D2_AUTHORIZED = NO
R10_READY = NO
R10_AUTHORIZED = NO
VERDICT = PASS
```
