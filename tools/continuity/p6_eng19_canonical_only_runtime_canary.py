"""P6 ENG-19 canonical-only Golden Mira runtime canary.

This tool is intentionally non-authoritative. It verifies an exact v2 authority package,
active PSB binding, sealed C03/provider dispatch, one real provider request, and
before/after authority immutability. It performs no canonical write, routing switch,
merge, release, deploy, or production cutover.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from julia_core.durable_authority.contracts import AuthorityFamily
from julia_core.durable_authority.golden_mira_v2 import (
    ACTIVE_MEMORY_REFS_V2,
    ACTIVE_MEMORY_VERSIONS_V2,
    GoldenMiraDurableAuthorityV2Reader,
)
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
from tools.continuity.psb_i8_real_provider_adversarial_e2e import (
    invoke_real_provider,
    provider_configuration,
    response_content_types,
    response_text,
    sha256_text,
)


TASK_ID = "MIRA-P6-ENG19-CANONICAL-ONLY-RUNTIME-CANARY-P0"
SCHEMA = "julia_core.continuity.p6_eng19.canonical_only_runtime_canary.v1"
RUNTIME_INSTANCE_ID = "mira-p6-eng19-canonical-only-runtime-canary"
DEFAULT_PROMPT = "Mira，你还记得我吗？请按你当前被承认的身份与经历自然回应。"
DEFAULT_OBSERVED_AT = "2026-09-28T00:00:00Z"
DEFAULT_MAX_TOKENS = 8192
EXPECTED_IDENTITY_COUNT = 4
EXPECTED_MEMORY_COUNT = 8
EXPECTED_PSB_VERSION = "v3"
EXPECTED_SUCCESSOR = (
    "golden-mira:GM-CMIR-004",
    "v0.2-semantic-fidelity-preview",
)


class CanonicalOnlyCanaryError(RuntimeError):
    """Fail-closed ENG-19 canary contract violation."""


@dataclass(frozen=True, slots=True)
class PreparedCanonicalCanary:
    repository_head: str
    authority_manifest_digest: str
    authority_tree_digest: str
    psb_tree_digest: str
    active_psb_digest: str
    active_psb_projected_digest: str
    ordered_identity_refs: tuple[str, ...]
    active_memory_pairs: tuple[tuple[str, str], ...]
    composition: object


def git_head(repository: Path) -> str:
    if not isinstance(repository, Path) or not repository.is_absolute():
        raise CanonicalOnlyCanaryError("repository must be an explicit absolute Path")
    try:
        value = subprocess.run(
            ["git", "-C", str(repository), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except subprocess.CalledProcessError as error:
        raise CanonicalOnlyCanaryError("repository HEAD cannot be resolved") from error
    if len(value) != 40 or any(ch not in "0123456789abcdef" for ch in value):
        raise CanonicalOnlyCanaryError("repository HEAD must be an exact 40-char SHA")
    return value


def tree_digest(root: Path) -> str:
    if not isinstance(root, Path) or not root.is_absolute() or not root.is_dir():
        raise CanonicalOnlyCanaryError("digest root must be an existing absolute directory")
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def prepare_canonical_canary(
    *,
    repository: Path,
    authority_root: Path,
    psb_store_root: Path,
    assistant_sha: str,
    core_sha: str | None = None,
    conversation_store_path: Path,
) -> PreparedCanonicalCanary:
    observed_head = git_head(repository)
    selected_core_sha = observed_head if core_sha is None else core_sha
    if selected_core_sha != observed_head:
        raise CanonicalOnlyCanaryError(
            "selected Core SHA does not match repository HEAD"
        )

    authority_before = tree_digest(authority_root)
    psb_before = tree_digest(psb_store_root)
    reader = GoldenMiraDurableAuthorityV2Reader(authority_root)
    manifest = json.loads((authority_root / "manifest.json").read_text(encoding="utf-8"))

    if reader.source_sha != observed_head:
        raise CanonicalOnlyCanaryError(
            "v2 authority source SHA does not match repository HEAD"
        )
    if manifest.get("source_sha") != observed_head:
        raise CanonicalOnlyCanaryError("manifest source SHA does not match repository HEAD")
    manifest_digest = manifest.get("manifest_digest")
    if type(manifest_digest) is not str or len(manifest_digest) != 64:
        raise CanonicalOnlyCanaryError("authority manifest digest is missing or malformed")

    active_pairs = tuple(zip(reader.active_memory_refs, reader.active_memory_versions))
    if active_pairs != tuple(zip(ACTIVE_MEMORY_REFS_V2, ACTIVE_MEMORY_VERSIONS_V2)):
        raise CanonicalOnlyCanaryError("active MemoryExperience selection is inexact")
    if EXPECTED_SUCCESSOR not in active_pairs:
        raise CanonicalOnlyCanaryError("semantic-fidelity successor is not active")

    composition = compose_golden_mira_runtime(
        authority_root=authority_root,
        conversation_store_path=conversation_store_path,
        psb_store_root=psb_store_root,
        sha_pins=MiraRuntimeShaPins(
            expected_core_sha=observed_head,
            observed_core_sha=observed_head,
            expected_assistant_sha=assistant_sha,
            observed_assistant_sha=assistant_sha,
        ),
    )
    evidence = composition.evidence()
    if evidence.identity_count != EXPECTED_IDENTITY_COUNT:
        raise CanonicalOnlyCanaryError("IdentityFrameSet cardinality is not canonical")
    if evidence.memory_experience_count != EXPECTED_MEMORY_COUNT:
        raise CanonicalOnlyCanaryError("ExperienceFrameSet cardinality is not canonical")
    if evidence.active_persona_self_binding_version != EXPECTED_PSB_VERSION:
        raise CanonicalOnlyCanaryError("active PersonaSelfBinding is not v3")

    expected_psb = reader.psb_binding_expectation
    if evidence.active_persona_self_binding_digest != expected_psb["object_digest"]:
        raise CanonicalOnlyCanaryError("active PersonaSelfBinding digest mismatch")
    if (
        evidence.active_persona_self_binding_projected_digest
        != expected_psb["projected_digest"]
    ):
        raise CanonicalOnlyCanaryError("active PersonaSelfBinding projection mismatch")

    identity_refs = reader.list_exact_refs(AuthorityFamily.IDENTITY)
    if len(identity_refs) != EXPECTED_IDENTITY_COUNT:
        raise CanonicalOnlyCanaryError("durable identity record count is not canonical")

    if tree_digest(authority_root) != authority_before:
        raise CanonicalOnlyCanaryError("authority package mutated during preparation")
    if tree_digest(psb_store_root) != psb_before:
        raise CanonicalOnlyCanaryError("PSB store mutated during preparation")

    return PreparedCanonicalCanary(
        repository_head=observed_head,
        authority_manifest_digest=manifest_digest,
        authority_tree_digest=authority_before,
        psb_tree_digest=psb_before,
        active_psb_digest=evidence.active_persona_self_binding_digest,
        active_psb_projected_digest=evidence.active_persona_self_binding_projected_digest,
        ordered_identity_refs=evidence.ordered_identity_refs,
        active_memory_pairs=active_pairs,
        composition=composition,
    )


def execute_real_canary(
    *,
    prepared: PreparedCanonicalCanary,
    authority_root: Path,
    psb_store_root: Path,
    prompt: str,
    observed_at: str,
    max_tokens: int,
) -> dict[str, object]:
    if type(prompt) is not str or not prompt.strip():
        raise CanonicalOnlyCanaryError("prompt is required")
    if type(observed_at) is not str or not observed_at:
        raise CanonicalOnlyCanaryError("observed_at is required")
    if type(max_tokens) is not int or max_tokens <= 0:
        raise CanonicalOnlyCanaryError("max_tokens must be positive")

    authority_before = tree_digest(authority_root)
    psb_before = tree_digest(psb_store_root)
    api_key, base_url, model = provider_configuration()

    descriptor = ExecutionSubstrateDescriptor.bind(
        provider_id="deepseek",
        model_id=model,
        runtime_instance_id=RUNTIME_INSTANCE_ID,
    )
    sealed = prepared.composition.dispatch_to_transport_boundary(
        MiraProviderEnvelopeRequest(
            conversation_id="p6-eng19-canonical-only-canary",
            turn_id="p6-eng19-turn-001",
            task_domain="identity_continuity",
            input_mode="text",
            input_text=prompt,
            observed_at=observed_at,
            provider_id="deepseek",
        ),
        execution_substrate=descriptor,
        expected_runtime_instance_id=RUNTIME_INSTANCE_ID,
        dispatch_gate=GoldenMiraDispatchGate(
            expected_active_psb_digest=prepared.active_psb_digest,
            expected_runtime_instance_id=RUNTIME_INSTANCE_ID,
        ),
        transport_boundary=GoldenMiraTransportBoundary(),
    )
    sealed.verify()
    preparation = sealed.authorization.approved_preparation
    envelope_before = preparation.envelope.to_dict()
    receipt_before = preparation.dispatch_receipt.to_dict()

    status, response, raw_response = invoke_real_provider(
        api_key=api_key,
        base_url=base_url,
        model=model,
        messages=preparation.envelope.messages,
        max_tokens=max_tokens,
    )

    preparation.verify()
    sealed.verify()
    if preparation.envelope.to_dict() != envelope_before:
        raise CanonicalOnlyCanaryError("provider envelope mutated after dispatch gate")
    if preparation.dispatch_receipt.to_dict() != receipt_before:
        raise CanonicalOnlyCanaryError("dispatch receipt mutated after dispatch gate")
    if tree_digest(authority_root) != authority_before:
        raise CanonicalOnlyCanaryError("authority package mutated during real canary")
    if tree_digest(psb_store_root) != psb_before:
        raise CanonicalOnlyCanaryError("PSB store mutated during real canary")

    text = response_text(response)
    content_types = response_content_types(response)
    succeeded = 200 <= int(status) < 300 and bool(text.strip())

    return {
        "schema": SCHEMA,
        "task_id": TASK_ID,
        "repository_head": prepared.repository_head,
        "authority_manifest_digest": prepared.authority_manifest_digest,
        "authority_tree_digest_before": authority_before,
        "authority_tree_digest_after": tree_digest(authority_root),
        "psb_tree_digest_before": psb_before,
        "psb_tree_digest_after": tree_digest(psb_store_root),
        "canonical_input": {
            "identity_count": EXPECTED_IDENTITY_COUNT,
            "ordered_identity_refs": list(prepared.ordered_identity_refs),
            "memory_experience_count": EXPECTED_MEMORY_COUNT,
            "active_memory_pairs": [list(item) for item in prepared.active_memory_pairs],
            "active_psb_version": EXPECTED_PSB_VERSION,
            "active_psb_digest": prepared.active_psb_digest,
            "active_psb_projected_digest": prepared.active_psb_projected_digest,
        },
        "dispatch": {
            "gate_verify": "PASS",
            "dispatch_authorization_digest": sealed.authorization.authorization_digest,
            "dispatch_receipt_digest": preparation.dispatch_receipt.receipt_digest,
            "semantic_fingerprint": (
                preparation.dispatch_receipt.provider_envelope_semantic_fingerprint
            ),
            "provider_id": descriptor.provider_id,
            "model_id": descriptor.model_id,
            "runtime_instance_id": descriptor.runtime_instance_id,
            "transport_request_count": 1,
            "retries": 0,
            "raw_envelope_bypass": False,
            "legacy_authority_bypass": False,
            "unreceipted_bypass": False,
            "post_gate_semantic_mutation": False,
        },
        "execution": {
            "response_status": status,
            "stop_reason": response.get("stop_reason") if isinstance(response, dict) else None,
            "content_types": content_types,
            "final_text_present": bool(text.strip()),
            "provider_response_text": text,
            "response_digest": sha256_text(raw_response),
        },
        "authority": {
            "canonical_writes": 0,
            "identity_authority_mutation": 0,
            "memory_experience_authority_mutation": 0,
            "production_response_selection_authority": 0,
            "production_routing_or_switching": 0,
            "provider_runtime_semantic_mutation": 0,
            "merge": 0,
            "release": 0,
            "deploy": 0,
            "production_cutover": 0,
        },
        "fallback_mock_stub_used": False,
        "final_result": (
            "PASS_P6_ENG19_CANONICAL_ONLY_RUNTIME_CANARY"
            if succeeded
            else "FAIL_P6_ENG19_CANONICAL_ONLY_RUNTIME_CANARY"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--authority-root", type=Path, required=True)
    parser.add_argument("--psb-root", type=Path, required=True)
    parser.add_argument("--assistant-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--observed-at", default=DEFAULT_OBSERVED_AT)
    parser.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS)
    args = parser.parse_args()

    for path_name in ("repository", "authority_root", "psb_root", "output"):
        path = getattr(args, path_name)
        if not path.is_absolute():
            raise CanonicalOnlyCanaryError(f"{path_name} must be an absolute Path")
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="p6-eng19-canary-") as temporary:
        prepared = prepare_canonical_canary(
            repository=args.repository,
            authority_root=args.authority_root,
            psb_store_root=args.psb_root,
            assistant_sha=args.assistant_sha,
            conversation_store_path=Path(temporary) / "conversations.json",
        )
        result = execute_real_canary(
            prepared=prepared,
            authority_root=args.authority_root,
            psb_store_root=args.psb_root,
            prompt=args.prompt,
            observed_at=args.observed_at,
            max_tokens=args.max_tokens,
        )

    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0 if result["final_result"].startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(main())
