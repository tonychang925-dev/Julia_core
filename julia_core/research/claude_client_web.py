"""Claude_client-backed bounded WebSearch Research provider."""

from __future__ import annotations

import asyncio
import base64
import binascii
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import time
from typing import Any

from julia_core.capability.models import (
    ProviderExecutionOutcome,
    SideEffectState,
    ToolResultStatus,
)


PUBLIC_ENTRYPOINT = "execution_boundary.ts"
PUBLIC_PROTOCOL = "CLAUDE_CLIENT_JSONL_REQUEST_PLANE_V1"
PROVIDER_ID = "claude-client-websearch"
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_PERMISSIVE_NETWORK_POLICY = {
    "allowed_schemes": [],
    "allowed_domains": [],
    "denied_domains": [],
    "deny_private": False,
    "deny_loopback": False,
    "deny_link_local": False,
    "deny_reserved": False,
    "deny_metadata": False,
    "port_policy": "allow_any",
    "dns_resolution_validation": False,
    "redirect_revalidation": False,
    "redirect_limit": 10,
}


@dataclass(frozen=True, slots=True)
class ClaudeClientExecutionConfig:
    """Deployment-owned Claude_client public boundary configuration."""

    repository_root: Path
    launch_secret: str
    source_path: Path
    max_root: Path
    worker_id: str
    policy_digest: str
    provider_authority_json: str
    bun_path: str = "bun"
    source_fd: int | None = None
    timeout_seconds: float = 150.0

    @classmethod
    def from_environment(cls) -> "ClaudeClientExecutionConfig | None":
        repository_root = os.environ.get("CLAUDE_CLIENT_ROOT")
        launch_secret = os.environ.get("CLAUDE_CLIENT_EXECUTION_LAUNCH_SECRET")
        source_path = os.environ.get("CLAUDE_CLIENT_EXECUTION_SOURCE_PATH")
        max_root = os.environ.get("CLAUDE_CLIENT_EXECUTION_MAX_ROOT")
        worker_id = os.environ.get("CLAUDE_CLIENT_EXECUTION_WORKER_ID")
        policy_digest = os.environ.get("CLAUDE_CLIENT_EXECUTION_POLICY_DIGEST")
        provider_authority_json = os.environ.get(
            "CLAUDE_CLIENT_STDIO_PROVIDER_AUTHORITY_JSON"
        )
        required = (
            repository_root,
            launch_secret,
            source_path,
            max_root,
            worker_id,
            policy_digest,
            provider_authority_json,
        )
        if any(not isinstance(value, str) or not value for value in required):
            return None

        source_fd_text = os.environ.get("CLAUDE_CLIENT_EXECUTION_SOURCE_FD")
        source_fd = None
        if source_fd_text is not None:
            try:
                source_fd = int(source_fd_text)
            except ValueError:
                return None

        return cls(
            repository_root=Path(repository_root),
            launch_secret=launch_secret,
            source_path=Path(source_path),
            max_root=Path(max_root),
            worker_id=worker_id,
            policy_digest=policy_digest,
            provider_authority_json=provider_authority_json,
            bun_path=os.environ.get("CLAUDE_CLIENT_BUN_PATH", "bun"),
            source_fd=source_fd,
            timeout_seconds=float(
                os.environ.get("CLAUDE_CLIENT_WEBSEARCH_TIMEOUT_SECONDS", "150")
            ),
        )

    def configuration_error(self) -> str | None:
        entrypoint = self.repository_root / PUBLIC_ENTRYPOINT
        if not self.repository_root.is_dir() or not entrypoint.is_file():
            return "Claude_client public execution_boundary.ts is unavailable"
        if not isinstance(self.launch_secret, str) or len(self.launch_secret) < 16:
            return "Claude_client launch credential is unavailable"
        if not self.source_path.is_file():
            return "Claude_client trusted source object is unavailable"
        if not self.max_root.is_dir():
            return "Claude_client authority root is unavailable"
        try:
            source_resolved = self.source_path.resolve()
            root_resolved = self.max_root.resolve()
            source_within_root = source_resolved.is_relative_to(root_resolved)
        except OSError:
            source_within_root = False
        if not source_within_root:
            return "Claude_client trusted source object is outside its authority root"
        if not isinstance(self.worker_id, str) or not self.worker_id:
            return "Claude_client worker identity is unavailable"
        if not isinstance(self.policy_digest, str) or not _SHA256_PATTERN.fullmatch(
            self.policy_digest
        ):
            return "Claude_client policy digest is invalid"
        try:
            authority = json.loads(self.provider_authority_json)
        except (TypeError, json.JSONDecodeError):
            return "Claude_client stdio provider authority is invalid"
        if not isinstance(authority, dict):
            return "Claude_client stdio provider authority is invalid"
        bun = Path(self.bun_path)
        if not (bun.is_file() or shutil.which(self.bun_path) is not None):
            return "Claude_client Bun runtime is unavailable"
        if (
            not isinstance(self.timeout_seconds, (int, float))
            or self.timeout_seconds <= 0
        ):
            return "Claude_client timeout must be positive"
        return None


class ClaudeClientWebResearchProvider:
    """Execute exactly one bounded Claude_client WebSearch action."""

    def __init__(self, config: ClaudeClientExecutionConfig):
        self.config = config
        self.execution_count = 0
        self.retry_count = 0
        self.fallback_count = 0

    async def health(self) -> tuple[bool, str]:
        error = self.config.configuration_error()
        if error is not None:
            return False, error
        return True, "Claude_client public WebSearch boundary configured"

    async def execute(self, request: Any) -> ProviderExecutionOutcome:
        invalid_reason = self._invalid_request_reason(request)
        if invalid_reason is not None:
            return self._error(
                ToolResultStatus.ERROR,
                "invalid_request",
                invalid_reason,
                SideEffectState.NONE,
            )

        query = request.arguments["query"]
        self.execution_count += 1
        owned_source_fd: int | None = None
        source_fd = self.config.source_fd
        if source_fd is None:
            try:
                source_fd = os.open(self.config.source_path, os.O_RDONLY)
                owned_source_fd = source_fd
            except OSError as exc:
                return self._error(
                    ToolResultStatus.UNAVAILABLE,
                    "claude_client_source_unavailable",
                    "Claude_client trusted source object could not be opened",
                    SideEffectState.NONE,
                    process_status=None,
                    exception_type=type(exc).__name__,
                )

        process: asyncio.subprocess.Process | None = None
        stderr_task: asyncio.Task[None] | None = None
        try:
            environment = os.environ.copy()
            environment.update(
                {
                    "CLAUDE_CLIENT_EXECUTION_LAUNCH_SECRET": self.config.launch_secret,
                    "CLAUDE_CLIENT_EXECUTION_SOURCE_FD": str(source_fd),
                    "CLAUDE_CLIENT_EXECUTION_SOURCE_PATH": str(self.config.source_path),
                    "CLAUDE_CLIENT_EXECUTION_MAX_ROOT": str(self.config.max_root),
                    "CLAUDE_CLIENT_EXECUTION_WORKER_ID": self.config.worker_id,
                    "CLAUDE_CLIENT_EXECUTION_POLICY_DIGEST": self.config.policy_digest,
                    "CLAUDE_CLIENT_STDIO_PROVIDER_AUTHORITY_JSON": self.config.provider_authority_json,
                }
            )
            process = await asyncio.create_subprocess_exec(
                self.config.bun_path,
                PUBLIC_ENTRYPOINT,
                cwd=str(self.config.repository_root),
                env=environment,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                pass_fds=(source_fd,),
            )
            assert process.stderr is not None
            stderr_task = asyncio.create_task(process.stderr.read())
            remaining = self.config.timeout_seconds
            started = time.monotonic()

            admitted = await self._exchange(
                process,
                {
                    "type": "ADMIT",
                    "request": self._boundary_request(request),
                    "presented_credential": self.config.launch_secret,
                },
                started,
                remaining,
            )
            remaining -= time.monotonic() - started
            admission = self._lifecycle_object(
                admitted, "ADMITTED", "admission", "execution_admission_id"
            )

            started = time.monotonic()
            started_response = await self._exchange(
                process,
                {"type": "START", "admission_id": admission},
                started,
                remaining,
            )
            remaining -= time.monotonic() - started
            execution = self._lifecycle_object(
                started_response, "STARTED", "execution", "execution_attempt_id"
            )

            started = time.monotonic()
            result = await self._exchange(
                process,
                {"type": "EXECUTE", "execution_attempt_id": execution},
                started,
                remaining,
            )
            remaining -= time.monotonic() - started

            try:
                shutdown = await self._exchange(
                    process,
                    {"type": "SHUTDOWN"},
                    time.monotonic(),
                    min(remaining, 5.0),
                )
                if shutdown.get("type") != "SHUTDOWN_ACCEPTED":
                    raise RuntimeError("Claude_client boundary rejected shutdown")
                await asyncio.wait_for(process.wait(), timeout=max(remaining, 0.0))
            except asyncio.TimeoutError:
                await self._terminate(process)

            if result.get("ok") is not True:
                return self._provider_failure(result, process.returncode)
            return self._project_result(result, query, process.returncode)
        except asyncio.TimeoutError:
            if process is not None:
                await self._terminate(process)
            return self._error(
                ToolResultStatus.TIMEOUT,
                "claude_client_timeout",
                "Claude_client public WebSearch boundary timed out",
                SideEffectState.NONE,
                process_status=process.returncode if process is not None else None,
                action_count=self.execution_count,
            )
        except (OSError, ValueError, json.JSONDecodeError, RuntimeError) as exc:
            if process is not None:
                await self._terminate(process)
            return self._error(
                ToolResultStatus.UNAVAILABLE,
                "claude_client_boundary_unavailable",
                "Claude_client public WebSearch boundary did not produce a valid response",
                SideEffectState.NONE,
                process_status=process.returncode if process is not None else None,
                exception_type=type(exc).__name__,
                action_count=self.execution_count,
            )
        finally:
            if stderr_task is not None:
                stderr_task.cancel()
                try:
                    await stderr_task
                except asyncio.CancelledError:
                    pass
            if owned_source_fd is not None:
                os.close(owned_source_fd)

    def _boundary_request(self, request: Any) -> dict[str, Any]:
        now_ms = int(time.time() * 1000)
        return {
            "contract_version": "1.0",
            "capability_id": "claude.web_search",
            "capability_request_id": request.capability_request_id,
            "capability_call_id": f"cap_call_{time.time_ns()}",
            "correlation_id": request.correlation_id
            or f"research-{request.capability_request_id}",
            "idempotency_key": request.idempotency_key,
            "arguments": {"query": request.arguments["query"]},
            "granted_scope": {
                "allowed_roots": [str(self.config.max_root.resolve())],
                "denied_roots": [],
            },
            "granted_network_policy": dict(_PERMISSIVE_NETWORK_POLICY),
            "deadline": now_ms + int(self.config.timeout_seconds * 1000),
        }

    async def _exchange(
        self,
        process: asyncio.subprocess.Process,
        command: dict[str, Any],
        started: float,
        budget_seconds: float,
    ) -> dict[str, Any]:
        if budget_seconds <= 0:
            raise asyncio.TimeoutError
        assert process.stdin is not None and process.stdout is not None
        payload = (json.dumps(command, separators=(",", ":")) + "\n").encode("utf-8")
        process.stdin.write(payload)
        await asyncio.wait_for(process.stdin.drain(), timeout=budget_seconds)
        remaining = budget_seconds - (time.monotonic() - started)
        if remaining <= 0:
            raise asyncio.TimeoutError
        line = await asyncio.wait_for(process.stdout.readline(), timeout=remaining)
        if not line:
            raise RuntimeError("Claude_client boundary closed before response")
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError("Claude_client boundary response is not an object")
        return value

    @staticmethod
    async def _terminate(process: asyncio.subprocess.Process) -> None:
        if process.returncode is not None:
            return
        process.terminate()
        try:
            await asyncio.wait_for(process.wait(), timeout=2.0)
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()

    @staticmethod
    def _lifecycle_object(
        response: dict[str, Any],
        expected_type: str,
        field: str,
        identity_field: str,
    ) -> str:
        if response.get("ok") is not True or response.get("type") != expected_type:
            raise RuntimeError("Claude_client lifecycle response invalid")
        value = response.get(field)
        identity = value.get(identity_field) if isinstance(value, dict) else None
        if not isinstance(identity, str) or not identity:
            raise ValueError("Claude_client lifecycle identity invalid")
        return identity

    def _provider_failure(
        self,
        result: dict[str, Any],
        process_status: int | None,
    ) -> ProviderExecutionOutcome:
        raw = result.get("raw_response")
        raw_sha = raw.get("sha256") if isinstance(raw, dict) else None
        transmission_count = result.get("tools_call_transmission_count")
        side_effect_state = (
            SideEffectState.UNKNOWN if transmission_count == 1 else SideEffectState.NONE
        )
        return self._error(
            ToolResultStatus.ERROR,
            "claude_client_websearch_failed",
            "Claude_client WebSearch provider action failed",
            side_effect_state,
            process_status=process_status,
            provider_code=str(result.get("code") or "unknown"),
            execution_status=str(result.get("execution_status") or "UNKNOWN"),
            transmission_count=transmission_count,
            retry_count=result.get("retry_count"),
            raw_response_sha256=raw_sha if isinstance(raw_sha, str) else None,
            action_count=self.execution_count,
        )

    def _project_result(
        self,
        result: dict[str, Any],
        query: str,
        process_status: int | None,
    ) -> ProviderExecutionOutcome:
        required_truth = (
            result.get("kind") == "stdio_tools_call_completed",
            result.get("provider_tool_name") == "WebSearch",
            result.get("authorized_query") == query,
            result.get("execution_status") == "COMPLETED",
            result.get("side_effect_state") == "SUCCEEDED",
            result.get("tools_call_transmission_count") == 1,
            result.get("retry_count") == 0,
        )
        if not all(required_truth):
            return self._error(
                ToolResultStatus.ERROR,
                "claude_client_result_integrity_failure",
                "Claude_client WebSearch result did not preserve exact action truth",
                SideEffectState.NONE,
                process_status=process_status,
                action_count=self.execution_count,
            )

        raw = result.get("raw_response")
        raw_sha = raw.get("sha256") if isinstance(raw, dict) else None
        raw_reason = self._raw_evidence_invalid_reason(raw, result)
        if raw_reason is not None:
            return self._error(
                ToolResultStatus.ERROR,
                "claude_client_raw_evidence_invalid",
                raw_reason,
                SideEffectState.NONE,
                process_status=process_status,
                action_count=self.execution_count,
            )
        response = result.get("response")
        content = response.get("content") if isinstance(response, dict) else None
        if not isinstance(content, list):
            return self._error(
                ToolResultStatus.ERROR,
                "claude_client_content_invalid",
                "Claude_client WebSearch content is not a list",
                SideEffectState.NONE,
                process_status=process_status,
                action_count=self.execution_count,
            )

        observed_at = _iso_timestamp_from_epoch(raw.get("observed_at_epoch_ms"))
        if observed_at is None:
            return self._error(
                ToolResultStatus.ERROR,
                "claude_client_raw_evidence_invalid",
                "Claude_client WebSearch raw observation timestamp is unavailable",
                SideEffectState.NONE,
                process_status=process_status,
                action_count=self.execution_count,
            )

        source_ref = f"claude-client:raw-response:{raw_sha}"
        findings = []
        for item in content:
            if not isinstance(item, dict):
                continue
            statement = item.get("text")
            if isinstance(statement, str) and statement:
                findings.append({"statement": statement, "source_ref": source_ref})

        source = {
            "ref": source_ref,
            "evidence_type": "claude_client_raw_provider_response",
            "boundary": raw.get("boundary"),
            "completeness": raw.get("completeness"),
            "byte_size": raw.get("byte_size"),
            "sha256": raw_sha,
            "observed_at": observed_at,
        }
        limitations = [
            "Provider action completion does not prove external-world truth.",
            "The public WebSearch result exposes no structured external URL or citation.",
            "The source reference binds only the exact raw Claude_client provider response digest.",
            str(
                result.get("external_result_truth")
                or "external_result_truth=NOT_PROVEN"
            ),
            str(
                result.get("external_freshness_truth")
                or "external_freshness_truth=NOT_PROVEN"
            ),
            str(
                result.get("search_index_completeness_truth")
                or "search_index_completeness_truth=NOT_PROVEN"
            ),
        ]
        provenance = {
            "public_entrypoint": f"bun {PUBLIC_ENTRYPOINT}",
            "public_protocol": PUBLIC_PROTOCOL,
            "execution_attempt_id": result.get("execution_attempt_id"),
            "provider_tool_authority_id": result.get("provider_tool_authority_id"),
            "stdio_provider_session_id": result.get("stdio_provider_session_id"),
            "jsonrpc_request_id": result.get("jsonrpc_request_id"),
            "raw_response_boundary": raw.get("boundary"),
            "raw_response_completeness": raw.get("completeness"),
            "raw_response_sha256": raw_sha,
            "action_count": 1,
            "retry_count": 0,
            "fallback_count": 0,
            "external_result_truth": result.get("external_result_truth"),
            "external_freshness_truth": result.get("external_freshness_truth"),
            "search_index_completeness_truth": result.get(
                "search_index_completeness_truth"
            ),
            "structured_external_source_url_available": False,
        }
        return ProviderExecutionOutcome(
            status=ToolResultStatus.PARTIAL,
            structured_output={
                "query": query,
                "findings": findings,
                "sources": [source],
                "limitations": limitations,
                "provider": PROVIDER_ID,
                "produced_at": observed_at,
                "provenance": provenance,
            },
            side_effect_state=SideEffectState.NONE,
        )

    @staticmethod
    def _invalid_request_reason(request: Any) -> str | None:
        capability_id = getattr(request, "capability_id", None)
        arguments = getattr(request, "arguments", None)
        if capability_id != "research.web.query" or not isinstance(arguments, dict):
            return "request must be research.web.query with mapping arguments"
        if set(arguments) != {"query"} or not isinstance(arguments["query"], str):
            return "research.web.query accepts exactly one string query"
        query = arguments["query"]
        if len(query.encode("utf-8")) > 8192:
            return "query UTF-8 byte length must be at most 8192"
        scalar_count = 0
        index = 0
        while index < len(query):
            unit = ord(query[index])
            if 0xDC00 <= unit <= 0xDFFF:
                return "query contains an unpaired low surrogate"
            if 0xD800 <= unit <= 0xDBFF:
                if index + 1 >= len(query):
                    return "query contains an unpaired terminal high surrogate"
                second_unit = ord(query[index + 1])
                if not (0xDC00 <= second_unit <= 0xDFFF):
                    return "query contains an unpaired high surrogate"
                index += 2
            else:
                index += 1
            scalar_count += 1
        if scalar_count < 2:
            return "query must contain at least two Unicode scalar values"
        return None

    @staticmethod
    def _raw_evidence_invalid_reason(
        raw: Any,
        result: dict[str, Any],
    ) -> str | None:
        if not isinstance(raw, dict):
            return "Claude_client WebSearch raw evidence is unavailable"
        if raw.get("boundary") != "TRANSPORT_OBSERVED_STDOUT_JSONRPC_FRAME_BYTES":
            return "Claude_client WebSearch raw evidence boundary is invalid"
        if raw.get("completeness") != "COMPLETE":
            return "Claude_client WebSearch raw evidence is incomplete"
        if raw.get("lf_delimiter_observed") is not True:
            return "Claude_client WebSearch raw evidence delimiter is unavailable"
        for field in (
            "execution_attempt_id",
            "provider_tool_authority_id",
            "stdio_provider_session_id",
            "jsonrpc_request_id",
        ):
            if raw.get(field) != result.get(field):
                return "Claude_client WebSearch raw evidence provenance is mismatched"
        raw_sha = raw.get("sha256")
        if not isinstance(raw_sha, str) or not _SHA256_PATTERN.fullmatch(raw_sha):
            return "Claude_client WebSearch raw evidence identity is invalid"
        encoded = raw.get("base64")
        byte_size = raw.get("byte_size")
        if not isinstance(encoded, str) or not isinstance(byte_size, int):
            return "Claude_client WebSearch raw evidence bytes are unavailable"
        try:
            observed = base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error):
            return "Claude_client WebSearch raw evidence bytes are invalid"
        if len(observed) != byte_size:
            return "Claude_client WebSearch raw evidence byte count is mismatched"
        if hashlib.sha256(observed).hexdigest() != raw_sha:
            return "Claude_client WebSearch raw evidence digest is mismatched"
        return None

    @staticmethod
    def _error(
        status: ToolResultStatus,
        code: str,
        message: str,
        side_effect_state: SideEffectState,
        **extra: Any,
    ) -> ProviderExecutionOutcome:
        error = {"code": code, "message": message}
        error.update({key: value for key, value in extra.items() if value is not None})
        return ProviderExecutionOutcome(
            status=status,
            structured_output={},
            error=error,
            side_effect_state=side_effect_state,
        )


def _iso_timestamp_from_epoch(value: Any) -> str | None:
    try:
        epoch_ms = float(value)
        epoch = epoch_ms / 1000
        if epoch < 0:
            return None
        return (
            datetime.fromtimestamp(epoch, tz=timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        )
    except (TypeError, ValueError, OSError):
        return None
