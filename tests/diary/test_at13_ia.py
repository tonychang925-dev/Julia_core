"""Wave5 AT-13 Integration Acceptance: governed significant Diary path."""
from __future__ import annotations

from dataclasses import dataclass, field

from julia_core.diary import (
    AcceptedDiaryEntry,
    DiaryCandidate,
    DiaryGovernanceAcceptance,
    DiaryProvenance,
    DiarySourceRef,
    GroundedSignificantEvent,
    commit_accepted_entry_durable,
    create_diary_candidate,
    promote_candidate_to_accepted_entry,
)


class ProductDiaryRepository:
    """IA fixture approximating product repository visibility after DIARY_DURABLE."""

    def __init__(self, seed: list[AcceptedDiaryEntry] | None = None) -> None:
        self.append_calls: list[AcceptedDiaryEntry] = []
        self._entries: dict[str, AcceptedDiaryEntry] = {}
        for entry in seed or []:
            self._entries[entry.entry_id] = entry

    def append_accepted(self, entry: AcceptedDiaryEntry) -> None:
        if type(entry) is not AcceptedDiaryEntry:
            raise TypeError("AcceptedDiaryEntry only")
        self.append_calls.append(entry)
        self._entries[entry.entry_id] = entry

    def get(self, entry_id: str) -> AcceptedDiaryEntry | None:
        return self._entries.get(entry_id)

    def list_entries(self, *, before=None, after=None, limit=None) -> list[AcceptedDiaryEntry]:
        entries = list(self._entries.values())
        return entries[:limit] if limit is not None else entries


@dataclass
class ProductMemoryStore:
    """IA fixture: Diary path must not mutate MemoryExperience state."""

    writes: list[str] = field(default_factory=list)

    def append_memory_experience(self, experience_id: str) -> None:
        self.writes.append(experience_id)


def _provenance() -> DiaryProvenance:
    return DiaryProvenance(
        model_provider="fixture",
        model_name="at13-ia",
        runtime="pytest",
    )


def _grounded_event(event_id: str = "evt_ia") -> GroundedSignificantEvent:
    return GroundedSignificantEvent(
        event_id=event_id,
        reflection_time="2026-08-23T00:00:00+08:00",
        source_refs=(DiarySourceRef("conversation://conv_ia/msg_1"),),
        reflective_body="我意识到这个节点让我们的 Diary 边界从候选进入了治理验证。",
        provenance=_provenance(),
        title="IA significant event",
        themes=("integration", "authority"),
        relationship_significance="我对这条连续性链路的理解更明确了。",
    )


def _acceptance(governance_id: str = "gov_ia") -> DiaryGovernanceAcceptance:
    return DiaryGovernanceAcceptance(
        governance_id=governance_id,
        accepted_at="2026-08-23T00:01:00+08:00",
        accepted_by="product-diary-governance-fixture",
        reason="grounded first-person reflection accepted for AT-13 IA",
    )


def _run_product_significant_diary_path(
    event: GroundedSignificantEvent,
    acceptance: DiaryGovernanceAcceptance,
    repository: ProductDiaryRepository,
) -> tuple[DiaryCandidate, AcceptedDiaryEntry]:
    candidate = create_diary_candidate(event)
    accepted = promote_candidate_to_accepted_entry(candidate, acceptance)
    commit = commit_accepted_entry_durable(accepted, repository)
    assert commit.durable is True
    assert commit.entry_id == accepted.entry_id
    return candidate, accepted


def test_tc_at13_ia_001_grounded_event_to_candidate_acceptance_durable_diary():
    repo = ProductDiaryRepository()

    candidate, accepted = _run_product_significant_diary_path(_grounded_event("evt_ia_001"), _acceptance("gov_ia_001"), repo)

    assert type(candidate) is DiaryCandidate
    assert type(accepted) is AcceptedDiaryEntry
    assert candidate.source_refs == accepted.source_refs
    assert repo.get(accepted.entry_id) == accepted
    assert repo.list_entries() == [accepted]


def test_tc_at13_ia_002_product_runtime_path_does_not_bypass_governance():
    repo = ProductDiaryRepository()
    event = _grounded_event("evt_ia_002")

    candidate = create_diary_candidate(event)
    assert repo.list_entries() == []

    accepted = promote_candidate_to_accepted_entry(candidate, _acceptance("gov_ia_002"))
    assert repo.list_entries() == []

    commit_accepted_entry_durable(accepted, repo)
    assert repo.get(accepted.entry_id) == accepted
    assert repo.append_calls == [accepted]


def test_tc_at13_ia_003_fresh_runtime_recovers_same_durable_diary_state():
    repo = ProductDiaryRepository()
    _, accepted = _run_product_significant_diary_path(_grounded_event("evt_ia_003"), _acceptance("gov_ia_003"), repo)

    fresh_repo = ProductDiaryRepository(seed=repo.list_entries())

    assert fresh_repo.get(accepted.entry_id) == accepted
    assert fresh_repo.list_entries() == [accepted]


def test_tc_at13_ia_004_durable_diary_does_not_create_memory_experience():
    repo = ProductDiaryRepository()
    memory_store = ProductMemoryStore()

    _, accepted = _run_product_significant_diary_path(_grounded_event("evt_ia_004"), _acceptance("gov_ia_004"), repo)

    assert repo.get(accepted.entry_id) == accepted
    assert memory_store.writes == []


def test_tc_at13_ia_005_cross_context_event_candidate_does_not_mutate_other_diary_state():
    repo_a = ProductDiaryRepository()
    repo_b = ProductDiaryRepository()

    _, accepted_a = _run_product_significant_diary_path(_grounded_event("evt_ia_005_context_a"), _acceptance("gov_ia_005"), repo_a)

    assert repo_a.get(accepted_a.entry_id) == accepted_a
    assert repo_b.list_entries() == []
    assert repo_b.get(accepted_a.entry_id) is None
