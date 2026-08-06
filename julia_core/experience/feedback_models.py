"""M3.3.0 Experience Feedback Models — Prediction → Outcome → Update.

ADR-031: Three core objects for the learning loop.
Julia learns through governed outcome validation, not model training.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from uuid import uuid4

CST = timezone(timedelta(hours=8))


@dataclass(frozen=True, slots=True)
class PredictionRecord:
    """What Julia (or her intelligence providers) thought might happen.

    Links back to the observation that triggered the prediction.
    prediction_id from ai_theme_app DecisionEnvelope is preserved.
    """
    prediction_id: str
    observation_id: str = ""         # source observation
    hypothesis: str = ""             # "AI机器人主题进入扩散阶段"
    confidence: float = 0.0          # 0.0-1.0
    expected_window: str = ""        # "5 trading days"
    evidence_refs: tuple[str, ...] = ()
    source: str = ""                 # "ai_theme_app" | "julia_reasoning"
    created_at: str = field(default_factory=lambda: datetime.now(CST).isoformat())


@dataclass(frozen=True, slots=True)
class RealityOutcome:
    """What actually happened in the world.

    Must carry prediction_id for binding.
    Unlinked outcomes are rejected.
    """
    outcome_id: str = field(default_factory=lambda: f"out_{uuid4().hex}")
    prediction_id: str = ""          # links to PredictionRecord
    actual_result: str = ""          # "confirmed" | "disconfirmed" | "partial"
    metrics: dict = field(default_factory=dict)  # {"theme_return": "+12%", "volume_confirmed": True}
    observed_at: str = field(default_factory=lambda: datetime.now(CST).isoformat())
    source: str = ""                 # "market_data" | "user_feedback" | "system_state"


@dataclass
class ExperienceUpdate:
    """What Julia learned from comparing prediction to outcome.

    Not a simple "right/wrong" flag. Carries delta, pattern key,
    and updated historical accuracy for the pattern.
    """
    update_id: str = field(default_factory=lambda: f"exp_{uuid4().hex}")
    prediction_id: str = ""
    outcome_id: str = ""
    pattern_key: str = ""            # "theme_breakout_with_leader_confirmation"
    delta: float = 0.0               # weight adjustment (+positive, -negative)
    reason: str = ""                 # "Confirmed: theme returned +12% with volume support"
    historical_accuracy: float = 0.0  # updated running accuracy for this pattern
    admitted: bool = False            # pass ExperienceAdmission?


__all__ = ["PredictionRecord", "RealityOutcome", "ExperienceUpdate"]
