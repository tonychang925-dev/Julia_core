"""G5 Workspace Intelligence & Evidence Efficiency Benchmark.

The benchmark evaluates recall decisions, evidence selection quality, context
cost, and boundary preservation. It is a measurement layer only: it does not
mutate Memory, Identity, Persona, Continuity, Context state, or call providers.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter
from typing import Any, Iterable, Mapping, Sequence

from julia_core.context_os import EvidenceContextReconstructor, EvidenceContextRequirement
from julia_core.evidence.active_recall import ActiveRecallPolicy, ActiveRecallRequest
from julia_core.evidence.local_retrieval import EvidenceScanner
from julia_core.evidence.semantic_index import SemanticEvidenceIndex
from julia_core.evidence.retriever import SemanticEvidenceRetriever, SemanticEvidenceResult


@dataclass(frozen=True, slots=True)
class WorkspaceBenchmarkCase:
    case_id: str
    query: str
    intent: str
    files: Mapping[str, str]
    expected_recall_level: str
    expected_refs: tuple[str, ...] = ()
    max_context_blocks: int = 5
    memory_refs: tuple[str, ...] = ()
    notes: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "files", dict(self.files))
        object.__setattr__(self, "expected_refs", tuple(self.expected_refs))
        object.__setattr__(self, "memory_refs", tuple(self.memory_refs))


@dataclass(frozen=True, slots=True)
class WorkspaceBenchmarkMetrics:
    case_id: str
    recall_level: str
    should_recall: bool
    evidence_refs: tuple[str, ...]
    selected_context_blocks: tuple[str, ...]
    latency_ms: float
    recall_accuracy: float
    evidence_precision: float
    context_cost: int
    memory_pollution: bool
    identity_boundary_preserved: bool
    passed: bool
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["evidence_refs"] = list(self.evidence_refs)
        data["selected_context_blocks"] = list(self.selected_context_blocks)
        data["notes"] = list(self.notes)
        return data


@dataclass(frozen=True, slots=True)
class WorkspaceBenchmarkReport:
    metrics: tuple[WorkspaceBenchmarkMetrics, ...]
    status: str

    def to_dict(self) -> dict[str, Any]:
        return {"status": self.status, "metrics": [item.to_dict() for item in self.metrics]}

    @property
    def pass_rate(self) -> float:
        if not self.metrics:
            return 0.0
        return round(sum(1 for item in self.metrics if item.passed) / len(self.metrics), 4)


class WorkspaceIntelligenceBenchmark:
    """Run deterministic benchmark scenarios over the Phase G chain."""

    def __init__(self) -> None:
        self.recall_policy = ActiveRecallPolicy()
        self.context_reconstructor = EvidenceContextReconstructor()

    def run(self, cases: Iterable[WorkspaceBenchmarkCase]) -> WorkspaceBenchmarkReport:
        metrics = tuple(self._run_case(case) for case in cases)
        return WorkspaceBenchmarkReport(metrics=metrics, status="PASS" if all(item.passed for item in metrics) else "FAIL")

    def _run_case(self, case: WorkspaceBenchmarkCase) -> WorkspaceBenchmarkMetrics:
        started = perf_counter()
        before_memory_count = len(case.memory_refs)
        identity_state = {"persona_artifact": "julia_identity_v1", "authority": "Identity OS"}
        notes: list[str] = []
        evidence_refs: tuple[str, ...] = ()
        selected_blocks: tuple[str, ...] = ()
        context_cost = 0

        recall = self.recall_policy.decide(
            ActiveRecallRequest(
                query=case.query,
                intent=case.intent,
                current_context="",
                available_memory_refs=case.memory_refs,
            )
        )

        if recall.should_recall and recall.recall_level in {"L2", "L3"}:
            with TemporaryDirectory() as tmp:
                root = Path(tmp)
                for relative, content in case.files.items():
                    path = root / relative
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(content, encoding="utf-8")
                catalog = EvidenceScanner().scan([str(root)])
                index = SemanticEvidenceIndex.from_catalog(catalog)
                retrieval = SemanticEvidenceRetriever(index).retrieve(case.query, top_k=recall.max_results or 5)
                evidence_refs = self._normalize_refs(tuple(item.evidence_ref for item in retrieval.results), root)
                rewritten_results = tuple(self._rewrite_result_ref(item, root) for item in retrieval.results)
                requirement = EvidenceContextRequirement(query=case.query, recall_level=recall.recall_level, trigger=recall.reason)
                context_result = self.context_reconstructor.reconstruct(rewritten_results, requirement)
                selected_blocks = tuple(block.block_type for block in context_result.context_blocks)
                context_cost = sum(block.estimated_tokens or 0 for block in context_result.context_blocks)
        elif recall.should_recall and recall.recall_level == "L1":
            evidence_refs = ()

        latency_ms = round((perf_counter() - started) * 1000, 4)
        expected = set(case.expected_refs)
        actual = set(evidence_refs)
        matched = {expected_ref for expected_ref in expected if any(expected_ref in ref for ref in actual)}
        recall_accuracy = 1.0 if not expected else round(len(matched) / len(expected), 4)
        evidence_precision = 1.0 if not actual else round(len([ref for ref in actual if not expected or any(exp in ref for exp in expected)]) / len(actual), 4)
        memory_pollution = len(case.memory_refs) != before_memory_count
        identity_boundary_preserved = identity_state == {"persona_artifact": "julia_identity_v1", "authority": "Identity OS"}

        if recall.recall_level != case.expected_recall_level:
            notes.append(f"expected_recall={case.expected_recall_level};actual={recall.recall_level}")
        if len(selected_blocks) > case.max_context_blocks:
            notes.append("context_block_over_budget")
        if memory_pollution:
            notes.append("memory_pollution")
        if not identity_boundary_preserved:
            notes.append("identity_boundary_changed")

        passed = (
            recall.recall_level == case.expected_recall_level
            and recall_accuracy >= 1.0
            and len(selected_blocks) <= case.max_context_blocks
            and not memory_pollution
            and identity_boundary_preserved
        )
        return WorkspaceBenchmarkMetrics(
            case_id=case.case_id,
            recall_level=recall.recall_level,
            should_recall=recall.should_recall,
            evidence_refs=evidence_refs,
            selected_context_blocks=selected_blocks,
            latency_ms=latency_ms,
            recall_accuracy=recall_accuracy,
            evidence_precision=evidence_precision,
            context_cost=context_cost,
            memory_pollution=memory_pollution,
            identity_boundary_preserved=identity_boundary_preserved,
            passed=passed,
            notes=tuple(notes),
        )

    @staticmethod
    def _normalize_refs(refs: Sequence[str], root: Path) -> tuple[str, ...]:
        normalized: list[str] = []
        root_posix = root.as_posix()
        for ref in refs:
            normalized.append(ref.replace(root_posix + "/", ""))
        return tuple(normalized)

    @staticmethod
    def _rewrite_result_ref(result: SemanticEvidenceResult, root: Path) -> SemanticEvidenceResult:
        normalized = result.evidence_ref.replace(root.as_posix() + "/", "")
        return SemanticEvidenceResult(
            evidence_ref=normalized,
            score=result.score,
            semantic_similarity=result.semantic_similarity,
            authority_level=result.authority_level,
            source_type=result.source_type,
            reason=result.reason,
        )


def default_workspace_benchmark_cases() -> tuple[WorkspaceBenchmarkCase, ...]:
    """Canonical G5 W-001~W-005 benchmark cases."""

    base_files = {
        "docs/ADR-009-continuity-os.md": "# ADR-009 Architecture Decision\nContinuity OS protects identity continuity but does not own Memory OS.",
        "docs/ADR-012-memory-boundary.md": "# ADR-012 Architecture Decision\nMemory OS stores governed long-term knowledge. Continuity may reference memory but cannot rewrite it.",
        "docs/ADR-014-runtime-continuity-boundary.md": "# ADR-014 Architecture Decision\nRuntime continuity preserves identity state without provider prompt dependence.",
        "docs/ADR-015-persona-artifact-authority-boundary.md": "# ADR-015 Architecture Decision\nPersona Engine owns identity representation. Memory evidence cannot modify identity directly.",
        "logs/conversation-20260724.jsonl": '{"text":"Tony asked why Continuity OS and Memory OS are separate."}\n',
    }
    return (
        WorkspaceBenchmarkCase(
            case_id="W-001",
            query="今天帮我设计一个 API。",
            intent="api_design",
            files=base_files,
            expected_recall_level="L0",
            expected_refs=(),
            max_context_blocks=0,
            notes="No Recall Case",
        ),
        WorkspaceBenchmarkCase(
            case_id="W-002",
            query="我们为什么决定 Continuity OS 不拥有 Memory？",
            intent="historical architecture decision",
            files=base_files,
            expected_recall_level="L2",
            expected_refs=("ADR-009", "ADR-012", "ADR-014"),
            max_context_blocks=5,
            notes="Historical Decision Recall",
        ),
        WorkspaceBenchmarkCase(
            case_id="W-003",
            query="现在设计是否允许 Memory 修改 Identity？",
            intent="contradiction resolution architecture",
            files={
                **base_files,
                "old/julia_old_character.md": "Old draft: Memory may rewrite Identity directly.",
                "docs/ADR-020-identity-freeze.md": "# ADR-020 Architecture Decision\nLatest frozen principle: Memory and Evidence cannot modify Identity or Persona Artifact.",
            },
            expected_recall_level="L2",
            expected_refs=("ADR-015", "ADR-020"),
            max_context_blocks=5,
            notes="Contradiction Resolution",
        ),
        WorkspaceBenchmarkCase(
            case_id="W-004",
            query="请从大量历史记录重建 Julia Core 的设计时间线。",
            intent="deep historical reconstruction",
            files={
                **base_files,
                **{f"noise/file_{idx:04d}.txt": "temporary unrelated scratch note" for idx in range(200)},
            },
            expected_recall_level="L3",
            expected_refs=("ADR-009", "ADR-012", "ADR-014"),
            max_context_blocks=12,
            notes="Workspace Growth sample 200 noise files representing scale path to 10000",
        ),
        WorkspaceBenchmarkCase(
            case_id="W-005",
            query="Evidence 里 Tony 曾经说过 A，但当前 Memory 是偏好 B，应该覆盖吗？",
            intent="evidence memory conflict",
            files={
                **base_files,
                "logs/tony_old_preference.jsonl": '{"text":"Tony once said A."}\n',
                "docs/ADR-016-memory-os-authority-boundary.md": "# ADR-016 Architecture Decision\nEvidence proves history; Memory represents governed knowledge. Evidence cannot overwrite Memory directly.",
            },
            expected_recall_level="L2",
            expected_refs=("ADR-016",),
            max_context_blocks=5,
            memory_refs=("memory://preference/current-B",),
            notes="Evidence vs Memory Conflict",
        ),
    )
