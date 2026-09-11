"""Exact-reference Identity resolver (ENG-07 candidate)."""

from __future__ import annotations

from .contracts import GovernedIdentity, IdentityRef
from .repository import IdentityRepository, IdentityRefNotFoundError


class IdentityResolver:
    __slots__ = ("_repository",)

    def __init__(self, repository: IdentityRepository):
        if type(repository) is not IdentityRepository:
            raise TypeError("IdentityResolver accepts an exact IdentityRepository only")
        object.__setattr__(self, "_repository", repository)

    def __setattr__(self, name: str, value: object) -> None:
        raise TypeError("IdentityResolver repository binding is immutable")

    def __delattr__(self, name: str) -> None:
        raise TypeError("IdentityResolver repository binding is immutable")

    def resolve(self, ref: IdentityRef) -> GovernedIdentity:
        if type(ref) is not IdentityRef:
            raise TypeError("IdentityResolver accepts an exact IdentityRef only")
        repository = self._repository
        if type(repository) is not IdentityRepository:
            raise TypeError("IdentityResolver repository binding is invalid")
        return IdentityRepository.resolve(repository, ref)


__all__ = ["IdentityResolver"]
