"""AT-12 minimal reflection decision surface.

This module deliberately does not generate prose, persist files, call providers,
or inspect UI/runtime caches. It only provides the explicit no-entry decision
needed by the governed Diary pipeline.
"""
from __future__ import annotations

from dataclasses import dataclass

from .models import NO_ENTRY, NoEntry, ReflectionResult


@dataclass(frozen=True)
class ReflectionOpportunity:
    """A trigger-created opportunity to reflect, not authority to write."""

    trigger_id: str
    reflection_type: str
    reflection_time: str
    reason: str = ""
    significance_markers: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self.trigger_id) is not str or not self.trigger_id.strip():
            raise ValueError("ReflectionOpportunity.trigger_id must be a non-empty str")
        if type(self.reflection_type) is not str or not self.reflection_type.strip():
            raise ValueError("ReflectionOpportunity.reflection_type must be a non-empty str")
        if type(self.reflection_time) is not str or not self.reflection_time.strip():
            raise ValueError("ReflectionOpportunity.reflection_time must be a non-empty str")
        if type(self.reason) is not str:
            raise ValueError("ReflectionOpportunity.reason must be a str")
        if type(self.significance_markers) is not tuple:
            raise ValueError("ReflectionOpportunity.significance_markers must be a tuple")
        if not all(type(item) is str for item in self.significance_markers):
            raise ValueError("ReflectionOpportunity.significance_markers must contain str only")


def decide_trivial_reflection(opportunity: ReflectionOpportunity) -> ReflectionResult:
    """Return explicit NO_ENTRY for a trivial reflection opportunity.

    A trigger firing is not enough to create Diary truth. Meaning-bearing
    reflection candidates are outside AT-12 and belong to later gates.
    """

    if type(opportunity) is not ReflectionOpportunity:
        raise ValueError("opportunity must be ReflectionOpportunity")
    if opportunity.significance_markers:
        raise ValueError("decide_trivial_reflection accepts trivial opportunities only")
    return NO_ENTRY


__all__ = ["ReflectionOpportunity", "decide_trivial_reflection", "NO_ENTRY", "NoEntry", "ReflectionResult"]
