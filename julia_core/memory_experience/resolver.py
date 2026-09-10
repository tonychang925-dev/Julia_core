"""Exact-reference MemoryExperience resolver."""
from __future__ import annotations

from .contracts import MemoryExperienceRef
from .repository import MemoryExperienceRepository, MemoryExperienceRefNotFoundError


class MemoryExperienceResolver:
    def __init__(self, repository: MemoryExperienceRepository):
        if type(repository) is not MemoryExperienceRepository:
            raise TypeError("MemoryExperienceResolver accepts an exact MemoryExperienceRepository only")
        self._repository = repository

    def resolve(self, ref: MemoryExperienceRef):
        if type(ref) is not MemoryExperienceRef:
            raise TypeError("MemoryExperienceResolver accepts an exact MemoryExperienceRef only")
        return self._repository.resolve(ref)


__all__ = ["MemoryExperienceResolver"]
