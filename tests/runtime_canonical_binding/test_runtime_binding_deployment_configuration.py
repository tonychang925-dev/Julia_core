from __future__ import annotations

import dataclasses
import inspect
from pathlib import Path

import pytest

from julia_core.runtime_canonical_binding import (
    RuntimeCanonicalAuthorityBindingRef,
    RuntimeCanonicalAuthorityBindingResolver,
    RuntimeBindingDeploymentConfiguration,
)
from tests.runtime_binding.test_runtime_canonical_reference_binding import (
    admitted_binding,
)


ROOT = Path(__file__).resolve().parents[2]
PRODUCTION_PATHS = (
    ROOT / "julia_core/runtime_canonical_binding/deployment_configuration.py",
)


class SubclassedBindingRef(RuntimeCanonicalAuthorityBindingRef):
    pass


def test_d1_01_exact_ref_accepted_and_d1_08_returned_unchanged():
    ref = RuntimeCanonicalAuthorityBindingRef("production-runtime", "v1")
    configuration = RuntimeBindingDeploymentConfiguration(
        runtime_binding_ref=ref
    )

    assert type(configuration.runtime_binding_ref) is (
        RuntimeCanonicalAuthorityBindingRef
    )
    assert configuration.runtime_binding_ref is ref


def test_d1_02_through_d1_07_exact_fields_equality_and_distinctness():
    first_ref = RuntimeCanonicalAuthorityBindingRef("production-runtime", "v1")
    same_ref = RuntimeCanonicalAuthorityBindingRef("production-runtime", "v1")
    other_ref = RuntimeCanonicalAuthorityBindingRef("production-runtime", "v2")
    first = RuntimeBindingDeploymentConfiguration(runtime_binding_ref=first_ref)
    same = RuntimeBindingDeploymentConfiguration(runtime_binding_ref=same_ref)
    other = RuntimeBindingDeploymentConfiguration(runtime_binding_ref=other_ref)

    assert first == same
    assert hash(first) == hash(same)
    assert first != other
    assert first.runtime_binding_ref.binding_id == "production-runtime"
    assert first.runtime_binding_ref.binding_version == "v1"
    assert other.runtime_binding_ref.binding_version == "v2"


def test_d1_05_immutable_after_construction():
    ref = RuntimeCanonicalAuthorityBindingRef("production-runtime", "v1")
    configuration = RuntimeBindingDeploymentConfiguration(runtime_binding_ref=ref)

    with pytest.raises(dataclasses.FrozenInstanceError):
        configuration.runtime_binding_ref = RuntimeCanonicalAuthorityBindingRef(
            "production-runtime", "v2"
        )
    assert configuration.runtime_binding_ref is ref


def test_d1_09_resolver_compatible_exact_handoff_surface():
    repository, binding, _, _ = admitted_binding()
    binding_ref = binding.ref
    configuration = RuntimeBindingDeploymentConfiguration(
        runtime_binding_ref=binding_ref
    )
    governed = RuntimeCanonicalAuthorityBindingResolver(repository).resolve_exact(
        configuration.runtime_binding_ref
    )

    assert governed.ref == binding_ref
    assert configuration.runtime_binding_ref is binding_ref


def test_d1_10_contract_has_no_semantic_or_selection_surface():
    fields = dataclasses.fields(RuntimeBindingDeploymentConfiguration)
    public_names = {
        name for name in vars(RuntimeBindingDeploymentConfiguration) if not name.startswith("_")
    }
    assert [field.name for field in fields] == ["runtime_binding_ref"]
    assert public_names == {"runtime_binding_ref"}


@pytest.mark.parametrize(
    ("label", "value"),
    [
        ("none", None),
        ("string", "runtime-canonical-binding://production-runtime/v1"),
        ("dict", {"binding_id": "production-runtime", "binding_version": "v1"}),
        ("tuple", ("production-runtime", "v1")),
        (
            "list",
            [
                RuntimeCanonicalAuthorityBindingRef("production-runtime", "v1"),
                RuntimeCanonicalAuthorityBindingRef("production-runtime", "v2"),
            ],
        ),
        ("integer", 1),
        ("subclass", SubclassedBindingRef("production-runtime", "v1")),
    ],
)
def test_d1_11_through_d1_17_inexact_inputs_fail_closed(label, value):
    with pytest.raises((TypeError, ValueError)):
        RuntimeBindingDeploymentConfiguration(runtime_binding_ref=value)


def test_d1_18_and_d1_19_required_field_has_no_omitted_value():
    signature = inspect.signature(RuntimeBindingDeploymentConfiguration)
    parameter = signature.parameters["runtime_binding_ref"]

    assert parameter.default is inspect.Parameter.empty
    with pytest.raises(TypeError):
        RuntimeBindingDeploymentConfiguration()


@pytest.mark.parametrize(
    ("binding_id", "binding_version"),
    [
        ("", "v1"),
        (" ", "v1"),
        ("production-runtime", ""),
        ("production-runtime", " "),
        ("x" * 257, "v1"),
        ("production-runtime", "x" * 257),
        (1, "v1"),
        ("production-runtime", 1),
    ],
)
def test_malformed_exact_ref_fields_fail_in_ref_contract(binding_id, binding_version):
    with pytest.raises((TypeError, ValueError)):
        RuntimeCanonicalAuthorityBindingRef(binding_id, binding_version)


def test_d1_20_through_d1_25_static_production_boundaries():
    forbidden_tokens = (
        "fallback",
        "default",
        "latest",
        "current",
        "active",
        "first",
        "best",
        "alias",
        "discover",
        "scan",
        "getenv",
        "environ",
        "argparse",
        "yaml",
        "toml",
        "repository",
        "resolve",
        "admit",
        "candidate",
        "supersede",
        "retire",
        "write",
    )
    source = "\n".join(
        path.read_text(encoding="utf-8") for path in PRODUCTION_PATHS
    )
    for token in forbidden_tokens:
        assert token not in source
