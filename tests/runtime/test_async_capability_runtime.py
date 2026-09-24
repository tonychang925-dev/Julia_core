from __future__ import annotations

import asyncio
import inspect
import math
from pathlib import Path
import threading

from julia_core.capability.models import (
    ProviderExecutionOutcome,
    SideEffectState,
    ToolResultStatus,
)
from julia_core.capability.providers.market_public import MarketPublicProviderAdapter
from julia_core.research import (
    ClaudeClientExecutionConfig,
    ClaudeClientWebResearchProvider,
)
from julia_core.runtime.async_capability_runtime import (
    AsyncCapabilityRuntime,
    DEFAULT_CAPABILITY_EXECUTION_TIMEOUT_SECONDS,
)
from julia_core.runtime.capability_bridge import RuntimeCapabilityBridge


class LoopAffineProvider:
    def __init__(self) -> None:
        self.execute_loops: list[int] = []
        self.execute_threads: list[int] = []
        self.close_loops: list[int] = []
        self.call_count = 0

    async def execute(self, request):
        loop_identity = id(asyncio.get_running_loop())
        if self.execute_loops and loop_identity != self.execute_loops[0]:
            raise AssertionError("provider moved to a different event loop")
        self.execute_loops.append(loop_identity)
        self.execute_threads.append(threading.get_ident())
        self.call_count += 1
        return ProviderExecutionOutcome(
            status=ToolResultStatus.SUCCESS,
            structured_output={"call": self.call_count},
            side_effect_state=SideEffectState.NONE,
        )

    async def health(self) -> tuple[bool, str]:
        return True, "loop-affine test provider"

    async def close(self) -> None:
        self.close_loops.append(id(asyncio.get_running_loop()))


class MarketLoopAffineProvider(LoopAffineProvider):
    async def execute(
        self,
        capability,
        request,
        *,
        request_id=None,
        correlation_id=None,
    ):
        loop_identity = id(asyncio.get_running_loop())
        if self.execute_loops and loop_identity != self.execute_loops[0]:
            raise AssertionError("provider moved to a different event loop")
        self.execute_loops.append(loop_identity)
        self.call_count += 1
        return {
            "capability_id": "market.product.read",
            "operation_status": "SUCCESS",
            "data_state": "READY",
            "payload": {"call": self.call_count},
            "provenance": {"provenance_status": "PROVENANCE_INCOMPLETE"},
            "failures": [],
        }


class BlockingLoopAffineProvider(LoopAffineProvider):
    def __init__(self) -> None:
        super().__init__()
        self.execution_started = threading.Event()
        self.may_complete = asyncio.Event()
        self.execution_completed = threading.Event()
        self.execution_loop = None
        self.order = []

    async def execute(self, request):
        self.execution_loop = asyncio.get_running_loop()
        self.order.append("execute-start")
        self.execution_started.set()
        await self.may_complete.wait()
        self.order.append("execute-complete")
        self.execution_completed.set()
        self.execute_loops.append(id(self.execution_loop))
        self.execute_threads.append(threading.get_ident())
        self.call_count += 1
        return ProviderExecutionOutcome(
            status=ToolResultStatus.SUCCESS,
            structured_output={"call": self.call_count},
            side_effect_state=SideEffectState.NONE,
        )

    async def close(self) -> None:
        self.order.append("provider-close")
        await super().close()


def _bridge(provider: LoopAffineProvider) -> RuntimeCapabilityBridge:
    bridge = RuntimeCapabilityBridge()
    bridge.register_provider("local", provider)
    bridge.initialize()
    return bridge


def _tool_json(call_number: int) -> str:
    return (
        '{"name":"file.read","arguments":{"path":"lifecycle-' f"{call_number}" + '"}}'
    )


def test_repeated_capability_calls_and_close_use_same_live_loop():
    provider = LoopAffineProvider()
    bridge = _bridge(provider)

    results = [bridge.execute_tool_typed(_tool_json(number)) for number in range(1, 4)]

    assert [result.tool_result.structured_output["call"] for result in results] == [
        1,
        2,
        3,
    ]
    assert provider.execute_loops == [provider.execute_loops[0]] * 3

    bridge.close()
    bridge.close()

    assert provider.close_loops == [provider.execute_loops[0]]
    assert bridge.async_runtime.is_closed is True


def test_concurrent_close_waits_for_accepted_in_flight_execution():
    provider = BlockingLoopAffineProvider()
    bridge = _bridge(provider)
    execute_errors = []

    def execute() -> None:
        try:
            bridge.execute_tool_typed(_tool_json(1))
        except BaseException as exc:
            execute_errors.append(exc)

    execute_thread = threading.Thread(target=execute)
    execute_thread.start()
    assert provider.execution_started.wait(timeout=5)

    close_thread = threading.Thread(target=bridge.close)
    close_thread.start()
    assert bridge.async_runtime.wait_for_state("CLOSING")

    assert provider.close_loops == []
    assert provider.order == ["execute-start"]
    assert execute_thread.is_alive()
    assert close_thread.is_alive()

    provider.execution_loop.call_soon_threadsafe(provider.may_complete.set)
    execute_thread.join(timeout=5)
    close_thread.join(timeout=5)

    assert execute_errors == []
    assert provider.order == ["execute-start", "execute-complete", "provider-close"]
    assert provider.close_loops == provider.execute_loops
    assert bridge.async_runtime.state == "CLOSED"

    try:
        bridge.execute_tool_typed(_tool_json(2))
    except RuntimeError as exc:
        assert str(exc) == "async capability runtime is CLOSED"
    else:
        raise AssertionError("closed runtime recreated itself")


def test_concurrent_first_use_shares_one_runtime_thread_and_loop():
    provider = LoopAffineProvider()
    bridge = _bridge(provider)
    results = []
    errors = []
    barrier = threading.Barrier(12)

    def invoke(number: int) -> None:
        try:
            barrier.wait()
            results.append(bridge.execute_tool_typed(_tool_json(number)))
        except BaseException as exc:
            errors.append(exc)

    threads = [threading.Thread(target=invoke, args=(number,)) for number in range(12)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert errors == []
    assert len(results) == 12
    assert provider.call_count == 12
    assert len(set(provider.execute_loops)) == 1
    assert set(provider.execute_threads) == {bridge.async_runtime.thread_identity}

    bridge.close()


def test_synchronous_bridge_api_works_inside_running_caller_loop():
    provider = LoopAffineProvider()
    bridge = _bridge(provider)

    async def caller() -> None:
        return bridge.execute_tool_typed(_tool_json(1))

    result = asyncio.run(caller())

    assert result.tool_result.status.value == "success"
    assert result.tool_result.structured_output == {"call": 1}

    bridge.close()


def test_close_before_first_execute_still_closes_provider():
    provider = LoopAffineProvider()
    bridge = _bridge(provider)

    bridge.close()

    assert provider.execute_loops == []
    assert provider.close_loops
    assert bridge.async_runtime.is_closed is True


def test_market_adapter_forwards_close_on_capability_runtime_loop():
    provider = MarketLoopAffineProvider()
    adapter = MarketPublicProviderAdapter(
        provider,
        {"market.product.read": lambda **arguments: arguments},
    )
    bridge = RuntimeCapabilityBridge()
    bridge.register_provider("market", adapter)
    bridge.initialize()

    result = bridge.execute_tool_typed(
        '{"name":"market.product.read","arguments":{"subject_key":"9022152"}}'
    )
    bridge.close()

    assert result.tool_result.status.value == "success"
    assert provider.close_loops == provider.execute_loops


def test_closed_runtime_fails_visibly_without_recreation():
    provider = LoopAffineProvider()
    bridge = _bridge(provider)
    bridge.close()

    try:
        bridge.execute_tool_typed(_tool_json(1))
    except RuntimeError as exc:
        assert str(exc) == "async capability runtime is CLOSED"
    else:
        raise AssertionError("closed runtime recreated itself or silently succeeded")


def test_provider_registration_after_bridge_close_is_rejected():
    provider = LoopAffineProvider()
    bridge = _bridge(provider)
    bridge.close()
    late_provider = LoopAffineProvider()

    try:
        bridge.register_provider("market", late_provider)
    except RuntimeError as exc:
        assert str(exc) == "runtime capability bridge is closing or closed"
    else:
        raise AssertionError("terminal bridge accepted a new provider")

    assert "market" not in bridge._providers
    assert "market" not in bridge.manager.providers


def test_canonical_sync_delivery_has_no_per_call_loop_or_executor():
    source = Path("julia_core/runtime/capability_bridge.py").read_text()
    delivery_source = source.split("def execute_tool_typed", 1)[1].split(
        "def requires_tool", 1
    )[0]

    assert "asyncio.run(" not in delivery_source
    assert "ThreadPoolExecutor" not in delivery_source


def test_default_execution_timeout_is_thirty_seconds():
    signature = inspect.signature(AsyncCapabilityRuntime.run)

    assert DEFAULT_CAPABILITY_EXECUTION_TIMEOUT_SECONDS == 30.0
    assert signature.parameters["timeout_seconds"].default is (
        DEFAULT_CAPABILITY_EXECUTION_TIMEOUT_SECONDS
    )


def test_explicit_trusted_timeout_completes_deterministic_work():
    runtime = AsyncCapabilityRuntime()

    async def operation() -> str:
        return "completed"

    try:
        assert runtime.run(operation, timeout_seconds=0.25) == "completed"
    finally:
        runtime.close({})


def test_timeout_cancellation_remains_fail_closed():
    runtime = AsyncCapabilityRuntime()
    completed = threading.Event()

    async def operation() -> str:
        await asyncio.sleep(1)
        completed.set()

    try:
        runtime.run(operation, timeout_seconds=0.01)
    except TimeoutError as exc:
        assert str(exc) == "capability execution exceeded 0.01 seconds"
    else:
        raise AssertionError("timed-out capability produced synthetic success")
    finally:
        runtime.close({})

    assert not completed.wait(timeout=0)


def test_invalid_timeout_is_rejected_before_provider_work_is_scheduled():
    runtime = AsyncCapabilityRuntime()
    provider_work_started = threading.Event()

    async def operation() -> None:
        provider_work_started.set()

    for timeout_seconds in (0, -0.1, math.nan, math.inf):
        try:
            runtime.run(operation, timeout_seconds=timeout_seconds)
        except ValueError as exc:
            assert str(exc) == "capability execution timeout must be finite and positive"
        else:
            raise AssertionError("invalid timeout was accepted")

    runtime.close({})
    assert not provider_work_started.is_set()


def test_bridge_selects_registered_research_provider_trusted_budget(tmp_path):
    repository = tmp_path / "Claude_client"
    authority_root = tmp_path / "authority"
    repository.mkdir()
    authority_root.mkdir()
    (repository / "execution_boundary.ts").write_text("")
    source = authority_root / "source.txt"
    source.write_text("trusted authority source")
    config = ClaudeClientExecutionConfig(
        repository_root=repository,
        launch_secret="launch-secret-0123456789",
        source_path=source,
        max_root=authority_root,
        worker_id="worker-test",
        policy_digest="b" * 64,
        provider_authority_json="{}",
        timeout_seconds=150.0,
    )
    provider = ClaudeClientWebResearchProvider(config)
    provider_requests = []

    async def execute(request):
        provider_requests.append(request)
        return ProviderExecutionOutcome(
            status=ToolResultStatus.SUCCESS,
            structured_output={
                "query": "robotics catalysts",
                "findings": [
                    {
                        "statement": "Robotics adoption is accelerating.",
                        "source_ref": "source:robotics-catalysts",
                    }
                ],
                "sources": [
                    {
                        "ref": "source:robotics-catalysts",
                        "title": "Robotics Catalyst Source",
                        "url": "https://example.com/robotics-catalysts",
                    }
                ],
                "limitations": [],
                "provider": "budget-test-provider",
                "produced_at": "2026-09-24T00:00:00Z",
            },
            side_effect_state=SideEffectState.NONE,
        )

    provider.execute = execute
    bridge = RuntimeCapabilityBridge()
    bridge.register_provider("research", provider)
    bridge.initialize()
    original_run = bridge.async_runtime.run
    captured_timeout = None

    def capture_run(
        operation,
        *,
        timeout_seconds=DEFAULT_CAPABILITY_EXECUTION_TIMEOUT_SECONDS,
    ):
        nonlocal captured_timeout
        captured_timeout = timeout_seconds
        return original_run(operation, timeout_seconds=timeout_seconds)

    bridge.async_runtime.run = capture_run
    execution = bridge.execute_tool_typed(
        '{"name":"research.web.query","arguments":{"query":"robotics catalysts"}}'
    )
    bridge.close()

    assert execution.tool_result.status.value == "success"
    assert provider_requests[0].arguments == {"query": "robotics catalysts"}
    assert captured_timeout == 155.0


def test_unrelated_provider_keeps_default_execution_budget(monkeypatch):
    provider = LoopAffineProvider()
    bridge = _bridge(provider)
    captured_timeout = object()
    original_run = bridge.async_runtime.run

    def capture_run(
        operation,
        *,
        timeout_seconds=DEFAULT_CAPABILITY_EXECUTION_TIMEOUT_SECONDS,
    ):
        nonlocal captured_timeout
        captured_timeout = timeout_seconds
        return original_run(operation, timeout_seconds=timeout_seconds)

    monkeypatch.setattr(bridge.async_runtime, "run", capture_run)
    bridge.execute_tool_typed(_tool_json(1))
    bridge.close()

    assert captured_timeout == DEFAULT_CAPABILITY_EXECUTION_TIMEOUT_SECONDS
