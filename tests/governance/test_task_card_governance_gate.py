from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "tools" / "task_card_governance_gate.py"
spec = importlib.util.spec_from_file_location("task_card_governance_gate", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


def valid_card(*, cross_boundary: bool = False) -> str:
    cross_value = "PASS" if cross_boundary else "N/A"
    body = f"""
FROZEN_AUTHORITY_TRACE
= DEVELOPMENT_CONSTITUTION.md Rule 11
RULE11_CLASSIFICATION
= A
CURRENT_PHASE
= RC4 / Stage B
TARGET_REQUIREMENT
= bounded implementation
DEFERRED_FINDINGS
= NONE
TASK_ID
= TEST-01
REPO
= tonychang925-dev/Julia_core
TARGET_BRANCH
= task/test-01
BASE_SHA
= 7534f233a79e443ed05de4cbf6cbaaa02d22d85b
AUTHORIZED_PATHS
= tools/example.py
FORBIDDEN_PATHS
= EVERYTHING ELSE
REQUIRED_BEHAVIOR
= implement exact frozen behavior
FORBIDDEN_BEHAVIOR
= no scope expansion
ACCEPTANCE_EVIDENCE
= exact candidate SHA + focused tests

TASK_CARD_AUTHOR_SELF_CHECK
AUTHOR_ROLE
= Mira
TASK_ID
= TEST-01
TASK_CARD_VERSION
= v0.1
AUTHORITY_SOURCE_FILES_CHECKED
= DEVELOPMENT_CONSTITUTION.md
CURRENT_MAIN_SHAS
= Julia_core=7534f233a79e443ed05de4cbf6cbaaa02d22d85b
MANDATORY_TASK_FIELDS_PRESENT
= 14/14
AUTHORIZED_PATH_COUNT
= 1
DEFERRED_FINDING_COUNT
= 0
AUTHORITY_IDENTITY
= PASS
MANDATORY_HEADER
= PASS
RULE11_CLASSIFICATION_CHECK
= PASS
PHASE_SCOPE_CHECK
= PASS
RESIDUAL_DECISION_AUDIT
= PASS
RESIDUAL_ARCHITECTURE_DECISIONS
= 0
RESIDUAL_CONTRACT_SEMANTIC_DECISIONS
= 0
CROSS_BOUNDARY_SEMANTICS
= {cross_value}
CURRENT_CODE_COMPATIBILITY
= PASS
ACCEPTANCE_EVIDENCE_CHECK
= PASS
NO_AGENT_ARCHITECTURE_DISCRETION
= PASS
SELF_CHECK_RESULT
= PASS
READY_FOR_SUBMISSION
= YES
"""
    if cross_boundary:
        body += """
adapter
SOURCE_CONTRACT
= source v1
TARGET_CONTRACT
= target v1
FIELD_MAPPING
= exact
STATUS_MAPPING
= exact
FAILURE_MAPPING
= exact
PROVENANCE_MAPPING
= exact
AUTHORITY_TRANSFER
= NONE
MALFORMED_INPUT_BEHAVIOR
= fail closed
UNKNOWN_VALUE_BEHAVIOR
= fail closed
LIFECYCLE_OWNERSHIP
= frozen owner
"""
    return body


class TaskCardGovernanceGateTests(unittest.TestCase):
    def test_valid_non_boundary_card_passes(self):
        self.assertEqual(mod.validate_task_card(valid_card()), [])

    def test_missing_self_check_fails(self):
        text = valid_card().replace("TASK_CARD_AUTHOR_SELF_CHECK", "")
        errors = mod.validate_task_card(text)
        self.assertTrue(any("missing TASK_CARD_AUTHOR_SELF_CHECK" in e for e in errors))

    def test_residual_semantic_decision_fails(self):
        text = valid_card().replace(
            "RESIDUAL_CONTRACT_SEMANTIC_DECISIONS\n= 0",
            "RESIDUAL_CONTRACT_SEMANTIC_DECISIONS\n= 1",
        )
        errors = mod.validate_task_card(text)
        self.assertTrue(any("RESIDUAL_CONTRACT_SEMANTIC_DECISIONS must be 0" in e for e in errors))

    def test_invalid_rule11_token_fails(self):
        text = valid_card().replace("RULE11_CLASSIFICATION\n= A", "RULE11_CLASSIFICATION\n= AUTHORITY_A")
        errors = mod.validate_task_card(text)
        self.assertTrue(any("illegal value" in e for e in errors))

    def test_cross_boundary_card_requires_mappings(self):
        text = valid_card().replace("CROSS_BOUNDARY_SEMANTICS\n= N/A", "CROSS_BOUNDARY_SEMANTICS\n= PASS") + "\nadapter\n"
        errors = mod.validate_task_card(text)
        self.assertTrue(any("cross-boundary task missing frozen mappings" in e for e in errors))

    def test_cross_boundary_card_passes_when_complete(self):
        self.assertEqual(mod.validate_task_card(valid_card(cross_boundary=True)), [])

    def test_base_sha_must_be_exact(self):
        text = valid_card().replace(
            "BASE_SHA\n= 7534f233a79e443ed05de4cbf6cbaaa02d22d85b",
            "BASE_SHA\n= main",
        )
        errors = mod.validate_task_card(text)
        self.assertTrue(any("BASE_SHA must be an exact 40-hex SHA" in e for e in errors))

    def test_author_pass_claim_cannot_hide_failure(self):
        text = valid_card().replace("PHASE_SCOPE_CHECK\n= PASS", "PHASE_SCOPE_CHECK\n= FAIL")
        errors = mod.validate_task_card(text)
        self.assertTrue(any("PHASE_SCOPE_CHECK must be PASS" in e for e in errors))

    def test_control_plane_template_is_not_misclassified_as_task_card(self):
        self.assertFalse(
            mod.looks_like_task_card(
                "docs/governance/RD1_TASK_CARD_AUTHOR_PRE_SUBMISSION_SELF_CHECK.md",
                "TASK_CARD_AUTHOR_SELF_CHECK\nTASK_ID\nBASE_SHA\nREPO",
            )
        )


if __name__ == "__main__":
    unittest.main()
