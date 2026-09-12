"""Read-only exact runtime canonical binding resolver."""

from __future__ import annotations

from enum import Enum

from .contracts import (
    GovernedRuntimeCanonicalAuthorityBinding,
    RuntimeCanonicalAuthorityBindingRef,
    RuntimeCanonicalAuthorityBindingStatus,
)
from .repository import (
    RuntimeCanonicalAuthorityBindingRefNotFoundError,
    RuntimeCanonicalAuthorityBindingRepository,
)


class RuntimeCanonicalAuthorityBindingErrorCode(str, Enum):
    SOURCE_NOT_BOUND = "SOURCE_NOT_BOUND"
    REF_NOT_FOUND = "REF_NOT_FOUND"
    REF_NOT_ADMITTED = "REF_NOT_ADMITTED"
    REF_RETIRED = "REF_RETIRED"
    TYPE_MISMATCH = "TYPE_MISMATCH"


class RuntimeCanonicalAuthorityBindingResolverError(Exception):
    def __init__(
        self,
        code: RuntimeCanonicalAuthorityBindingErrorCode,
        message: str,
    ) -> None:
        if type(code) is not RuntimeCanonicalAuthorityBindingErrorCode:
            raise TypeError("binding resolver error code is inexact")
        if type(message) is not str or not message:
            raise TypeError("binding resolver error message is inexact")
        super().__init__(message)
        object.__setattr__(self, "_code", code)

    @property
    def code(self) -> RuntimeCanonicalAuthorityBindingErrorCode:
        return self._code

    def __setattr__(self, name: str, value: object) -> None:
        raise TypeError("binding resolver errors are immutable")

    def __delattr__(self, name: str) -> None:
        raise TypeError("binding resolver errors are immutable")


class RuntimeCanonicalAuthorityBindingResolver:
    __slots__ = ("_repository",)

    def __init__(
        self,
        repository: RuntimeCanonicalAuthorityBindingRepository | None = None,
    ) -> None:
        if repository is not None and (
            type(repository) is not RuntimeCanonicalAuthorityBindingRepository
        ):
            raise RuntimeCanonicalAuthorityBindingResolverError(
                RuntimeCanonicalAuthorityBindingErrorCode.TYPE_MISMATCH,
                "runtime binding resolver requires an exact repository",
            )
        object.__setattr__(self, "_repository", repository)

    def __setattr__(self, name: str, value: object) -> None:
        raise TypeError("runtime binding resolver fields are immutable")

    def __delattr__(self, name: str) -> None:
        raise TypeError("runtime binding resolver fields are immutable")

    def resolve_exact(
        self, ref: RuntimeCanonicalAuthorityBindingRef
    ) -> GovernedRuntimeCanonicalAuthorityBinding:
        repository = self._require_repository()
        if type(ref) is not RuntimeCanonicalAuthorityBindingRef:
            raise RuntimeCanonicalAuthorityBindingResolverError(
                RuntimeCanonicalAuthorityBindingErrorCode.TYPE_MISMATCH,
                "runtime binding resolution requires an exact binding ref",
            )
        try:
            governed = repository.resolve(ref)
        except RuntimeCanonicalAuthorityBindingRefNotFoundError as error:
            raise RuntimeCanonicalAuthorityBindingResolverError(
                RuntimeCanonicalAuthorityBindingErrorCode.REF_NOT_FOUND,
                f"exact runtime binding is not present: {ref.uri}",
            ) from error
        if governed.status is RuntimeCanonicalAuthorityBindingStatus.CANDIDATE:
            raise RuntimeCanonicalAuthorityBindingResolverError(
                RuntimeCanonicalAuthorityBindingErrorCode.REF_NOT_ADMITTED,
                f"runtime binding is candidate: {ref.uri}",
            )
        if governed.status is RuntimeCanonicalAuthorityBindingStatus.SUPERSEDED:
            raise RuntimeCanonicalAuthorityBindingResolverError(
                RuntimeCanonicalAuthorityBindingErrorCode.REF_NOT_ADMITTED,
                f"runtime binding is superseded: {ref.uri}",
            )
        if governed.status is RuntimeCanonicalAuthorityBindingStatus.RETIRED:
            raise RuntimeCanonicalAuthorityBindingResolverError(
                RuntimeCanonicalAuthorityBindingErrorCode.REF_RETIRED,
                f"runtime binding is retired: {ref.uri}",
            )
        return governed

    def _require_repository(self) -> RuntimeCanonicalAuthorityBindingRepository:
        repository = self._repository
        if type(repository) is not RuntimeCanonicalAuthorityBindingRepository:
            raise RuntimeCanonicalAuthorityBindingResolverError(
                RuntimeCanonicalAuthorityBindingErrorCode.SOURCE_NOT_BOUND,
                "runtime binding repository is not bound",
            )
        return repository


__all__ = [
    "RuntimeCanonicalAuthorityBindingErrorCode",
    "RuntimeCanonicalAuthorityBindingResolver",
    "RuntimeCanonicalAuthorityBindingResolverError",
]
