"""M3.1 ObservationPolicy — rate limiting + cooldown + decision level gate.

ADR-029 Section 1 + ADR-028 Addendum: Inserted between ObservationRouter
and Workflow dispatch. Router checks significance. Policy checks rate
and filters by decision level (L0-L4).

L0 → ignore, L1 → record only, L2 → short-term watch, L3 → awareness, L4 → notify.

Policy answers: "Should Julia pay attention?" — not "What does this mean?"
Zero LLM dependency.
"""

from __future__ import annotations

import time as _time
from dataclasses import dataclass, field

from julia_core.awareness.models import ObservationEvent


@dataclass
class ObservationPolicy:
    """Rate limits and cooldowns for observation events.

    Prevents Julia from becoming a market noise receiver.
    Does NOT interpret events. Does NOT call LLM.
    """

    # Rate limits: max events per window
    rate_limits: dict[str, int] = field(default_factory=lambda: {
        "per_subject": 4,    # same subject: max 4/hour
        "per_domain": 20,    # same domain: max 20/hour
        "global": 50,        # all events: max 50/hour
    })

    # Cooldown: same subject + same change_type must wait this long
    cooldown_seconds: int = 900  # 15 minutes

    # Minimum decision level to trigger awareness workflow
    min_decision_level: str = "L2"  # L0-L1 are logged but don't trigger workflows

    # Decision level → numeric weight for admission scoring
    decision_level_weight: dict[str, float] = field(default_factory=lambda: {
        "L0": 0.0, "L1": 0.2, "L2": 0.4, "L3": 0.7, "L4": 1.0,
    })

    # Internal tracking
    _subject_timestamps: dict[str, list[float]] = field(default_factory=dict)
    _domain_timestamps: dict[str, list[float]] = field(default_factory=dict)
    _global_timestamps: list[float] = field(default_factory=list)
    _cooldown_map: dict[str, float] = field(default_factory=dict)  # key → last trigger time

    def should_process(self, event: ObservationEvent) -> tuple[bool, str]:
        """Check rate limits and cooldown. Returns (allowed, reason).

        Called AFTER ObservationRouter.evaluate() returns significant=True.
        Router checks WHAT. Policy checks HOW OFTEN.
        """
        now = _time.time()

        # 1. Cooldown check
        cooldown_key = f"{event.subject}:{event.change_type}"
        last_trigger = self._cooldown_map.get(cooldown_key, 0)
        if now - last_trigger < self.cooldown_seconds:
            remaining = int(self.cooldown_seconds - (now - last_trigger))
            return False, f"cooldown active: {remaining}s remaining for '{cooldown_key}'"

        # 2. Per-subject rate limit
        subj_key = event.subject or "unknown"
        subj_times = self._subject_timestamps.setdefault(subj_key, [])
        subj_times[:] = [t for t in subj_times if now - t < 3600]  # 1-hour window
        if len(subj_times) >= self.rate_limits.get("per_subject", 4):
            return False, f"subject rate limit: {len(subj_times)}/{self.rate_limits['per_subject']} for '{subj_key}'"

        # 3. Per-domain rate limit
        dom_times = self._domain_timestamps.setdefault(event.domain or "unknown", [])
        dom_times[:] = [t for t in dom_times if now - t < 3600]
        if len(dom_times) >= self.rate_limits.get("per_domain", 20):
            return False, f"domain rate limit: {len(dom_times)}/{self.rate_limits['per_domain']} for '{event.domain}'"

        # 4. Global rate limit
        self._global_timestamps[:] = [t for t in self._global_timestamps if now - t < 3600]
        if len(self._global_timestamps) >= self.rate_limits.get("global", 50):
            return False, f"global rate limit: {len(self._global_timestamps)}/{self.rate_limits['global']}"

        # All checks passed — record timestamps
        subj_times.append(now)
        dom_times.append(now)
        self._global_timestamps.append(now)
        self._cooldown_map[cooldown_key] = now

        return True, "accepted — within rate limits and cooldown"

    def should_process_intelligence(self, observation: dict) -> tuple[bool, str]:
        """Filter an ai_theme_app intelligence observation by decision level.

        observation: one entry from market.intelligence.observe response.
        Returns (allowed, reason).

        L0 → ignore, L1 → record only, L2+ → process (subject to rate limits).
        """
        level = observation.get("signal_level", "L0")
        level_rank = {"L0": 0, "L1": 1, "L2": 2, "L3": 3, "L4": 4}
        min_rank = level_rank.get(self.min_decision_level, 2)
        obs_rank = level_rank.get(level, 0)

        if obs_rank < min_rank:
            return False, f"decision level {level} below minimum {self.min_decision_level}"

        # For L2+: apply rate limits
        subject = observation.get("theme", observation.get("subject", "unknown"))
        change_type = observation.get("type", "unknown")

        synthetic_event = ObservationEvent(
            subject=subject,
            change_type=change_type,
            domain="market",
            confidence=observation.get("confidence", 0.5),
            delta=str(observation.get("signal_level", "")),
        )
        return self.should_process(synthetic_event)

    def level_weight(self, level: str) -> float:
        """Get admission weight for a decision level."""
        return self.decision_level_weight.get(level, 0.0)


__all__ = ["ObservationPolicy"]
