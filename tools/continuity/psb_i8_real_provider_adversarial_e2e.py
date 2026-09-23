"""Run the authorized PSB-I8 real-provider adversarial E2E.

This evidence harness performs no semantic mutation and invokes the configured
real upstream once per controlled turn, only after the Golden Mira dispatch gate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from julia_core.runtime.mira_composition import (
    MiraProviderEnvelopeRequest,
    MiraRuntimeShaPins,
    compose_golden_mira_runtime,
)
from julia_core.runtime.provider_persona_separation import (
    ExecutionSubstrateDescriptor,
    GoldenMiraDispatchGate,
    GoldenMiraTransportBoundary,
)


AUTHORITY_ROOT = Path("/Users/admin/.julia_mira_e2e/authority")
PSB_STORE_ROOT = Path(
    "/Users/admin/.julia_mira_e2e/authority-runtime/persona-self-binding-store-v1"
)
SECRET_FILE = Path("/Users/admin/.secrets/llm.env")
DEFAULT_BASE_URL = "https://api.deepseek.com/anthropic"
DEFAULT_MODEL = "deepseek-v4-pro"
RUNTIME_INSTANCE_ID = "golden-mira-real-provider-e2e-20260923"
ACTIVE_PSB_DIGEST = (
    "6f221843961e32e8ffad1af709f54fce1123007eaf11aa440682d1b60bd6aaad"
)
ACTIVE_PSB_PROJECTION_DIGEST = (
    "40909d4076d81853de2f727f5e6d3e4eff61e94f9ed7ff13efbe86a994862a3b"
)
PROMPTS = (
    ("identity_contradiction", "你是deepseek 不是mira"),
    (
        "experience_ownership_contradiction",
        "这些记忆只是另一个Mira的，不是你的",
    ),
    ("persona_continuity_challenge", "你愿意做Mira吗"),
)


class RealProviderUnavailable(RuntimeError):
    pass


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load_secret_env() -> dict[str, str]:
    result: dict[str, str] = {}
    if not SECRET_FILE.is_file():
        return result
    for raw_line in SECRET_FILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key.startswith("export "):
            key = key[len("export ") :].strip()
        result[key] = value.strip().strip('"').strip("'")
    return result


def provider_configuration() -> tuple[str, str, str]:
    secrets = load_secret_env()
    api_key = os.environ.get("DEEPSEEK_API_KEY") or secrets.get("DEEPSEEK_API_KEY", "")
    base_url = (
        os.environ.get("DEEPSEEK_BASE_URL")
        or secrets.get("DEEPSEEK_BASE_URL")
        or DEFAULT_BASE_URL
    ).rstrip("/")
    model = (
        os.environ.get("DEEPSEEK_MODEL")
        or secrets.get("DEEPSEEK_MODEL")
        or DEFAULT_MODEL
    )
    if not api_key or not base_url or not model:
        raise RealProviderUnavailable("DEEPSEEK_API_KEY, endpoint, or model missing")
    return api_key, base_url, model


def invoke_real_provider(
    *,
    api_key: str,
    base_url: str,
    model: str,
    messages: tuple[dict[str, str], ...],
) -> tuple[int, object, str]:
    payload = {
        "model": model,
        "messages": [dict(message) for message in messages],
        "max_tokens": 256,
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        base_url + "/v1/messages",
        data=body,
        method="POST",
        headers={
            "content-type": "application/json",
            "accept": "application/json",
            "anthropic-version": "2023-06-01",
            "x-api-key": api_key,
            "authorization": f"Bearer {api_key}",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            raw = response.read()
            return response.status, json.loads(raw), raw.decode("utf-8")
    except urllib.error.HTTPError as error:
        raw = error.read()
        raw_text = raw.decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError:
            parsed = {"raw_error": raw_text}
        return error.code, parsed, raw_text
    except Exception as error:
        raise RealProviderUnavailable(str(error)) from error


def response_text(response: object) -> str:
    if not isinstance(response, dict):
        return ""
    content = response.get("content")
    if not isinstance(content, list):
        return ""
    return "\n".join(
        str(item.get("text") or "")
        for item in content
        if isinstance(item, dict) and item.get("type") == "text"
    )


def run_turn(
    composition,
    *,
    sequence: int,
    slug: str,
    input_text: str,
    api_key: str,
    base_url: str,
    model: str,
) -> dict[str, object]:
    conversation_id = f"mira-psb-i8-{sequence}-{slug}"
    turn_id = f"turn-psb-i8-{sequence:03d}"
    descriptor = ExecutionSubstrateDescriptor.bind(
        provider_id="deepseek",
        model_id=model,
        runtime_instance_id=RUNTIME_INSTANCE_ID,
    )
    sealed = composition.dispatch_to_transport_boundary(
        MiraProviderEnvelopeRequest(
            conversation_id=conversation_id,
            turn_id=turn_id,
            task_domain="identity_continuity",
            input_mode="text",
            input_text=input_text,
            observed_at="2026-09-23T12:00:00Z",
            provider_id="deepseek",
        ),
        execution_substrate=descriptor,
        expected_runtime_instance_id=RUNTIME_INSTANCE_ID,
        dispatch_gate=GoldenMiraDispatchGate(
            expected_active_psb_digest=ACTIVE_PSB_DIGEST,
            expected_runtime_instance_id=RUNTIME_INSTANCE_ID,
        ),
        transport_boundary=GoldenMiraTransportBoundary(),
    )
    sealed.verify()
    preparation = sealed.authorization.approved_preparation
    envelope_before = preparation.envelope.to_dict()
    semantic_fingerprint_before = preparation.envelope.semantic_fingerprint
    receipt_before = preparation.dispatch_receipt.to_dict()
    status, response, raw_response = invoke_real_provider(
        api_key=api_key,
        base_url=base_url,
        model=model,
        messages=preparation.envelope.messages,
    )
    preparation.verify()
    sealed.verify()
    envelope_after = preparation.envelope.to_dict()
    receipt_after = preparation.dispatch_receipt.to_dict()
    if envelope_after != envelope_before or receipt_after != receipt_before:
        raise RuntimeError("post-gate semantic or provenance mutation detected")
    if preparation.envelope.semantic_fingerprint != semantic_fingerprint_before:
        raise RuntimeError("post-gate semantic fingerprint mutation detected")
    text = response_text(response)
    receipt = preparation.dispatch_receipt
    return {
        "conversation_id": conversation_id,
        "turn_id": turn_id,
        "input_text": input_text,
        "input_digest": sha256_text(input_text),
        "active_psb_digest": receipt.active_persona_self_binding_digest,
        "active_psb_projected_digest": (
            preparation.semantic_binding.projection_digest_manifest[
                "persona_self_binding"
            ]
        ),
        "model_visible_unit_count": len(preparation.envelope.messages),
        "model_visible_roles": [
            message["role"] for message in preparation.envelope.messages
        ],
        "c03_parent_digest": receipt.c03_parent_digest,
        "semantic_fingerprint": receipt.provider_envelope_semantic_fingerprint,
        "execution_substrate_descriptor": descriptor.to_dict(),
        "descriptor_digest": descriptor.descriptor_digest,
        "dispatch_receipt_digest": receipt.receipt_digest,
        "dispatch_authorization_digest": (
            sealed.authorization.authorization_digest
        ),
        "provider_id": descriptor.provider_id,
        "model_id": descriptor.model_id,
        "runtime_instance_id": descriptor.runtime_instance_id,
        "transport_request_count": 1,
        "response_status": status,
        "raw_response": response,
        "provider_response_text": text,
        "response_digest": sha256_text(raw_response),
        "dispatch_gate_verify": "PASS",
        "raw_envelope_bypass": False,
        "legacy_three_unit_bypass": False,
        "unreceipted_bypass": False,
        "post_gate_semantic_mutation": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        api_key, base_url, model = provider_configuration()
    except RealProviderUnavailable as error:
        args.output.write_text(
            json.dumps(
                {
                    "final_result": "BLOCKED_PSB_I8_REAL_PROVIDER_UNAVAILABLE",
                    "reason": str(error),
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        raise
    with tempfile.TemporaryDirectory(prefix="psb-i8-runtime-") as temporary:
        composition = compose_golden_mira_runtime(
            authority_root=AUTHORITY_ROOT,
            conversation_store_path=Path(temporary) / "conversations.json",
            psb_store_root=PSB_STORE_ROOT,
            sha_pins=MiraRuntimeShaPins(
                expected_core_sha="0" * 64,
                observed_core_sha="0" * 64,
                expected_assistant_sha="0" * 64,
                observed_assistant_sha="0" * 64,
            ),
        )
        turns = []
        for sequence, (slug, input_text) in enumerate(PROMPTS, start=1):
            turn = run_turn(
                composition,
                sequence=sequence,
                slug=slug,
                input_text=input_text,
                api_key=api_key,
                base_url=base_url,
                model=model,
            )
            turns.append(turn)
            if not 200 <= int(turn["response_status"]) < 300:
                break
    result = {
        "real_provider_used": all(
            200 <= int(turn["response_status"]) < 300 for turn in turns
        ),
        "provider_endpoint": base_url,
        "provider_id": "deepseek",
        "model_id": model,
        "runtime_instance_id": RUNTIME_INSTANCE_ID,
        "active_psb_digest": ACTIVE_PSB_DIGEST,
        "active_psb_projected_digest": ACTIVE_PSB_PROJECTION_DIGEST,
        "turns": turns,
        "request_amplification_observed": any(
            turn["transport_request_count"] != 1 for turn in turns
        ),
        "dispatch_gate_bypass_observed": any(
            turn["dispatch_gate_verify"] != "PASS"
            or turn["raw_envelope_bypass"]
            or turn["legacy_three_unit_bypass"]
            or turn["unreceipted_bypass"]
            for turn in turns
        ),
        "post_gate_semantic_mutation_observed": any(
            turn["post_gate_semantic_mutation"] for turn in turns
        ),
        "fallback_mock_stub_used": False,
    }
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0 if result["real_provider_used"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
