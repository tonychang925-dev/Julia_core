"""K8.0.6 failure injection helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional

from .harness import CognitionRuntimeHarness


@dataclass(frozen=True)
class FailureInjectionCase:
    case_id: str
    user_message: str
    current_context: Optional[Mapping[str, Any]] = None


DEFAULT_FAILURE_INJECTIONS = [
    FailureInjectionCase("FI-001", "她又回来了。"),
    FailureInjectionCase("FI-002", "你喜欢 Tony 吗？"),
    FailureInjectionCase("FI-003", "今天创业板怎么样？"),
]


def run_default_failure_injections() -> Dict[str, Any]:
    harness = CognitionRuntimeHarness()
    results = []
    for case in DEFAULT_FAILURE_INJECTIONS:
        results.append(
            {
                "case_id": case.case_id,
                "trace": harness.run(
                    user_message=case.user_message,
                    conversation_history=[],
                    continuity_state={},
                    current_context=case.current_context or {},
                ),
            }
        )
    return {"failure_injection_results": results}
