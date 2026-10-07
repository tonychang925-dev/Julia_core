"""#246: no hard-coded Desktop ai_theme_app paths in Julia_core.

ai_theme_app is located only through explicit configuration (JULIA_AI_THEME_ROOT,
STRATEGY_CARD_DIR); an unconfigured or missing location fails closed with a clear error.
Allowed file-capability roots that mention the Desktop are a different matter (not covered here).
"""
from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
NEEDLE = "Desktop" + "/ai_theme_app"          # built from pieces so this file does not match itself
THIS = Path(__file__).resolve()


def _scan_files():
    for base in ("julia_core", "tests"):
        yield from (ROOT / base).rglob("*.py")
    yield from ROOT.glob("*.py")


def test_static_no_desktop_ai_theme_app_literal_in_python_sources():
    offenders = []
    for path in _scan_files():
        if path.resolve() == THIS:
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if NEEDLE in line:
                offenders.append(f"{path.relative_to(ROOT)}:{number}")
    assert offenders == [], "hard-coded Desktop ai_theme_app paths:\n" + "\n".join(offenders)


def test_runtime_importing_the_official_ingress_never_touches_the_desktop_workspace(tmp_path):
    """Build the official ingress (what voice_api/server.py builds) in a clean interpreter."""
    script = textwrap.dedent(
        f"""
        import os, sys
        sys.path.insert(0, {str(ROOT)!r})
        for var in ("JULIA_AI_THEME_ROOT", "STRATEGY_CARD_DIR"):
            os.environ.pop(var, None)
        import julia_core.events.store as es
        es._store = es.EventStore(storage_dir={str(tmp_path / "events")!r})
        from julia_core.public import CoreConversationConfig, CoreConversationIngress
        CoreConversationIngress(CoreConversationConfig({str(tmp_path / "data")!r}), provider_factory=lambda: object())
        needle = "Desktop" + "/ai_theme_app"
        bad_path = [p for p in sys.path if needle in p]
        bad_mod = [m for m, v in list(sys.modules.items()) if needle in (getattr(v, "__file__", None) or "")]
        print("BAD", bad_path, bad_mod)
        sys.exit(1 if (bad_path or bad_mod) else 0)
        """
    )
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr


# ── adapter.py: explicit configuration only, fail closed ───────────────────

@pytest.fixture()
def clean_env(monkeypatch):
    monkeypatch.delenv("JULIA_AI_THEME_ROOT", raising=False)
    monkeypatch.delenv("STRATEGY_CARD_DIR", raising=False)
    saved_path = list(sys.path)
    saved_modules = {k: v for k, v in sys.modules.items() if k == "mcp_server" or k.startswith("mcp_server.")}
    for name in saved_modules:
        sys.modules.pop(name)
    yield
    sys.path[:] = saved_path
    for name in [k for k in sys.modules if k == "mcp_server" or k.startswith("mcp_server.")]:
        sys.modules.pop(name)
    sys.modules.update(saved_modules)


def test_adapter_unconfigured_root_fails_closed_without_touching_sys_path(clean_env):
    from julia_core.capability.providers.ai_theme.adapter import MCPToolAdapter

    before = list(sys.path)
    with pytest.raises(RuntimeError, match="JULIA_AI_THEME_ROOT"):
        MCPToolAdapter()._call_in_process("review_market_snapshot", {})
    assert sys.path == before and "mcp_server" not in sys.modules


def test_adapter_missing_configured_root_fails_closed(clean_env, monkeypatch, tmp_path):
    from julia_core.capability.providers.ai_theme.adapter import MCPToolAdapter

    monkeypatch.setenv("JULIA_AI_THEME_ROOT", str(tmp_path / "does-not-exist"))
    before = list(sys.path)
    with pytest.raises(RuntimeError, match="JULIA_AI_THEME_ROOT"):
        MCPToolAdapter()._call_in_process("review_market_snapshot", {})
    assert sys.path == before


def test_adapter_configured_root_is_used_and_only_that_root(clean_env, monkeypatch, tmp_path):
    from julia_core.capability.providers.ai_theme.adapter import MCPToolAdapter

    root = tmp_path / "theme"
    (root / "mcp_server").mkdir(parents=True)
    (root / "mcp_server" / "__init__.py").write_text("")
    (root / "mcp_server" / "server.py").write_text("MCP_TOOLS = {'review_market_snapshot': lambda: {'ok': True}}\n")
    monkeypatch.setenv("JULIA_AI_THEME_ROOT", str(root))
    before = list(sys.path)
    assert MCPToolAdapter()._call_in_process("review_market_snapshot", {}) == {"ok": True}
    added = [p for p in sys.path if p not in before]
    assert added == [str(root)]


# ── handoff.py: STRATEGY_CARD_DIR / explicit argument only ─────────────────

def test_handoff_unconfigured_card_dir_fails_closed(clean_env):
    from julia_core.capability.financial.research.handoff import RecursiveResearchHandoff

    handoff = RecursiveResearchHandoff()          # building it is fine; the first USE fails closed
    with pytest.raises(RuntimeError, match="STRATEGY_CARD_DIR"):
        handoff.card_dir


def test_handoff_missing_card_dir_fails_closed(clean_env, monkeypatch, tmp_path):
    from julia_core.capability.financial.research.handoff import RecursiveResearchHandoff

    monkeypatch.setenv("STRATEGY_CARD_DIR", str(tmp_path / "missing"))
    with pytest.raises(RuntimeError, match="STRATEGY_CARD_DIR"):
        RecursiveResearchHandoff().card_dir
    with pytest.raises(RuntimeError):
        RecursiveResearchHandoff(card_dir=str(tmp_path / "also-missing")).card_dir


def test_handoff_env_and_explicit_argument_are_honoured(clean_env, monkeypatch, tmp_path):
    from julia_core.capability.financial.research.handoff import RecursiveResearchHandoff

    env_dir, arg_dir = tmp_path / "env-cards", tmp_path / "arg-cards"
    env_dir.mkdir()
    arg_dir.mkdir()
    monkeypatch.setenv("STRATEGY_CARD_DIR", str(env_dir))
    assert RecursiveResearchHandoff().card_dir == env_dir
    assert RecursiveResearchHandoff(card_dir=str(arg_dir)).card_dir == arg_dir      # explicit argument wins


# ── julia_agent_server.py (not the official entry): no Desktop CLAUDE.md ───

def test_agent_server_has_no_desktop_claude_md_dependency(monkeypatch, tmp_path):
    monkeypatch.delenv("JULIA_AGENT_CLAUDE_MD", raising=False)
    sys.path.insert(0, str(ROOT))
    try:
        import importlib
        server = importlib.import_module("julia_agent_server")
        importlib.reload(server)
    finally:
        sys.path.remove(str(ROOT))
    assert "Desktop" not in str(getattr(server, "CLAUDE_MD", ""))
    assert "朱婉清" in server._build_system_prompt()                  # built-in persona text, no external file
    persona = tmp_path / "CLAUDE.md"
    persona.write_text("PERSONA-FROM-CONFIG")
    monkeypatch.setenv("JULIA_AGENT_CLAUDE_MD", str(persona))
    importlib.reload(server)
    assert "PERSONA-FROM-CONFIG" in server._build_system_prompt()
    monkeypatch.setenv("JULIA_AGENT_CLAUDE_MD", str(tmp_path / "missing.md"))
    importlib.reload(server)
    with pytest.raises(RuntimeError, match="JULIA_AGENT_CLAUDE_MD"):
        server._build_system_prompt()


# ── frozen strategy-card snapshot (test-only) ──────────────────────────────

FIXTURE_DIR = ROOT / "tests" / "fixtures" / "strategy_cards"


def test_production_code_never_references_test_fixtures():
    offenders = []
    for path in (ROOT / "julia_core").rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="replace")
        for needle in ("tests/fixtures", "fixtures/strategy_cards", "tests.fixtures"):
            if needle in text:
                offenders.append(f"{path.relative_to(ROOT)}: {needle}")
    for path in ROOT.glob("*.py"):
        if "tests/fixtures" in path.read_text(encoding="utf-8", errors="replace"):
            offenders.append(f"{path.name}: tests/fixtures")
    assert offenders == [], "\n".join(offenders)


def test_strategy_card_snapshot_is_frozen_documented_and_sourced():
    import hashlib

    readme = (FIXTURE_DIR / "README.md").read_text(encoding="utf-8")
    assert "测试冻结快照，非正本；正本以 ai_theme_app 为准，更新须另开卡" in readme
    sums = {}
    for line in (FIXTURE_DIR / "SHA256SUMS").read_text().splitlines():
        digest, name = line.split(None, 1)
        sums[name.strip().lstrip("*")] = digest
    cards = sorted(p.name for p in FIXTURE_DIR.glob("*.json"))
    assert cards and cards == sorted(sums), "every card needs exactly one SHA256SUMS entry"
    for name in cards:
        assert hashlib.sha256((FIXTURE_DIR / name).read_bytes()).hexdigest() == sums[name], f"{name} was modified"
    sources = (FIXTURE_DIR / "SOURCES.tsv").read_text(encoding="utf-8").splitlines()[1:]
    rows = {row.split("\t")[0]: row.split("\t") for row in sources}
    assert sorted(rows) == cards
    for name, (_f, source_path, commit, digest) in rows.items():
        assert source_path == f"strategy_knowledge/cards/{name}" and commit.startswith("e1f1b9ad") and digest == sums[name]
