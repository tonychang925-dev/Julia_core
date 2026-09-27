"""Deterministic prep-only semantic-fidelity correction tooling.

This module verifies explicit source-language semantic distinctions against exact
RAW messages and prepares successor migration candidates. It has no repository,
admission, context, runtime, provider, or production authority.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


MANIFEST_SCHEMA = "julia_core.mira_migration.semantic_fidelity_manifest.v1"
RESULT_SCHEMA = "julia_core.mira_migration.semantic_fidelity_correction.v1"


class SemanticFidelityCorrectionError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if condition is not True:
        raise SemanticFidelityCorrectionError(message)
def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    _require(type(value) is dict, f"{path} must contain a JSON object")
    return value


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def _canonical_digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _message_text(message: dict[str, Any]) -> str:
    parts = message["content"]["parts"]
    return "".join(
        part if type(part) is str else part.get("text", "")
        for part in parts
    )
def _git_show_json(repository: Path, commit: str, path: str) -> dict[str, Any]:
    resolved = subprocess.run(
        ["git", "rev-parse", f"{commit}^{{commit}}"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    _require(resolved == commit, f"historical commit does not resolve exactly: {commit}")
    blob = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=repository,
        check=True,
        capture_output=True,
    ).stdout
    value = json.loads(blob.decode("utf-8"))
    _require(type(value) is dict, f"historical artifact is not a JSON object: {path}")
    return value


def _candidate(preview: dict[str, Any], candidate_id: str) -> dict[str, Any]:
    matches = [
        item
        for item in preview.get("memory_experience_previews", [])
        if item.get("candidate_id") == candidate_id
    ]
    _require(len(matches) == 1, f"expected exactly one historical candidate: {candidate_id}")
    return matches[0]


def _at_path(value: dict[str, Any], path: list[str]) -> Any:
    current: Any = value
    for key in path:
        _require(type(current) is dict and key in current, f"missing target path segment: {key}")
        current = current[key]
    return current
def _set_path(value: dict[str, Any], path: list[str], replacement: Any) -> None:
    _require(bool(path), "target_path must not be empty")
    current: Any = value
    for key in path[:-1]:
        _require(type(current) is dict and key in current, f"missing target path segment: {key}")
        current = current[key]
    _require(type(current) is dict and path[-1] in current, "missing target field")
    current[path[-1]] = replacement


def _raw_message(raw_export: dict[str, Any], message_id: str) -> dict[str, Any]:
    entry = raw_export.get("mapping", {}).get(message_id)
    _require(type(entry) is dict, f"RAW message not found: {message_id}")
    message = entry.get("message")
    _require(type(message) is dict, f"RAW message payload missing: {message_id}")
    return message


def _verify_authority(manifest: dict[str, Any]) -> None:
    authority = manifest.get("authority")
    _require(type(authority) is dict, "manifest authority block is required")
    forbidden = (
        "canonical_admission",
        "canonical_write",
        "supersession",
        "psb_rebind",
        "runtime_wiring",
        "provider_wiring",
        "production_cutover",
    )
    _require(
        all(authority.get(key) is False for key in forbidden),
        "Phase A manifest must remain prep-only and authority-free",
    )
def build_successor(
    *,
    preview: dict[str, Any],
    raw_export: dict[str, Any],
    raw_sha256: str,
    manifest: dict[str, Any],
) -> dict[str, Any]:
    _require(manifest.get("schema") == MANIFEST_SCHEMA, "wrong manifest schema")
    _require(manifest.get("status") == "PREP_ONLY", "manifest must be PREP_ONLY")
    _verify_authority(manifest)

    raw_spec = manifest.get("raw_export", {})
    _require(raw_spec.get("sha256") == raw_sha256, "RAW export SHA mismatch")

    historical = manifest.get("historical_candidate", {})
    candidate_id = historical.get("candidate_id")
    _require(type(candidate_id) is str and bool(candidate_id), "candidate_id is required")
    old_item = _candidate(preview, candidate_id)
    old_preview = old_item["canonical_preview"]
    _require(
        old_preview.get("digest") == historical.get("canonical_digest"),
        "historical canonical digest mismatch",
    )
    old_payload = old_preview["payload"]
    _require(
        old_payload.get("version_id") == historical.get("version_id"),
        "historical version mismatch",
    )

    proposed = copy.deepcopy(old_payload)
    successor = manifest.get("successor", {})
    proposed_version_id = successor.get("proposed_version_id")
    _require(type(proposed_version_id) is str and bool(proposed_version_id), "successor version is required")
    proposed["version_id"] = proposed_version_id
    proposed["predecessor_version_id"] = old_payload["version_id"]
    corrections = manifest.get("corrections")
    _require(type(corrections) is list and bool(corrections), "corrections are required")
    correction_ids: set[str] = set()
    correction_evidence: list[dict[str, Any]] = []

    for correction in corrections:
        _require(type(correction) is dict, "correction must be an object")
        correction_id = correction.get("correction_id")
        _require(type(correction_id) is str and correction_id not in correction_ids, "correction_id must be unique")
        correction_ids.add(correction_id)

        source_attribute = correction.get("source_semantic_attribute")
        normalized_attribute = correction.get("normalized_semantic_attribute")
        _require(type(source_attribute) is dict, f"{correction_id}: source semantic attribute required")
        _require(type(normalized_attribute) is dict, f"{correction_id}: normalized semantic attribute required")
        _require(
            source_attribute == normalized_attribute,
            f"{correction_id}: normalized semantics do not preserve source attribute",
        )

        target_path = correction.get("target_path")
        _require(
            type(target_path) is list
            and len(target_path) >= 2
            and target_path[0] == "content"
            and all(type(part) is str and part for part in target_path),
            f"{correction_id}: target_path must identify a content field",
        )
        current_text = _at_path(proposed, target_path)
        _require(type(current_text) is str, f"{correction_id}: target field must be text")
        old_span = correction.get("old_normalized_span")
        corrected_span = correction.get("corrected_normalized_span")
        _require(type(old_span) is str and bool(old_span), f"{correction_id}: old span required")
        _require(type(corrected_span) is str and bool(corrected_span), f"{correction_id}: corrected span required")
        _require(old_span != corrected_span, f"{correction_id}: correction must change the normalized span")
        _require(
            current_text.count(old_span) == 1,
            f"{correction_id}: old normalized span must occur exactly once",
        )

        raw_evidence = correction.get("raw_evidence")
        _require(type(raw_evidence) is list and bool(raw_evidence), f"{correction_id}: RAW evidence required")
        proofs: list[dict[str, Any]] = []
        for evidence in raw_evidence:
            message_id = evidence.get("message_id")
            message = _raw_message(raw_export, message_id)
            body = _message_text(message)
            text_sha256 = hashlib.sha256(body.encode("utf-8")).hexdigest()
            _require(
                text_sha256 == evidence.get("text_sha256"),
                f"{correction_id}: RAW text SHA mismatch for {message_id}",
            )
            source_span = evidence.get("required_source_span")
            _require(
                type(source_span) is str and source_span in body,
                f"{correction_id}: required source span missing from {message_id}",
            )
            proofs.append(
                {
                    "binding_id": evidence.get("binding_id"),
                    "causal_role": evidence.get("causal_role"),
                    "message_id": message_id,
                    "text_sha256": text_sha256,
                    "required_source_span": source_span,
                    "source_span_occurrences": body.count(source_span),
                }
            )

        replacement = current_text.replace(old_span, corrected_span, 1)
        _set_path(proposed, target_path, replacement)
        correction_evidence.append(
            {
                "correction_id": correction_id,
                "target_path": target_path,
                "source_semantic_attribute": source_attribute,
                "normalized_semantic_attribute": normalized_attribute,
                "old_normalized_span": old_span,
                "corrected_normalized_span": corrected_span,
                "raw_evidence": proofs,
                "verdict": "SEMANTIC_SPECIFICITY_PRESERVED",
            }
        )

    _require(
        old_preview["payload"] == old_payload,
        "historical candidate mutated during correction preparation",
    )
    manifest_digest = _canonical_digest(manifest)
    correction_source_ref = (
        "mira-semantic-fidelity://correction/"
        f"{manifest['artifact_id']}/{old_item['chain_id']}"
    )
    proposed["provenance_refs"] = [
        *proposed["provenance_refs"],
        {
            "source_type": "semantic-fidelity-correction",
            "source_ref": correction_source_ref,
            "source_digest": manifest_digest,
            "admission_metadata": {
                "artifact_id": manifest["artifact_id"],
                "task_id": manifest["task_id"],
                "raw_export_sha256": raw_sha256,
                "correction_ids": ",".join(sorted(correction_ids)),
                "authority_scope": "PREP_ONLY_NO_ADMISSION",
            },
        },
    ]
    proposed_digest = _canonical_digest(proposed)
    result = {
        "schema": RESULT_SCHEMA,
        "artifact_id": manifest["artifact_id"],
        "task_id": manifest["task_id"],
        "status": "PREP_COMPLETE_NO_ADMISSION",
        "source": {
            "raw_export_sha256": raw_sha256,
            "correction_manifest_digest": manifest_digest,
            "historical_preview_commit": historical["preview_commit"],
            "historical_preview_path": historical["preview_path"],
            "historical_candidate_id": candidate_id,
            "historical_canonical_ref": historical["canonical_ref"],
            "historical_canonical_digest": historical["canonical_digest"],
        },
        "semantic_fidelity": {
            "provenance_identity_verified": True,
            "semantic_fidelity_verified": True,
            "binding_coverage_is_not_semantic_fidelity": True,
            "corrections": correction_evidence,
        },
        "successor_candidate": {
            "candidate_id": successor["candidate_id"],
            "chain_id": old_item["chain_id"],
            "experience_type": proposed["experience_type"],
            "proposed_version_id": proposed_version_id,
            "predecessor_version_id": old_payload["version_id"],
            "predecessor_ref": historical["canonical_ref"],
            "proposed_canonical_payload": proposed,
            "proposed_canonical_digest": proposed_digest,
        },
        "authority": copy.deepcopy(manifest["authority"]),
    }
    result["deterministic_digest"] = _canonical_digest(result)
    return result
def run(
    *,
    repository: Path,
    raw_path: Path,
    manifest_path: Path,
) -> dict[str, Any]:
    manifest = _load_json(manifest_path)
    raw_export = _load_json(raw_path)
    raw_sha256 = _sha256_file(raw_path)
    historical = manifest.get("historical_candidate", {})
    preview = _git_show_json(
        repository.resolve(),
        historical["preview_commit"],
        historical["preview_path"],
    )
    return build_successor(
        preview=preview,
        raw_export=raw_export,
        raw_sha256=raw_sha256,
        manifest=manifest,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--raw", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    result = run(
        repository=args.repository,
        raw_path=args.raw,
        manifest_path=args.manifest,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
