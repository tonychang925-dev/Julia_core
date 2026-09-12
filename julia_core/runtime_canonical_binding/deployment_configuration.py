"""Immutable Owner-recorded runtime binding deployment choice."""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import RuntimeCanonicalAuthorityBindingRef


@dataclass(frozen=True, slots=True, kw_only=True)
class RuntimeBindingDeploymentConfiguration:
    """Carry one exact ref selected by deployment governance."""

    runtime_binding_ref: RuntimeCanonicalAuthorityBindingRef

    def __post_init__(self) -> None:
        if type(self.runtime_binding_ref) is not RuntimeCanonicalAuthorityBindingRef:
            raise TypeError(
                "runtime_binding_ref requires an exact RuntimeCanonicalAuthorityBindingRef"
            )


__all__ = ["RuntimeBindingDeploymentConfiguration"]
