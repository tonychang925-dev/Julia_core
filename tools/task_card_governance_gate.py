#!/usr/bin/env python3
"""Mechanical RD1 task-card governance gate.

This gate enforces the active control plane before a task card may advance.
It validates task-card structure/self-check evidence and, in CI, verifies the
bound BASE_SHA against the current main SHA of the declared REPO.

Architecture remains defined by frozen sources; this parser only enforces
required governance evidence and never invents architecture.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Iterable

MANDATORY_TASK_FIELDS = (
    "FROZEN_AUTHORITY_TRACE", "RULE11_CLASSIFICATION", "CURRENT_PHASE",
    "TARGET_REQUIREMENT", "DEFERRED_FINDINGS", "TASK_ID", "REPO",
    "TARGET_BRANCH", "BASE_SHA", "AUTHORIZED_PATHS", "FORBIDDEN_PATHS",
    "REQUIRED_BEHAVIOR", "FORBIDDEN_BEHAVIOR", "ACCEPTANCE_EVIDENCE",
)

MANDATORY_SELF_CHECK_FIELDS = (
    "AUTHOR_ROLE", "TASK_ID", "TASK_CARD_VERSION", "AUTHORITY_SOURCE_FILES_CHECKED",
    "CURRENT_MAIN_SHAS", "MANDATORY_TASK_FIELDS_PRESENT", "AUTHORIZED_PATH_COUNT",
    "DEFERRED_FINDING_COUNT", "AUTHORITY_IDENTITY", "MANDATORY_HEADER",
    "RULE11_CLASSIFICATION_CHECK", "PHASE_SCOPE_CHECK", "RESIDUAL_DECISION_AUDIT",
    "RESIDUAL_ARCHITECTURE_DECISIONS", "RESIDUAL_CONTRACT_SEMANTIC_DECISIONS",
    "CROSS_BOUNDARY_SEMANTICS", "CURRENT_CODE_COMPATIBILITY",
    "ACCEPTANCE_EVIDENCE_CHECK", "NO_AGENT_ARCHITECTURE_DISCRETION",
    "SELF_CHECK_RESULT", "READY_FOR_SUBMISSION",
)

MANDATORY_PERMISSION_FIELDS = (
    "PERMISSION_MODEL", "PERMISSION_REPOSITORY", "PERMISSION_BASE_SHA",
    "PERMISSION_TARGET_BRANCH", "READ_SCOPE", "WRITE_SCOPE",
    "ARCHITECTURE_MUTATION", "PUBLIC_CONTRACT_MUTATION",
    "CROSS_BOUNDARY_SEMANTIC_DECISION", "DEPENDENCY_MUTATION",
    "TEST_CREATION", "BRANCH_CREATION", "COMMIT", "PR_CREATION",
    "MERGE", "RELEASE", "DEPLOY", "PRODUCTION_MUTATION",
    "FALLBACK", "SYNTHETIC_SUCCESS", "FUTURE_PHASE_SCOPE",
)

MANDATORY_DENY_PERMISSION_FIELDS = (
    "ARCHITECTURE_MUTATION", "CROSS_BOUNDARY_SEMANTIC_DECISION",
    "MERGE", "RELEASE", "DEPLOY", "PRODUCTION_MUTATION",
    "FALLBACK", "SYNTHETIC_SUCCESS", "FUTURE_PHASE_SCOPE",
)

CROSS_BOUNDARY_TOKENS = (
    "adapter", "bridge", "translator", "proxy", "serializer",
    "provider wrapper", "public boundary conversion", "cross-repo contract conversion",
)

CROSS_BOUNDARY_REQUIRED = (
    "SOURCE_CONTRACT", "TARGET_CONTRACT", "FIELD_MAPPING", "STATUS_MAPPING",
    "FAILURE_MAPPING", "PROVENANCE_MAPPING", "AUTHORITY_TRANSFER",
    "MALFORMED_INPUT_BEHAVIOR", "UNKNOWN_VALUE_BEHAVIOR", "LIFECYCLE_OWNERSHIP",
)

CONTROL_PLANE_EXCLUSIONS = {
    "docs/governance/RD1_AGENT_TASK_AUTHORITY_HEADER_TEMPLATE.md",
    "docs/governance/RD1_TASK_CARD_AUTHOR_PRE_SUBMISSION_SELF_CHECK.md",
    "docs/governance/RD1_ARCHITECTURE_AUTHORITY_PRECHECK.md",
    "docs/governance/RD1_TASK_CARD_CI_PARSER_GATE.md",
    "docs/governance/RD1_AGENT_EXECUTION_PERMISSION_MATRIX.md",
}

SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def _field_value(text: str, key: str) -> str | None:
    m = re.search(rf"(?m)^\s*{re.escape(key)}\s*\n\s*=\s*([^\n]+)", text)
    if m:
        return m.group(1).strip()
    m = re.search(rf"(?m)^\s*{re.escape(key)}\s*=\s*([^\n]+)", text)
    return m.group(1).strip() if m else None


def _has_field(text: str, key: str) -> bool:
    return _field_value(text, key) is not None or re.search(
        rf"(?m)^\s*{re.escape(key)}\s*$", text
    ) is not None


def looks_like_task_card(path: str, text: str) -> bool:
    normalized = path.replace("\\", "/")
    if normalized in CONTROL_PLANE_EXCLUSIONS:
        return False
    if normalized != "PR_BODY" and Path(normalized).suffix.lower() not in {".md", ".markdown"}:
        return False
    name = Path(path).name.lower()
    by_name = "task_card" in name or "task-card" in name or "task card" in name
    by_content = "TASK_CARD_AUTHOR_SELF_CHECK" in text or (
        _has_field(text, "TASK_ID") and _has_field(text, "BASE_SHA") and _has_field(text, "REPO")
    )
    return by_name or by_content


def is_cross_boundary_task(text: str) -> bool:
    lower = text.lower()
    return any(token in lower for token in CROSS_BOUNDARY_TOKENS)


def _int_value(text: str, key: str) -> int | None:
    value = _field_value(text, key)
    if value is None:
        return None
    m = re.search(r"-?\d+", value)
    return int(m.group(0)) if m else None


def validate_task_card(text: str, *, path: str = "<memory>") -> list[str]:
    errors: list[str] = []

    missing_task = [key for key in MANDATORY_TASK_FIELDS if not _has_field(text, key)]
    if missing_task:
        errors.append("missing mandatory task fields: " + ", ".join(missing_task))

    if "TASK_CARD_AUTHOR_SELF_CHECK" not in text:
        errors.append("missing TASK_CARD_AUTHOR_SELF_CHECK block")

    missing_self = [key for key in MANDATORY_SELF_CHECK_FIELDS if not _has_field(text, key)]
    if missing_self:
        errors.append("missing self-check fields: " + ", ".join(missing_self))

    if "AGENT_EXECUTION_PERMISSION_MATRIX" not in text:
        errors.append("missing AGENT_EXECUTION_PERMISSION_MATRIX block")

    missing_permissions = [key for key in MANDATORY_PERMISSION_FIELDS if not _has_field(text, key)]
    if missing_permissions:
        errors.append("missing permission-matrix fields: " + ", ".join(missing_permissions))

    expected_values = {
        "AUTHORITY_IDENTITY": "PASS",
        "MANDATORY_HEADER": "PASS",
        "RULE11_CLASSIFICATION_CHECK": "PASS",
        "PHASE_SCOPE_CHECK": "PASS",
        "RESIDUAL_DECISION_AUDIT": "PASS",
        "CURRENT_CODE_COMPATIBILITY": "PASS",
        "ACCEPTANCE_EVIDENCE_CHECK": "PASS",
        "NO_AGENT_ARCHITECTURE_DISCRETION": "PASS",
        "SELF_CHECK_RESULT": "PASS",
        "READY_FOR_SUBMISSION": "YES",
        "PERMISSION_MODEL": "DEFAULT_DENY",
        "TEST_CREATION": "BOUNDED_TO_ACCEPTANCE_EVIDENCE",
        "BRANCH_CREATION": "EXACT_TARGET_ONLY",
        "COMMIT": "TASK_BRANCH_ONLY",
    }
    for key, expected in expected_values.items():
        value = _field_value(text, key)
        if value is not None and value.upper() != expected:
            errors.append(f"{key} must be {expected}, got {value!r}")

    for key in MANDATORY_DENY_PERMISSION_FIELDS:
        value = _field_value(text, key)
        if value is not None and value.upper() != "DENY":
            errors.append(f"{key} must be DENY, got {value!r}")

    public_contract = _field_value(text, "PUBLIC_CONTRACT_MUTATION")
    if public_contract is not None and not (
        public_contract.upper() == "DENY" or public_contract.startswith("EXPLICITLY_AUTHORIZED:")
    ):
        errors.append("PUBLIC_CONTRACT_MUTATION must be DENY or EXPLICITLY_AUTHORIZED:<scope>")

    dependency = _field_value(text, "DEPENDENCY_MUTATION")
    if dependency is not None and not (
        dependency.upper() == "DENY" or dependency.startswith("EXPLICITLY_AUTHORIZED:")
    ):
        errors.append("DEPENDENCY_MUTATION must be DENY or EXPLICITLY_AUTHORIZED:<scope>")

    pr_creation = _field_value(text, "PR_CREATION")
    if pr_creation is not None and pr_creation.upper() not in {"ALLOW", "DENY"}:
        errors.append("PR_CREATION must be ALLOW or DENY")

    permission_identity_pairs = (
        ("PERMISSION_REPOSITORY", "REPO"),
        ("PERMISSION_BASE_SHA", "BASE_SHA"),
        ("PERMISSION_TARGET_BRANCH", "TARGET_BRANCH"),
    )
    for permission_key, task_key in permission_identity_pairs:
        permission_value = _field_value(text, permission_key)
        task_value = _field_value(text, task_key)
        if permission_value is not None and task_value is not None and permission_value != task_value:
            errors.append(f"{permission_key} must exactly equal {task_key}")

    for key in ("RESIDUAL_ARCHITECTURE_DECISIONS", "RESIDUAL_CONTRACT_SEMANTIC_DECISIONS"):
        value = _int_value(text, key)
        if value is not None and value != 0:
            errors.append(f"{key} must be 0, got {value}")

    classification = _field_value(text, "RULE11_CLASSIFICATION")
    if classification is not None and classification not in {"A", "B", "C", "D", "NO_ACTIVE_FINDING"}:
        errors.append(f"RULE11_CLASSIFICATION has illegal value {classification!r}")

    base_sha = _field_value(text, "BASE_SHA")
    if base_sha is not None and not SHA_RE.fullmatch(base_sha):
        errors.append(f"BASE_SHA must be an exact 40-hex SHA, got {base_sha!r}")

    if is_cross_boundary_task(text):
        missing_mapping = [key for key in CROSS_BOUNDARY_REQUIRED if not _has_field(text, key)]
        if missing_mapping:
            errors.append("cross-boundary task missing frozen mappings: " + ", ".join(missing_mapping))
        semantic_result = _field_value(text, "CROSS_BOUNDARY_SEMANTICS")
        if semantic_result is not None and semantic_result.upper() != "PASS":
            errors.append(f"CROSS_BOUNDARY_SEMANTICS must be PASS, got {semantic_result!r}")

    mandatory_count = _field_value(text, "MANDATORY_TASK_FIELDS_PRESENT")
    if mandatory_count is not None:
        expected = len(MANDATORY_TASK_FIELDS)
        m = re.match(r"\s*(\d+)\s*/\s*(\d+)\s*$", mandatory_count)
        if not m or int(m.group(1)) != expected or int(m.group(2)) != expected:
            errors.append(
                f"MANDATORY_TASK_FIELDS_PRESENT must be {expected}/{expected}, got {mandatory_count!r}"
            )

    return [f"{path}: {error}" for error in errors]


def github_main_sha(repo: str, token: str | None) -> str:
    url = f"https://api.github.com/repos/{repo}/branches/main"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "rd1-task-card-governance-gate"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            payload = json.load(resp)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise RuntimeError(f"cannot verify current main for {repo}: {exc}") from exc
    sha = payload.get("commit", {}).get("sha", "")
    if not SHA_RE.fullmatch(sha):
        raise RuntimeError(f"invalid current main SHA returned for {repo}: {sha!r}")
    return sha


def validate_remote_base(text: str, *, token: str | None) -> list[str]:
    repo = _field_value(text, "REPO")
    base_sha = _field_value(text, "BASE_SHA")
    if not repo or not base_sha or not SHA_RE.fullmatch(base_sha):
        return []
    current = github_main_sha(repo, token)
    if current != base_sha:
        return [f"BASE_DRIFT: {repo}/main={current}, task BASE_SHA={base_sha}"]
    return []


def changed_files(base_ref: str) -> list[str]:
    proc = subprocess.run(
        ["git", "diff", "--name-only", f"{base_ref}...HEAD"],
        check=True,
        text=True,
        capture_output=True,
    )
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def validate_pr_body(event_path: str | None) -> list[str]:
    if not event_path:
        return []
    path = Path(event_path)
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    body = ((payload.get("pull_request") or {}).get("body") or "")
    if not body or not looks_like_task_card("PR_BODY", body):
        return []
    return validate_task_card(body, path="PR_BODY")


def validate_paths(paths: Iterable[str], *, verify_remote: bool, token: str | None) -> dict:
    checked: list[str] = []
    errors: list[str] = []
    for raw in paths:
        path = Path(raw)
        if not path.exists() or path.is_dir():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if not looks_like_task_card(raw, text):
            continue
        checked.append(raw)
        errors.extend(validate_task_card(text, path=raw))
        if verify_remote:
            try:
                errors.extend(f"{raw}: {e}" for e in validate_remote_base(text, token=token))
            except RuntimeError as exc:
                errors.append(f"{raw}: REMOTE_BASE_VERIFICATION_FAIL: {exc}")
    return {"checked_task_cards": checked, "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*")
    parser.add_argument("--base-ref", default=None)
    parser.add_argument("--event-path", default=os.getenv("GITHUB_EVENT_PATH"))
    parser.add_argument("--verify-remote-base", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    paths = list(args.paths)
    if args.base_ref:
        paths.extend(changed_files(args.base_ref))
    result = validate_paths(
        dict.fromkeys(paths),
        verify_remote=args.verify_remote_base,
        token=os.getenv("GITHUB_TOKEN"),
    )
    result["errors"].extend(validate_pr_body(args.event_path))
    result["status"] = "PASS" if not result["errors"] else "FAIL"

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"RD1_TASK_CARD_GOVERNANCE_GATE={result['status']}")
        for item in result["checked_task_cards"]:
            print(f"checked: {item}")
        for error in result["errors"]:
            print(f"ERROR: {error}")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
