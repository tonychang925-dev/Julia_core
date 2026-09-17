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

BASE = "ffc28788dda461a16a2e5b4e6b013a7b6ab4e6c6"


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
= repository source needed for authorized task
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


def rule12_block() -> str:
    return """
TASK_AUTHOR_ARCHITECTURE_COMPLETION_CHECK
= PASS
FROZEN_SOURCE_BINDING_COMPLETE
= PASS
TASK_AUTHOR_NEW_ARCHITECTURE_DECISIONS
= 0
NEW_OWNER_COUNT
= 0
NEW_DOMAIN_COUNT
= 0
NEW_COMPOSITION_ROOT_COUNT
= 0
NEW_BINDING_AUTHORITY_COUNT
= 0
NEW_PACKAGE_BOUNDARY_COUNT
= 0
NEW_DEPENDENCY_DIRECTION_COUNT
= 0
NEW_RUNTIME_AUTHORITY_COUNT
= 0
NEW_TRANSPORT_COUNT
= 0
"""


def valid_card(*, cross_boundary: bool = False) -> str:
    cross_value = "PASS" if cross_boundary else "N/A"
    body = f"""
FROZEN_AUTHORITY_TRACE
= DEVELOPMENT_CONSTITUTION.md Rule 11 + Rule 12
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
= {BASE}
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
= v0.1
AUTHORITY_SOURCE_FILES_CHECKED
= DEVELOPMENT_CONSTITUTION.md + RD1_RULE12_ARCHITECTURE_COMPLETION_PROHIBITION.md
CURRENT_MAIN_SHAS
= Julia_core={BASE}
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
{rule12_block()}
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
        errors = mod.validate_task_card(valid_card().replace("TASK_CARD_AUTHOR_SELF_CHECK", ""))
        self.assertTrue(any("missing TASK_CARD_AUTHOR_SELF_CHECK" in e for e in errors))

    def test_missing_permission_matrix_fails(self):
        text = valid_card().replace(permission_matrix(), "")
        errors = mod.validate_task_card(text)
        self.assertTrue(any("missing AGENT_EXECUTION_PERMISSION_MATRIX" in e for e in errors))

    def test_architecture_mutation_cannot_be_allowed(self):
        text = valid_card().replace("ARCHITECTURE_MUTATION\n= DENY", "ARCHITECTURE_MUTATION\n= ALLOW")
        errors = mod.validate_task_card(text)
        self.assertTrue(any("ARCHITECTURE_MUTATION must be DENY" in e for e in errors))

    def test_merge_permission_cannot_be_granted(self):
        text = valid_card().replace("MERGE\n= DENY", "MERGE\n= ALLOW")
        errors = mod.validate_task_card(text)
        self.assertTrue(any("MERGE must be DENY" in e for e in errors))

    def test_permission_identity_must_match_task_identity(self):
        text = valid_card().replace(f"PERMISSION_BASE_SHA\n= {BASE}", "PERMISSION_BASE_SHA\n= " + "0" * 40)
        errors = mod.validate_task_card(text)
        self.assertTrue(any("PERMISSION_BASE_SHA must exactly equal BASE_SHA" in e for e in errors))

    def test_default_deny_is_required(self):
        text = valid_card().replace("PERMISSION_MODEL\n= DEFAULT_DENY", "PERMISSION_MODEL\n= ALLOW_UNLESS_DENIED")
        errors = mod.validate_task_card(text)
        self.assertTrue(any("PERMISSION_MODEL must be DEFAULT_DENY" in e for e in errors))

    def test_rule12_block_is_mandatory(self):
        text = valid_card().replace(rule12_block(), "")
        errors = mod.validate_task_card(text)
        self.assertTrue(any("TASK_AUTHOR_ARCHITECTURE_COMPLETION_CHECK" in e for e in errors))

    def test_rule12_author_check_must_pass(self):
        text = valid_card().replace(
            "TASK_AUTHOR_ARCHITECTURE_COMPLETION_CHECK\n= PASS",
            "TASK_AUTHOR_ARCHITECTURE_COMPLETION_CHECK\n= FAIL",
        )
        errors = mod.validate_task_card(text)
        self.assertTrue(any("TASK_AUTHOR_ARCHITECTURE_COMPLETION_CHECK must be PASS" in e for e in errors))

    def test_frozen_source_binding_must_pass(self):
        text = valid_card().replace("FROZEN_SOURCE_BINDING_COMPLETE\n= PASS", "FROZEN_SOURCE_BINDING_COMPLETE\n= FAIL")
        errors = mod.validate_task_card(text)
        self.assertTrue(any("FROZEN_SOURCE_BINDING_COMPLETE must be PASS" in e for e in errors))

    def test_task_author_cannot_introduce_architecture_decision(self):
        text = valid_card().replace("TASK_AUTHOR_NEW_ARCHITECTURE_DECISIONS\n= 0", "TASK_AUTHOR_NEW_ARCHITECTURE_DECISIONS\n= 1")
        errors = mod.validate_task_card(text)
        self.assertTrue(any("TASK_AUTHOR_NEW_ARCHITECTURE_DECISIONS must be 0" in e for e in errors))

    def test_new_composition_root_count_must_be_zero(self):
        text = valid_card().replace("NEW_COMPOSITION_ROOT_COUNT\n= 0", "NEW_COMPOSITION_ROOT_COUNT\n= 1")
        errors = mod.validate_task_card(text)
        self.assertTrue(any("NEW_COMPOSITION_ROOT_COUNT must be 0" in e for e in errors))

    def test_new_binding_authority_count_must_be_zero(self):
        text = valid_card().replace("NEW_BINDING_AUTHORITY_COUNT\n= 0", "NEW_BINDING_AUTHORITY_COUNT\n= 1")
        errors = mod.validate_task_card(text)
        self.assertTrue(any("NEW_BINDING_AUTHORITY_COUNT must be 0" in e for e in errors))

    def test_residual_semantic_decision_fails(self):
        text = valid_card().replace("RESIDUAL_CONTRACT_SEMANTIC_DECISIONS\n= 0", "RESIDUAL_CONTRACT_SEMANTIC_DECISIONS\n= 1")
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
        text = valid_card().replace(f"BASE_SHA\n= {BASE}", "BASE_SHA\n= main", 1)
        errors = mod.validate_task_card(text)
        self.assertTrue(any("BASE_SHA must be an exact 40-hex SHA" in e for e in errors))

    def test_author_pass_claim_cannot_hide_failure(self):
        text = valid_card().replace("PHASE_SCOPE_CHECK\n= PASS", "PHASE_SCOPE_CHECK\n= FAIL")
        errors = mod.validate_task_card(text)
        self.assertTrue(any("PHASE_SCOPE_CHECK must be PASS" in e for e in errors))

    def test_control_plane_template_is_not_misclassified_as_task_card(self):
        self.assertFalse(
            mod.looks_like_task_card(
                "docs/governance/RD1_AGENT_EXECUTION_PERMISSION_MATRIX.md",
                "TASK_CARD_AUTHOR_SELF_CHECK\nTASK_ID\nBASE_SHA\nREPO",
            )
        )

    def test_rule12_control_plane_doc_is_not_misclassified_as_task_card(self):
        self.assertFalse(
            mod.looks_like_task_card(
                "docs/governance/RD1_RULE12_ARCHITECTURE_COMPLETION_PROHIBITION.md",
                "TASK_AUTHOR_ARCHITECTURE_COMPLETION_CHECK\nTASK_ID\nBASE_SHA\nREPO",
            )
        )


if __name__ == "__main__":
    unittest.main()
