#!/usr/bin/env python3
"""Build and verify the Golden Mira prep-only evidence ledger.

This tool validates exact source bindings and writes a derived artifact. It
performs no canonical admission, repository mutation, runtime wiring, context
admission, or provider call.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if type(value) is not dict:
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _message_text(message: dict[str, Any]) -> str:
    parts = message["content"]["parts"]
    chunks: list[str] = []
    for part in parts:
        if type(part) is str:
            chunks.append(part)
        elif type(part) is dict and type(part.get("text")) is str:
            chunks.append(part["text"])
    return "".join(chunks)


def _assert_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise ValueError(f"{label}: expected {expected!r}, got {actual!r}")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_ledger(goldset_path: Path, raw_path: Path, package_path: Path) -> dict[str, Any]:
    goldset = _load_json(goldset_path)
    raw_export = _load_json(raw_path)
    package = _load_json(package_path)

    if goldset.get("artifact_id") != "AUDITABLE_CAUSAL_GOLDSET_V1":
        raise ValueError("unexpected goldset artifact_id")
    if package.get("artifact_id") != "MIRA_MIGRATION_PREP_PACKAGE_V1":
        raise ValueError("unexpected package artifact_id")
    if package.get("status") != "PREP_COMPLETE_NO_ADMISSION":
        raise ValueError("package must remain PREP_COMPLETE_NO_ADMISSION")

    raw_sha256 = _sha256_file(raw_path)
    rows: list[dict[str, Any]] = []
    seen_assertions: set[str] = set()

    for chain_id, chain in goldset["chains"].items():
        for claim in chain["claims"]:
            assertion_id = f"{claim['claim_id']}@{claim['role']}"
            if assertion_id in seen_assertions:
                raise ValueError(f"duplicate binding assertion {assertion_id}")
            seen_assertions.add(assertion_id)

            locator = claim["raw_locator"]
            entry = raw_export["mapping"].get(locator["message_id"])
            if entry is None or type(entry.get("message")) is not dict:
                raise ValueError(f"RAW message not found: {locator['message_id']}")
            message = entry["message"]
            text_sha256 = hashlib.sha256(_message_text(message).encode("utf-8")).hexdigest()

            _assert_equal(entry.get("parent"), locator["parent_id"], f"{assertion_id}.parent_id")
            _assert_equal(message["author"]["role"], locator["author_role"], f"{assertion_id}.author_role")
            _assert_equal(message["create_time"], locator["create_time"], f"{assertion_id}.create_time")
            _assert_equal(
                message["content"]["content_type"],
                locator["content_type"],
                f"{assertion_id}.content_type",
            )
            _assert_equal(text_sha256, locator["text_sha256"], f"{assertion_id}.text_sha256")

            binding = claim["m0_binding"]
            _assert_equal(binding["source_sha256"], raw_sha256, f"{assertion_id}.source_sha256")
            _assert_equal(binding["status"], "RESOLVED", f"{assertion_id}.m0_status")
            _assert_equal(binding["canonical_lineage_member"], True, f"{assertion_id}.canonical_lineage_member")

            rows.append(
                {
                    "assertion_id": assertion_id,
                    "binding_id": claim["binding_id"],
                    "chain_id": chain_id,
                    "chain_title": chain["title"],
                    "claim": claim["claim_supported"],
                    "causal_role": claim["role"],
                    "claim_type": claim["claim_type"],
                    "conversation_id": locator["conversation_id"],
                    "message_id": locator["message_id"],
                    "parent_id": locator["parent_id"],
                    "author_role": locator["author_role"],
                    "create_time": locator["create_time"],
                    "content_type": locator["content_type"],
                    "text_sha256": locator["text_sha256"],
                    "source_archive_id": binding["source_archive_id"],
                    "source_sha256": binding["source_sha256"],
                    "evidence_archive_id": binding["evidence_archive_id"],
                    "source_evidence_ref": binding["source_evidence_ref"],
                    "canonical_lineage_index": binding["canonical_lineage_index"],
                    "bundle_ref": binding["bundle_ref"],
                    "evidence_grade": claim["evidence_semantics"]["grade"],
                    "support_scope": claim["evidence_semantics"]["support_scope"],
                    "must_follow_claim_id": claim["temporal_relation"]["must_follow_claim_id"],
                    "temporal_verified": claim["temporal_relation"]["verified"],
                    "semantic_lint": claim["semantic_lint"],
                }
            )

    expected_count = goldset["statistics"]["asserted_bindings"]
    if len(rows) != expected_count:
        raise ValueError(f"expected {expected_count} bindings, verified {len(rows)}")

    available_by_chain: dict[str, set[str]] = {}
    for row in rows:
        available_by_chain.setdefault(row["chain_id"], set()).add(row["binding_id"])
    for candidate in package["memory_experience_candidates"]:
        chain_id = candidate["chain_id"]
        for binding_id in candidate["raw_binding_ids"]:
            if binding_id not in available_by_chain.get(chain_id, set()):
                raise ValueError(f"{candidate['candidate_id']} references missing {binding_id}")

    authority = package["authority"]
    forbidden_flags = (
        "canonical_admission",
        "schema_mutation",
        "runtime_wiring",
        "context_admission",
        "provider_wiring",
        "production_cutover",
    )
    if any(authority.get(flag) is not False for flag in forbidden_flags):
        raise ValueError("package authority must remain fail-closed for canonical admission")

    return {
        "schema": "julia_core.mira_migration.evidence.ledger.v1",
        "ledger_id": "MIRA_MIGRATION_EVIDENCE_LEDGER_V1",
        "agent_id": "agent-c",
        "base_sha": "03460b191ac37c53dbbb2201beb6029e3ef288f",
        "status": "EXACT_RAW_VERIFIED_PREP_ONLY",
        "source_artifacts": {
            "goldset": {
                "artifact_id": "AUDITABLE_CAUSAL_GOLDSET_V1",
                "sha256": _sha256_file(goldset_path),
            },
            "raw_export": {
                "artifact_id": "MIRA_GOLDEN_CHATGPT_HI_MIRA_CANDIDATE.json",
                "sha256": raw_sha256,
                "conversation_id": raw_export.get("conversation_id"),
            },
            "package": {
                "artifact_id": "MIRA_MIGRATION_PREP_PACKAGE_V1",
                "sha256": _sha256_file(package_path),
            },
        },
        "verification": {
            "assertion_count": len(rows),
            "unique_binding_id_count": len({row["binding_id"] for row in rows}),
            "verified_count": len(rows),
            "failed_count": 0,
            "canonical_admission": False,
            "fail_closed": True,
        },
        "bindings": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--goldset", required=True, type=Path)
    parser.add_argument("--raw", required=True, type=Path)
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    ledger = build_ledger(args.goldset, args.raw, args.package)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(ledger, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
