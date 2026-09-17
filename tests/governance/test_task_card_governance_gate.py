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

BASE = "8c17edb596622e23aecb29b27bb50e3055ed2071"


def permission_matrix() -> str:
    return f"""
AGENT_EXECUTION_PERMISSION_MATRIX
PERMISSION_MODEL
= DEFAULT_DENY
PERMISSION_REPOSITORY
= tonychang925-dev/Julia_core
PERMISSION_BASE_SHA
= {BASE}
PERMISSION_TARGET_BRANCH
= task/test-01
READ_SCOPE
= exact authorized sources
WRITE_SCOPE
= tools/example.py
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
"""


def valid_card(*, task_type: str = "STANDARD") -> str:
    body = f"""
TASK_ID
= TEST-01
TASK_TYPE
= {task_type}
REPO
= tonychang925-dev/Julia_core
BASE_SHA
= {BASE}
TARGET_BRANCH
= task/test-01
CONTROL_PLANE_COMPATIBILITY_VERSION
= 1
CONTROL_PLANE_SHA_OBSERVED
= {BASE}
CURRENT_PHASE
= RC4
RULE11_CLASSIFICATION
= A
FROZEN_AUTHORITY_BINDING
= DEVELOPMENT_CONSTITUTION.md + frozen authority
ARCHITECTURE_DELTA
= NONE
TARGET_REQUIREMENT
= bounded implementation
SEMANTIC_ATOM
= one invariant closure
VALID_MERGE_END_STATE
= main remains complete and valid
DEFERRED_FINDINGS
= NONE
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
{permission_matrix()}
TASK_CARD_AUTHOR_SELF_CHECK
AUTHOR_ROLE
= Mira
TASK_ID
= TEST-01
TASK_CARD_VERSION
= v1
AUTHORITY_SOURCE_FILES_CHECKED
= constitution + frozen authority
CURRENT_MAIN_SHAS
= Julia_core={BASE}
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
    if task_type == "CROSS_BOUNDARY":
        body += """
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
    def test_valid_standard_card_passes(self):
        self.assertEqual(mod.validate_task_card(valid_card()), [])

    def test_missing_semantic_atom_fails(self):
        text = valid_card().replace("SEMANTIC_ATOM\n= one invariant closure\n", "")
        errors = mod.validate_task_card(text)
        self.assertTrue(any("SEMANTIC_ATOM" in e for e in errors))

    def test_missing_valid_merge_end_state_fails(self):
        text = valid_card().replace("VALID_MERGE_END_STATE\n= main remains complete and valid\n", "")
        errors = mod.validate_task_card(text)
        self.assertTrue(any("VALID_MERGE_END_STATE" in e for e in errors))

    def test_architecture_delta_must_be_none(self):
        text = valid_card().replace("ARCHITECTURE_DELTA\n= NONE", "ARCHITECTURE_DELTA\n= NEW_OWNER")
        errors = mod.validate_task_card(text)
        self.assertTrue(any("ARCHITECTURE_DELTA must be NONE" in e for e in errors))

    def test_missing_permission_matrix_fails(self):
        errors = mod.validate_task_card(valid_card().replace(permission_matrix(), ""))
        self.assertTrue(any("missing AGENT_EXECUTION_PERMISSION_MATRIX" in e for e in errors))

    def test_architecture_mutation_cannot_be_allowed(self):
        text = valid_card().replace("ARCHITECTURE_MUTATION\n= DENY", "ARCHITECTURE_MUTATION\n= ALLOW")
        errors = mod.validate_task_card(text)
        self.assertTrue(any("ARCHITECTURE_MUTATION must be DENY" in e for e in errors))

    def test_permission_identity_must_match_task_identity(self):
        text = valid_card().replace(f"PERMISSION_BASE_SHA\n= {BASE}", "PERMISSION_BASE_SHA\n= " + "0" * 40)
        errors = mod.validate_task_card(text)
        self.assertTrue(any("PERMISSION_BASE_SHA must exactly equal BASE_SHA" in e for e in errors))

    def test_residual_architecture_decision_fails(self):
        text = valid_card().replace("RESIDUAL_ARCHITECTURE_DECISIONS\n= 0", "RESIDUAL_ARCHITECTURE_DECISIONS\n= 1")
        errors = mod.validate_task_card(text)
        self.assertTrue(any("RESIDUAL_ARCHITECTURE_DECISIONS must be 0" in e for e in errors))

    def test_invalid_rule11_token_fails(self):
        text = valid_card().replace("RULE11_CLASSIFICATION\n= A", "RULE11_CLASSIFICATION\n= AUTHORITY_A")
        errors = mod.validate_task_card(text)
        self.assertTrue(any("illegal value" in e for e in errors))

    def test_keyword_does_not_infer_cross_boundary(self):
        text = valid_card() + "\nThe future adapter is explicitly deferred.\n"
        self.assertEqual(mod.validate_task_card(text), [])

    def test_cross_boundary_task_requires_mappings(self):
        text = valid_card(task_type="CROSS_BOUNDARY")
        text = text.replace("FIELD_MAPPING\n= exact\n", "")
        errors = mod.validate_task_card(text)
        self.assertTrue(any("cross-boundary task missing frozen mappings" in e for e in errors))

    def test_cross_boundary_task_passes_when_complete(self):
        self.assertEqual(mod.validate_task_card(valid_card(task_type="CROSS_BOUNDARY")), [])

    def test_old_new_count_fields_are_not_mandatory(self):
        self.assertNotIn("NEW_OWNER_COUNT", mod.MANDATORY_SELF_CHECK_FIELDS)
        self.assertEqual(mod.validate_task_card(valid_card()), [])


if __name__ == "__main__":
    unittest.main()
