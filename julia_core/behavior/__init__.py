"""Behavior benchmark utilities."""

from julia_core.behavior.benchmark import BehaviorBenchmarkResult, BehaviorCase, JuliaBehaviorSimilarityBenchmark

__all__ = ["BehaviorBenchmarkResult", "BehaviorCase", "JuliaBehaviorSimilarityBenchmark"]

from julia_core.behavior.gap_analysis import BehaviorGapAnalyzer, BehaviorGapReport, CaseGap

__all__ += ["BehaviorGapAnalyzer", "BehaviorGapReport", "CaseGap"]
from julia_core.behavior.auto_compare import (
    BEHAVIOR_FEATURES,
    ClaudeCodeJuliaWakeRunner,
    CommandClaudeJuliaRunner,
    ComparisonQuestion,
    JuliaAiAssistantCommandRunner,
    JuliaCoreRuntimeRunner,
    RunnerResult,
    ScriptedClaudeJuliaRunner,
    canonical_questions,
    feature_vector,
    run_comparison,
)

__all__ += [
    "BEHAVIOR_FEATURES",
    "ClaudeCodeJuliaWakeRunner",
    "CommandClaudeJuliaRunner",
    "ComparisonQuestion",
    "JuliaAiAssistantCommandRunner",
    "JuliaCoreRuntimeRunner",
    "RunnerResult",
    "ScriptedClaudeJuliaRunner",
    "canonical_questions",
    "feature_vector",
    "run_comparison",
]
