from __future__ import annotations


from julia_core.public import conversation
from julia_core.research import ClaudeClientWebResearchProvider
from julia_core.runtime import capability_bridge as bridge_module
from julia_core.runtime.capability_bridge import RuntimeCapabilityBridge


from tests.research.test_claude_client_web_research_provider import make_config


def reset_research_binding(monkeypatch):
    monkeypatch.setattr(conversation, "_research_binding_provider", None)
    monkeypatch.setattr(conversation, "_research_binding_attempted", False)
    monkeypatch.setattr(conversation, "_research_binding_error", None)


def remove_claude_environment(monkeypatch):
    for name in (
        "CLAUDE_CLIENT_ROOT",
        "CLAUDE_CLIENT_EXECUTION_LAUNCH_SECRET",
        "CLAUDE_CLIENT_EXECUTION_SOURCE_FD",
        "CLAUDE_CLIENT_EXECUTION_SOURCE_PATH",
        "CLAUDE_CLIENT_EXECUTION_MAX_ROOT",
        "CLAUDE_CLIENT_EXECUTION_WORKER_ID",
        "CLAUDE_CLIENT_EXECUTION_POLICY_DIGEST",
        "CLAUDE_CLIENT_STDIO_PROVIDER_AUTHORITY_JSON",
    ):
        monkeypatch.delenv(name, raising=False)


def test_missing_claude_configuration_leaves_research_typed_unavailable(
    monkeypatch, tmp_path
):
    reset_research_binding(monkeypatch)
    remove_claude_environment(monkeypatch)
    bridge = RuntimeCapabilityBridge()
    monkeypatch.setattr(bridge_module, "get_capability_bridge", lambda: bridge)

    conversation._ensure_claude_client_research_binding()

    assert bridge.manager.providers.get("research") is None
    execution = bridge.execute_tool_typed(
        '{"name":"research.web.query","arguments":{"query":"robotics catalysts"}}'
    )
    assert execution.tool_result.status.value == "unavailable"
    assert execution.tool_result.error["code"] == "provider_not_found"


def test_configured_claude_public_provider_wins_research_without_market_shadow(
    monkeypatch, tmp_path
):
    reset_research_binding(monkeypatch)
    config = make_config(tmp_path)
    monkeypatch.setenv("CLAUDE_CLIENT_ROOT", str(config.repository_root))
    monkeypatch.setenv("CLAUDE_CLIENT_EXECUTION_LAUNCH_SECRET", config.launch_secret)
    monkeypatch.setenv("CLAUDE_CLIENT_EXECUTION_SOURCE_PATH", str(config.source_path))
    monkeypatch.setenv("CLAUDE_CLIENT_EXECUTION_MAX_ROOT", str(config.max_root))
    monkeypatch.setenv("CLAUDE_CLIENT_EXECUTION_WORKER_ID", config.worker_id)
    monkeypatch.setenv("CLAUDE_CLIENT_EXECUTION_POLICY_DIGEST", config.policy_digest)
    monkeypatch.setenv(
        "CLAUDE_CLIENT_STDIO_PROVIDER_AUTHORITY_JSON",
        config.provider_authority_json,
    )
    monkeypatch.setenv("CLAUDE_CLIENT_BUN_PATH", config.bun_path)
    bridge = RuntimeCapabilityBridge()
    bridge.initialize()
    monkeypatch.setattr(bridge_module, "get_capability_bridge", lambda: bridge)

    conversation._ensure_claude_client_research_binding()

    provider = bridge._providers.get("research")
    assert isinstance(provider, ClaudeClientWebResearchProvider)
    assert bridge.manager.providers.get("research") is not None
    assert bridge.manager.providers.get("market") is None
