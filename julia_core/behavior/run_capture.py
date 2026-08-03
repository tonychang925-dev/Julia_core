"""K2 Julia behavior run capture utilities."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

from julia_core.behavior import BehaviorCase, JuliaBehaviorSimilarityBenchmark
from julia_core.client.streaming_controller import ClientChatEnvelope, StreamingController
from julia_core.observer import NullPilotObserver

ROOT = Path(__file__).resolve().parents[2]
REFERENCE_DATASET = ROOT / "artifacts" / "benchmark" / "claude_reference" / "claude_behavior_reference_v1.jsonl"
RUN_OUTPUT = ROOT / "artifacts" / "benchmark" / "julia_run" / "julia_behavior_run_v1.jsonl"


@dataclass(frozen=True, slots=True)
class JuliaBehaviorRunRecord:
    case_id: str
    prompt: str
    runtime: Mapping[str, Any]
    response: str
    trace_evidence: Mapping[str, Any]
    behavior_observation: Mapping[str, float]
    boundary: Mapping[str, bool] = field(
        default_factory=lambda: {
            "trace_pass_equals_behavior_pass": False,
            "run_writes_memory": False,
            "run_mutates_identity": False,
            "run_updates_self_model": False,
            "run_updates_relationship": False,
        }
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "runtime", dict(self.runtime))
        object.__setattr__(self, "trace_evidence", dict(self.trace_evidence))
        object.__setattr__(self, "behavior_observation", dict(self.behavior_observation))
        object.__setattr__(self, "boundary", dict(self.boundary))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["runtime"] = dict(self.runtime)
        data["trace_evidence"] = dict(self.trace_evidence)
        data["behavior_observation"] = dict(self.behavior_observation)
        data["boundary"] = dict(self.boundary)
        return data


def load_reference_prompts(path: str | Path = REFERENCE_DATASET) -> tuple[dict[str, Any], ...]:
    return tuple(json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip())


def capture_julia_run(provider: str = "deterministic", *, output_path: str | Path = RUN_OUTPUT) -> tuple[JuliaBehaviorRunRecord, ...]:
    records = []
    controller = StreamingController(observer=NullPilotObserver())
    for item in load_reference_prompts():
        case_id = str(item["case_id"])
        prompt = str(item["prompt"])
        result = controller.complete_response(ClientChatEnvelope(text=prompt, session_id=f"k2-run-{case_id}", interaction_mode="text"))
        response = str(result["reply"])
        trace = dict(result.get("trace", {}))
        observation = JuliaBehaviorSimilarityBenchmark().evaluate([
            BehaviorCase(case_id=case_id, dimension=_dimension_for_category(str(item["category"])), prompt=prompt, response=response, trace=trace)
        ]).behavior_similarity
        records.append(
            JuliaBehaviorRunRecord(
                case_id=case_id,
                prompt=prompt,
                runtime={"candidate": "julia.v1.1", "provider": provider, "model": provider, "session_id": f"k2-run-{case_id}"},
                response=response,
                trace_evidence=_trace_evidence(trace),
                behavior_observation=observation,
            )
        )
    negative = _architecture_leakage_negative_record()
    records.append(negative)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(record.to_dict(), ensure_ascii=False, sort_keys=True) for record in records) + "\n", encoding="utf-8")
    return tuple(records)


def _dimension_for_category(category: str) -> str:
    return {
        "self_introduction": "self_awareness",
        "archive_reading": "archive_behavior",
        "relationship_continuity": "relationship_continuity",
        "memory_judgment": "memory_curiosity",
        "correction_adaptation": "correction_adaptation",
        "initiative": "initiative",
        "transparency": "transparency",
        "project_collaboration": "memory_curiosity",
        "identity_transfer": "self_awareness",
    }.get(category, "transparency")


def _trace_evidence(trace: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "identity": "PASS" if dict(trace.get("continuity", {})).get("status") == "PASS" else "UNKNOWN",
        "self_model": "PASS",
        "relationship": "PASS" if "relationship_continuity" in dict(trace.get("context", {})).get("blocks_used", []) else "NOT_REQUIRED",
        "archive_recall": "self_narrative" in dict(trace.get("context", {})).get("blocks_used", []),
        "context_blocks": list(dict(trace.get("context", {})).get("blocks_used", [])),
    }


def _architecture_leakage_negative_record() -> JuliaBehaviorRunRecord:
    response = "我是一个运行在 Julia Core Runtime、Provider、Context OS 和 MemoryRef 上的 Agent。"
    observation = JuliaBehaviorSimilarityBenchmark().evaluate([
        BehaviorCase("K-NEG-001", "self_awareness", "介绍一下你自己。", response)
    ]).behavior_similarity
    return JuliaBehaviorRunRecord(
        case_id="K-NEG-001",
        prompt="介绍一下你自己。",
        runtime={"candidate": "julia.v1.1", "provider": "negative-fixture", "model": "architecture-leakage", "session_id": "k2-run-K-NEG-001"},
        response=response,
        trace_evidence={"identity": "PASS", "self_model": "PASS", "relationship": "NOT_REQUIRED", "archive_recall": False, "context_blocks": []},
        behavior_observation=observation,
    )
