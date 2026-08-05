"""Context Budget Management v1.

E2.2.2 scope:
    allocate bounded cognitive context budget over ranked candidates.

This module does not retrieve memory, summarize with LLMs, mutate continuity,
modify persona, or call providers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from .priority_model import ContextCandidate, CurrentIntent, RankedContextCandidate, ContextPriorityResolver


DEFAULT_CATEGORY_ORDER = ("identity", "relationship", "project", "task", "conversation", "general")
SEMANTIC_CATEGORY_MAP = {
    "identity": "identity",
    "identity_origin": "identity",
    "relationship": "relationship",
    "project": "project",
    "task": "task",
    "session": "conversation",
    "recent": "conversation",
    "general": "general",
}
DEFAULT_MIN_FLOORS = {
    "identity": 0.10,
    "relationship": 0.05,
    "project": 0.10,
    "task": 0.15,
    "conversation": 0.10,
    "general": 0.0,
}


@dataclass(frozen=True, slots=True)
class ContextBudget:
    total_budget: int
    identity_budget: int | None = None
    relationship_budget: int | None = None
    project_budget: int | None = None
    task_budget: int | None = None
    conversation_budget: int | None = None
    general_budget: int | None = None

    def __post_init__(self) -> None:
        if self.total_budget <= 0:
            raise ValueError("total_budget must be positive")
        for name in (
            "identity_budget",
            "relationship_budget",
            "project_budget",
            "task_budget",
            "conversation_budget",
            "general_budget",
        ):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise ValueError(f"{name} must be non-negative")

    def explicit_allocations(self) -> dict[str, int]:
        return {
            "identity": self.identity_budget or 0,
            "relationship": self.relationship_budget or 0,
            "project": self.project_budget or 0,
            "task": self.task_budget or 0,
            "conversation": self.conversation_budget or 0,
            "general": self.general_budget or 0,
        }


@dataclass(frozen=True, slots=True)
class BudgetedContextSelection:
    selected: tuple[RankedContextCandidate, ...]
    dropped: tuple[RankedContextCandidate, ...]
    budget: ContextBudget
    used_tokens: int
    category_allocations: Mapping[str, int]
    category_used: Mapping[str, int]
    authority: str = "ContextOS"

    def to_dict(self) -> dict[str, Any]:
        return {
            "authority": self.authority,
            "total_budget": self.budget.total_budget,
            "used_tokens": self.used_tokens,
            "category_allocations": dict(self.category_allocations),
            "category_used": dict(self.category_used),
            "selected": [item.to_dict() for item in self.selected],
            "dropped": [item.to_dict() for item in self.dropped],
        }


class ContextBudgetAllocator:
    """Selects ranked candidates under bounded cognitive budget."""

    def __init__(self, priority_resolver: ContextPriorityResolver | None = None) -> None:
        self.priority_resolver = priority_resolver or ContextPriorityResolver()

    def allocate(
        self,
        candidates: Iterable[ContextCandidate | Mapping[str, Any]],
        intent: CurrentIntent | Mapping[str, Any],
        budget: ContextBudget,
    ) -> BudgetedContextSelection:
        ranked = self.priority_resolver.rank(candidates, intent).ranked_candidates
        allocations = self._allocations_for(budget, intent)
        used_by_category = {category: 0 for category in allocations}
        selected: list[RankedContextCandidate] = []
        dropped: list[RankedContextCandidate] = []
        total_used = 0

        for item in ranked:
            category = self._category_for(item.candidate)
            cost = max(1, item.candidate.estimated_tokens or 1)
            category_cap = allocations.get(category, 0)
            fits_total = total_used + cost <= budget.total_budget
            fits_category = used_by_category.get(category, 0) + cost <= category_cap
            if fits_total and fits_category:
                selected.append(item)
                used_by_category[category] = used_by_category.get(category, 0) + cost
                total_used += cost
            else:
                dropped.append(item)

        return BudgetedContextSelection(
            selected=tuple(selected),
            dropped=tuple(dropped),
            budget=budget,
            used_tokens=total_used,
            category_allocations=allocations,
            category_used=used_by_category,
        )

    def _allocations_for(self, budget: ContextBudget, intent: CurrentIntent | Mapping[str, Any]) -> dict[str, int]:
        current_intent = self.priority_resolver._normalize_intent(intent)
        explicit = budget.explicit_allocations()
        if any(explicit.values()):
            allocations = explicit
            remainder = max(0, budget.total_budget - sum(allocations.values()))
            allocations["task"] += remainder
            return allocations

        weights = dict(DEFAULT_MIN_FLOORS)
        targets = set(current_intent.semantic_targets)
        if {"identity", "identity_origin"} & targets:
            weights["identity"] += 0.15
        if current_intent.relationship_sensitive:
            weights["relationship"] += 0.10
        if current_intent.task_domain:
            weights["project"] += 0.10
            weights["task"] += 0.10
        if "recent" in targets or "session" in targets:
            weights["conversation"] += 0.20
        total_weight = sum(weights.values()) or 1.0
        allocations = {category: int(budget.total_budget * (weights.get(category, 0.0) / total_weight)) for category in DEFAULT_CATEGORY_ORDER}
        drift = budget.total_budget - sum(allocations.values())
        allocations["task"] += drift
        return allocations

    @staticmethod
    def _category_for(candidate: ContextCandidate) -> str:
        return SEMANTIC_CATEGORY_MAP.get(candidate.semantic_type, "general")
