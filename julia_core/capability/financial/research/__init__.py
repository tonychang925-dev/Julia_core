"""Julia Strategy Research Compiler — Card → ResearchPlan → CapabilityRequest.

ADR-032/033: Compiles ai_theme_app StrategyCards into executable Julia ResearchPlans.
Deterministic. Zero LLM. Owns: requirement binding, evidence bundle creation.

M3.3.0: Adds CognitiveLoopOrchestrator — autonomous recursive research runtime.
"""

from julia_core.capability.financial.research.orchestrator import (
    CognitiveLoopConfig,
    CognitiveLoopOrchestrator,
    CognitiveLoopResult,
    ConstraintViolation,
    RoundRecord,
)
