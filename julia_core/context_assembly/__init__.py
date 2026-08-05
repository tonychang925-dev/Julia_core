"""J0.6 Context Assembly — Controlled Context Density Engine.

Historical Universe → Density Engine → Context Density Profile
   (everything)         (select)       (what fits + what's excluded)

Key distinction from Claude:
  Claude: has data → may enter context (implicit)
  Julia:  has data ≠ should enter context (explicit exclusion)

The Context Density Engine assembles per-turn context with controlled density
— not maximum density. It explicitly excludes irrelevant context, prioritizes
relationship dynamics, and computes identity competition weight to ensure
Julia's identity signal can compete against system identity.
"""

from julia_core.context_assembly.density_engine import (
    CategoryAllocation,
    ContextDensityEngine,
    ContextDensityProfile,
    ContextSource,
    DensitySelection,
    SourceCategory,
    build_identity_anchor_source,
    build_relationship_context_source,
)
from julia_core.context_assembly.cd_gate import (
    CDGateResult,
    CDGateValidator,
    CDIntegrationReport,
    create_canonical_cd_scenario,
)

__all__ = [
    "CategoryAllocation",
    "CDGateResult",
    "CDGateValidator",
    "CDIntegrationReport",
    "ContextDensityEngine",
    "ContextDensityProfile",
    "ContextSource",
    "DensitySelection",
    "SourceCategory",
    "build_identity_anchor_source",
    "build_relationship_context_source",
    "create_canonical_cd_scenario",
]
