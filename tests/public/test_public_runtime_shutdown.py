from __future__ import annotations


from julia_core.public import shutdown_core_runtime
from julia_core.runtime import capability_bridge as bridge_module
from julia_core.runtime.capability_bridge import RuntimeCapabilityBridge
from tests.runtime.test_async_capability_runtime import LoopAffineProvider


def _install_singleton(monkeypatch, bridge: RuntimeCapabilityBridge) -> None:
    monkeypatch.setattr(bridge_module, "_bridge", bridge)


def test_public_shutdown_api_exports_lifecycle_intent_only():
    import inspect

    from julia_core.public import lifecycle

    assert inspect.signature(shutdown_core_runtime).parameters == {}
    assert lifecycle.shutdown_core_runtime is shutdown_core_runtime


def test_public_shutdown_closes_canonical_singleton_before_first_execution(
    monkeypatch,
):
    provider = LoopAffineProvider()
    bridge = RuntimeCapabilityBridge()
    bridge.register_provider("local", provider)
    bridge.initialize()
    _install_singleton(monkeypatch, bridge)

    shutdown_core_runtime()
    shutdown_core_runtime()

    assert provider.execute_loops == []
    assert len(provider.close_loops) == 1
    assert bridge.async_runtime.state == "CLOSED"
    assert bridge_module.get_capability_bridge() is bridge


def test_public_shutdown_is_safe_when_singleton_was_never_created(monkeypatch):
    monkeypatch.setattr(bridge_module, "_bridge", None)

    shutdown_core_runtime()

    bridge = bridge_module.get_capability_bridge()
    assert bridge.async_runtime.state == "CLOSED"
    assert bridge_module.get_capability_bridge() is bridge


def test_public_shutdown_closes_canonical_singleton_after_repeated_execution(
    monkeypatch,
):
    provider = LoopAffineProvider()
    bridge = RuntimeCapabilityBridge()
    bridge.register_provider("local", provider)
    bridge.initialize()
    _install_singleton(monkeypatch, bridge)

    for call_number in range(1, 4):
        result = bridge.execute_tool_typed(
            f'{{"name":"file.read","arguments":{{"path":"call-{call_number}"}}}}'
        )
        assert result.tool_result.structured_output == {"call": call_number}

    shutdown_core_runtime()
    shutdown_core_runtime()

    assert provider.close_loops * 3 == provider.execute_loops
    assert bridge.async_runtime.state == "CLOSED"
    assert bridge_module.get_capability_bridge() is bridge


def test_public_shutdown_leaves_canonical_runtime_terminal(monkeypatch):
    provider = LoopAffineProvider()
    bridge = RuntimeCapabilityBridge()
    bridge.register_provider("local", provider)
    bridge.initialize()
    _install_singleton(monkeypatch, bridge)
    shutdown_core_runtime()

    try:
        bridge.execute_tool_typed(
            '{"name":"file.read","arguments":{"path":"post-shutdown"}}'
        )
    except RuntimeError as exc:
        assert str(exc) == "async capability runtime is CLOSED"
    else:
        raise AssertionError("public shutdown allowed execution restart")

    try:
        bridge.register_provider("market", LoopAffineProvider())
    except RuntimeError as exc:
        assert str(exc) == "runtime capability bridge is closing or closed"
    else:
        raise AssertionError("public shutdown allowed late provider registration")
