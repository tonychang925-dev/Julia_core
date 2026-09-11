"""Exact-reference MemoryExperience resolver."""
from __future__ import annotations

from .contracts import MemoryExperienceRef
from .repository import MemoryExperienceRepository, MemoryExperienceRefNotFoundError


class MemoryExperienceResolver:
    __slots__ = ("_repository",)

    def __init__(self, repository: MemoryExperienceRepository):
        if type(repository) is not MemoryExperienceRepository:
            raise TypeError("MemoryExperienceResolver accepts an exact MemoryExperienceRepository only")
        object.__setattr__(self, "_repository", repository)

    def __setattr__(self, name: str, value: object) -> None:
        raise TypeError("MemoryExperienceResolver repository binding is immutable")

    def __delattr__(self, name: str) -> None:
        raise TypeError("MemoryExperienceResolver repository binding is immutable")

    def resolve(self, ref: MemoryExperienceRef):
        if type(ref) is not MemoryExperienceRef:
            raise TypeError("MemoryExperienceResolver accepts an exact MemoryExperienceRef only")
        repository = self._repository
        if type(repository) is not MemoryExperienceRepository:
            raise TypeError("MemoryExperienceResolver repository binding is invalid")
        return repository.resolve(ref)


__all__ = ["MemoryExperienceResolver"]
