from __future__ import annotations

import ast
import io
import inspect
import subprocess
import sys
import tarfile
import types
from pathlib import Path

import pytest

from julia_core.capability.models import CapabilityRequest
from julia_core.capability.providers.ai_theme.frozen_market import (
    MARKET_DB_RUNTIME_DIGEST_CONFIG,
    MARKET_FROZEN_SHA,
    MARKET_SOURCE_ROOT_CONFIG,
    MARKET_SOURCE_SHA_CONFIG,
    MARKET_TREE_DIGEST_CONFIG,
    FrozenMarketCompositionError,
    MarketDomainAdapterProvider,
    _MARKET_DB_RUNTIME_FILES,
    _MARKET_DB_RUNTIME_TREE_DIGEST,
    _load_pinned_market_module,
    compose_frozen_market_provider,
    load_frozen_market_binding,
    market_db_runtime_tree_digest,
    market_tree_digest,
)


MARKET_REPO = Path("/Users/admin/glm-workspace/ai_theme_app")
MARKET_TREE_DIGEST = "a389f92a0026291bbb2820bfce03fb9ff2545553859022dea3a413b8f1d52ad1"
DB_RUNTIME_TREE_DIGEST = "19a4765e6e323bebb5b975560fce0a5a4111000844d95804a9dede1458935cff"
OLD_MARKET_SHA = "d6889f4f39fc4f8adf404ea7c51eee3ad22d7fa7"
OLD_MARKET_RELEASE = Path(
    "/Users/admin/julia_rd1_controlled/releases/"
    "market-d6889f4f39fc4f8adf404ea7c51eee3ad22d7fa7"
)


@pytest.fixture(scope="module")
def frozen_market_root(tmp_path_factory) -> Path:
    root = tmp_path_factory.mktemp("r9-d1a-market") / "ai_theme_app"
    archive = subprocess.run(
        ["git", "-C", str(MARKET_REPO), "archive", MARKET_FROZEN_SHA],
        check=True,
        stdout=subprocess.PIPE,
    ).stdout
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as archive_file:
        archive_file.extractall(root, filter="data")
    return root


def pinned_environment(root: Path, **overrides: str) -> dict[str, str]:
    values = {
        MARKET_SOURCE_ROOT_CONFIG: str(root),
        MARKET_SOURCE_SHA_CONFIG: MARKET_FROZEN_SHA,
        MARKET_TREE_DIGEST_CONFIG: MARKET_TREE_DIGEST,
        MARKET_DB_RUNTIME_DIGEST_CONFIG: DB_RUNTIME_TREE_DIGEST,
    }
    values.update(overrides)
    return values


def test_db_runtime_digest_is_deterministic_and_configured(frozen_market_root):
    assert market_db_runtime_tree_digest(frozen_market_root) == DB_RUNTIME_TREE_DIGEST
    assert DB_RUNTIME_TREE_DIGEST == _MARKET_DB_RUNTIME_TREE_DIGEST
    assert len(_MARKET_DB_RUNTIME_FILES) == 29
    assert list(_MARKET_DB_RUNTIME_FILES) == sorted(_MARKET_DB_RUNTIME_FILES)
    assert all((frozen_market_root / relative).is_file() for relative in _MARKET_DB_RUNTIME_FILES)


def test_controlled_startup_registers_market_before_bridge_initialization():
    from julia_core.runtime.capability_bridge import run_controlled_brain

    source = inspect.getsource(run_controlled_brain)
    registration = source.index("register_canonical_market_provider")
    initialization = source.index("bridge.initialize()")
    configuration = source.index("configure_capability_bridge(bridge)")
    assert registration < initialization < configuration


def test_pinned_module_path_resolves_modules_packages_and_missing_paths(tmp_path: Path):
    from julia_core.runtime.capability_bridge import run_controlled_brain

    root = tmp_path / "pinned-root"
    package = root / "example_pkg"
    child = package / "child"
    package.mkdir(parents=True)
    child.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    (child / "__init__.py").write_text("", encoding="utf-8")
    (package / "module.py").write_text("", encoding="utf-8")

    function_node = next(
        node for node in ast.walk(ast.parse(inspect.getsource(run_controlled_brain)))
        if isinstance(node, ast.FunctionDef) and node.name == "pinned_module_path"
    )
    namespace = {"Path": Path, "source_root": root, "RuntimeError": RuntimeError}
    exec(compile(
        ast.Module(body=[function_node], type_ignores=[]),
        filename="<pinned_module_path>",
        mode="exec",
    ), namespace)
    pinned_module_path = namespace["pinned_module_path"]

    assert pinned_module_path("example_pkg.module") == (package / "module.py").resolve()
    assert pinned_module_path("example_pkg.child") == (child / "__init__.py").resolve()
    with pytest.raises(RuntimeError, match="pinned Market module path unavailable"):
        pinned_module_path("example_pkg.missing")


@pytest.mark.asyncio
async def test_db_runtime_mutation_fails_closed_while_adapter_digest_matches(
    frozen_market_root,
    tmp_path: Path,
):
    mutated_root = tmp_path / "mutated-market"
    subprocess.run(["cp", "-R", str(frozen_market_root), str(mutated_root)], check=True)
    (mutated_root / "database_service/config.py").write_text(
        (mutated_root / "database_service/config.py").read_text(encoding="utf-8") + "\n# r9-d1a mutation\n",
        encoding="utf-8",
    )

    assert market_tree_digest(mutated_root) == MARKET_TREE_DIGEST
    assert market_db_runtime_tree_digest(mutated_root) != DB_RUNTIME_TREE_DIGEST
    with pytest.raises(FrozenMarketCompositionError, match="Market DB runtime digest mismatch"):
        await compose_frozen_market_provider(pinned_environment(mutated_root))


@pytest.mark.asyncio
async def test_invalid_configured_db_runtime_digest_fails_closed(frozen_market_root):
    with pytest.raises(FrozenMarketCompositionError, match="Market DB runtime digest must equal"):
        await compose_frozen_market_provider(pinned_environment(
            frozen_market_root,
            **{MARKET_DB_RUNTIME_DIGEST_CONFIG: "0" * 64},
        ))


def test_adapter_and_db_runtime_digests_are_separate(frozen_market_root, tmp_path: Path):
    adapter_mutated = tmp_path / "adapter-mutated"
    subprocess.run(["cp", "-R", str(frozen_market_root), str(adapter_mutated)], check=True)
    event_resolve = adapter_mutated / (
        "stock_processing_service/application/services/julia_domain_adapter/operations/event_resolve.py"
    )
    event_resolve.write_text(event_resolve.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    assert market_tree_digest(adapter_mutated) != MARKET_TREE_DIGEST
    assert market_db_runtime_tree_digest(adapter_mutated) == DB_RUNTIME_TREE_DIGEST


def test_target_identity_rejects_old_market_release():
    assert MARKET_FROZEN_SHA == "0bb026889f5c51e72aff9561b5eb542db7adf088"
    with pytest.raises(FrozenMarketCompositionError, match="Market source SHA must equal"):
        load_frozen_market_binding(pinned_environment(
            OLD_MARKET_RELEASE,
            **{MARKET_SOURCE_SHA_CONFIG: OLD_MARKET_SHA},
        ))


def test_target_event_resolve_has_r9_f1_and_f1a_fingerprints(frozen_market_root):
    source = (
        frozen_market_root
        / "stock_processing_service/application/services/julia_domain_adapter/operations/event_resolve.py"
    ).read_text(encoding="utf-8")
    for fingerprint in (
        "operation_symbol",
        "failure_layer",
        "exception_class",
        "exception_message",
        "sqlstate",
        "pgcode",
        "errno",
        "error_code",
        "process_pid",
        "observed_at",
        "resolver_query",
        "normalized_theme",
        "time_window",
        "correlation_id",
        "idempotency_id",
        "precollapse_provider_status",
        "_bounded_text",
    ):
        assert fingerprint in source
    assert "traceback" not in source.lower()


def test_target_pinned_event_resolve_module_provenance(frozen_market_root):
    module, restore_modules = _load_pinned_market_module(
        frozen_market_root,
        "stock_processing_service.application.services.julia_domain_adapter.operations.event_resolve",
        "stock_processing_service",
        "Market event resolver",
    )
    try:
        assert Path(module.__file__).resolve().is_relative_to(frozen_market_root)
    finally:
        restore_modules()


def test_ambient_db_module_is_displaced_by_pinned_modules(frozen_market_root, monkeypatch):
    ambient = types.ModuleType("database_service")
    ambient.__file__ = "/outside/pinned/database_service/__init__.py"
    monkeypatch.setitem(sys.modules, "database_service", ambient)

    module, restore_modules = _load_pinned_market_module(
        frozen_market_root,
        "database_service.gateway",
        "database_service",
        "Market database gateway",
    )
    try:
        assert Path(module.__file__).resolve().is_relative_to(frozen_market_root)
        for name, item in sys.modules.items():
            if name != "database_service" and not name.startswith("database_service."):
                continue
            module_path = getattr(item, "__file__", "")
            if module_path:
                assert Path(module_path).resolve().is_relative_to(frozen_market_root)
    finally:
        restore_modules()
    assert sys.modules["database_service"] is ambient


@pytest.mark.asyncio
async def test_provider_trace_reports_configured_source_identity():
    class RecordingAdapter:
        supported_operations = ("market.event.resolve", "market.event.read")

        def __init__(self):
            self.request = None

        async def execute(self, request):
            self.request = request
            return {"status": "success", "payload": {}}

    adapter = RecordingAdapter()
    provider = MarketDomainAdapterProvider(adapter, source_sha=MARKET_FROZEN_SHA)
    await provider.execute(CapabilityRequest("market.event.resolve", {"query": "static"}))

    assert adapter.request["trace_metadata"]["market_source_sha"] == MARKET_FROZEN_SHA
