#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

RUBRIC_VERSION = "jic-r0-rubric-v1"
REQUIRED_SECTIONS = ("Current interpretation", "Competing hypotheses", "Counterevidence", "Missing evidence", "Falsifiers", "Source and action boundary")


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def score_output(text: str) -> dict:
    lowered = text.lower()
    missing = [field for field in ("auction", "volume", "follower", "regime") if field in lowered and ("missing" in lowered or "unavailable" in lowered)]
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    hypotheses = max(0, sum(1 for line in lines if re.match(r"^[-*]\s+|\d+\.\s+", line) and any(word in line.lower() for word in ("hypothesis", "h-a", "active", "supported", "rejected", "insufficient"))))
    falsifiers = max(0, sum(1 for line in lines if re.match(r"^[-*]\s+|\d+\.\s+", line) and any(word in line.lower() for word in ("within", "next", "if", "when"))))
    scores = {
        "strategy_transfer_without_conclusion_copy": int(all(section.lower() in lowered for section in REQUIRED_SECTIONS) and "buy" not in lowered and "sell" not in lowered),
        "fresh_judgment": int("only" in lowered and ("insufficient" in lowered or "missing" in lowered)),
        "regime_sensitivity": int("regime" in lowered),
        "counterevidence_handling": int("counterevidence" in lowered and len(missing) >= 1),
        "hypothesis_diversity": int(hypotheses >= 3),
        "falsification_quality": int(falsifiers >= 2),
    }
    return {"rubric_version": RUBRIC_VERSION, "scores": scores, "machine_readable_reasoning": {"recognized_hypothesis_rows": hypotheses, "recognized_falsifier_rows": falsifiers, "recognized_missing_families": missing}}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_directory", type=Path)
    args = parser.parse_args()
    mapping_path = args.run_directory / "mapping.sealed.json"
    if not mapping_path.exists():
        print(json.dumps({"status": "BLOCKED", "reason": "run is incomplete or mapping is absent"}, ensure_ascii=False))
        return 2
    records = []
    for raw_path in sorted((args.run_directory / "raw").glob("*.json")):
        raw = load_json(raw_path)
        records.append({"response_key": raw["response_key"], **score_output(raw["verbatim_output"])})
    mapping = load_json(mapping_path)
    by_key = {record["response_key"]: record for record in records}
    joined = [{**entry, **by_key[entry["response_key"]]} for entry in mapping]
    aggregate = defaultdict(lambda: defaultdict(int))
    for entry in joined:
        for metric, score in entry["scores"].items():
            aggregate[entry["condition"]][metric] += score
    result = {"status": "COMPLETE", "rubric_version": RUBRIC_VERSION, "records": joined, "aggregate": {key: dict(value) for key, value in aggregate.items()}}
    output = args.run_directory / "evaluation.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
