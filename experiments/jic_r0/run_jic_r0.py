#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CASES = ROOT / "cases"
RESULTS = ROOT / "results"
SHELL = ROOT / "prompts" / "generic_reasoning_shell.md"
CORE_SOURCES = {
    "theme_lifecycle": ("bcf91d547d247e25016037d70d99dcdef227dc40", "docs/rd1/cognition/GIC-001_THEME_LIFECYCLE.md"),
    "leader_divergence": ("ef1f4137faa7ac16f3e58e9cbaa8c5231f7725f0", "docs/rd1/cognition/GIC-002_LEADER_DIVERGENCE.md"),
    "weak_to_strong": ("59c21f3aeadf67fadfe2c70019287af104dc1c0a", "docs/rd1/cognition/GIC-003_WEAK_TO_STRONG.md"),
}
CARD_SOURCES = {
    "theme_lifecycle": "strategy_knowledge/cards/theme_lifecycle.json",
    "leader_divergence": "strategy_knowledge/cards/leader_divergence.json",
    "weak_to_strong": "strategy_knowledge/cards/weak_to_strong.json",
}
CARD_SHA = "f1bc3def72e0c4184799201aaf1ac5d02d6084d6"


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def blob_at(repo: Path, commit: str, path: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo), "show", f"{commit}:{path}"], text=True, stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as error:
        raise RuntimeError(f"cannot read {commit}:{path} in {repo}: {error.stderr.strip()}") from error


def validate_sources(core_repo: Path, market_repo: Path) -> None:
    for family, (commit, path) in CORE_SOURCES.items():
        blob_at(core_repo, commit, path)
    blob_at(market_repo, CARD_SHA, CARD_SOURCES["theme_lifecycle"])
    blob_at(market_repo, CARD_SHA, CARD_SOURCES["leader_divergence"])
    blob_at(market_repo, CARD_SHA, CARD_SOURCES["weak_to_strong"])


def prompt_for(case: dict, condition: str, core_repo: Path, market_repo: Path) -> str:
    prompt = SHELL.read_text(encoding="utf-8") + "\n\n# Question\n" + case["question"]
    model_visible_case = {
        "question": case["question"],
        "source": case["source"],
        "evidence_snapshot": case["evidence_snapshot"],
    }
    prompt += "\n\n# Case evidence and source\n```json\n" + json.dumps(model_visible_case, ensure_ascii=False, indent=2) + "\n```"
    if condition == "B":
        prompt += "\n\n# Historical cognition context (exact frozen source)\n```json\n" + blob_at(market_repo, CARD_SHA, CARD_SOURCES[case["family"]]) + "\n```"
    elif condition == "C":
        commit, path = CORE_SOURCES[case["family"]]
        prompt += "\n\n# Historical cognition context (exact frozen source)\n```markdown\n" + blob_at(core_repo, commit, path) + "\n```"
    return prompt


def extract_response_text(payload: dict) -> str:
    output_items = payload.get("output", [])
    if any(item.get("type") == "refusal" for item in output_items):
        raise ValueError("model returned a refusal item")
    texts = []
    for item in output_items:
        for content in item.get("content", []):
            content_type = content.get("type")
            if content_type == "refusal":
                raise ValueError("model returned refusal content")
            if content_type == "output_text":
                texts.append(content.get("text", ""))
    return "\n".join(texts)


def call_openai(prompt: str, model: str, api_key: str) -> dict:
    request_body = {
        "model": model,
        "input": prompt,
        "temperature": 0,
        "max_output_tokens": 3000,
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(request_body).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    started = time.time()
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            body = json.loads(response.read().decode("utf-8"))
            status = response.status
        if body.get("status") not in (None, "completed"):
            return {
                "http_status": status,
                "elapsed_ms": int((time.time() - started) * 1000),
                "response": body,
                "failure_kind": "incomplete_response_status",
                "failure_detail": str(body.get("status")),
            }
        try:
            output_text = extract_response_text(body)
        except ValueError as error:
            return {
                "http_status": status,
                "elapsed_ms": int((time.time() - started) * 1000),
                "response": body,
                "failure_kind": "refusal_or_non_text_response",
                "failure_detail": str(error),
            }
        if not output_text.strip():
            return {
                "http_status": status,
                "elapsed_ms": int((time.time() - started) * 1000),
                "response": body,
                "failure_kind": "empty_output_text",
            }
        return {
            "http_status": status,
            "elapsed_ms": int((time.time() - started) * 1000),
            "response": body,
            "output_text": output_text,
        }
    except urllib.error.HTTPError as error:
        try:
            body = json.loads(error.read().decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            body = {}
        status = error.code
        return {
            "http_status": status,
            "elapsed_ms": int((time.time() - started) * 1000),
            "response": body,
            "failure_kind": "http_error",
        }
    except urllib.error.URLError as error:
        return {
            "http_status": None,
            "elapsed_ms": int((time.time() - started) * 1000),
            "response": {},
            "failure_kind": "url_error",
            "failure_detail": type(error.reason).__name__,
        }
    except TimeoutError:
        return {
            "http_status": None,
            "elapsed_ms": int((time.time() - started) * 1000),
            "response": {},
            "failure_kind": "timeout",
        }
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {
            "http_status": None,
            "elapsed_ms": int((time.time() - started) * 1000),
            "response": {},
            "failure_kind": "json_decode",
        }
    except OSError as error:
        return {
            "http_status": None,
            "elapsed_ms": int((time.time() - started) * 1000),
            "response": {},
            "failure_kind": "transport_error",
            "failure_detail": type(error).__name__,
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--core-repo", type=Path, required=True)
    parser.add_argument("--market-repo", type=Path, required=True)
    args = parser.parse_args()
    run_id = os.environ.get("JIC_R0_RUN_ID") or time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    output = RESULTS / f"run-{run_id}"
    provider = os.environ.get("JIC_R0_PROVIDER", "")
    model = os.environ.get("JIC_R0_MODEL", "")
    api_key = os.environ.get("OPENAI_API_KEY", "")
    blocking: list[str] = []
    if provider != "openai":
        blocking.append("JIC_R0_PROVIDER must equal openai")
    if not model:
        blocking.append("JIC_R0_MODEL is required")
    if not api_key:
        blocking.append("OPENAI_API_KEY is required")
    try:
        validate_sources(args.core_repo.resolve(), args.market_repo.resolve())
    except RuntimeError as error:
        blocking.append(str(error))
    if blocking:
        write_json(output / "BLOCKED.json", {"status": "BLOCKED", "blocking_reasons": blocking, "run_id": run_id})
        return 2

    mappings = []
    for case_path in sorted(CASES.glob("*.json")):
        case = json.loads(case_path.read_text(encoding="utf-8"))
        for condition in ("A", "B", "C"):
            prompt = prompt_for(case, condition, args.core_repo.resolve(), args.market_repo.resolve())
            result = call_openai(prompt, model, api_key)
            response_key = "r_" + uuid.uuid4().hex
            failure_kind = result.get("failure_kind")
            if failure_kind:
                write_json(output / "BLOCKED.json", {
                    "status": "BLOCKED",
                    "run_id": run_id,
                    "blocking_reasons": [f"real OpenAI request failed with {failure_kind}; no fallback permitted"],
                    "last_request": {
                        "case_id": case["case_id"],
                        "condition": condition,
                        "http_status": result["http_status"],
                        "failure_kind": failure_kind,
                        **({"failure_detail": result["failure_detail"]} if result.get("failure_detail") else {}),
                    },
                })
                return 3
            write_json(output / "raw" / f"{response_key}.json", {"response_key": response_key, "verbatim_output": result["output_text"], "http_status": result["http_status"]})
            write_json(output / "prompts" / f"{response_key}.json", {
                "response_key": response_key,
                "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                "prompt_verbatim": prompt,
            })
            mappings.append({"case_id": case["case_id"], "condition": condition, "response_key": response_key})
    write_json(output / "mapping.sealed.json", mappings)
    write_json(output / "manifest.json", {
        "run_id": run_id,
        "status": "COMPLETE",
        "provider": "openai",
        "model": model,
        "settings": {"temperature": 0, "max_output_tokens": 3000},
        "core_source_sha_validated": True,
        "strategy_card_source_sha_validated": True,
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
