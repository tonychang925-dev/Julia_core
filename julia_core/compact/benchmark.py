"""K6 Experience-aware Compact Survival Benchmark."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from statistics import mean
from typing import Any, Mapping

from julia_core.compact.recovery import CompactRecoveryEngine, CompactRecoveryResult
from julia_core.compact.simulator import CompactStateSimulator

ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = ROOT / "artifacts" / "compact" / "compact_survival_report_v1.json"


@dataclass(frozen=True, slots=True)
class CompactSurvivalReport:
    version: str
    status: str
    principle: str
    results: tuple[CompactRecoveryResult, ...]
    comparison: Mapping[str, Any]
    boundary: Mapping[str, bool] = field(
        default_factory=lambda: {
            "benchmark_stores_full_conversation": False,
            "benchmark_mutates_identity": False,
            "benchmark_writes_memory": False,
            "benchmark_accepts_fabricated_experience": False,
        }
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "results", tuple(self.results))
        object.__setattr__(self, "comparison", dict(self.comparison))
        object.__setattr__(self, "boundary", dict(self.boundary))

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "status": self.status,
            "principle": self.principle,
            "results": [result.to_dict() for result in self.results],
            "comparison": dict(self.comparison),
            "boundary": dict(self.boundary),
        }


class CompactSurvivalBenchmark:
    def __init__(self) -> None:
        self.simulator = CompactStateSimulator()
        self.recovery = CompactRecoveryEngine()

    def run(self) -> CompactSurvivalReport:
        self.simulator.freeze_pre_compact_state()
        results = tuple(self.recovery.recover(case) for case in self.simulator.simulation_cases())
        by_mode = {result.mode: result for result in results}
        experience_advantage = round(by_mode["experience_aware_compact"].overall_score - by_mode["identity_aware_compact"].overall_score, 4)
        ordinary_drop = round(by_mode["experience_aware_compact"].overall_score - by_mode["ordinary_compact"].overall_score, 4)
        status = "PASS" if by_mode["experience_aware_compact"].passed and not by_mode["experience_injection_without_history"].passed and experience_advantage > 0.25 else "FAIL"
        return CompactSurvivalReport(
            version="v1",
            status=status,
            principle="Compact may compress information, but it must not erase the conditions that allow behavior continuity to emerge.",
            results=results,
            comparison={
                "experience_advantage_over_identity_only": experience_advantage,
                "experience_advantage_over_ordinary_compact": ordinary_drop,
                "mean_overall_score": round(mean(result.overall_score for result in results), 4),
            },
        )

    def write_report(self, output_path: str | Path = REPORT_PATH) -> CompactSurvivalReport:
        report = self.run()
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return report
