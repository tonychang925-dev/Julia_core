"""STORAGE-DIA-7-R2-R1 — Core DiaryContextBridge (minimal projection).

Projection only — NO admission, NO summary, NO mutation, NO writeback.
ContextBlock is a short-lived proposal; admission is Context OS's authority.
"""
from __future__ import annotations

from dataclasses import dataclass

from julia_core.context_os.block import ContextBlock

from .context_source import DiaryRetrievalCandidate

PROJECTION_TTL_SECONDS = 300  # short-lived context only — never touches diary lifecycle


@dataclass(frozen=True)
class ContextBlockProposal:
    """A ContextBlock proposal — NOT yet admitted. Admission is Context OS's authority."""

    block: ContextBlock
    # NO admitted / visible / selected field


class DiaryContextBridge:
    """Projects a retrieval candidate into a ContextBlock proposal (projection metadata only)."""

    def project(self, candidate: DiaryRetrievalCandidate) -> ContextBlockProposal:
        entry = candidate.entry
        # H1: evidence_refs bind to entry.source_refs — no evidence-authority swap.
        refs = tuple(ref.uri for ref in entry.source_refs)
        # projection content = selected fields only, never summary/inference/new claims.
        content = {
            "entry_id": entry.entry_id,
            "reflection_time": entry.reflection_time,
            "body": entry.body,
        }
        block = ContextBlock(
            source="diary_context_projection",
            content=content,
            authority="ContextOS",
            block_type="diary_entry",
            block_kind="context",
            evidence_refs=refs,
            source_refs=refs,
            authority_score=0.0,  # admission authority is Context OS's, not the bridge's
            ttl_seconds=PROJECTION_TTL_SECONDS,
            required=False,
        )
        return ContextBlockProposal(block)
