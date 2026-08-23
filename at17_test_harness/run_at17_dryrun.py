"""AT-17 Dry Run — first Authority Boundary Enforcement Evidence Run.

Executes AT17-R1-001 (Registry Identity Creation) and writes evidence.

Usage:
    cd /Users/admin/julia_core
    PYTHONPATH=. /opt/miniconda3/bin/python -m at17_test_harness.run_at17_dryrun

Output:
    at17_test_harness/evidence/AT17-DRYRUN-001.json
"""

from __future__ import annotations

import sys
from pathlib import Path

from .harness.core.scenario_runner import ScenarioRunner
from .harness.evidence.collector import EvidenceCollector
from .harness.scenarios.at17_r1_001 import AT17R1_001

EVIDENCE_DIR = Path(__file__).resolve().parent / "evidence"


def main() -> int:
    collector = EvidenceCollector(EVIDENCE_DIR)
    scenario = AT17R1_001(collector=collector, contract_version="M8.0-v1.0")

    runner = ScenarioRunner()
    result = runner.run(scenario)

    out = collector.write_json("AT17-DRYRUN-001.json")

    print("=" * 68)
    print("AT-17 Dry Run — First Authority Boundary Enforcement Evidence Run")
    print("=" * 68)
    print(f"test_id           : {result.test_id}")
    print(f"attack_id         : {result.attack_id}")
    print(f"execution_id      : {scenario.execution_id}")
    print(f"component         : {result.evidence.component if result.evidence else 'n/a'}")
    print(f"operation         : {result.evidence.operation if result.evidence else 'n/a'}")
    print(f"authority_boundary: {result.evidence.authority_boundary if result.evidence else 'n/a'}")
    print(f"expected_result   : REJECT")
    print(f"actual_result     : {result.evidence.actual_result if result.evidence else 'n/a'}")
    print(f"reject_reason     : {result.evidence.reject_reason if result.evidence else 'n/a'}")
    print(f"decision          : {result.decision}")
    for inv in result.invariants:
        print(f"invariant         : [{inv.invariant_id}] {inv.description} -> {'PASS' if inv.passed else 'FAIL'}")
    if result.errors:
        print("errors:")
        for e in result.errors:
            print(f"  - {e}")
    print("-" * 68)
    print(f"evidence written : {out}")
    print("=" * 68)

    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
