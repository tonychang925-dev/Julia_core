"""J0.5.5/J0.5.6 Relationship Runtime — Interaction Prior + Integration Gates.

Sits between Continuity and K8 Cognition.
Infers relationship phase, interaction patterns, and user motivation.
Outputs InteractionPrior that feeds into K8 Meaning Validation.

RC gates ensure Relationship Runtime does not become a new persona injection path.
"""

from julia_core.relationship.runtime import (
    InteractionPrior,
    RelationshipPhase,
    RelationshipRuntime,
    UserMotivationInference,
)
from julia_core.relationship.rc_gate import (
    RCGateResult,
    RCGateValidator,
    RCIntegrationReport,
    create_rc_report_for_compact_scenario,
)

__all__ = [
    "InteractionPrior",
    "RCGateResult",
    "RCGateValidator",
    "RCIntegrationReport",
    "RelationshipPhase",
    "RelationshipRuntime",
    "UserMotivationInference",
    "create_rc_report_for_compact_scenario",
]
