"""Exact-reference MemoryExperience resolver."""
from __future__ import annotations

from .contracts import MemoryExperienceRef
from .repository import MemoryExperienceRepository, MemoryExperienceRefNotFoundError


class MemoryExperienceResolver:
    def __init__(self, repository: MemoryExperienceRepository):
        self._repository = repository

    def resolve(self, ref: MemoryExperienceRef):
        if not isinstance(ref, MemoryExperienceRef):
            raise TypeError("MemoryExperienceResolver accepts an exact MemoryExperienceRef only")
        return self._repository.resolve(ref)


__all__ = ["MemoryExperienceResolver"]
