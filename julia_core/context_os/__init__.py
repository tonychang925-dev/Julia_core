"""Minimal Julia Core Context OS skeleton.

Imports are intentionally lazy so leaf modules such as ``context_os.block`` can
be used without importing optional continuity/runtime adapters.
"""

__all__ = [
    "ContextBlock",
    "ContextPlanner",
    "ContextPriority",
    "ContextReconstructionRequest",
    "ContextReconstructionResult",
    "ContextReconstructor",
    "ContextRequirement",
    "ContextRequest",
    "ContextResolver",
]


def __getattr__(name: str):
    if name == "ContextBlock":
        from .block import ContextBlock

        return ContextBlock
    if name == "ContextPlanner":
        from .planner import ContextPlanner

        return ContextPlanner
    if name == "ContextRequest":
        from .request import ContextRequest

        return ContextRequest
    if name == "ContextResolver":
        from .resolver import ContextResolver

        return ContextResolver
    if name in {"ContextPriority", "ContextReconstructionRequest", "ContextReconstructionResult", "ContextRequirement"}:
        from .requirements import ContextPriority, ContextReconstructionRequest, ContextReconstructionResult, ContextRequirement

        return {
            "ContextPriority": ContextPriority,
            "ContextReconstructionRequest": ContextReconstructionRequest,
            "ContextReconstructionResult": ContextReconstructionResult,
            "ContextRequirement": ContextRequirement,
        }[name]
    if name == "ContextReconstructor":
        from .reconstruction import ContextReconstructor

        return ContextReconstructor
    raise AttributeError(name)
