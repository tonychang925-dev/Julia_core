"""H6.0 Pilot Observation Layer.

This module records lightweight pilot interaction telemetry. It is deliberately
not an OS layer: it does not own or mutate Identity, Persona, Memory,
Continuity, Context, Evidence, Voice, Provider, or Client state.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any, Iterable, Mapping, Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class InteractionObservation:
    duration_ms: int
    turns: int = 1


@dataclass(frozen=True, slots=True)
class ContinuityObservation:
    checkpoint_used: bool
    reconstruction_required: bool


@dataclass(frozen=True, slots=True)
class MemoryObservation:
    memory_hit: bool
    useful: bool | None = None


@dataclass(frozen=True, slots=True)
class EvidenceObservation:
    retrieval_triggered: bool
    successful: bool
    refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "refs", tuple(self.refs))


@dataclass(frozen=True, slots=True)
class VoiceObservation:
    input: bool
    output: bool
    fallback_count: int = 0


@dataclass(frozen=True, slots=True)
class HumanFrictionObservation:
    correction_count: int = 0
    repetition_required: int = 0
    wrong_assumption_count: int = 0


@dataclass(frozen=True, slots=True)
class PilotObservationRecord:
    session: str
    timestamp: str
    interaction: InteractionObservation
    continuity: ContinuityObservation
    memory: MemoryObservation
    evidence: EvidenceObservation
    voice: VoiceObservation
    human: HumanFrictionObservation = field(default_factory=HumanFrictionObservation)
    boundary: Mapping[str, bool] = field(
        default_factory=lambda: {
            "observer_writes_memory": False,
            "observer_mutates_identity": False,
            "observer_changes_context": False,
            "observer_changes_provider_output": False,
        }
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "boundary", dict(self.boundary))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["evidence"]["refs"] = list(self.evidence.refs)
        data["boundary"] = dict(self.boundary)
        return data


@dataclass(frozen=True, slots=True)
class DailyRelationshipSnapshot:
    date: str
    sessions: int
    turns: int
    topics: tuple[str, ...]
    continuity_success: float
    repeated_explanation_rate: float
    memory_usefulness: float
    evidence_success_rate: float
    manual_corrections: int
    human_friction_score: int
    voice_usage_ratio: float
    boundary: Mapping[str, bool] = field(
        default_factory=lambda: {
            "snapshot_writes_memory": False,
            "snapshot_mutates_identity": False,
            "snapshot_updates_persona": False,
            "snapshot_is_memory": False,
        }
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "topics", tuple(self.topics))
        object.__setattr__(self, "boundary", dict(self.boundary))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["topics"] = list(self.topics)
        data["boundary"] = dict(self.boundary)
        return data


@dataclass(frozen=True, slots=True)
class PilotObservationSummary:
    total_sessions: int
    total_turns: int
    voice_usage_ratio: float
    evidence_hit_rate: float
    memory_hit_rate: float
    human_friction_score: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@runtime_checkable
class PilotObserverPort(Protocol):
    def observe(self, record: PilotObservationRecord) -> PilotObservationRecord:
        ...


class NullPilotObserver:
    """No-op observer for tests or deployments that disable pilot telemetry."""

    def observe(self, record: PilotObservationRecord) -> PilotObservationRecord:
        return record


class JsonlPilotObserver:
    """Append-only JSONL observer for H6 pilot instrumentation."""

    def __init__(self, path: str | Path = "runtime_observations/pilot_observations.jsonl") -> None:
        self.path = Path(path)

    def observe(self, record: PilotObservationRecord) -> PilotObservationRecord:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")
        return record

    def read_records(self) -> tuple[PilotObservationRecord, ...]:
        if not self.path.exists():
            return ()
        records = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            raw = json.loads(line)
            records.append(record_from_dict(raw))
        return tuple(records)

    def summarize(self) -> PilotObservationSummary:
        return summarize_observations(self.read_records())


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def start_timer() -> float:
    return perf_counter()


def elapsed_ms(started: float) -> int:
    return max(0, int((perf_counter() - started) * 1000))


def record_from_runtime_trace(
    *,
    session_id: str,
    duration_ms: int,
    trace: Mapping[str, Any],
    input_mode: str = "text",
    voice_output: bool = False,
    human: HumanFrictionObservation | None = None,
) -> PilotObservationRecord:
    continuity = dict(trace.get("continuity", {}))
    context = dict(trace.get("context", {}))
    memory = dict(trace.get("memory", {}))
    evidence = dict(trace.get("evidence", {}))
    evidence_refs = tuple(str(ref) for ref in evidence.get("refs", ()))
    evidence_status = str(evidence.get("status", ""))
    memory_status = str(memory.get("status", ""))
    context_blocks = tuple(str(block) for block in context.get("blocks_used", ()))
    return PilotObservationRecord(
        session=session_id,
        timestamp=utc_timestamp(),
        interaction=InteractionObservation(duration_ms=duration_ms, turns=1),
        continuity=ContinuityObservation(
            checkpoint_used=str(continuity.get("status")) == "PASS",
            reconstruction_required=bool(context_blocks or evidence_refs),
        ),
        memory=MemoryObservation(memory_hit=memory_status.startswith("PASS") and "NO_DUMP" not in memory_status, useful=None),
        evidence=EvidenceObservation(
            retrieval_triggered=evidence_status not in {"", "PASS_NOT_REQUIRED"},
            successful=evidence_status == "PASS" and bool(evidence_refs),
            refs=evidence_refs,
        ),
        voice=VoiceObservation(input=input_mode == "voice", output=voice_output),
        human=human or HumanFrictionObservation(),
    )


def summarize_observations(records: Iterable[PilotObservationRecord]) -> PilotObservationSummary:
    items = tuple(records)
    total_turns = sum(item.interaction.turns for item in items)
    total_sessions = len({item.session for item in items})
    if not items:
        return PilotObservationSummary(0, 0, 0.0, 0.0, 0.0, 0)
    voice_turns = sum(1 for item in items if item.voice.input or item.voice.output)
    evidence_triggered = sum(1 for item in items if item.evidence.retrieval_triggered)
    evidence_success = sum(1 for item in items if item.evidence.successful)
    memory_hits = sum(1 for item in items if item.memory.memory_hit)
    friction = sum(
        item.human.correction_count + item.human.repetition_required + item.human.wrong_assumption_count for item in items
    )
    return PilotObservationSummary(
        total_sessions=total_sessions,
        total_turns=total_turns,
        voice_usage_ratio=round(voice_turns / len(items), 4),
        evidence_hit_rate=round(evidence_success / evidence_triggered, 4) if evidence_triggered else 0.0,
        memory_hit_rate=round(memory_hits / len(items), 4),
        human_friction_score=friction,
    )


def record_from_dict(raw: Mapping[str, Any]) -> PilotObservationRecord:
    return PilotObservationRecord(
        session=str(raw["session"]),
        timestamp=str(raw["timestamp"]),
        interaction=InteractionObservation(**dict(raw["interaction"])),
        continuity=ContinuityObservation(**dict(raw["continuity"])),
        memory=MemoryObservation(**dict(raw["memory"])),
        evidence=EvidenceObservation(
            retrieval_triggered=bool(raw["evidence"]["retrieval_triggered"]),
            successful=bool(raw["evidence"]["successful"]),
            refs=tuple(raw["evidence"].get("refs", ())),
        ),
        voice=VoiceObservation(**dict(raw["voice"])),
        human=HumanFrictionObservation(**dict(raw.get("human", {}))),
        boundary=dict(raw.get("boundary", {})),
    )


def daily_relationship_snapshot(
    records: Iterable[PilotObservationRecord],
    *,
    date: str,
    topics: Iterable[str] = (),
) -> DailyRelationshipSnapshot:
    items = tuple(records)
    if not items:
        return DailyRelationshipSnapshot(
            date=date,
            sessions=0,
            turns=0,
            topics=tuple(topics),
            continuity_success=0.0,
            repeated_explanation_rate=0.0,
            memory_usefulness=0.0,
            evidence_success_rate=0.0,
            manual_corrections=0,
            human_friction_score=0,
            voice_usage_ratio=0.0,
        )
    total = len(items)
    sessions = len({item.session for item in items})
    turns = sum(item.interaction.turns for item in items)
    continuity_success = sum(1 for item in items if item.continuity.checkpoint_used) / total
    repeated_explanations = sum(item.human.repetition_required for item in items)
    memory_observed = [item for item in items if item.memory.useful is not None]
    memory_useful = sum(1 for item in memory_observed if item.memory.useful)
    evidence_triggered = [item for item in items if item.evidence.retrieval_triggered]
    evidence_success = sum(1 for item in evidence_triggered if item.evidence.successful)
    manual_corrections = sum(item.human.correction_count for item in items)
    friction = sum(
        item.human.correction_count + item.human.repetition_required + item.human.wrong_assumption_count for item in items
    )
    voice_turns = sum(1 for item in items if item.voice.input or item.voice.output)
    return DailyRelationshipSnapshot(
        date=date,
        sessions=sessions,
        turns=turns,
        topics=tuple(topics),
        continuity_success=round(continuity_success, 4),
        repeated_explanation_rate=round(repeated_explanations / max(1, turns), 4),
        memory_usefulness=round(memory_useful / len(memory_observed), 4) if memory_observed else 0.0,
        evidence_success_rate=round(evidence_success / len(evidence_triggered), 4) if evidence_triggered else 0.0,
        manual_corrections=manual_corrections,
        human_friction_score=friction,
        voice_usage_ratio=round(voice_turns / total, 4),
    )
