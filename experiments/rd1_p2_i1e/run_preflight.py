#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
from dataclasses import is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile
from typing import Any
from uuid import uuid4

CORE_ACCEPTED_SHA = "71919611416ad8c440f8a2d06995947181d846f4"
MARKET_ACCEPTED_SHA = "0e6b599614842085e3f6cb505a0695ae5a80d1c3"
ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
LINKAGE_ALLOWED_FIELDS = {
    "subject_key", "theme_id", "theme_name", "stock_id", "stock_name",
    "relation_type_candidate", "mapping_scope", "source_type", "reason",
    "remark", "confidence", "top", "sort", "stock_remark",
}
LINKAGE_FORBIDDEN_FIELDS = {"detail_html", "price", "pct_chg"}


class PreflightHarnessError(RuntimeError):
    """Expected harness prerequisite failure that must produce a BLOCKED artifact."""


def run_git(repo: Path, arguments: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *arguments],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def verify_candidate(repo: Path, commit: str, label: str) -> None:
    result = run_git(repo, ["cat-file", "-e", f"{commit}^{{commit}}"])
    if result.returncode != 0:
        raise PreflightHarnessError(f"{label} candidate {commit} is unavailable in {repo}")


def extract_archive(repo: Path, commit: str, destination: Path) -> None:
    process = subprocess.Popen(
        ["git", "-C", str(repo), "archive", "--format=tar", commit],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert process.stdout is not None
    try:
        with tarfile.open(fileobj=process.stdout, mode="r|") as archive:
            archive.extractall(destination, filter="data")
    finally:
        process.stdout.close()
        stderr = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
        return_code = process.wait()
    if return_code != 0:
        raise PreflightHarnessError(f"git archive failed for {commit}: {stderr.strip()}")


def materialize_candidates(core_repo: Path, market_repo: Path, root: Path) -> tuple[Path, Path]:
    verify_candidate(core_repo, CORE_ACCEPTED_SHA, "Core")
    verify_candidate(market_repo, MARKET_ACCEPTED_SHA, "Market")
    core_root = root / "core-candidate"
    market_root = root / "market-candidate"
    core_root.mkdir()
    market_root.mkdir()
    extract_archive(core_repo, CORE_ACCEPTED_SHA, core_root)
    extract_archive(market_repo, MARKET_ACCEPTED_SHA, market_root)
    for path in (str(core_root), str(market_root)):
        if path not in sys.path:
            sys.path.insert(0, path)
    return core_root, market_root


def plain(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        from dataclasses import asdict
        return {key: plain(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(item) for item in value]
    return value


def json_safe(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return value


def sanitize(value: Any) -> Any:
    if isinstance(value, str):
        value = re.sub(r"(?i)(postgresql?://[^:@/\s]+:)[^@\s]+(@)", r"\1***\2", value)
        return re.sub(r"(?i)(authorization['\"]?\s*[:=]\s*)\S+", r"\1***", value)
    if isinstance(value, dict):
        return {key: sanitize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [sanitize(item) for item in value]
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sanitize(json_safe(value)), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class RecordingProvider:
    def __init__(self, real_provider: Any) -> None:
        self.real_provider = real_provider
        self.last_envelope: Any = None

    async def execute(self, capability: str, request: Any, *, request_id: str | None = None, correlation_id: str | None = None) -> Any:
        self.last_envelope = await self.real_provider.execute(
            capability,
            request,
            request_id=request_id,
            correlation_id=correlation_id,
        )
        return self.last_envelope

    async def close(self) -> None:
        close = getattr(self.real_provider, "close", None)
        if close is not None:
            await close()


async def isolated_negative_matrix() -> list[dict[str, Any]]:
    from market_public import MarketPublicFactory  # noqa: F401 - proves exact module is importable
    from market_public import MarketProvenance, MarketResultEnvelope
    from market_public.contracts import MarketDataState, MarketFailure, MarketFailureKind, MarketOperationStatus
    from julia_core.capability.models import CapabilityRequest
    from julia_core.capability.providers.market_public import MarketPublicProviderAdapter, _to_plain_mapping
    from julia_core.runtime.capability_bridge import RuntimeCapabilityBridge

    class FixtureProvider:
        def __init__(self) -> None:
            self.calls = []

        async def execute(self, capability: str, request: Any, *, request_id: str | None = None, correlation_id: str | None = None) -> MarketResultEnvelope:
            self.calls.append((capability, request, request_id, correlation_id))
            return MarketResultEnvelope(
                contract_version="0.3.0",
                capability_id=capability,
                request_id=request_id,
                correlation_id=correlation_id or "isolated",
                operation_status=MarketOperationStatus.FAILURE,
                data_state=MarketDataState.NOT_APPLICABLE,
                payload=None,
                provenance=MarketProvenance(None, produced_at="2026-09-19T00:00:00Z"),
                failures=(MarketFailure(MarketFailureKind.CONTRACT_MISMATCH, "invalid_request", "isolated invalid request"),),
                boundary_identity_ref="market.public",
                runtime_observation=None,
                produced_at="2026-09-19T00:00:00Z",
            )

    class ExplodingProvider(FixtureProvider):
        async def execute(self, capability: str, request: Any, *, request_id: str | None = None, correlation_id: str | None = None) -> MarketResultEnvelope:
            self.calls.append((capability, request, request_id, correlation_id))
            raise RuntimeError("isolated pre-envelope provider exception")

    def bind(provider: Any) -> tuple[Any, MarketPublicProviderAdapter, Any]:
        adapter = MarketPublicProviderAdapter(provider)
        bridge = RuntimeCapabilityBridge()
        bridge.register_provider("market", adapter)
        bridge.initialize()
        return bridge, adapter, provider

    records = []

    missing_bridge = RuntimeCapabilityBridge()
    missing_bridge.initialize()
    missing = await missing_bridge.manager.execute_typed(CapabilityRequest("market.product.read", {"subject_key": "9043089"}))
    records.append({
        "classification": "ISOLATED_UNIT_ONLY",
        "outcome": "missing_core_market_binding",
        "core_status": missing.tool_result.status.value,
        "error_code": missing.tool_result.error["code"],
    })

    fixture = FixtureProvider()
    c08_bridge, _, _ = bind(fixture)
    c08_bridge.policy.remove_scope("market.observe")
    denied = await c08_bridge.manager.execute_typed(CapabilityRequest("market.product.read", {"subject_key": "9043089"}))
    records.append({
        "classification": "ISOLATED_UNIT_ONLY",
        "outcome": "c08_denial_before_provider",
        "allowed": denied.authorization_decision.allowed,
        "provider_invoked": bool(fixture.calls),
    })

    exploding_bridge, _, exploding = bind(ExplodingProvider())
    exception_result = await exploding_bridge.manager.execute_typed(CapabilityRequest("market.event.read", {"event_id": 8410}))
    records.append({
        "classification": "ISOLATED_UNIT_ONLY",
        "outcome": "pre_envelope_provider_exception",
        "core_status": exception_result.tool_result.status.value,
        "provider_invoked": bool(exploding.calls),
    })
    return records


async def run_real_preflight() -> dict[str, Any]:
    from market_public import MarketPublicFactory
    from julia_core.capability.models import CapabilityRequest
    from julia_core.capability.providers.market_public import MarketPublicProviderAdapter, _to_plain_mapping
    from julia_core.runtime.capability_bridge import RuntimeCapabilityBridge

    real_provider = MarketPublicFactory.create()
    provider = RecordingProvider(real_provider)
    adapter = MarketPublicProviderAdapter(provider)
    bridge = RuntimeCapabilityBridge()
    bridge.register_provider("market", adapter)
    bridge.initialize()

    cases = [
        {
            "capability_id": "market.event.resolve",
            "arguments": {"feed_date": "2026-05-19", "stock_id": None, "limit": 200},
            "case_source": "real exact-date structured event feed; identity selected only from READY resolve payload",
        },
        {
            "capability_id": "market.event.read",
            "arguments": None,
            "case_source": "evaluate_service/output/baselines/pm_e2e_phase47_final_100_20260519/sps_payload.json item event:8410:9043089",
        },
        {
            "capability_id": "market.product.read",
            "arguments": {"subject_key": "9043089"},
            "case_source": "same source-bound event subject identity",
        },
        {
            "capability_id": "market.product.linkage.read",
            "arguments": {"subject_key": "9043089", "mapping_scope": "all", "include_leaders": True, "limit": 100},
            "case_source": "same source-bound event subject identity",
        },
        {
            "capability_id": "market.state.read",
            "arguments": {"trade_date": "2026-05-15"},
            "case_source": "same SPS payload exact trade_date",
        },
    ]
    records = []
    envelope_by_capability = {}
    try:
        for case in cases:
            arguments = case["arguments"]
            if arguments is None:
                resolve = envelope_by_capability.get("market.event.resolve")
                event_id = None
                identity_source = None
                if resolve is not None and resolve.get("data_state") == "READY" and isinstance(resolve.get("payload"), list):
                    for row in resolve["payload"]:
                        item_id = row.get("item_id") if isinstance(row, dict) else None
                        if isinstance(item_id, str) and len(item_id.split(":")) >= 3:
                            parts = item_id.split(":")
                            candidate = parts[1] if parts[1].isdigit() else (parts[2] if parts[:2] == ["event", "jyhf_cdp"] and parts[2].isdigit() else None)
                            if candidate is not None:
                                event_id = int(candidate)
                                identity_source = "market.event.resolve READY payload"
                                break
                if event_id is None or identity_source is None:
                    raise PreflightHarnessError("event.read identity unresolved; refusing to invent an identity")
                arguments = {"event_id": event_id}
                case["identity_source"] = identity_source
            request_id = "core-" + uuid4().hex
            correlation_id = "i1e-" + uuid4().hex
            outcome = await bridge.manager.execute_typed(
                CapabilityRequest(case["capability_id"], arguments, capability_request_id=request_id, correlation_id=correlation_id)
            )
            envelope = provider.last_envelope
            envelope_plain = plain(envelope)
            structured = outcome.tool_result.structured_output if outcome.tool_result is not None else None
            semantic_match = structured == _to_plain_mapping(envelope)
            record = {
                "classification": "REAL_PRIMARY",
                "capability_id": case["capability_id"],
                "request_id": request_id,
                "correlation_id": correlation_id,
                "request_arguments": arguments,
                "case_source": case["case_source"],
                "core_execution_outcome": outcome.tool_result.status.value if outcome.tool_result is not None else "error",
                "core_error": outcome.tool_result.error if outcome.tool_result is not None and outcome.tool_result.error else None,
                "market_envelope": envelope_plain,
                "core_structured_output": structured,
                "semantic_match": semantic_match,
            }
            if case["capability_id"] == "market.event.read":
                record["identity_source"] = case.get("identity_source")
            records.append(record)
            envelope_by_capability[case["capability_id"]] = envelope_plain

        invalid_request_id = "core-invalid-" + uuid4().hex
        invalid_correlation_id = "i1e-invalid-" + uuid4().hex
        invalid = await bridge.manager.execute_typed(
            CapabilityRequest(
                "market.event.resolve",
                {"feed_date": "2026-05-19", "stock_id": None, "limit": 0},
                capability_request_id=invalid_request_id,
                correlation_id=invalid_correlation_id,
            )
        )
        invalid_envelope = plain(provider.last_envelope)
        records.append({
            "classification": "REAL_PRIMARY_NEGATIVE",
            "capability_id": "market.event.resolve",
            "request_id": invalid_request_id,
            "correlation_id": invalid_correlation_id,
            "request_arguments": {"feed_date": "2026-05-19", "stock_id": None, "limit": 0},
            "case_source": "mechanically invalid contract request",
            "core_execution_outcome": invalid.tool_result.status.value,
            "market_envelope": invalid_envelope,
            "core_structured_output": invalid.tool_result.structured_output,
            "semantic_match": invalid.tool_result.structured_output == _to_plain_mapping(provider.last_envelope),
        })
    finally:
        await provider.close()

    linkage = envelope_by_capability["market.product.linkage.read"]
    linkage_check = {
        "data_state": linkage.get("data_state"),
        "checked": linkage.get("data_state") == "READY",
        "forbidden_fields_absent": None,
        "only_narrow_fields_present": None,
        "source_type_preserved": None,
    }
    if linkage_check["checked"]:
        rows = linkage.get("payload") if isinstance(linkage.get("payload"), list) else []
        keys = {key for row in rows if isinstance(row, dict) for key in row}
        linkage_check["forbidden_fields_absent"] = not (keys & LINKAGE_FORBIDDEN_FIELDS)
        linkage_check["only_narrow_fields_present"] = keys <= LINKAGE_ALLOWED_FIELDS
        linkage_check["source_type_preserved"] = all(isinstance(row.get("source_type"), str) and row.get("source_type") for row in rows)

    state = envelope_by_capability["market.state.read"]
    state_payload = state.get("payload") if isinstance(state.get("payload"), dict) else {}
    state_check = {
        "data_state": state.get("data_state"),
        "requested_trade_date": "2026-05-15",
        "ready_trade_date_exact": None,
        "source_identity_present": None,
    }
    if state.get("data_state") == "READY":
        state_check["ready_trade_date_exact"] = str(state_payload.get("trade_date")) == "2026-05-15"
        state_check["source_identity_present"] = bool(state_payload.get("snapshot_version") or state_payload.get("batch_id") or state_payload.get("trace_id"))

    core_errors = [record for record in records if record["core_execution_outcome"] != "success" or not record.get("semantic_match", False)]
    unavailable = [record for record in records if record.get("market_envelope", {}).get("data_state") == "UNAVAILABLE"]
    dependency_unavailable = [
        record for record in unavailable
        if all(failure.get("kind") == "MarketUnavailable" for failure in record.get("market_envelope", {}).get("failures", []))
    ]
    outcome = "REAL_INTEGRATION_PASS"
    if core_errors:
        outcome = "FAIL_CORE_BINDING_OR_SEMANTICS"
    elif dependency_unavailable:
        outcome = "BLOCKED_REAL_MARKET_DEPENDENCY"
    elif unavailable:
        outcome = "FAIL_REAL_MARKET_INTERNAL_FAILURE"
    elif linkage_check["checked"] and not all((linkage_check["forbidden_fields_absent"], linkage_check["only_narrow_fields_present"], linkage_check["source_type_preserved"])):
        outcome = "FAIL_LINKAGE_PROJECTION"
    elif state_check["data_state"] == "READY" and not all((state_check["ready_trade_date_exact"], state_check["source_identity_present"])):
        outcome = "FAIL_EXACT_DATE_STATE"

    return {
        "status": outcome,
        "core_candidate_sha": CORE_ACCEPTED_SHA,
        "market_candidate_sha": MARKET_ACCEPTED_SHA,
        "five_capability_matrix": [
            {
                "capability_id": capability,
                "operation_status": envelope_by_capability[capability].get("operation_status"),
                "data_state": envelope_by_capability[capability].get("data_state"),
                "core_status": next(record["core_execution_outcome"] for record in records if record["capability_id"] == capability and record["classification"] == "REAL_PRIMARY"),
                "semantic_match": next(record["semantic_match"] for record in records if record["capability_id"] == capability and record["classification"] == "REAL_PRIMARY"),
            }
            for capability in (
                "market.event.resolve",
                "market.event.read",
                "market.product.read",
                "market.product.linkage.read",
                "market.state.read",
            )
        ],
        "linkage_projection_check": linkage_check,
        "exact_state_check": state_check,
        "raw_call_records": records,
    }


async def execute_self_test() -> dict[str, Any]:
    records = await isolated_negative_matrix()
    return {"status": "PASS", "classification": "ISOLATED_UNIT_ONLY", "records": records}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--core-repo", type=Path, required=True)
    parser.add_argument("--market-repo", type=Path, required=True)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run-id", default=None)
    arguments = parser.parse_args()
    run_id = arguments.run_id or datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    output = RESULTS / f"run-{run_id}"
    try:
        with tempfile.TemporaryDirectory(prefix="rd1-p2-i1e-") as temporary:
            materialize_candidates(arguments.core_repo.resolve(), arguments.market_repo.resolve(), Path(temporary))
            if arguments.self_test:
                result = asyncio.run(execute_self_test())
            else:
                isolated = asyncio.run(isolated_negative_matrix())
                result = asyncio.run(run_real_preflight())
                result["isolated_negative_matrix"] = isolated
    except PreflightHarnessError as error:
        write_json(output / "BLOCKED.json", {
            "status": "BLOCKED_PREFLIGHT_HARNESS",
            "failure_kind": type(error).__name__,
            "message": str(error),
            "core_candidate_sha": CORE_ACCEPTED_SHA,
            "market_candidate_sha": MARKET_ACCEPTED_SHA,
        })
        print(output / "BLOCKED.json")
        raise

    write_json(output / "preflight.json", result)
    write_json(output / "raw_calls.json", result.get("raw_call_records", []))
    print(output / "preflight.json")
    return 0 if result["status"] in {"PASS", "REAL_INTEGRATION_PASS"} else 3


if __name__ == "__main__":
    raise SystemExit(main())
