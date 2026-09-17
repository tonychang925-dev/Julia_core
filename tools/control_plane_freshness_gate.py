#!/usr/bin/env python3
"""Mechanical RD1 control-plane compatibility/freshness gate.

Compatibility is versioned. Exact Julia_core SHAs remain audit evidence and do
not invalidate a task merely because main advanced without a compatibility
version change.
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

CONTROL_PLANE_REPO = "tonychang925-dev/Julia_core"
COMPATIBILITY_PATH = "docs/governance/RD1_CONTROL_PLANE_COMPATIBILITY.md"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
INT_RE = re.compile(r"^\d+$")

CONTROL_PLANE_EXCLUSIONS = {
    "docs/governance/RD1_CONTROL_PLANE_COMPATIBILITY.md",
    "docs/governance/RD1_CONTROL_PLANE_CONSOLIDATION_CONSTITUTIONAL_AMENDMENT_v1.1.md",
    "docs/governance/RD1_V1_Control_Plane_Consolidation_and_Semantic_Atomicity_Plan_v1.1.md",
    "docs/governance/RD1_CONTROL_PLANE_CONSOLIDATION_IMPLEMENTATION_CONTRACT_v1.0.md",
    "docs/governance/RD1_CONTROL_PLANE_FRESHNESS_GATE.md",
    "docs/governance/RD1_RULE12_ARCHITECTURE_COMPLETION_PROHIBITION.md",
    "docs/governance/RD1_AGENT_TASK_AUTHORITY_HEADER_TEMPLATE.md",
    "docs/governance/RD1_TASK_CARD_AUTHOR_PRE_SUBMISSION_SELF_CHECK.md",
    "docs/governance/RD1_ARCHITECTURE_AUTHORITY_PRECHECK.md",
    "docs/governance/RD1_TASK_CARD_CI_PARSER_GATE.md",
    "docs/governance/RD1_AGENT_EXECUTION_PERMISSION_MATRIX.md",
}


def _field_value(text: str, key: str) -> str | None:
    m = re.search(rf"(?m)^\s*{re.escape(key)}\s*\n\s*=\s*([^\n]+)", text)
    if m:
        return m.group(1).strip()
    m = re.search(rf"(?m)^\s*{re.escape(key)}\s*=\s*([^\n]+)", text)
    return m.group(1).strip() if m else None


def looks_like_task_card(path: str, text: str) -> bool:
    normalized = path.replace("\\", "/")
    if normalized in CONTROL_PLANE_EXCLUSIONS:
        return False
    if normalized != "PR_BODY" and Path(normalized).suffix.lower() not in {".md", ".markdown"}:
        return False
    name = Path(path).name.lower()
    return (
        "task_card" in name
        or "task-card" in name
        or "task card" in name
        or "TASK_CARD_AUTHOR_SELF_CHECK" in text
        or all(token in text for token in ("TASK_ID", "BASE_SHA", "REPO"))
    )


def local_compatibility_version(root: Path = Path(".")) -> int:
    path = root / COMPATIBILITY_PATH
    if not path.exists():
        return 0  # legacy/unversioned control plane
    text = path.read_text(encoding="utf-8")
    value = _field_value(text, "CONTROL_PLANE_COMPATIBILITY_VERSION")
    if value is None or not INT_RE.fullmatch(value):
        raise RuntimeError("canonical compatibility source has invalid/missing version")
    return int(value)


def github_main_sha(repo: str, token: str | None) -> str:
    url = f"https://api.github.com/repos/{repo}/branches/main"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "rd1-control-plane-compatibility-gate"}
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


def github_file_text(repo: str, path: str, ref: str, token: str | None) -> str | None:
    url = f"https://raw.githubusercontent.com/{repo}/{ref}/{path}"
    headers = {"User-Agent": "rd1-control-plane-compatibility-gate"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise RuntimeError(f"cannot read {repo}@{ref}:{path}: {exc}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"cannot read {repo}@{ref}:{path}: {exc}") from exc


def remote_compatibility_version(repo: str, ref: str, token: str | None) -> int:
    text = github_file_text(repo, COMPATIBILITY_PATH, ref, token)
    if text is None:
        return 0
    value = _field_value(text, "CONTROL_PLANE_COMPATIBILITY_VERSION")
    if value is None or not INT_RE.fullmatch(value):
        raise RuntimeError("remote canonical compatibility source has invalid/missing version")
    return int(value)


def validate_task_card(
    text: str,
    *,
    path: str = "<memory>",
    current_compatibility_version: int | None = None,
) -> list[str]:
    errors: list[str] = []
    repo = _field_value(text, "CONTROL_PLANE_AUTHORITY_REPO")
    declared_version = _field_value(text, "CONTROL_PLANE_COMPATIBILITY_VERSION")
    observed_sha = _field_value(text, "CONTROL_PLANE_SHA_OBSERVED")
    freshness = _field_value(text, "CONTROL_PLANE_FRESHNESS_CHECK")

    if repo is None:
        errors.append("missing CONTROL_PLANE_AUTHORITY_REPO")
    elif repo != CONTROL_PLANE_REPO:
        errors.append(f"CONTROL_PLANE_AUTHORITY_REPO must be {CONTROL_PLANE_REPO}, got {repo!r}")

    if declared_version is None:
        errors.append("missing CONTROL_PLANE_COMPATIBILITY_VERSION")
    elif not INT_RE.fullmatch(declared_version):
        errors.append(f"CONTROL_PLANE_COMPATIBILITY_VERSION must be an integer, got {declared_version!r}")

    if observed_sha is None:
        errors.append("missing CONTROL_PLANE_SHA_OBSERVED")
    elif not SHA_RE.fullmatch(observed_sha):
        errors.append(f"CONTROL_PLANE_SHA_OBSERVED must be exact 40-hex evidence, got {observed_sha!r}")

    if freshness is None:
        errors.append("missing CONTROL_PLANE_FRESHNESS_CHECK")
    elif freshness.upper() != "PASS":
        errors.append(f"CONTROL_PLANE_FRESHNESS_CHECK must be PASS, got {freshness!r}")

    if current_compatibility_version is not None and declared_version and INT_RE.fullmatch(declared_version):
        if int(declared_version) != current_compatibility_version:
            errors.append(
                "CONTROL_PLANE_COMPATIBILITY_DRIFT: "
                f"current version={current_compatibility_version}, task version={declared_version}"
            )

    return [f"{path}: {error}" for error in errors]


def validate_governance_impact(
    *,
    base_version: int,
    head_version: int,
    impact: str | None,
) -> list[str]:
    errors: list[str] = []
    if impact is None:
        return errors
    impact = impact.upper()
    if impact not in {"NONE", "BREAKING"}:
        return [f"CONTROL_PLANE_COMPATIBILITY_IMPACT must be NONE or BREAKING, got {impact!r}"]
    if impact == "BREAKING" and head_version != base_version + 1:
        errors.append(
            f"BREAKING governance change must increment compatibility version exactly once: "
            f"base={base_version}, head={head_version}"
        )
    if impact == "NONE" and head_version != base_version:
        errors.append(
            f"NONE governance change must not change compatibility version: base={base_version}, head={head_version}"
        )
    return errors


def changed_files(base_ref: str) -> list[str]:
    proc = subprocess.run(
        ["git", "diff", "--name-only", f"{base_ref}...HEAD"],
        check=True,
        text=True,
        capture_output=True,
    )
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def validate_pr_body(event_path: str | None, *, current_version: int | None) -> tuple[list[str], str | None]:
    if not event_path:
        return [], None
    path = Path(event_path)
    if not path.exists():
        return [], None
    payload = json.loads(path.read_text(encoding="utf-8"))
    body = ((payload.get("pull_request") or {}).get("body") or "")
    impact = _field_value(body, "CONTROL_PLANE_COMPATIBILITY_IMPACT") if body else None
    errors: list[str] = []
    if body and looks_like_task_card("PR_BODY", body):
        errors.extend(validate_task_card(body, path="PR_BODY", current_compatibility_version=current_version))
    return errors, impact


def validate_paths(paths: Iterable[str], *, current_version: int | None) -> dict:
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
        errors.extend(validate_task_card(text, path=raw, current_compatibility_version=current_version))
    return {"checked_task_cards": checked, "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*")
    parser.add_argument("--base-ref", default=None)
    parser.add_argument("--event-path", default=os.getenv("GITHUB_EVENT_PATH"))
    parser.add_argument("--verify-remote-control-plane", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    paths = list(args.paths)
    if args.base_ref:
        paths.extend(changed_files(args.base_ref))

    errors: list[str] = []
    head_version = local_compatibility_version()
    current_sha: str | None = None
    current_version: int | None = head_version
    base_version: int | None = None

    if args.verify_remote_control_plane:
        token = os.getenv("GITHUB_TOKEN")
        try:
            current_sha = github_main_sha(CONTROL_PLANE_REPO, token)
            current_version = remote_compatibility_version(CONTROL_PLANE_REPO, current_sha, token)
            base_version = current_version
        except RuntimeError as exc:
            errors.append(f"CONTROL_PLANE_REMOTE_VERIFICATION_FAIL: {exc}")
            current_version = None

    result = validate_paths(dict.fromkeys(paths), current_version=current_version)
    errors.extend(result["errors"])
    pr_errors, impact = validate_pr_body(args.event_path, current_version=current_version)
    errors.extend(pr_errors)

    if base_version is not None and impact is not None:
        errors.extend(validate_governance_impact(base_version=base_version, head_version=head_version, impact=impact))

    result.update(
        {
            "control_plane_sha": current_sha,
            "control_plane_compatibility_version": current_version,
            "head_compatibility_version": head_version,
            "compatibility_impact": impact,
            "errors": errors,
        }
    )
    result["status"] = "PASS" if not errors else "FAIL"

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"RD1_CONTROL_PLANE_COMPATIBILITY_GATE={result['status']}")
        print(f"head_compatibility_version={head_version}")
        if current_sha:
            print(f"control_plane_sha_observed={current_sha}")
        if current_version is not None:
            print(f"current_compatibility_version={current_version}")
        for item in result["checked_task_cards"]:
            print(f"checked: {item}")
        for error in errors:
            print(f"ERROR: {error}")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
