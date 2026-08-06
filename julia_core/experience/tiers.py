"""M3.2.2 Experience Tier Router — cache/working/experience routing.

ADR-030 Section 4: Routes AwarenessArtifacts to the correct tier based
on signal_level + confidence + evidence_count.

L0 → discard  (EventStore only, no storage)
L1 → cache    (24hr temporary log)
L2 → working  (current-cycle observation)
L3 → experience (long-term) if confidence>=0.7 and evidence>=2
L4 → experience (long-term) if confidence>=0.8 and evidence>=2

This protects Memory OS from low-signal pollution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from julia_core.awareness.models import AwarenessArtifact


class ExperienceTier(str, Enum):
    DISCARD    = "discard"     # Not stored
    CACHE      = "cache"       # 24-hour temporary
    WORKING    = "working"     # Current observation cycle
    EXPERIENCE = "experience"  # Long-term governed memory


@dataclass
class TierResult:
    """Routing decision for an artifact."""
    tier: ExperienceTier
    reason: str
    artifact: AwarenessArtifact


@dataclass
class ExperienceTierRouter:
    """Routes artifacts to experience tiers based on signal quality.

    Does NOT evaluate content. Does NOT call LLM.
    Purely rule-based routing based on signal_level, confidence, evidence.
    """

    # Configurable thresholds
    l34_min_confidence: float = 0.7
    l34_min_evidence: int = 2
    l4_min_confidence: float = 0.8
    l2_min_confidence: float = 0.6

    _cache_store: list[TierResult] = field(default_factory=list)
    _working_store: list[TierResult] = field(default_factory=list)
    _experience_store: list[TierResult] = field(default_factory=list)

    def route(self, artifact: AwarenessArtifact, signal_level: str = "L1") -> TierResult:
        """Route artifact to the correct tier.

        signal_level: extracted from the observation that produced this artifact.
        confidence: from artifact.confidence
        evidence: len(artifact.evidence_refs)
        """
        level_map = {"L0": 0, "L1": 1, "L2": 2, "L3": 3, "L4": 4}
        lvl = level_map.get(signal_level, 0)
        confidence = artifact.confidence
        evidence_count = len(artifact.evidence_refs)

        # L0: discard
        if lvl <= 0:
            return TierResult(ExperienceTier.DISCARD, "L0 signal — noise", artifact)

        # L1: cache
        if lvl == 1:
            result = TierResult(ExperienceTier.CACHE, "L1 signal — temporary observation", artifact)
            self._cache_store.append(result)
            return result

        # L2: working if confident, else cache
        if lvl == 2:
            if confidence >= self.l2_min_confidence:
                result = TierResult(ExperienceTier.WORKING, f"L2 confidence {confidence:.2f} >= {self.l2_min_confidence}", artifact)
                self._working_store.append(result)
                return result
            result = TierResult(ExperienceTier.CACHE, f"L2 confidence {confidence:.2f} < {self.l2_min_confidence}", artifact)
            self._cache_store.append(result)
            return result

        # L3/L4: experience if meets thresholds
        if lvl >= 3:
            if lvl == 4:
                required_conf = self.l4_min_confidence
            else:
                required_conf = self.l34_min_confidence

            if confidence >= required_conf and evidence_count >= self.l34_min_evidence:
                result = TierResult(ExperienceTier.EXPERIENCE,
                    f"L{lvl} confidence {confidence:.2f} >= {required_conf}, evidence {evidence_count} >= {self.l34_min_evidence}",
                    artifact)
                self._experience_store.append(result)
                return result

            # Falls to working if doesn't meet experience thresholds
            result = TierResult(ExperienceTier.WORKING,
                f"L{lvl} insufficient: confidence {confidence:.2f} or evidence {evidence_count}", artifact)
            self._working_store.append(result)
            return result

        return TierResult(ExperienceTier.CACHE, "unknown level — default cache", artifact)

    @property
    def cache_count(self) -> int:
        return len(self._cache_store)

    @property
    def working_count(self) -> int:
        return len(self._working_store)

    @property
    def experience_count(self) -> int:
        return len(self._experience_store)


__all__ = ["ExperienceTier", "ExperienceTierRouter", "TierResult"]
