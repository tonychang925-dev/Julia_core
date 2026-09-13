from __future__ import annotations

from dataclasses import fields, replace
from pathlib import Path

import pytest

from julia_core.alignment_os import ProviderExecutionEnvelope
from julia_core.context_admission import (
    C03AdmissionRejected,
    ExactAdmittedSemanticBinder,
    ExclusiveAdmissionGate,
    SemanticBindingRequest,
)
from julia_core.execution_observer import (
    CanonicalExecutionObservation,
    CanonicalExecutionObservationRejected,
    CanonicalExecutionProvenance,
    ExecutionAuthorityAttestation,
    EvidenceOnlyCanonicalExecutionObserver,
    ProviderExecutionOutcome,
    ProviderExecutionRejected,
)
from julia_core.identity import IdentityRef
from julia_core.projection.contracts import ExperienceFrameSet, IdentityFrame
from julia_core.runtime.assistant_runtime import (
    JuliaAssistantRuntime,
    RuntimeTurnRequest,
)
from tests.context_admission.production_fixtures import (
    canonical_current_task_context,
    canonical_experience_frame,
    canonical_identity_frame,
    canonical_request,
)


SOURCE_PATH = Path("julia_core/execution_observer.py")


class IdentityFrameSubclass(IdentityFrame):
    pass


class ProviderExecutionOutcomeSubclass(ProviderExecutionOutcome):
    pass


def experience_frame_set(count: int = 1) -> ExperienceFrameSet:
    base = canonical_experience_frame()
    frames = []
    for index in range(count):
        source_ref = replace(
            base.source_ref,
            experience_id=f"experience-eng12a-{index + 1}",
            version_id=f"v{index + 1}",
        )
        frames.append(
            replace(
                base,
                source_ref=source_ref,
                experience_id=source_ref.experience_id,
                version_id=source_ref.version_id,
                provenance_refs=(
                    {
                        "source_ref": (
                            f"fixture://eng12a/experience/{index + 1}"
                        ),
                        "source_digest": base.source_digest,
                    },
                ),
            )
        )
    return ExperienceFrameSet(schema_version="1.0.0", frames=tuple(frames))


def exact_chain(*, identity=None, experiences=None, current_task=None):
    identity = identity or canonical_identity_frame()
    experiences = experiences or experience_frame_set()
    current_task = current_task or canonical_current_task_context()
    admission = canonical_request(
        identity=identity,
        experiences=experiences,
        current_task=current_task,
    )
    package = ExclusiveAdmissionGate().seal(admission)
    binding = ExactAdmittedSemanticBinder().bind(
        SemanticBindingRequest(
            package,
            admission.identity_frame,
            admission.experience_frames,
            admission.current_task_context,
        )
    )
    envelope = JuliaAssistantRuntime().prepare(
        RuntimeTurnRequest(binding=binding, provider_id="deepseek")
    )
    return identity, experiences, current_task, package, binding, envelope


def observe(chain, value: str = "provider output"):
    identity, experiences, current_task, package, binding, envelope = chain
    return EvidenceOnlyCanonicalExecutionObserver().observe(
        identity_frame=identity,
        experience_frames=experiences,
        current_task_context=current_task,
        package=package,
        binding=binding,
        envelope=envelope,
        provider_execution=lambda _envelope: value,
    )


def alternative_identity():
    digest = "d" * 64
    base = canonical_identity_frame()
    source_ref = IdentityRef("identity-lineage-eng12b", "v1")
    return replace(
        base,
        source_ref=source_ref,
        source_digest=digest,
        provenance_refs=(
            {
                "source_ref": "fixture://eng12b/identity",
                "source_digest": digest,
            },
        ),
    )


def test_exact_one_frame_provenance_manifest_is_visible() -> None:
    record = observe(exact_chain())

    provenance = record.provenance
    assert provenance.identity_frame.source_ref == {
        "lineage_id": "identity-lineage-eng12a",
        "version_id": "v1",
    }
    assert provenance.identity_frame.source_digest == "a" * 64
    assert provenance.experience_frames[0].source_ref == {
        "experience_id": "experience-eng12a-1",
        "version_id": "v1",
    }
    assert len(provenance.ordered_frame_digest_manifest) == 1
    assert provenance.current_task_context.source_ref == {
        "source_ref": "conversation_runtime://eng12a/current-task"
    }
    assert provenance.gate_receipt
    assert provenance.semantic_fingerprint
    assert provenance.ordered_unit_digests
    assert provenance.provider_id == "deepseek"
    assert provenance.alignment_identity


def test_n_frame_order_and_complete_manifest_are_preserved() -> None:
    experiences = experience_frame_set(3)
    chain = exact_chain(experiences=experiences)
    record = observe(chain)

    expected = tuple(frame.digest() for frame in experiences.frames)
    assert record.provenance.ordered_frame_digest_manifest == expected
    assert record.provenance.experience_frame_set_digest == experiences.digest()
    assert tuple(
        item.source_ref["experience_id"]
        for item in record.provenance.experience_frames
    ) == ("experience-eng12a-1", "experience-eng12a-2", "experience-eng12a-3")


@pytest.mark.parametrize(
    ("value", "disposition", "present", "failure_class"),
    [
        ("provider output", "SUCCEEDED", True, None),
        ("  ", "FAILED", False, "EMPTY_OUTPUT"),
    ],
)
def test_mechanical_success_and_empty_output_dispositions(
    value, disposition, present, failure_class
) -> None:
    record = observe(exact_chain(), value)

    assert record.execution.disposition == disposition
    assert record.execution.output_present is present
    assert record.execution.failure_class == failure_class
    assert "provider output" not in str(record.to_dict())


def test_provider_failure_and_error_dispositions_are_non_semantic() -> None:
    chain = exact_chain()
    identity, experiences, current_task, package, binding, envelope = chain
    observer = EvidenceOnlyCanonicalExecutionObserver()
    common = {
        "identity_frame": identity,
        "experience_frames": experiences,
        "current_task_context": current_task,
        "package": package,
        "binding": binding,
        "envelope": envelope,
    }

    failed = observer.observe(
        **common,
        provider_execution=lambda _envelope: (
            lambda: (_ for _ in ()).throw(ProviderExecutionRejected("RATE_LIMIT"))
        )(),
    )
    errored = observer.observe(
        **common,
        provider_execution=lambda _envelope: (
            lambda: (_ for _ in ()).throw(TimeoutError())
        )(),
    )
    not_run = observer.observe_outcome(
        **common,
        outcome=ProviderExecutionOutcome.not_run("PROVIDER_UNAVAILABLE"),
    )

    assert failed.execution.disposition == "FAILED"
    assert failed.execution.failure_class == "RATE_LIMIT"
    assert errored.execution.disposition == "ERROR"
    assert errored.execution.failure_class == "TIMEOUTERROR"
    assert not_run.execution.disposition == "NOT_RUN"
    assert not_run.execution.failure_class == "PROVIDER_UNAVAILABLE"


def test_execution_bound_zero_authority_and_exact_correlation() -> None:
    chain = exact_chain()
    record = observe(chain)

    authority = record.authority.to_dict()
    assert authority == {
        "OBSERVABILITY_OUTPUT_AUTHORITY": 0,
        "SEMANTIC_AUTHORITY": 0,
        "PRODUCTION_RESPONSE_SELECTION_AUTHORITY": 0,
        "CANONICAL_WRITES": 0,
        "IDENTITY_AUTHORITY_MUTATION": 0,
        "MEMORY_EXPERIENCE_AUTHORITY_MUTATION": 0,
        "POST_C03_SEMANTIC_RECONSTRUCTION": 0,
    }
    assert record.provenance.conversation_id == "conversation-eng12a"
    assert record.provenance.turn_id == "turn-eng12a-1"
    assert record.provenance.gate_receipt == chain[3].gate_receipt
    assert record.provenance.semantic_fingerprint == chain[5].semantic_fingerprint


def test_replay_digest_is_deterministic_and_material_change_sensitive() -> None:
    chain = exact_chain()
    first = observe(chain)
    same = observe(chain)
    changed_disposition = EvidenceOnlyCanonicalExecutionObserver().observe_outcome(
        identity_frame=chain[0],
        experience_frames=chain[1],
        current_task_context=chain[2],
        package=chain[3],
        binding=chain[4],
        envelope=chain[5],
        outcome=ProviderExecutionOutcome.not_run("PROVIDER_UNAVAILABLE"),
    )
    changed_provenance = observe(exact_chain(identity=alternative_identity()))

    assert first.digest() == same.digest()
    assert first.digest() != changed_disposition.digest()
    assert first.digest() != changed_provenance.digest()


def test_mismatched_canonical_execution_identity_rejected() -> None:
    first = exact_chain()
    second = exact_chain(current_task=canonical_current_task_context(turn_id="turn-2"))

    with pytest.raises(
        CanonicalExecutionObservationRejected, match="identities do not match"
    ):
        EvidenceOnlyCanonicalExecutionObserver().observe(
            identity_frame=second[0],
            experience_frames=second[1],
            current_task_context=second[2],
            package=first[3],
            binding=second[4],
            envelope=second[5],
            provider_execution=lambda _envelope: "output",
        )


def test_exact_types_and_outcome_subclasses_rejected() -> None:
    identity, experiences, current_task, package, binding, envelope = exact_chain()
    observer = EvidenceOnlyCanonicalExecutionObserver()

    with pytest.raises(TypeError, match="evidence is inexact"):
        observer.observe_outcome(
            identity_frame=object.__new__(IdentityFrameSubclass),
            experience_frames=experiences,
            current_task_context=current_task,
            package=package,
            binding=binding,
            envelope=envelope,
            outcome=ProviderExecutionOutcome.not_run("NOT_RUN"),
        )
    with pytest.raises(TypeError, match="outcome is inexact"):
        observer.observe_outcome(
            identity_frame=identity,
            experience_frames=experiences,
            current_task_context=current_task,
            package=package,
            binding=binding,
            envelope=envelope,
            outcome=object.__new__(ProviderExecutionOutcomeSubclass),
        )
    with pytest.raises(TypeError, match="issued_by"):
        ProviderExecutionOutcome(
            disposition="SUCCEEDED",
            output_present=True,
        )


def test_missing_required_provenance_rejected_before_observation() -> None:
    identity = replace(canonical_identity_frame(), provenance_refs=())

    with pytest.raises(C03AdmissionRejected, match="provenance is absent"):
        exact_chain(identity=identity)


def test_caller_cannot_inject_choice_or_switch_fields() -> None:
    chain = exact_chain()
    all_fields = {
        field.name
        for dataclass in (
            ProviderExecutionOutcome,
            CanonicalExecutionProvenance,
            ExecutionAuthorityAttestation,
            CanonicalExecutionObservation,
        )
        for field in fields(dataclass)
    }

    assert not all_fields & {
        "winner",
        "preferred",
        "selected",
        "selected_response",
        "switch",
        "routing",
    }
    with pytest.raises(TypeError):
        observe(chain, winner="provider")


def test_observer_constructs_no_semantic_or_authority_objects() -> None:
    source = SOURCE_PATH.read_text(encoding="utf-8")

    assert "IdentityFrame(" not in source
    assert "ExperienceFrameSet(" not in source
    assert "CurrentConversationalTaskContext(" not in source
    assert "get_llm_provider" not in source
    assert "ProviderAlignmentBoundary" not in source
    assert "winner" not in source
    assert "preferred" not in source
    assert "selected" not in source
    assert "switch" not in source
    assert "routing" not in source
    assert "repository" not in source
    assert "save(" not in source
    assert "commit(" not in source
