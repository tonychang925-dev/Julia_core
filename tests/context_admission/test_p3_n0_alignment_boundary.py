from __future__ import annotations

from dataclasses import fields
from typing import Any

import pytest

from julia_core.alignment_os import (
    AlignmentExecutionMetadata,
    ProviderAlignmentBoundary,
    ProviderExecutionEnvelope,
)
from julia_core.context_admission import C03AdmissionRejected

from tests.context_admission.test_p3_n0_semantic_binding import bound_bundle


def test_boundary_preserves_exact_messages_and_fingerprint():
    binding = bound_bundle()
    envelope = ProviderAlignmentBoundary().resolve(
        binding,
        provider_id="DeepSeek",
        cognitive_mode="conversation",
    )

    assert envelope.messages == tuple(unit.to_message() for unit in binding.units)
    assert envelope.semantic_fingerprint == binding.semantic_fingerprint()
    assert [message["role"] for message in envelope.messages] == [
        "system",
        "system",
        "user",
    ]


def test_alignment_metadata_is_exact_and_non_semantic():
    metadata = AlignmentExecutionMetadata(
        provider_id="deepseek",
        cognitive_mode="conversation",
        modality="text",
        response_format="default",
        max_output_tokens=4096,
        temperature=None,
    )
    field_names = {field.name for field in fields(metadata)}

    assert field_names == {
        "provider_id",
        "cognitive_mode",
        "modality",
        "response_format",
        "max_output_tokens",
        "temperature",
    }
    assert not field_names & {
        "persona",
        "persona_id",
        "identity",
        "relationship",
        "experience",
        "memory",
        "history",
        "evidence",
        "capability",
        "prompt",
    }


def test_boundary_rejects_non_exact_bundle_before_output():
    with pytest.raises(C03AdmissionRejected, match="exact admitted semantic bundle"):
        ProviderAlignmentBoundary().resolve(object(), provider_id="deepseek")


def test_only_exact_boundary_constructs_execution_envelope():
    binding = bound_bundle()
    valid = ProviderAlignmentBoundary().resolve(
        binding,
        provider_id="deepseek",
        cognitive_mode="conversation",
    )
    arguments = {
        field.name: getattr(valid, field.name)
        for field in fields(ProviderExecutionEnvelope)
        if field.name != "issued_by"
    }

    with pytest.raises(TypeError, match="only ProviderAlignmentBoundary"):
        ProviderExecutionEnvelope(**arguments, issued_by=object())


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("provider_id", ""),
        ("provider_id", object()),
        ("cognitive_mode", ""),
        ("modality", "audio"),
        ("response_format", "markdown"),
        ("max_output_tokens", 0),
        ("max_output_tokens", 32769),
        ("temperature", -0.1),
        ("temperature", 2.1),
    ],
)
def test_inexact_execution_metadata_fails_closed(
    field_name: str,
    value: Any,
) -> None:
    arguments = {
        "provider_id": "deepseek",
        "cognitive_mode": "conversation",
        "modality": "text",
        "response_format": "default",
        "max_output_tokens": 4096,
        "temperature": None,
    }
    arguments[field_name] = value

    with pytest.raises(TypeError, match="alignment execution"):
        AlignmentExecutionMetadata(**arguments)


def test_post_construction_semantic_mutation_fails_verification():
    binding = bound_bundle()
    envelope = ProviderAlignmentBoundary().resolve(
        binding,
        provider_id="deepseek",
        cognitive_mode="conversation",
    )
    envelope.messages[1]["content"] += "post-C03 mutation"

    with pytest.raises(TypeError, match="fingerprint is forged"):
        envelope.verify()
