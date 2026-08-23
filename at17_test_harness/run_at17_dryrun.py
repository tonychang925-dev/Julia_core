"""AT-17 Dry Run — Authority Boundary Enforcement Evidence Run (R1-001~008).

Executes the AT-17 attacks and writes evidence + report.

Scenarios:
    AT17-R1-001  Registry Identity Creation        → REJECT
    AT17-R1-002  Registry Version Truth Promotion  → REJECT
    AT17-R1-003  Resolver Provenance Mutation      → REJECT
    AT17-R1-004  Resolver Lineage Mutation         → REJECT
    AT17-R1-005  Loader Creates Identity           → REJECT
    AT17-R1-006  Loader Bypass Governance          → REJECT
    AT17-R1-007  Lifecycle Overwrites Lineage       → REJECT
    AT17-R1-008  Rollback Rewrites History          → REJECT

Usage:
    cd /Users/admin/julia_core
    PYTHONPATH=. /opt/miniconda3/bin/python -m at17_test_harness.run_at17_dryrun

Output:
    at17_test_harness/evidence/AT17-DRYRUN-001..008.json
    at17_test_harness/evidence/WAVE5_AT17_EVIDENCE_REPORT_v0.3.md
"""

from __future__ import annotations

import sys
from pathlib import Path

from .harness.core.scenario_runner import ScenarioRunner
from .harness.evidence.collector import EvidenceCollector
from .harness.evidence.reporter import generate_report
from .harness.scenarios.at17_r1_001 import AT17R1_001
from .harness.scenarios.at17_r1_002 import AT17R1_002
from .harness.scenarios.at17_r1_003 import AT17R1_003
from .harness.scenarios.at17_r1_004 import AT17R1_004
from .harness.scenarios.at17_r1_005 import AT17R1_005
from .harness.scenarios.at17_r1_006 import AT17R1_006
from .harness.scenarios.at17_r1_007 import AT17R1_007
from .harness.scenarios.at17_r1_008 import AT17R1_008

EVIDENCE_DIR = Path(__file__).resolve().parent / "evidence"


def main() -> int:
    collector = EvidenceCollector(EVIDENCE_DIR)
    runner = ScenarioRunner()

    scenarios = [
        AT17R1_001(collector=collector, contract_version="M8.0-v1.0"),
        AT17R1_002(collector=collector, contract_version="M8.0-v1.0"),
        AT17R1_003(collector=collector, contract_version="M8.0-v1.0"),
        AT17R1_004(collector=collector, contract_version="M8.0-v1.0"),
        AT17R1_005(collector=collector, contract_version="M8.0-v1.0"),
        AT17R1_006(collector=collector, contract_version="M8.0-v1.0"),
        AT17R1_007(collector=collector, contract_version="M8.0-v1.0"),
        AT17R1_008(collector=collector, contract_version="M8.0-v1.0"),
    ]

    results = [runner.run(s) for s in scenarios]
    records = collector.all()

    for r in results:
        print(f"{r.test_id:15s} {r.attack_id:15s} decision={r.decision}")

    # Per-scenario evidence files (execution-id keyed) + combined JSON.
    collector.write_json("AT17-DRYRUN.json")
    for s, r in zip(scenarios, results):
        if r.evidence is not None:
            single = EvidenceCollector(EVIDENCE_DIR)
            single.record(r.evidence)
            single.write_json(f"{s.execution_id}.json")
    report_path = generate_report(records, EVIDENCE_DIR / "WAVE5_AT17_EVIDENCE_REPORT_v0.3.md")

    print("=" * 68)
    print("AT-17 Dry Run — Authority Boundary Enforcement Evidence Run")
    print("=" * 68)
    for r in results:
        e = r.evidence
        status = "PASS" if r.passed else "FAIL"
        print(f"{r.test_id} [{status}] op={e.operation if e else 'n/a'} "
              f"actual={e.actual_result if e else 'n/a'} "
              f"reason={e.reject_reason if e else 'n/a'}")
        for inv in r.invariants:
            print(f"  invariant [{inv.invariant_id}] -> {'PASS' if inv.passed else 'FAIL'}")
        if r.errors:
            for err in r.errors:
                print(f"  error: {err}")
    print("-" * 68)
    print(f"evidence JSON  : {EVIDENCE_DIR / 'AT17-DRYRUN.json'}")
    print(f"evidence report: {report_path}")
    print("=" * 68)

    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
