"""M3.1 ExperienceAdmission — confidence + evidence gate.

ADR-029 Section 2: Inserted between Artifact creation and Experience storage.
Not every observation should become long-term memory.

This protects Memory OS from low-confidence observation pollution.
"""

from __future__ import annotations

from dataclasses import dataclass

from julia_core.awareness.models import AwarenessArtifact


@dataclass
class ExperienceAdmission:
    """Gates which artifacts become long-term experience.

    Low-confidence, single-source observations stay in EventStore (short-term).
    High-confidence, multi-evidence observations enter Experience (long-term).

    This is a cognitive filter, not a semantic evaluator. Zero LLM dependency.
    """

    min_confidence: float = 0.7
    min_evidence_refs: int = 2

    def admit(self, artifact: AwarenessArtifact) -> tuple[bool, str]:
        """Evaluate artifact for long-term experience admission.

        Returns (admitted, reason).
        """
        if artifact.confidence < self.min_confidence:
            return False, (
                f"confidence {artifact.confidence:.2f} < {self.min_confidence} "
                f"— short-term log only"
            )

        if len(artifact.evidence_refs) < self.min_evidence_refs:
            return False, (
                f"evidence_refs {len(artifact.evidence_refs)} < {self.min_evidence_refs} "
                f"— single-source observations are unreliable"
            )

        return True, (
            f"admitted: confidence={artifact.confidence:.2f}, "
            f"evidence_refs={len(artifact.evidence_refs)}"
        )


__all__ = ["ExperienceAdmission"]
