from __future__ import annotations

import argparse
import json
from pathlib import Path

from .compiler import compile_preview, verify_repository_binding


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, default=Path("artifacts/mira_migration_prep/MIRA_MIGRATION_PREP_PACKAGE_V1.json"))
    parser.add_argument("--ledger", type=Path, default=Path("artifacts/mira_migration_prep/MIRA_MIGRATION_EVIDENCE_LEDGER_V1.json"))
    parser.add_argument("--dry-run", type=Path, default=Path("artifacts/mira_migration_prep/MIRA_MIGRATION_DRY_RUN_RESULT_V1.json"))
    parser.add_argument("--repository", type=Path, default=Path("."))
    parser.add_argument("--schema-sha", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    verify_repository_binding(args.repository, args.schema_sha)
    preview = compile_preview(
        args.package,
        args.ledger,
        args.dry_run,
        schema_sha=args.schema_sha,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(preview, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
