#!/usr/bin/env python3
"""Mechanical RD1 control-plane compatibility/freshness gate."""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Iterable

CONTROL_PLANE_REPO = "tonychang925-dev/Julia_core"
COMPATIBILITY_PATH = "docs/governance/RD1_CONTROL_PLANE_COMPATIBILITY.md"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
VERSION_RE = re.compile(r"^\d+$")
NORMATIVE_PREFIXES = ("docs/governance/", "tools/", ".github/workflows/")

CONTROL_PLANE_EXCLUSIONS = {
    "docs/governance/RD1_CONTROL_PLANE_FRESHNESS_GATE.md",
    "docs/governance/RD1_CONTROL_PLANE_COMPATIBILITY.md",
    "docs/governance/RD1_CONTROL_PLANE_CONSOLIDATION_CONSTITUTIONAL_AMENDMENT_v1.1.md",
    "docs/governance/RD1_V1_Control_Plane_Consolidation_and_Semantic_Atomicity_Plan_v1.1.md",
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


def _request_json(url: str, token: str | None) -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "rd1-control-plane-compatibility-gate",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"GitHub HTTP {exc.code}: {exc.reason}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"GitHub verification failed: {exc}") from exc


def github_main_sha(repo: str, token: str | None) -> str:
    payload = _request_json(f"https://api.github.com/repos/{repo}/branches/main", token)
    sha = payload.get("commit", {}).get("sha", "")
    if not SHA_RE.fullmatch(sha):
        raise RuntimeError(f"invalid current main SHA returned for {repo}: {sha!r}")
    return sha


def github_file_text(repo: str, path: str, ref: str, token: str | None) -> str:
    quoted = urllib.parse.quote(path, safe="/")
    payload = _request_json(
        f"https://api.github.com/repos/{repo}/contents/{quoted}?ref={ref}", token
    )
    if payload.get("encoding") != "base64" or "content" not in payload:
        raise RuntimeError(f"cannot decode {repo}:{path}@{ref}")
    return base64.b64decode(payload["content"]).decode("utf-8")


def compatibility_version_from_text(text: str) -> int:
    value = _field_value(text, "CONTROL_PLANE_COMPATIBILITY_VERSION")
    if value is None or not VERSION_RE.fullmatch(value):
        raise RuntimeError("invalid or missing CONTROL_PLANE_COMPATIBILITY_VERSION")
    return int(value)


def github_current_control_plane(token: str | None) -> tuple[str, int]:
    sha = github_main_sha(CONTROL_PLANE_REPO, token)
    try:
        text = github_file_text(CONTROL_PLANE_REPO, COMPATIBILITY_PATH, sha, token)
    except RuntimeError as exc:
        # Bootstrap: legacy main before the first consolidated compatibility file.
        if "HTTP 404" in str(exc):
            return sha, 0
        raise
    return sha, compatibility_version_from_text(text)


def validate_task_card(
    text: str,
    *,
    path: str = "<memory>",
    current_control_plane_sha: str | None = None,
    current_compatibility_version: int | None = None,
) -> list[str]:
    errors: list[str] = []
    repo = _field_value(text, "CONTROL_PLANE_AUTHORITY_REPO")
    version = _field_value(text, "SELF_CHECK_CONTROL_PLANE_COMPATIBILITY_VERSION")
    observed_sha = _field_value(text, "SELF_CHECK_CONTROL_PLANE_SHA")
    freshness = _field_value(text, "CONTROL_PLANE_FRESHNESS_CHECK")

    if repo is None:
        errors.append("missing CONTROL_PLANE_AUTHORITY_REPO")
    elif repo != CONTROL_PLANE_REPO:
        errors.append(f"CONTROL_PLANE_AUTHORITY_REPO must be {CONTROL_PLANE_REPO}, got {repo!r}")

    if version is None:
        errors.append("missing SELF_CHECK_CONTROL_PLANE_COMPATIBILITY_VERSION")
    elif not VERSION_RE.fullmatch(version):
        errors.append(f"SELF_CHECK_CONTROL_PLANE_COMPATIBILITY_VERSION must be integer, got {version!r}")

    if observed_sha is None:
        errors.append("missing SELF_CHECK_CONTROL_PLANE_SHA")
    elif not SHA_RE.fullmatch(observed_sha):
        errors.append(f"SELF_CHECK_CONTROL_PLANE_SHA must be exact 40-hex evidence, got {observed_sha!r}")

    if freshness is None:
        errors.append("missing CONTROL_PLANE_FRESHNESS_CHECK")
    elif freshness.upper() != "PASS":
        errors.append(f"CONTROL_PLANE_FRESHNESS_CHECK must be PASS, got {freshness!r}")

    if current_compatibility_version is not None and version and VERSION_RE.fullmatch(version):
        if int(version) != current_compatibility_version:
            errors.append(
                "CONTROL_PLANE_COMPATIBILITY_DRIFT: "
                f"current_version={current_compatibility_version}, self_check_version={version}"
            )

    # Exact SHA drift alone is intentionally not an error when compatibility matches.
    _ = current_control_plane_sha
    return [f"{path}: {error}" for error in errors]


def changed_files(base_ref: str) -> list[str]:
    proc = subprocess.run(
        ["git", "diff", "--name-only", f"{base_ref}...HEAD"],
        check=True,
        text=True,
        capture_output=True,
    )
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def git_compatibility_version(ref: str) -> int:
    proc = subprocess.run(
        ["git", "show", f"{ref}:{COMPATIBILITY_PATH}"],
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        return 0
    return compatibility_version_from_text(proc.stdout)


def current_head_compatibility_version() -> int:
    path = Path(COMPATIBILITY_PATH)
    if not path.exists():
        return 0
    return compatibility_version_from_text(path.read_text(encoding="utf-8"))


def pr_body(event_path: str | None) -> str:
    if not event_path:
        return ""
    path = Path(event_path)
    if not path.exists():
        return ""
    payload = json.loads(path.read_text(encoding="utf-8"))
    return ((payload.get("pull_request") or {}).get("body") or "")


def validate_governance_transition(*, base_ref: str | None, event_path: str | None, changed: list[str]) -> list[str]:
    if not base_ref or not any(p.startswith(NORMATIVE_PREFIXES) for p in changed):
        return []

    body = pr_body(event_path)
    impact = _field_value(body, "CONTROL_PLANE_COMPATIBILITY_IMPACT")
    if impact not in {"NONE", "BREAKING"}:
        return ["governance PR must declare CONTROL_PLANE_COMPATIBILITY_IMPACT = NONE | BREAKING"]

    base_version = git_compatibility_version(base_ref)
    head_version = current_head_compatibility_version()

    if impact == "BREAKING" and head_version != base_version + 1:
        return [
            "BREAKING compatibility impact requires version increment exactly once: "
            f"base={base_version}, head={head_version}"
        ]
    if impact == "NONE" and head_version != base_version:
        return [
            "NONE compatibility impact forbids version movement: "
            f"base={base_version}, head={head_version}"
        ]
    return []


def validate_paths(paths: Iterable[str], *, verify_remote: bool, token: str | None) -> dict:
    checked: list[str] = []
    errors: list[str] = []
    current_sha: str | None = None
    current_version: int | None = None
    if verify_remote:
        try:
            current_sha, current_version = github_current_control_plane(token)
        except RuntimeError as exc:
            return {
                "checked_task_cards": [],
                "control_plane_sha": None,
                "control_plane_compatibility_version": None,
                "errors": [f"CONTROL_PLANE_REMOTE_VERIFICATION_FAIL: {exc}"],
            }

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
        errors.extend(validate_task_card(
            text,
            path=raw,
            current_control_plane_sha=current_sha,
            current_compatibility_version=current_version,
        ))

    return {
        "checked_task_cards": checked,
        "control_plane_sha": current_sha,
        "control_plane_compatibility_version": current_version,
        "errors": errors,
    }


def validate_pr_body(event_path: str | None, *, current_sha: str | None, current_version: int | None) -> list[str]:
    body = pr_body(event_path)
    if not body or not looks_like_task_card("PR_BODY", body):
        return []
    return validate_task_card(
        body,
        path="PR_BODY",
        current_control_plane_sha=current_sha,
        current_compatibility_version=current_version,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*")
    parser.add_argument("--base-ref", default=None)
    parser.add_argument("--event-path", default=os.getenv("GITHUB_EVENT_PATH"))
    parser.add_argument("--verify-remote-control-plane", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    paths = list(args.paths)
    changed: list[str] = []
    if args.base_ref:
        changed = changed_files(args.base_ref)
        paths.extend(changed)

    result = validate_paths(
        dict.fromkeys(paths),
        verify_remote=args.verify_remote_control_plane,
        token=os.getenv("GITHUB_TOKEN"),
    )
    result["errors"].extend(validate_pr_body(
        args.event_path,
        current_sha=result.get("control_plane_sha"),
        current_version=result.get("control_plane_compatibility_version"),
    ))
    result["errors"].extend(validate_governance_transition(
        base_ref=args.base_ref,
        event_path=args.event_path,
        changed=changed,
    ))
    result["status"] = "PASS" if not result["errors"] else "FAIL"

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"RD1_CONTROL_PLANE_FRESHNESS_GATE={result['status']}")
        if result.get("control_plane_sha"):
            print(f"control_plane_sha={result['control_plane_sha']}")
        if result.get("control_plane_compatibility_version") is not None:
            print(f"control_plane_compatibility_version={result['control_plane_compatibility_version']}")
        for item in result["checked_task_cards"]:
            print(f"checked: {item}")
        for error in result["errors"]:
            print(f"ERROR: {error}")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
