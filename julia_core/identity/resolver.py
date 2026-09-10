"""Exact-reference Identity resolver (ENG-07 candidate)."""
from __future__ import annotations

from .contracts import GovernedIdentity, IdentityRef
from .repository import IdentityRepository, IdentityRefNotFoundError


class IdentityResolver:
    def __init__(self, repository: IdentityRepository):
        if type(repository) is not IdentityRepository:
            raise TypeError("IdentityResolver accepts an exact IdentityRepository only")
        self._repository = repository

    def resolve(self, ref: IdentityRef) -> GovernedIdentity:
        if type(ref) is not IdentityRef:
            raise TypeError("IdentityResolver accepts an exact IdentityRef only")
        return self._repository.resolve(ref)


__all__ = ["IdentityResolver"]
