from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


def load_module(name: str, rel: str):
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


task_gate = load_module("task_card_governance_gate_review", "tools/task_card_governance_gate.py")
fresh_gate = load_module("control_plane_freshness_gate_review", "tools/control_plane_freshness_gate.py")

BASE = "a" * 40
CONTROL = "b" * 40


def minimal_card() -> str:
    return f"""
TASK_ID
= TEST-REVIEW
TASK_TYPE
= STANDARD
REPO
= tonychang925-dev/ai_theme_app
BASE_SHA
= {BASE}
TARGET_BRANCH
= task/test-review
CONTROL_PLANE_COMPATIBILITY_VERSION
= 1
CONTROL_PLANE_SHA_OBSERVED
= {CONTROL}
CURRENT_PHASE
= RC4
RULE11_CLASSIFICATION
= A
FROZEN_AUTHORITY_BINDING
= frozen source
ARCHITECTURE_DELTA
= NONE
TARGET_REQUIREMENT
= bounded
SEMANTIC_ATOM
= one invariant closure
VALID_MERGE_END_STATE
= complete
DEFERRED_FINDINGS
= NONE
AUTHORIZED_PATHS
= a.py
FORBIDDEN_PATHS
= EVERYTHING ELSE
REQUIRED_BEHAVIOR
= bounded
FORBIDDEN_BEHAVIOR
= no expansion
ACCEPTANCE_EVIDENCE
= exact candidate SHA + tests
AGENT_EXECUTION_PERMISSION_MATRIX
PERMISSION_MODEL
= DEFAULT_DENY
PERMISSION_REPOSITORY
= tonychang925-dev/ai_theme_app
PERMISSION_BASE_SHA
= {BASE}
PERMISSION_TARGET_BRANCH
= task/test-review
READ_SCOPE
= bounded
WRITE_SCOPE
= a.py
ARCHITECTURE_MUTATION
= DENY
PUBLIC_CONTRACT_MUTATION
= DENY
CROSS_BOUNDARY_SEMANTIC_DECISION
= DENY
DEPENDENCY_MUTATION
= DENY
TEST_CREATION
= BOUNDED_TO_ACCEPTANCE_EVIDENCE
BRANCH_CREATION
= EXACT_TARGET_ONLY
COMMIT
= TASK_BRANCH_ONLY
PR_CREATION
= ALLOW
MERGE
= DENY
RELEASE
= DENY
DEPLOY
= DENY
PRODUCTION_MUTATION
= DENY
FALLBACK
= DENY
SYNTHETIC_SUCCESS
= DENY
FUTURE_PHASE_SCOPE
= DENY
TASK_CARD_AUTHOR_SELF_CHECK
AUTHOR_ROLE
= Mira
TASK_ID
= TEST-REVIEW
TASK_CARD_VERSION
= v1
AUTHORITY_SOURCE_FILES_CHECKED
= frozen source
CURRENT_MAIN_SHAS
= ai_theme_app={BASE}
SELF_CHECK_CONTROL_PLANE_COMPATIBILITY_VERSION
= 1
AUTHORITY_GATE
= PASS
SEMANTIC_ATOMICITY_GATE
= PASS
PERMISSION_GATE
= PASS
RESIDUAL_ARCHITECTURE_DECISIONS
= 0
RESIDUAL_CONTRACT_SEMANTIC_DECISIONS
= 0
SELF_CHECK_RESULT
= PASS
READY_FOR_SUBMISSION
= YES
"""


class ConsolidationReviewRegressionTests(unittest.TestCase):
    def test_blank_task_type_is_rejected(self):
        text = minimal_card().replace("TASK_TYPE\n= STANDARD", "TASK_TYPE")
        errors = task_gate.validate_task_card(text)
        self.assertTrue(any("TASK_TYPE must have a nonempty value" in e for e in errors))

    def test_task_and_self_check_compatibility_versions_must_match(self):
        text = minimal_card().replace(
            "SELF_CHECK_CONTROL_PLANE_COMPATIBILITY_VERSION\n= 1",
            "SELF_CHECK_CONTROL_PLANE_COMPATIBILITY_VERSION\n= 2",
        )
        errors = task_gate.validate_task_card(text)
        self.assertTrue(any("must exactly equal" in e for e in errors))

    def test_non_governance_tools_are_not_normative_transition_paths(self):
        self.assertFalse(fresh_gate.is_normative_governance_path("tools/continuity/example.py"))
        self.assertFalse(fresh_gate.is_normative_governance_path("tools/mira_migration/example.py"))

    def test_governance_gate_tools_are_normative_transition_paths(self):
        self.assertTrue(fresh_gate.is_normative_governance_path("tools/control_plane_freshness_gate.py"))
        self.assertTrue(fresh_gate.is_normative_governance_path("tools/task_card_governance_gate.py"))

    def test_root_constitution_and_index_are_normative_transition_paths(self):
        self.assertTrue(fresh_gate.is_normative_governance_path("DEVELOPMENT_CONSTITUTION.md"))
        self.assertTrue(fresh_gate.is_normative_governance_path("RD1_ARCHITECTURE_AUTHORITY_INDEX.md"))


if __name__ == "__main__":
    unittest.main()
