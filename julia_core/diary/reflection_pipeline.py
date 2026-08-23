"""AT-12 governed reflection integration surface.

This is intentionally narrow: it proves the NO_ENTRY product path without
implementing AT-13 meaningful-entry generation. Non-trivial reflection markers
remain outside AT-12.
"""
from __future__ import annotations

from dataclasses import dataclass

from .models import NO_ENTRY, NoEntry
from .reflection_decision import ReflectionOpportunity, decide_trivial_reflection
from .repository_protocol import DiaryRepository


@dataclass(frozen=True)
class ReflectionExecutionResult:
    """Observable result of a reflection opportunity execution."""

    trigger_id: str
    decision: NoEntry
    diary_mutated: bool
    accepted_entry_id: str | None = None

    def __post_init__(self) -> None:
        if type(self.trigger_id) is not str or not self.trigger_id.strip():
            raise ValueError("ReflectionExecutionResult.trigger_id must be a non-empty str")
        if type(self.decision) is not NoEntry:
            raise ValueError("ReflectionExecutionResult.decision must be NoEntry for AT-12")
        if type(self.diary_mutated) is not bool:
            raise ValueError("ReflectionExecutionResult.diary_mutated must be bool")
        if self.accepted_entry_id is not None and type(self.accepted_entry_id) is not str:
            raise ValueError("ReflectionExecutionResult.accepted_entry_id must be None or str")


def run_trivial_reflection_opportunity(
    opportunity: ReflectionOpportunity,
    repository: DiaryRepository,
) -> ReflectionExecutionResult:
    """Execute the AT-12 governed no-entry path.

    The repository is an explicit dependency so tests can prove no canonical
    append occurs. This function never imports or calls legacy DiaryWriter and
    never writes files directly.
    """

    if repository is None:
        raise ValueError("repository is required")
    decision = decide_trivial_reflection(opportunity)
    if decision is not NO_ENTRY:
        raise RuntimeError("AT-12 trivial reflection path expected NO_ENTRY")
    return ReflectionExecutionResult(
        trigger_id=opportunity.trigger_id,
        decision=decision,
        diary_mutated=False,
        accepted_entry_id=None,
    )


__all__ = ["ReflectionExecutionResult", "run_trivial_reflection_opportunity"]
