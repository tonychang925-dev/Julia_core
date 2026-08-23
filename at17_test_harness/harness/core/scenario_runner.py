"""Scenario runner — unified attack execution flow.

    Scenario → Setup → Inject Attack → Capture Boundary Response →
    Verify Invariant → Store Evidence

The scenario runner must not define identity, approve evolution, or modify
continuity. It only injects, observes, and records.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .invariant_checker import InvariantResult
from ..evidence.schema import EvidenceRecord


@dataclass
class ScenarioResult:
    test_id: str
    attack_id: str
    decision: str                    # PASS | FAIL
    evidence: EvidenceRecord | None = None
    invariants: list[InvariantResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.decision == "PASS"


class ScenarioRunner:
    """Executes one AT-17 scenario and returns a normalized result."""

    def run(self, scenario) -> ScenarioResult:
        """Run a scenario object exposing: test_id, attack_id, execute(runner, result)."""
        result = ScenarioResult(
            test_id=scenario.test_id,
            attack_id=scenario.attack_id,
            decision="PASS",
        )
        try:
            scenario.execute(self, result)
        except Exception as exc:  # noqa: BLE001 — scenario failure surfaces as FAIL
            result.decision = "FAIL"
            result.errors.append(f"{type(exc).__name__}: {exc}")
        return result
