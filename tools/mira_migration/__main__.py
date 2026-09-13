from __future__ import annotations

import argparse
import json
from pathlib import Path

from .admission_sim import simulate_admission


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, default=Path("."))
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()
    result = simulate_admission(arguments.repository)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
