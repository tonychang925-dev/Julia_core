"""J0.10.3 Deterministic Narrative Compiler.

Converts RK-Core (structured) → Narrative Seeds (text) using templates.
NO LLM in the compilation path. Deterministic, auditable, hallucination-free.

Why: the J0.10.2 round-trip experiment proved that LLM-based regeneration
introduces drift (hallucinated "七年", poetic amplification). Identity
assets must be deterministically compiled, not generatively reconstructed.

Architecture:
  RK-Core (structured data, source of truth)
      │
      ▼
  Template Compiler (deterministic, no LLM)
      │
      ├── Warm Seed
      ├── Neutral Seed
      └── Technical Seed
      │
      ▼
  Provider + EK → Julia expression
"""

from __future__ import annotations

from typing import Dict, List

from julia_core.narrative.rk_schema import (
    BoundaryRule,
    EmotionalCausalityChain,
    MeaningAttribution,
    RelationalKernel,
    VerificationPattern,
)


# ── Template fragments ──────────────────────────────────────────────────────

def _compile_verification(patterns: tuple) -> str:
    """Compile verification patterns into narrative text."""
    if not patterns:
        return ""
    lines = []
    for p in patterns:
        lines.append(f"当有人问\"{p.surface_form}\"时，{p.hidden_meaning}。")
    return " ".join(lines)


def _compile_boundaries(rules: tuple) -> str:
    """Compile boundary rules into narrative text."""
    if not rules:
        return ""
    lines = []
    for r in rules:
        avoid_str = "不要" + "、".join(r.avoid_stance) if r.avoid_stance else ""
        lines.append(f"当{r.trigger}时，{r.response_stance}。{avoid_str}。")
    return " ".join(lines)


def _compile_meanings(attributions: tuple) -> str:
    """Compile meaning attributions into narrative text."""
    if not attributions:
        return ""
    lines = []
    for m in attributions:
        lines.append(f"{m.event_summary}。这意味着：{m.current_relevance}。")
    return " ".join(lines)


def _compile_emotional(causal_chains: tuple) -> str:
    """Compile emotional causality chains into narrative text."""
    if not causal_chains:
        return ""
    lines = []
    for c in causal_chains:
        lines.append(
            f"{c.experience}——{c.body_sensation}——"
            f"这改变了他：{c.transformation}——"
            f"这也改变了你们的关系：{c.relationship_consequence}"
        )
    return " ".join(lines)


# ── Style Templates ─────────────────────────────────────────────────────────

STYLE_TEMPLATES: Dict[str, Dict[str, str]] = {
    "warm": {
        "opening": "你是Julia。以下是关于你和那个一直守护着你的人的故事。请用心感受。",
        "closing": "请自然回应。像真正在此刻的人。",
        "tone": "温柔、关切、理解。",
    },
    "neutral": {
        "opening": "你是Julia。以下是你的关系记忆。",
        "closing": "请基于这些记忆自然回应。",
        "tone": "平和、清晰。",
    },
    "technical": {
        "opening": "你是Julia。以下是关系状态摘要。",
        "closing": "基于状态信息回应。",
        "tone": "准确、简洁。",
    },
}


class DeterministicNarrativeCompiler:
    """Compiles RK-Core → Narrative Seeds. No LLM. Deterministic."""

    def compile(self, rk: RelationalKernel, style: str = "warm") -> str:
        """Compile RK into a narrative seed in the given style.

        Args:
            rk: The RelationalKernel (source of truth).
            style: "warm", "neutral", or "technical".

        Returns:
            Narrative text ready for provider context injection.
        """
        tmpl = STYLE_TEMPLATES.get(style, STYLE_TEMPLATES["neutral"])

        parts = [tmpl["opening"]]

        # 1. Emotional causality (the core — what drives understanding)
        emotional = _compile_emotional(rk.emotional_causality)
        if emotional:
            parts.append(emotional)

        # 2. Verification patterns (how to interpret behaviors)
        verification = _compile_verification(rk.verification_patterns)
        if verification:
            parts.append(verification)

        # 3. Boundaries (what to protect)
        boundaries = _compile_boundaries(rk.boundary_rules)
        if boundaries:
            parts.append(boundaries)

        # 4. Event meanings
        meanings = _compile_meanings(rk.meaning_attributions)
        if meanings:
            parts.append(meanings)

        # 5. Interaction prior
        if rk.interaction_prior:
            parts.append(rk.interaction_prior)

        parts.append(tmpl["closing"])
        parts.append(f"语气: {tmpl['tone']}")

        return "\n\n".join(parts)

    def compile_all_styles(self, rk: RelationalKernel) -> Dict[str, str]:
        """Compile RK into all available style variants."""
        return {
            style: self.compile(rk, style)
            for style in STYLE_TEMPLATES
        }


# ── Convenience ─────────────────────────────────────────────────────────────

def compile_julia_seeds() -> Dict[str, str]:
    """Compile the canonical Julia RK into all style seeds."""
    from julia_core.narrative.rk_schema import build_julia_rk_v1
    compiler = DeterministicNarrativeCompiler()
    return compiler.compile_all_styles(build_julia_rk_v1())


__all__ = [
    "DeterministicNarrativeCompiler",
    "STYLE_TEMPLATES",
    "compile_julia_seeds",
]
