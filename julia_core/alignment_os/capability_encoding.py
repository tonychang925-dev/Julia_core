"""C-09 governed capability encoding foundation (P3-CC I1b-2).

Encoder contract
================
This module implements the C-09 seam that converts the governed C-03
capability frame into provider-compatible capability *representations*.

Authority boundaries (frozen):
- Context OS decides WHAT governed capability information exists.
- Alignment (this encoder) decides HOW that same information is represented.
- Alignment does NOT choose tools, authorize tools, execute tools, or
  recompute availability.
- Input is the governed ``capability_frame["manifest_entries"]`` ONLY. This
  module never reads CapabilityRegistry / CapabilityManager /
  RuntimeCapabilityBridge / provider binding state and never calls
  ``provider.health()``. Those authorities are upstream of C-09.
- The encoder accepts NO user text. It performs NO semantic/keyword/topic
  filtering, ranking, or tool recommendation. Julia cognition remains the
  semantic selector.
- ``availability`` is immutable input: the encoder never promotes REGISTERED,
  never demotes AVAILABLE.
- ``permission_requirements`` is faithfully represented descriptive metadata;
  it is NOT an AuthorizationDecision and the encoder never evaluates
  PermissionPolicy.
- Encoding is deterministic: entries are ordered by ``capability_id``
  ascending and the digest is computed over the normalized representation.
- A requested representation that cannot be faithfully produced yields a
  structured ``REPRESENTATION_UNSUPPORTED`` diagnostic — never a silent
  omission, never an availability rewrite, never a fallback.

Encoder output is DERIVED REPRESENTATION, not canonical capability state.
Deleting/rebuilding it never changes Julia capability authority.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

# Representation modes this foundation can faithfully produce.
SUPPORTED_REPRESENTATION_MODES = frozenset({"structured", "text_protocol"})

# Source lineage marker: the only upstream capability information source.
_SOURCE_LINEAGE = "governed capability_frame"

# Full governed manifest field set (semantic fidelity contract).
_GOVERNED_MANIFEST_FIELDS = (
    "capability_id",
    "description",
    "input_schema",
    "output_schema",
    "side_effect_class",
    "permission_requirements",
    "idempotency_support",
    "latency_cost_hints",
    "data_sensitivity",
    "availability",
    "schema_version",
    "provenance",
)


@dataclass(frozen=True, slots=True)
class CapabilityEncodingResult:
    """Deterministic derived representation of the governed capability frame.

    ``descriptors`` are provider-neutral structured descriptors (one per
    admitted governed manifest entry, sorted by capability_id ascending).
    ``text`` carries the deterministic textual capability protocol rendering
    when ``representation_mode == "text_protocol"`` (else None).
    ``diagnostics`` carries structured representation diagnostics (e.g.
    REPRESENTATION_UNSUPPORTED); it never silently drops an entry.
    ``digest`` is a sha256 over the deterministic normalized representation.
    """

    representation_mode: str
    encoding_version: str
    source: str
    source_capability_ids: tuple[str, ...]
    descriptors: tuple[dict[str, Any], ...]
    text: str | None
    diagnostics: tuple[dict[str, Any], ...]
    digest: str


def _manifest_entries_from_frame(
    capability_frame: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Extract governed manifest entries + frame-level diagnostics.

    The only accepted logical source is ``capability_frame["manifest_entries"]``
    (I1b-1 governed projection). A frame missing that key is a representation
    input error surfaced as a structured diagnostic — never silently treated
    as an empty/legacy catalog.
    """
    entries = capability_frame.get("manifest_entries")
    if entries is None:
        return [], [
            {
                "code": "INVALID_CAPABILITY_FRAME",
                "reason": "capability_frame has no governed manifest_entries",
            }
        ]
    if not isinstance(entries, (list, tuple)):
        return [], [
            {
                "code": "INVALID_CAPABILITY_FRAME",
                "reason": "manifest_entries must be a sequence",
            }
        ]
    return list(entries), []


def _sorted_manifest_entries(
    entries: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Validate + deterministically order entries; surface invalid entries.

    Invalid entries (non-dict, or missing capability_id) are never silently
    omitted: they become an INVALID_MANIFEST_ENTRY diagnostic.
    """
    valid: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, Mapping):
            diagnostics.append(
                {
                    "code": "INVALID_MANIFEST_ENTRY",
                    "index": index,
                    "reason": "entry is not a mapping",
                }
            )
            continue
        capability_id = entry.get("capability_id")
        if not isinstance(capability_id, str) or not capability_id.strip():
            diagnostics.append(
                {
                    "code": "INVALID_MANIFEST_ENTRY",
                    "index": index,
                    "reason": "entry has no capability_id",
                }
            )
            continue
        valid.append(dict(entry))
    valid.sort(key=lambda entry: entry["capability_id"])
    return valid, diagnostics


def _structured_descriptor(entry: Mapping[str, Any]) -> dict[str, Any]:
    """Provider-neutral structured descriptor preserving governed semantics.

    Representation may differ from the frame serialization; meaning may not.
    Only the governed manifest fields are represented. No provider/transport
    field, no token/authorization field, no semantic-selection material.
    """
    descriptor: dict[str, Any] = {}
    for field in _GOVERNED_MANIFEST_FIELDS:
        descriptor[field] = dict(entry[field]) if isinstance(
            entry.get(field), Mapping
        ) else entry[field]
    return descriptor


def _render_text_protocol(
    descriptors: Sequence[Mapping[str, Any]],
) -> str:
    """Deterministic structural textual capability protocol.

    Structural description only (id, description, schemas, safety class,
    permission requirements, availability). It NEVER adds cognition
    instructions such as "you should use this tool when ..." / "best tool for
    ..." — that would recreate a semantic router.
    """
    if not descriptors:
        return ""
    blocks: list[str] = []
    for descriptor in descriptors:
        lines = [f"capability: {descriptor['capability_id']}"]
        lines.append(f"  description: {descriptor['description']}")
        lines.append(
            "  input_schema: "
            + json.dumps(descriptor["input_schema"], sort_keys=True, ensure_ascii=False)
        )
        lines.append(
            "  output_schema: "
            + json.dumps(descriptor["output_schema"], sort_keys=True, ensure_ascii=False)
        )
        lines.append(f"  side_effect_class: {descriptor['side_effect_class']}")
        lines.append(
            "  permission_requirements: "
            + json.dumps(
                list(descriptor["permission_requirements"]),
                sort_keys=True,
                ensure_ascii=False,
            )
        )
        lines.append(
            f"  idempotency_support: {descriptor['idempotency_support']}"
        )
        lines.append(f"  data_sensitivity: {descriptor['data_sensitivity']}")
        lines.append(f"  availability: {descriptor['availability']}")
        lines.append(f"  schema_version: {descriptor['schema_version']}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def _normalized_repr(
    *,
    representation_mode: str,
    encoding_version: str,
    descriptors: Sequence[Mapping[str, Any]],
) -> str:
    payload = json.dumps(
        [
            {
                **{k: sorted(v) if isinstance(v, (list, tuple)) else v
                   for k, v in descriptor.items()},
            }
            for descriptor in descriptors
        ],
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return json.dumps(
        {
            "source": _SOURCE_LINEAGE,
            "representation_mode": representation_mode,
            "encoding_version": encoding_version,
            "descriptors": payload,
        },
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )


def encode_capability_frame(
    capability_frame: Mapping[str, Any],
    *,
    representation_mode: str = "structured",
    encoding_version: str = "1.0",
) -> CapabilityEncodingResult:
    """Encode the governed capability frame into a provider-neutral form.

    ``representation_mode`` must be an explicit frozen adaptation-profile
    value ("structured" or "text_protocol"). The encoder never infers provider
    selection and never branches on provider identity strings. An unsupported
    mode yields a structured REPRESENTATION_UNSUPPORTED diagnostic with no
    descriptors and no text — never a silent fallback.
    """
    diagnostics: list[dict[str, Any]] = []

    if representation_mode not in SUPPORTED_REPRESENTATION_MODES:
        return CapabilityEncodingResult(
            representation_mode=representation_mode,
            encoding_version=encoding_version,
            source=_SOURCE_LINEAGE,
            source_capability_ids=(),
            descriptors=(),
            text=None,
            diagnostics=[
                {
                    "code": "REPRESENTATION_UNSUPPORTED",
                    "mode": representation_mode,
                    "reason": (
                        f"unsupported representation mode; supported="
                        f"{sorted(SUPPORTED_REPRESENTATION_MODES)}"
                    ),
                }
            ],
            digest="",
        )

    entries, frame_diagnostics = _manifest_entries_from_frame(capability_frame)
    diagnostics.extend(frame_diagnostics)

    valid_entries, entry_diagnostics = _sorted_manifest_entries(entries)
    diagnostics.extend(entry_diagnostics)

    descriptors = tuple(
        _structured_descriptor(entry) for entry in valid_entries
    )
    capability_ids = tuple(
        descriptor["capability_id"] for descriptor in descriptors
    )

    text: str | None = None
    if representation_mode == "text_protocol":
        text = _render_text_protocol(descriptors)

    digest_source = _normalized_repr(
        representation_mode=representation_mode,
        encoding_version=encoding_version,
        descriptors=descriptors,
    )
    digest = hashlib.sha256(digest_source.encode("utf-8")).hexdigest()

    return CapabilityEncodingResult(
        representation_mode=representation_mode,
        encoding_version=encoding_version,
        source=_SOURCE_LINEAGE,
        source_capability_ids=capability_ids,
        descriptors=descriptors,
        text=text,
        diagnostics=tuple(diagnostics),
        digest=digest,
    )
