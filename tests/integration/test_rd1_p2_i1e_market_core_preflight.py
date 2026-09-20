from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


REPO = Path(__file__).resolve().parents[2]
RUNNER = REPO / "experiments" / "rd1_p2_i1e" / "run_preflight.py"


def test_harness_candidate_and_isolated_negative_mechanics(tmp_path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--core-repo",
            str(REPO),
            "--market-repo",
            str(REPO.parent / "ai_theme_app"),
            "--self-test",
            "--run-id",
            "pytest-isolated",
        ],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=120,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    result_path = next(line.strip() for line in completed.stdout.splitlines() if line.strip().endswith("preflight.json"))
    result = json.loads(Path(result_path).read_text(encoding="utf-8"))
    assert result["status"] == "PASS"
    outcomes = {record["outcome"] for record in result["records"]}
    assert "missing_core_market_binding" in outcomes
    assert "c08_denial_before_provider" in outcomes
    assert "pre_envelope_provider_exception" in outcomes
    assert all(record["classification"] == "ISOLATED_UNIT_ONLY" for record in result["records"])
