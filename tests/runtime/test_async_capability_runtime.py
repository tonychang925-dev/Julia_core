from __future__ import annotations

import asyncio
from pathlib import Path
import threading

from julia_core.capability.models import (
    ProviderExecutionOutcome,
    SideEffectState,
    ToolResultStatus,
)
from julia_core.capability.providers.market_public import MarketPublicProviderAdapter
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
        assert str(exc) == "async capability runtime is closed"
    else:
        raise AssertionError("closed runtime recreated itself or silently succeeded")


def test_canonical_sync_delivery_has_no_per_call_loop_or_executor():
    source = Path("julia_core/runtime/capability_bridge.py").read_text()
    delivery_source = source.split("def execute_tool_typed", 1)[1].split(
        "def requires_tool", 1
    )[0]

    assert "asyncio.run(" not in delivery_source
    assert "ThreadPoolExecutor" not in delivery_source
