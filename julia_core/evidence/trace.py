"""Evidence trace helpers for Phase G."""

from __future__ import annotations

from typing import Iterable


def evidence_trace(refs: Iterable[str], *, mode: str, used_for_context: bool) -> dict:
    refs_tuple = tuple(refs)
    return {
        "evidence": {
            "used": bool(refs_tuple) and used_for_context,
            "refs": list(refs_tuple),
            "retrieval_mode": mode,
            "used_for_context": used_for_context,
            "raw_dump_injected": False,
            "memory_updated": False,
            "identity_updated": False,
        }
    }
