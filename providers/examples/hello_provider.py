"""Hello World Provider — minimal Domain Provider example.

This shows how to create a custom provider that plugs into Julia Core.
"""
from dataclasses import dataclass
from datetime import datetime, timezone

from julia_core.providers.interface import DomainProvider
from julia_core.providers.registry import ProviderIdentity
from julia_core.context_os.request import ContextRequest
from julia_core.context_os.block import ContextBlock


class HelloWorldProvider:
    """A minimal provider that returns a greeting context block.

    This demonstrates the Domain Provider protocol:
      1. Declare identity (metadata + capabilities)
      2. Accept ContextRequest
      3. Return ContextBlock(s) with evidence_refs
    """

    domain = "demo"

    _IDENTITY = ProviderIdentity(
        provider_id="demo-hello-v1",
        provider_name="Hello World Provider",
        version="1.0.0",
        domain="demo",
        capabilities=("greeting",),
    )

    def metadata(self) -> ProviderIdentity:
        return self._IDENTITY

    def capabilities(self) -> tuple[str, ...]:
        return self._IDENTITY.capabilities

    def provide(self, request: ContextRequest) -> tuple[ContextBlock, ...]:
        return (
            ContextBlock(
                source="demo-hello-v1",
                block_type="greeting",
                domain="demo",
                authority="demo.provider",
                authority_score=1.0,
                content={"message": "Hello from Julia Core Provider!"},
                evidence_refs=("demo-greeting-001",),
                source_refs=("demo.hello",),
                metadata={"provider_version": "1.0.0"},
            ),
        )
