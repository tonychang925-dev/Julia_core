#!/usr/bin/env python3
"""Mechanical control-plane freshness gate for RD1 task cards."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Iterable

CONTROL_PLANE_REPO = "tonychang925-dev/Julia_core"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")

CONTROL_PLANE_EXCLUSIONS = {
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


def github_main_sha(repo: str, token: str | None) -> str:
    url = f"https://api.github.com/repos/{repo}/branches/main"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "rd1-control-plane-freshness-gate",
    }
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


def validate_task_card(
    text: str,
    *,
    path: str = "<memory>",
    current_control_plane_sha: str | None = None,
) -> list[str]:
    errors: list[str] = []

    repo = _field_value(text, "CONTROL_PLANE_AUTHORITY_REPO")
    self_check_sha = _field_value(text, "SELF_CHECK_CONTROL_PLANE_SHA")
    freshness = _field_value(text, "CONTROL_PLANE_FRESHNESS_CHECK")

    if repo is None:
        errors.append("missing CONTROL_PLANE_AUTHORITY_REPO")
    elif repo != CONTROL_PLANE_REPO:
        errors.append(
            f"CONTROL_PLANE_AUTHORITY_REPO must be {CONTROL_PLANE_REPO}, got {repo!r}"
        )

    if self_check_sha is None:
        errors.append("missing SELF_CHECK_CONTROL_PLANE_SHA")
    elif not SHA_RE.fullmatch(self_check_sha):
        errors.append(
            f"SELF_CHECK_CONTROL_PLANE_SHA must be exact 40-hex, got {self_check_sha!r}"
        )

    if freshness is None:
        errors.append("missing CONTROL_PLANE_FRESHNESS_CHECK")
    elif freshness.upper() != "PASS":
        errors.append(f"CONTROL_PLANE_FRESHNESS_CHECK must be PASS, got {freshness!r}")

    if (
        current_control_plane_sha is not None
        and self_check_sha is not None
        and SHA_RE.fullmatch(self_check_sha)
        and self_check_sha != current_control_plane_sha
    ):
        errors.append(
            "CONTROL_PLANE_DRIFT: "
            f"current {CONTROL_PLANE_REPO}/main={current_control_plane_sha}, "
            f"SELF_CHECK_CONTROL_PLANE_SHA={self_check_sha}"
        )

    return [f"{path}: {error}" for error in errors]


def validate_paths(
    paths: Iterable[str],
    *,
    verify_remote: bool,
    token: str | None,
) -> dict:
    checked: list[str] = []
    errors: list[str] = []
    current_sha: str | None = None
    if verify_remote:
        try:
            current_sha = github_main_sha(CONTROL_PLANE_REPO, token)
        except RuntimeError as exc:
            return {
                "checked_task_cards": [],
                "control_plane_sha": None,
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
        errors.extend(
            validate_task_card(
                text,
                path=raw,
                current_control_plane_sha=current_sha,
            )
        )

    return {
        "checked_task_cards": checked,
        "control_plane_sha": current_sha,
        "errors": errors,
    }


def validate_pr_body(
    event_path: str | None,
    *,
    current_control_plane_sha: str | None,
) -> list[str]:
    if not event_path:
        return []
    path = Path(event_path)
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    body = ((payload.get("pull_request") or {}).get("body") or "")
    if not body or not looks_like_task_card("PR_BODY", body):
        return []
    return validate_task_card(
        body,
        path="PR_BODY",
        current_control_plane_sha=current_control_plane_sha,
    )


def changed_files(base_ref: str) -> list[str]:
    import subprocess

    proc = subprocess.run(
        ["git", "diff", "--name-only", f"{base_ref}...HEAD"],
        check=True,
        text=True,
        capture_output=True,
    )
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


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

    result = validate_paths(
        dict.fromkeys(paths),
        verify_remote=args.verify_remote_control_plane,
        token=os.getenv("GITHUB_TOKEN"),
    )
    result["errors"].extend(
        validate_pr_body(
            args.event_path,
            current_control_plane_sha=result.get("control_plane_sha"),
        )
    )
    result["status"] = "PASS" if not result["errors"] else "FAIL"

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"RD1_CONTROL_PLANE_FRESHNESS_GATE={result['status']}")
        if result.get("control_plane_sha"):
            print(f"control_plane_sha={result['control_plane_sha']}")
        for item in result["checked_task_cards"]:
            print(f"checked: {item}")
        for error in result["errors"]:
            print(f"ERROR: {error}")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
