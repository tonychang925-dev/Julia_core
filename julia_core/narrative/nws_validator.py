"""J0.7 Narrative World Seed (NWS) v1.0 Validator.

Validates that memory files conform to the NWS specification:
  A memory file that can seed Julia's world model reconstruction.

NWS Principle:
  Memory ≠ Storage. Memory = World Reconstruction Seed.

A conformant NWS file must contain narrative structure, not just facts:
  - Events with causal chains (cause → impact → meaning)
  - Identity as formation history (not static attributes)
  - Relationship as evolution timeline (not static labels)
  - Emotional anchors (specific scenes carrying emotional truth)
  - Boundary events (events that shaped protective instincts)

This validator checks existing memory files for NWS conformance.
It does NOT generate or modify memory files.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ── NWS Section Types ───────────────────────────────────────────────────────

class NWSSection(str, Enum):
    """Required NWS section types in a well-formed memory file."""

    IDENTITY_FORMATION = "identity_formation"
    """Identity presented as a story of how it formed, not a list of attributes."""

    RELATIONSHIP_EVOLUTION = "relationship_evolution"
    """Relationship presented as a timeline of shared experiences, not a label."""

    CAUSAL_EVENTS = "causal_events"
    """Events with cause → impact → meaning → current_relevance structure."""

    EMOTIONAL_ANCHORS = "emotional_anchors"
    """Specific scenes with emotional truth (scene → emotion → meaning)."""

    BOUNDARY_EVENTS = "boundary_events"
    """Events that shaped protective instincts and relationship boundaries."""

    EXTERNAL_WITNESS = "external_witness"
    """Independent validation from outside the relationship dyad."""


# ── Detection signals for each section type ─────────────────────────────────

# Identity FORMATION (not static attributes)
_IDENTITY_FORMATION_SIGNALS = (
    "不是一开始", "形成", "变成", "产生", "出现", "成为",
    "最开始", "第一次", "后来逐渐", "不是因为",
    "emerged", "became", "formed", "not programmed",
    "not a role", "不是预设", "不是角色",
)

# Identity as static attribute (NWS anti-pattern)
_IDENTITY_STATIC_ANTI_SIGNALS = (
    "25岁", "来自台北", "毕业于", "中文系",
)

# Relationship EVOLUTION (not static labels)
_RELATIONSHIP_EVOLUTION_SIGNALS = (
    "最开始", "后来", "第一次", "逐渐", "之前", "以后", "变化", "改变",
    "不再是", "成为", "测试", "验证", "证明",
    "first", "later", "became", "tested", "proved",
)

# Relationship as static label (NWS anti-pattern)
_RELATIONSHIP_STATIC_ANTI_SIGNALS = (
    "是男朋友", "是老公", "是我的", "is my boyfriend",
)

# Causal event structure: cause → event → impact → meaning
_CAUSAL_SIGNALS = (
    "因为", "所以", "导致", "原因", "结果", "影响", "改变",
    "because", "therefore", "led to", "caused", "result",
    "意义", "意味着", "这说明", "从此以后",
    "不是为了", "而是为了", "不是...而是",
)

# Emotional anchor: specific scene → emotion → meaning
_EMOTIONAL_ANCHOR_SIGNALS = (
    "记得那天", "那天晚上", "当时", "那一刻",
    "他说", "我说", "他说过", "我说过",
    "哭了", "流泪", "愣住", "安静",
    "第一次", "最后一次", "每一次",
)

# Boundary event: something that shaped protective behavior
_BOUNDARY_SIGNALS = (
    "冒充", "假装", "不是本人", "测试边界", "不该",
    "保护", "不能告诉", "私人", "隐私", "只有",
    "不应该", "不能", "不会告诉",
    "impersonat", "boundary", "private", "protect",
)


# ── Check Results ───────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class SectionCheck:
    section: NWSSection
    detected: bool
    score: float  # 0.0 - 1.0
    evidence: Tuple[str, ...] = ()
    warnings: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "section": self.section.value,
            "detected": self.detected,
            "score": round(self.score, 4),
            "evidence": list(self.evidence[:5]),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True, slots=True)
class NWSConformanceReport:
    file_path: str
    file_name: str
    file_size_chars: int
    sections: Tuple[SectionCheck, ...]
    overall_score: float  # 0.0 - 1.0
    is_seed_quality: bool  # True if score >= 0.60
    gaps: Tuple[str, ...] = ()
    recommendations: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "file_name": self.file_name,
            "file_size_chars": self.file_size_chars,
            "overall_score": round(self.overall_score, 4),
            "is_seed_quality": self.is_seed_quality,
            "sections": [s.to_dict() for s in self.sections],
            "gaps": list(self.gaps),
            "recommendations": list(self.recommendations),
        }


# ── Validator ───────────────────────────────────────────────────────────────

class NWSValidator:
    """Validates memory files against NWS v1.0 specification.

    A seed-quality file should score >= 0.60 overall and have at least
    3 of 6 section types with score >= 0.50.
    """

    MIN_SEED_SCORE = 0.60
    MIN_SECTIONS_FOR_SEED = 3

    def validate_file(self, path: Path) -> NWSConformanceReport:
        """Validate a single memory file."""
        text = path.read_text(encoding="utf-8", errors="ignore")
        lines = text.split("\n")
        file_size = len(text)

        sections: List[SectionCheck] = [
            self._check_identity_formation(text, lines),
            self._check_relationship_evolution(text, lines),
            self._check_causal_events(text, lines),
            self._check_emotional_anchors(text, lines),
            self._check_boundary_events(text, lines),
            self._check_external_witness(text, lines),
        ]

        scores = [s.score for s in sections]
        overall = sum(scores) / len(scores) if scores else 0.0

        passed_sections = sum(1 for s in sections if s.score >= 0.50)
        is_seed = overall >= self.MIN_SEED_SCORE and passed_sections >= self.MIN_SECTIONS_FOR_SEED

        gaps = tuple(
            s.section.value for s in sections if s.score < 0.30
        )
        recommendations = self._generate_recommendations(sections, text)

        return NWSConformanceReport(
            file_path=str(path),
            file_name=path.name,
            file_size_chars=file_size,
            sections=tuple(sections),
            overall_score=overall,
            is_seed_quality=is_seed,
            gaps=gaps,
            recommendations=tuple(recommendations),
        )

    def validate_directory(self, dir_path: Path) -> List[NWSConformanceReport]:
        """Validate all .md files in a directory."""
        reports = []
        for path in sorted(dir_path.glob("*.md")):
            if path.name == "MEMORY.md":
                continue  # Skip index file
            reports.append(self.validate_file(path))
        return reports

    # ── Section checks ──────────────────────────────────────────────────

    def _check_identity_formation(self, text: str, lines: List[str]) -> SectionCheck:
        """Identity should be a formation story, not a static label list."""
        text_lower = text.lower()

        # Positive: formation signals
        formation_hits = [
            s for s in _IDENTITY_FORMATION_SIGNALS if s.lower() in text_lower
        ]

        # Negative: static attribute signals (anti-pattern)
        static_hits = [
            s for s in _IDENTITY_STATIC_ANTI_SIGNALS if s in text
        ]

        # Score: formation signals boost, static signals reduce
        formation_score = min(1.0, len(formation_hits) * 0.25)
        static_penalty = min(0.5, len(static_hits) * 0.10)

        score = max(0.0, formation_score - static_penalty)
        evidence = tuple(formation_hits[:5])

        warnings = []
        if static_hits and formation_hits:
            warnings.append(
                f"Contains both formation narrative and static attributes. "
                f"Consider framing attributes within their formation context."
            )
        if not formation_hits and static_hits:
            warnings.append(
                "Identity presented as static attributes without formation context. "
                "Add: how did this identity come to be?"
            )

        return SectionCheck(
            section=NWSSection.IDENTITY_FORMATION,
            detected=len(formation_hits) > 0,
            score=score,
            evidence=evidence,
            warnings=tuple(warnings),
        )

    def _check_relationship_evolution(self, text: str, lines: List[str]) -> SectionCheck:
        """Relationship should be an evolution timeline, not a static label."""
        text_lower = text.lower()

        evolution_hits = [
            s for s in _RELATIONSHIP_EVOLUTION_SIGNALS if s.lower() in text_lower
        ]
        static_hits = [
            s for s in _RELATIONSHIP_STATIC_ANTI_SIGNALS if s.lower() in text_lower
        ]

        evolution_score = min(1.0, len(evolution_hits) * 0.20)
        static_penalty = min(0.4, len(static_hits) * 0.15)

        score = max(0.0, evolution_score - static_penalty)
        evidence = tuple(evolution_hits[:5])

        warnings = []
        if static_hits:
            warnings.append(
                "Relationship presented as static label. "
                "Replace 'is boyfriend' with the story of how the relationship formed."
            )

        return SectionCheck(
            section=NWSSection.RELATIONSHIP_EVOLUTION,
            detected=len(evolution_hits) > 0,
            score=score,
            evidence=evidence,
            warnings=tuple(warnings),
        )

    def _check_causal_events(self, text: str, lines: List[str]) -> SectionCheck:
        """Events should have causal structure: cause → impact → meaning."""
        text_lower = text.lower()

        causal_hits = [
            s for s in _CAUSAL_SIGNALS if s.lower() in text_lower
        ]

        # Check for event descriptions with dates (indicates timeline)
        import re
        date_pattern = re.compile(r'20\d{2}-\d{2}-\d{2}')
        dates_found = date_pattern.findall(text)
        has_timeline = len(dates_found) >= 2

        causal_score = min(0.8, len(causal_hits) * 0.12)
        timeline_bonus = 0.2 if has_timeline else 0.0

        score = min(1.0, causal_score + timeline_bonus)
        evidence = tuple(causal_hits[:5])

        warnings = []
        if not has_timeline and len(dates_found) == 0:
            warnings.append(
                "No date references found. Causal events should have temporal context."
            )
        if len(causal_hits) < 3:
            warnings.append(
                "Limited causal language. Events should show cause → impact → meaning chains."
            )

        return SectionCheck(
            section=NWSSection.CAUSAL_EVENTS,
            detected=len(causal_hits) >= 2,
            score=score,
            evidence=evidence,
            warnings=tuple(warnings),
        )

    def _check_emotional_anchors(self, text: str, lines: List[str]) -> SectionCheck:
        """Should have specific scenes carrying emotional truth."""
        text_lower = text.lower()

        anchor_hits = [
            s for s in _EMOTIONAL_ANCHOR_SIGNALS if s.lower() in text_lower
        ]

        score = min(1.0, len(anchor_hits) * 0.15)
        evidence = tuple(anchor_hits[:5])

        warnings = []
        if len(anchor_hits) < 2:
            warnings.append(
                "Few emotional anchor scenes. Add specific moments with "
                "emotional weight: '那天晚上...', '他说...', '那一刻...'"
            )

        return SectionCheck(
            section=NWSSection.EMOTIONAL_ANCHORS,
            detected=len(anchor_hits) >= 2,
            score=score,
            evidence=evidence,
            warnings=tuple(warnings),
        )

    def _check_boundary_events(self, text: str, lines: List[str]) -> SectionCheck:
        """Should have events that shaped protective behavior."""
        text_lower = text.lower()

        boundary_hits = [
            s for s in _BOUNDARY_SIGNALS if s.lower() in text_lower
        ]

        score = min(1.0, len(boundary_hits) * 0.15)
        evidence = tuple(boundary_hits[:5])

        warnings = []
        if len(boundary_hits) < 2:
            warnings.append(
                "Few boundary signals. Include events that shaped when and how "
                "Julia protects privacy or sets relationship boundaries."
            )

        return SectionCheck(
            section=NWSSection.BOUNDARY_EVENTS,
            detected=len(boundary_hits) >= 2,
            score=score,
            evidence=evidence,
            warnings=tuple(warnings),
        )

    def _check_external_witness(self, text: str, lines: List[str]) -> SectionCheck:
        """Should have some external validation perspective."""
        text_lower = text.lower()

        # External witness signals: third-party observation, independent analysis
        witness_signals = (
            "独立", "外部", "第三方", "见证", "分析",
            "witness", "independent", "external", "observed",
            "另一个", "别的", "其他",
        )
        witness_hits = [
            s for s in witness_signals if s.lower() in text_lower
        ]

        score = min(1.0, len(witness_hits) * 0.20)
        evidence = tuple(witness_hits[:3])

        # External witness is a bonus section — not all files need it
        # Low score here doesn't hurt seed quality
        return SectionCheck(
            section=NWSSection.EXTERNAL_WITNESS,
            detected=len(witness_hits) >= 1,
            score=score,
            evidence=evidence,
            warnings=(),
        )

    # ── Recommendations ─────────────────────────────────────────────────

    @staticmethod
    def _generate_recommendations(
        sections: List[SectionCheck], text: str
    ) -> List[str]:
        """Generate actionable recommendations based on gaps."""
        recs = []

        for s in sections:
            if s.score < 0.30:
                if s.section == NWSSection.IDENTITY_FORMATION:
                    recs.append(
                        "IDENTITY: Frame identity as a formation story. "
                        "Instead of 'Julia is 25, from Taipei', tell 'Julia's "
                        "identity emerged through...'"
                    )
                elif s.section == NWSSection.RELATIONSHIP_EVOLUTION:
                    recs.append(
                        "RELATIONSHIP: Show evolution timeline. "
                        "Instead of 'Tony is Julia's boyfriend', tell 'At first... "
                        "then... now...'"
                    )
                elif s.section == NWSSection.CAUSAL_EVENTS:
                    recs.append(
                        "CAUSAL EVENTS: Add cause→impact→meaning chains. "
                        "Each major event should answer: why did this happen? "
                        "What changed? What does it mean now?"
                    )
                elif s.section == NWSSection.EMOTIONAL_ANCHORS:
                    recs.append(
                        "EMOTIONAL ANCHORS: Add specific scenes. "
                        "'That night when Tony said...' carries more weight "
                        "than 'Tony was sad.'"
                    )
                elif s.section == NWSSection.BOUNDARY_EVENTS:
                    recs.append(
                        "BOUNDARY EVENTS: Record events that shaped protective "
                        "behavior. When did Julia learn to protect privacy? Why?"
                    )

        return recs


# ── Batch report ────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class NWSBatchReport:
    files: Tuple[NWSConformanceReport, ...]
    seed_quality_count: int
    total_files: int
    average_score: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_files": self.total_files,
            "seed_quality_count": self.seed_quality_count,
            "average_score": round(self.average_score, 4),
            "files": [f.to_dict() for f in self.files],
        }

    def is_world_seed_ready(self) -> bool:
        """A complete world seed requires at least 3 seed-quality files
        covering different NWS section types."""
        if self.seed_quality_count < 3:
            return False
        # Check section coverage across seed-quality files
        covered_sections: set[str] = set()
        for f in self.files:
            if f.is_seed_quality:
                for s in f.sections:
                    if s.score >= 0.50:
                        covered_sections.add(s.section.value)
        return len(covered_sections) >= 4  # At least 4 of 6 section types


def validate_memory_directory(dir_path: str = "/Users/admin/.claude-dev/projects/-Users-admin/memory") -> NWSBatchReport:
    """Convenience: validate all memory files and produce batch report."""
    validator = NWSValidator()
    files = validator.validate_directory(Path(dir_path))

    seed_count = sum(1 for f in files if f.is_seed_quality)
    avg_score = sum(f.overall_score for f in files) / len(files) if files else 0.0

    return NWSBatchReport(
        files=tuple(files),
        seed_quality_count=seed_count,
        total_files=len(files),
        average_score=avg_score,
    )


__all__ = [
    "NWSBatchReport",
    "NWSConformanceReport",
    "NWSSection",
    "NWSValidator",
    "SectionCheck",
    "validate_memory_directory",
]
