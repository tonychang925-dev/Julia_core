"""Domain Provider interface for Julia Core.

Domains provide facts and evidence as context candidates. They do not provide
prompts, final answers, or memory mutations.
"""

from __future__ import annotations

from typing import Protocol

from julia_core.context_os.block import ContextBlock
from julia_core.context_os.request import ContextRequest


class DomainProvider(Protocol):
    domain: str

    def provide(self, request: ContextRequest) -> tuple[ContextBlock, ...]:
        ...
