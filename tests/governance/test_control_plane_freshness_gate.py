from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "tools" / "control_plane_freshness_gate.py"
spec = importlib.util.spec_from_file_location("control_plane_freshness_gate", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

CURRENT = "e" * 40
OLD = "f" * 40


def card(sha: str = CURRENT) -> str:
    return f"""
TASK_ID
= TEST-01
REPO
= tonychang925-dev/ai_theme_app
BASE_SHA
= {'a' * 40}
TASK_CARD_AUTHOR_SELF_CHECK
CONTROL_PLANE_AUTHORITY_REPO
= tonychang925-dev/Julia_core
SELF_CHECK_CONTROL_PLANE_SHA
= {sha}
CONTROL_PLANE_FRESHNESS_CHECK
= PASS
"""


class ControlPlaneFreshnessGateTests(unittest.TestCase):
    def test_current_control_plane_passes(self):
        self.assertEqual(
            mod.validate_task_card(card(), current_control_plane_sha=CURRENT), []
        )

    def test_stale_control_plane_sha_fails(self):
        errors = mod.validate_task_card(card(OLD), current_control_plane_sha=CURRENT)
        self.assertTrue(any("CONTROL_PLANE_DRIFT" in e for e in errors))

    def test_missing_control_plane_sha_fails(self):
        text = card().replace(f"SELF_CHECK_CONTROL_PLANE_SHA\n= {CURRENT}\n", "")
        errors = mod.validate_task_card(text, current_control_plane_sha=CURRENT)
        self.assertTrue(any("missing SELF_CHECK_CONTROL_PLANE_SHA" in e for e in errors))

    def test_non_exact_control_plane_sha_fails(self):
        text = card().replace(CURRENT, "main")
        errors = mod.validate_task_card(text, current_control_plane_sha=CURRENT)
        self.assertTrue(any("must be exact 40-hex" in e for e in errors))

    def test_freshness_claim_must_pass(self):
        text = card().replace("CONTROL_PLANE_FRESHNESS_CHECK\n= PASS", "CONTROL_PLANE_FRESHNESS_CHECK\n= FAIL")
        errors = mod.validate_task_card(text, current_control_plane_sha=CURRENT)
        self.assertTrue(any("must be PASS" in e for e in errors))

    def test_control_plane_repo_is_fixed(self):
        text = card().replace("tonychang925-dev/Julia_core", "tonychang925-dev/ai_theme_app", 1)
        errors = mod.validate_task_card(text, current_control_plane_sha=CURRENT)
        self.assertTrue(any("CONTROL_PLANE_AUTHORITY_REPO must be" in e for e in errors))

    def test_control_plane_doc_not_misclassified_as_task_card(self):
        self.assertFalse(
            mod.looks_like_task_card(
                "docs/governance/RD1_CONTROL_PLANE_FRESHNESS_GATE.md",
                "TASK_ID\nBASE_SHA\nREPO\nTASK_CARD_AUTHOR_SELF_CHECK",
            )
        )


if __name__ == "__main__":
    unittest.main()
