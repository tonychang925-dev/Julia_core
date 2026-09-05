"""Pinned composition for the frozen Market DomainIntelligenceAdapter."""

from __future__ import annotations

import hashlib
import importlib
import os
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from julia_core.capability.models import (
    CapabilityDefinition,
    CapabilityLayer,
    CapabilityRequest,
    CapabilityStatus,
    ProviderExecutionOutcome,
    SideEffectState,
    ToolResultStatus,
)

MARKET_FROZEN_SHA = "0bb026889f5c51e72aff9561b5eb542db7adf088"
MARKET_ADAPTER_SCHEMA_VERSION = "1.0"
MARKET_SOURCE_ROOT_CONFIG = "JULIA_MARKET_SOURCE_ROOT"
MARKET_SOURCE_SHA_CONFIG = "JULIA_MARKET_SOURCE_SHA"
MARKET_TREE_DIGEST_CONFIG = "JULIA_MARKET_TREE_DIGEST"
MARKET_DB_RUNTIME_DIGEST_CONFIG = "JULIA_MARKET_DB_RUNTIME_DIGEST"
_MARKET_TREE_DIGEST = "a389f92a0026291bbb2820bfce03fb9ff2545553859022dea3a413b8f1d52ad1"
_MARKET_IMPORT_MODULE = "stock_processing_service.application.services.julia_domain_adapter"
_MARKET_DATABASE_GATEWAY_MODULE = "database_service.gateway"
_MARKET_DB_RUNTIME_TREE_DIGEST = "19a4765e6e323bebb5b975560fce0a5a4111000844d95804a9dede1458935cff"
_MARKET_DB_RUNTIME_FILES = (
    "database_service/__init__.py",
    "database_service/client.py",
    "database_service/config.py",
    "database_service/factory.py",
    "database_service/gateway.py",
    "database_service/interface.py",
    "database_service/managers/__init__.py",
    "database_service/managers/base_manager.py",
    "database_service/managers/memory_manager.py",
    "database_service/managers/postgres_manager.py",
    "database_service/managers/redis_cached_manager.py",
    "database_service/managers/redis_event_bus.py",
    "database_service/managers/redis_stream_bus.py",
    "database_service/streams/__init__.py",
    "database_service/streams/database_interface_ext.py",
    "database_service/streams/producers/__init__.py",
    "database_service/streams/producers/event_producer.py",
    "database_service/streams/producers/news_producer.py",
    "database_service/streams/producers/theme_producer.py",
    "database_service/streams/stream_config.py",
    "database_service/streams/stream_factory.py",
    "database_service/streams/stream_gateway.py",
    "database_service/streams/stream_interface.py",
    "database_service/streams/stream_manager.py",
    "database_service/streams/utils/__init__.py",
    "database_service/streams/utils/alert_service.py",
    "database_service/streams/utils/consumer_group_manager.py",
    "database_service/streams/utils/error_handler.py",
    "database_service/streams/utils/retry_manager.py",
)
_APPROVED_MARKET_FILES = (
    "stock_processing_service/__init__.py",
    "stock_processing_service/application/services/__init__.py",
    "stock_processing_service/application/services/julia_domain_adapter/__init__.py",
    "stock_processing_service/application/services/julia_domain_adapter/adapter.py",
    "stock_processing_service/application/services/julia_domain_adapter/contracts.py",
    "stock_processing_service/application/services/julia_domain_adapter/provenance.py",
    "stock_processing_service/application/services/julia_domain_adapter/operations/__init__.py",
    "stock_processing_service/application/services/julia_domain_adapter/operations/alerts.py",
    "stock_processing_service/application/services/julia_domain_adapter/operations/event_read.py",
    "stock_processing_service/application/services/julia_domain_adapter/operations/event_resolve.py",
    "stock_processing_service/application/services/julia_domain_adapter/operations/snapshot.py",
)
_OPERATIONS_BY_CAPABILITY = {
    "market.event.resolve": "market.event.resolve",
    "market.event.read": "market.event.read",
    "market.snapshot.read": "market.snapshot",
    "market.alert.query": "market.alerts",
}
_REQUIRED_OPERATIONS = frozenset({"market.event.resolve", "market.event.read"})
_FROZEN_MARKET_CAPABILITIES = (
    CapabilityDefinition(
        name="market.event.resolve",
        description="Resolve one bounded query/theme hint into canonical Market event candidates",
        layer=CapabilityLayer.INTELLIGENCE,
        provider="ai_theme_app",
        permission_scope="market.observe",
        input_schema={"query": "bounded inert user query"},
        adapter="direct",
        schema_version="1.0",
    ),
    CapabilityDefinition(
        name="market.event.read",
        description="Read one canonical Market event by Market-owned event_id",
        layer=CapabilityLayer.INTELLIGENCE,
        provider="ai_theme_app",
        permission_scope="market.observe",
        input_schema={"event_id": "canonical public.news_event.id integer"},
        adapter="direct",
        schema_version="1.0",
    ),
    CapabilityDefinition(
        name="market.snapshot.read",
        description="Read the frozen Market snapshot observation",
        layer=CapabilityLayer.INTELLIGENCE,
        provider="ai_theme_app",
        permission_scope="market.observe",
        adapter="direct",
        schema_version="1.0",
    ),
    CapabilityDefinition(
        name="market.alert.query",
        description="Query frozen Market alert observations",
        layer=CapabilityLayer.INTELLIGENCE,
        provider="ai_theme_app",
        permission_scope="market.observe",
        adapter="direct",
        schema_version="1.0",
    ),
)


class FrozenMarketCompositionError(ValueError):
    """The configured Market source is missing, unpinned, or modified."""


@dataclass(frozen=True, slots=True)
class FrozenMarketBinding:
    source_root: Path
    source_sha: str
    tree_digest: str
    adapter_class: type


class MarketDomainAdapterProvider:
    """Compose Core Market capabilities through the frozen Market facade."""

    def __init__(self, adapter: Any, *, source_sha: str = MARKET_FROZEN_SHA):
        self.adapter = adapter
        self.source_sha = source_sha

    async def health(self) -> tuple[bool, str]:
        supported = getattr(self.adapter, "supported_operations", ())
        missing = sorted(_REQUIRED_OPERATIONS - set(supported))
        if missing:
            return False, f"frozen Market operations unavailable: {', '.join(missing)}"
        if not frozen_market_database_gateways_bound(self.adapter):
            return False, "frozen Market database gateway is not bound"
        return True, f"frozen Market adapter sha:{self.source_sha}"

    async def execute(self, request: CapabilityRequest) -> ProviderExecutionOutcome:
        operation = _OPERATIONS_BY_CAPABILITY.get(request.capability_id)
        if operation is None:
            raise ValueError(f"unsupported frozen Market capability: {request.capability_id}")
        adapter_request = {
            "operation": operation,
            "arguments": dict(request.arguments),
            "correlation_id": request.correlation_id,
            "idempotency_key": request.idempotency_key,
            "requested_at": "",
            "schema_version": MARKET_ADAPTER_SCHEMA_VERSION,
            "trace_metadata": {
                "capability_id": request.capability_id,
                "capability_request_id": request.capability_request_id,
                "turn_id": request.turn_id,
                "generation_id": request.generation_id,
                "market_source_sha": self.source_sha,
            },
        }
        envelope = await self.adapter.execute(adapter_request)
        payload = envelope.to_dict() if hasattr(envelope, "to_dict") else dict(envelope)
        return _outcome_from_envelope(payload)


def register_frozen_market_capabilities(
    registry: Any,
    *,
    status: CapabilityStatus = CapabilityStatus.AVAILABLE,
) -> None:
    for definition in _FROZEN_MARKET_CAPABILITIES:
        registry.register_definition(
            CapabilityDefinition(
                name=definition.name,
                description=definition.description,
                layer=definition.layer,
                provider=definition.provider,
                permission_scope=definition.permission_scope,
                input_schema=dict(definition.input_schema),
                adapter=definition.adapter,
                status=status,
                schema_version=definition.schema_version,
            )
        )


def load_frozen_market_binding(
    environment: Mapping[str, str] | None = None,
) -> FrozenMarketBinding:
    env = dict(environment if environment is not None else os.environ)
    missing = [
        name
        for name in (
            MARKET_SOURCE_ROOT_CONFIG,
            MARKET_SOURCE_SHA_CONFIG,
            MARKET_TREE_DIGEST_CONFIG,
        )
        if not env.get(name, "").strip()
    ]
    if missing:
        raise FrozenMarketCompositionError(
            f"frozen Market configuration is incomplete: {', '.join(missing)}"
        )
    if env[MARKET_SOURCE_SHA_CONFIG] != MARKET_FROZEN_SHA:
        raise FrozenMarketCompositionError(
            f"Market source SHA must equal {MARKET_FROZEN_SHA}"
        )
    if env[MARKET_TREE_DIGEST_CONFIG] != _MARKET_TREE_DIGEST:
        raise FrozenMarketCompositionError("Market tree digest is not the frozen value")

    try:
        root = Path(env[MARKET_SOURCE_ROOT_CONFIG]).expanduser().resolve(strict=True)
    except OSError as exc:
        raise FrozenMarketCompositionError(
            f"frozen Market source root unavailable: {exc}"
        ) from exc
    observed_digest = market_tree_digest(root)
    if observed_digest != _MARKET_TREE_DIGEST:
        raise FrozenMarketCompositionError(
            f"Market source digest mismatch: expected {_MARKET_TREE_DIGEST}, got {observed_digest}"
        )
    module = _import_frozen_market_module(root)
    adapter_class = getattr(module, "DomainIntelligenceAdapter", None)
    if not isinstance(adapter_class, type):
        raise FrozenMarketCompositionError("frozen Market adapter export is missing")
    return FrozenMarketBinding(
        source_root=root,
        source_sha=env[MARKET_SOURCE_SHA_CONFIG],
        tree_digest=observed_digest,
        adapter_class=adapter_class,
    )


def create_frozen_market_provider(
    environment: Mapping[str, str] | None = None,
    *,
    database_gateway: Any | None = None,
    market_context_exporter: Any | None = None,
    workbench_base_dir: str | None = None,
    clock: Any | None = None,
) -> MarketDomainAdapterProvider:
    binding = load_frozen_market_binding(environment)
    adapter = binding.adapter_class(
        database_gateway=database_gateway,
        market_context_exporter=market_context_exporter,
        workbench_base_dir=workbench_base_dir,
        clock=clock,
    )
    return MarketDomainAdapterProvider(adapter, source_sha=binding.source_sha)


async def compose_frozen_market_provider(
    environment: Mapping[str, str] | None = None,
    *,
    retain_modules: bool = False,
) -> tuple[MarketDomainAdapterProvider, Any]:
    binding = load_frozen_market_binding(environment)
    validate_frozen_market_db_runtime(environment, binding.source_root)
    gateway_module, restore_gateway_modules = _load_pinned_market_module(
        binding.source_root,
        _MARKET_DATABASE_GATEWAY_MODULE,
        "database_service",
        "Market database gateway",
    )
    try:
        gateway_class = getattr(gateway_module, "DatabaseGateway", None)
        if not isinstance(gateway_class, type):
            raise FrozenMarketCompositionError("frozen Market DatabaseGateway export is missing")
        gateway = await gateway_class.initialize()
    finally:
        if not retain_modules:
            restore_gateway_modules()
    if not isinstance(gateway, gateway_class) or getattr(gateway, "_initialized", None) is not True:
        raise FrozenMarketCompositionError("frozen Market DatabaseGateway initialization failed")
    adapter = binding.adapter_class(database_gateway=gateway)
    provider = MarketDomainAdapterProvider(adapter, source_sha=binding.source_sha)
    if not frozen_market_database_gateways_bound(provider.adapter):
        raise FrozenMarketCompositionError("composed frozen Market provider lost its DatabaseGateway")
    return provider, gateway


def frozen_market_database_gateways_bound(adapter: Any) -> bool:
    operations = getattr(adapter, "_operations", None)
    if not isinstance(operations, Mapping):
        return True
    for capability in ("market.event.resolve", "market.event.read"):
        operation = operations.get(capability)
        gateway = getattr(operation, "_database_gateway", None)
        if gateway is None or getattr(gateway, "_initialized", None) is False:
            return False
    return True


def validate_frozen_market_db_runtime(
    environment: Mapping[str, str] | None,
    root: Path,
) -> str:
    env = dict(environment if environment is not None else os.environ)
    configured = env.get(MARKET_DB_RUNTIME_DIGEST_CONFIG, "").strip()
    if not configured:
        raise FrozenMarketCompositionError(
            f"frozen Market configuration is incomplete: {MARKET_DB_RUNTIME_DIGEST_CONFIG}"
        )
    if configured != _MARKET_DB_RUNTIME_TREE_DIGEST:
        raise FrozenMarketCompositionError(
            f"Market DB runtime digest must equal {_MARKET_DB_RUNTIME_TREE_DIGEST}"
        )
    observed = market_db_runtime_tree_digest(root)
    if observed != _MARKET_DB_RUNTIME_TREE_DIGEST:
        raise FrozenMarketCompositionError(
            f"Market DB runtime digest mismatch: expected {_MARKET_DB_RUNTIME_TREE_DIGEST}, got {observed}"
        )
    return observed


def market_tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for relative in _APPROVED_MARKET_FILES:
        path = root / relative
        try:
            content = path.read_bytes()
        except OSError as exc:
            raise FrozenMarketCompositionError(
                f"frozen Market file unavailable: {relative}"
            ) from exc
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(content).digest())
        digest.update(b"\0")
    return digest.hexdigest()


def market_db_runtime_tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for relative in _MARKET_DB_RUNTIME_FILES:
        path = root / relative
        try:
            content = path.read_bytes()
        except OSError as exc:
            raise FrozenMarketCompositionError(
                f"frozen Market DB runtime file unavailable: {relative}"
            ) from exc
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(content).digest())
        digest.update(b"\0")
    return digest.hexdigest()


def _import_frozen_market_module(root: Path):
    module, restore_modules = _load_pinned_market_module(
        root,
        _MARKET_IMPORT_MODULE,
        "stock_processing_service",
        "frozen Market adapter",
    )
    restore_modules()
    return module


def _load_pinned_market_module(
    root: Path,
    module_name: str,
    package_name: str,
    description: str,
):
    original_path = list(sys.path)
    package_prefix = f"{package_name}."
    displaced_modules = {
        name: module
        for name, module in sys.modules.items()
        if name == package_name or name.startswith(package_prefix)
    }
    for name in displaced_modules:
        del sys.modules[name]
    try:
        sys.path.insert(0, str(root))
        module = importlib.import_module(module_name)
    except Exception as exc:
        raise FrozenMarketCompositionError(
            f"{description} import failed: {exc}"
        ) from exc
    finally:
        sys.path[:] = original_path

    module_file = Path(getattr(module, "__file__", ""))
    if not module_file.is_relative_to(root):
        def restore_modules() -> None:
            sys.path[:] = original_path
            _restore_modules(displaced_modules, package_name)

        restore_modules()
        raise FrozenMarketCompositionError(f"{description} import escaped the pinned source root")
    for name, module_item in sys.modules.items():
        if name != package_name and not name.startswith(package_prefix):
            continue
        module_path = getattr(module_item, "__file__", "")
        if module_path and not Path(module_path).is_relative_to(root):
            def restore_modules() -> None:
                sys.path[:] = original_path
                _restore_modules(displaced_modules, package_name)

            restore_modules()
            raise FrozenMarketCompositionError(f"ambient Market module won {description} import resolution")

    def restore_modules() -> None:
        sys.path[:] = original_path
        _restore_modules(displaced_modules, package_name)

    return module, restore_modules


def _restore_displaced_modules(modules: Mapping[str, Any]) -> None:
    _restore_modules(modules, "stock_processing_service")


def _restore_modules(modules: Mapping[str, Any], package_name: str) -> None:
    package_prefix = f"{package_name}."
    for name in list(sys.modules):
        if name == package_name or name.startswith(package_prefix):
            del sys.modules[name]
    sys.modules.update(modules)


def _outcome_from_envelope(envelope: Mapping[str, Any]) -> ProviderExecutionOutcome:
    status = str(envelope.get("status", "error"))
    failures = envelope.get("failures") or []
    failure = dict(failures[0]) if isinstance(failures, list) and failures else None
    if status == "success":
        outcome_status = ToolResultStatus.SUCCESS
    elif status == "partial":
        outcome_status = ToolResultStatus.PARTIAL
    elif status == "unavailable":
        outcome_status = ToolResultStatus.UNAVAILABLE
    else:
        outcome_status = ToolResultStatus.ERROR
    return ProviderExecutionOutcome(
        status=outcome_status,
        structured_output=dict(envelope),
        error=failure,
        side_effect_state=SideEffectState.NONE,
    )


__all__ = [
    "FrozenMarketBinding",
    "FrozenMarketCompositionError",
    "MARKET_FROZEN_SHA",
    "MARKET_SOURCE_ROOT_CONFIG",
    "MARKET_SOURCE_SHA_CONFIG",
    "MARKET_TREE_DIGEST_CONFIG",
    "MARKET_DB_RUNTIME_DIGEST_CONFIG",
    "MarketDomainAdapterProvider",
    "compose_frozen_market_provider",
    "create_frozen_market_provider",
    "frozen_market_database_gateways_bound",
    "load_frozen_market_binding",
    "market_tree_digest",
    "market_db_runtime_tree_digest",
    "register_frozen_market_capabilities",
]
