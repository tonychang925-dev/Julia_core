"""Wave5 test-local conftest.

Makes the test-only `support/` compatibility modules importable as
`from conversation_management import ...` without depending on a `tests`
package resolution. (A third-party `tests` package inside the environment's
site-packages shadows the repository's namespace package, so `tests.wave5.*`
absolute imports are unreliable here.)

TEST SUPPORT ONLY — no production runtime authority is introduced.
"""
import sys
from pathlib import Path

SUPPORT_DIR = Path(__file__).resolve().parent / "support"
if str(SUPPORT_DIR) not in sys.path:
    sys.path.insert(0, str(SUPPORT_DIR))
