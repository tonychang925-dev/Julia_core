"""Atomic durable PersonaSelfBinding lineage storage and governance."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from julia_core.persona_self_binding.contracts import (
    GovernanceEventType,
    GovernanceProvenanceEvent,
    PersonaSelfBinding,
    PersonaSelfBindingContractError,
    PersonaSelfBindingErrorCode,
    PersonaSelfBindingLifecycle,
    SupersessionContract,
)


DURABLE_SCHEMA_VERSION = "julia_core.persona_self_binding.durable.v1"
STORE_MARKER = ".julia-core-persona-self-binding-store-v1"


@dataclass(frozen=True, slots=True)
class PersonaSelfBindingRecord:
    binding: PersonaSelfBinding
    object_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "binding": self.binding.to_dict(),
            "object_digest": self.object_digest,
        }


@dataclass(frozen=True, slots=True)
class PersonaSelfBindingInventory:
    lineages: tuple[dict[str, Any], ...]
    active_object_digest: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lineages": [item for item in self.lineages],
            "active_object_digest": self.active_object_digest,
        }


class PersonaSelfBindingStore:
    """Immutable-record lineage store with atomic whole-lineage replacement."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self._require_store()

    @classmethod
    def create(cls, root: Path) -> PersonaSelfBindingStore:
        root = Path(root)
        marker = root / STORE_MARKER
        if root.exists():
            if not root.is_dir():
                raise PersonaSelfBindingContractError(
                    PersonaSelfBindingErrorCode.PSB_STORE_CORRUPT,
                    "PersonaSelfBinding store root must be a directory",
                    path=str(root),
                )
            if any(root.iterdir()):
                raise PersonaSelfBindingContractError(
                    PersonaSelfBindingErrorCode.PSB_STORE_CORRUPT,
                    "PersonaSelfBinding store creation requires an empty root",
                    path=str(root),
                )
        else:
            root.mkdir(parents=True)
        (root / "lineages").mkdir()
        (root / "quarantine").mkdir()
        marker.write_text(
            json.dumps(
                {"schema_version": DURABLE_SCHEMA_VERSION},
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )
        return cls(root)

    def store_proposed(
        self,
        binding: PersonaSelfBinding,
    ) -> PersonaSelfBindingRecord:
        if type(binding) is not PersonaSelfBinding:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_SCHEMA_INVALID,
                "proposed value must be an exact PersonaSelfBinding",
            )
        if binding.lifecycle_status is not PersonaSelfBindingLifecycle.DRAFT:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_ILLEGAL_TRANSITION,
                "initial durable storage requires a DRAFT binding",
            )
        if not binding.governance_provenance:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_GOVERNANCE_EVENT_INVALID,
                "initial durable storage requires governance provenance",
            )
        if (
            binding.governance_provenance[-1].event_type
            is not GovernanceEventType.PROPOSE_BINDING
        ):
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_ILLEGAL_TRANSITION,
                "initial governance event must be PROPOSE_BINDING",
            )
        self._require_unique_lineage(binding)
        record = PersonaSelfBindingRecord(binding, binding.digest())
        snapshot = {
            "schema_version": DURABLE_SCHEMA_VERSION,
            "lineage_id": binding.lineage_id,
            "records": [record.to_dict()],
            "active_object_digest": None,
        }
        path = self._lineage_path(binding.lineage_id)
        if path.exists():
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_LINEAGE_BROKEN,
                "lineage already exists",
                path=str(path),
            )
        self._validate_snapshot(snapshot, path)
        self._atomic_write(path, snapshot)
        return record

    def apply_transition(
        self,
        object_digest: str,
        event_type: GovernanceEventType,
        *,
        event_id: str,
        actor: str,
        reason: str,
        occurred_at: str,
        successor: PersonaSelfBinding | None = None,
        successor_event_id: str | None = None,
    ) -> PersonaSelfBindingRecord:
        if type(event_type) is not GovernanceEventType:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_GOVERNANCE_EVENT_INVALID,
                "transition event must be an exact GovernanceEventType",
            )
        current_record, snapshot, path = self._record_by_digest(object_digest)
        current = current_record.binding
        event = GovernanceProvenanceEvent(
            event_id=event_id,
            event_type=event_type,
            actor=actor,
            reason=reason,
            occurred_at=occurred_at,
        )
        records = list(snapshot["records"])

        if event_type in {
            GovernanceEventType.REBIND_AUTHORITY_VERSION,
            GovernanceEventType.SUPERSEDE_BINDING,
        }:
            if current.lifecycle_status is not (
                PersonaSelfBindingLifecycle.ADMITTED_ACTIVE
            ):
                raise PersonaSelfBindingContractError(
                    PersonaSelfBindingErrorCode.PSB_ILLEGAL_TRANSITION,
                    "successor transitions require an ADMITTED_ACTIVE predecessor",
                    path=str(path),
                    object_digest=object_digest,
                )
            if type(successor) is not PersonaSelfBinding:
                raise PersonaSelfBindingContractError(
                    PersonaSelfBindingErrorCode.PSB_PREDECESSOR_MISMATCH,
                    "successor transitions require an exact successor binding",
                    path=str(path),
                    object_digest=object_digest,
                )
            self._validate_successor(current, successor)
            old_successor = SupersessionContract(
                successor.binding_id, successor.binding_version
            )
            historical = replace(
                current,
                lifecycle_status=PersonaSelfBindingLifecycle.ADMITTED_SUPERSEDED,
                supersession=old_successor,
                governance_provenance=(*current.governance_provenance, event),
            )
            successor_event = GovernanceProvenanceEvent(
                event_id=event_id if successor_event_id is None else successor_event_id,
                event_type=event_type,
                actor=actor,
                reason=reason,
                occurred_at=occurred_at,
            )
            activated_successor = replace(
                successor,
                lifecycle_status=PersonaSelfBindingLifecycle.ADMITTED_ACTIVE,
                governance_provenance=(
                    *successor.governance_provenance,
                    successor_event,
                ),
            )
            historical_record = PersonaSelfBindingRecord(
                historical, historical.digest()
            )
            successor_record = PersonaSelfBindingRecord(
                activated_successor, activated_successor.digest()
            )
            candidate = {
                **snapshot,
                "records": [
                    *records,
                    historical_record.to_dict(),
                    successor_record.to_dict(),
                ],
                "active_object_digest": successor_record.object_digest,
            }
            self._validate_snapshot(candidate, path)
            self._assert_no_conflicting_active(candidate, path)
            self._atomic_write(path, candidate)
            return successor_record

        legal_targets = _NORMAL_TRANSITIONS.get(current.lifecycle_status, frozenset())
        if event_type not in legal_targets or successor is not None:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_ILLEGAL_TRANSITION,
                f"{current.lifecycle_status.value} does not permit "
                f"{event_type.value}",
                path=str(path),
                object_digest=object_digest,
            )
        target = _TARGET_BY_EVENT[event_type]
        updated = replace(
            current,
            lifecycle_status=target,
            governance_provenance=(*current.governance_provenance, event),
        )
        updated_record = PersonaSelfBindingRecord(updated, updated.digest())
        candidate = {
            **snapshot,
            "records": [*records, updated_record.to_dict()],
            "active_object_digest": (
                updated_record.object_digest
                if target is PersonaSelfBindingLifecycle.ADMITTED_ACTIVE
                else (
                    None
                    if current.lifecycle_status
                    is PersonaSelfBindingLifecycle.ADMITTED_ACTIVE
                    else snapshot["active_object_digest"]
                )
            ),
        }
        self._validate_snapshot(candidate, path)
        if target is PersonaSelfBindingLifecycle.ADMITTED_ACTIVE:
            self._assert_no_conflicting_active(candidate, path)
        self._atomic_write(path, candidate)
        return updated_record

    def load_lineage(self, lineage_id: str) -> tuple[PersonaSelfBindingRecord, ...]:
        path = self._lineage_path(lineage_id)
        if not path.is_file():
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_LINEAGE_BROKEN,
                "lineage snapshot is missing",
                path=str(path),
            )
        snapshot = self._read_snapshot(path)
        return tuple(
            PersonaSelfBindingRecord(
                PersonaSelfBinding.from_mapping(item["binding"]),
                item["object_digest"],
            )
            for item in snapshot["records"]
        )

    def resolve_active(
        self, persona_self_id: str | None = None
    ) -> PersonaSelfBindingRecord:
        snapshots = self._load_all_snapshots()
        active = [
            record
            for snapshot in snapshots
            for record in self._current_records(snapshot)
            if record.binding.lifecycle_status
            is PersonaSelfBindingLifecycle.ADMITTED_ACTIVE
        ]
        if persona_self_id is not None:
            active = [
                record
                for record in active
                if record.binding.persona_self_id == persona_self_id
            ]
        if not active:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_NO_ACTIVE_BINDING,
                "no governed ADMITTED_ACTIVE PersonaSelfBinding exists",
            )
        if len(active) > 1:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_DUPLICATE_ACTIVE_BINDING,
                "multiple ADMITTED_ACTIVE PersonaSelfBinding records exist",
                object_digest=active[0].object_digest,
            )
        return active[0]

    def inventory(self) -> PersonaSelfBindingInventory:
        snapshots = self._load_all_snapshots()
        lineages = []
        active_digests = []
        for snapshot in snapshots:
            current_records = self._current_records(snapshot)
            active = [
                record
                for record in current_records
                if record.binding.lifecycle_status
                is PersonaSelfBindingLifecycle.ADMITTED_ACTIVE
            ]
            active_digests.extend(record.object_digest for record in active)
            records = self._snapshot_records(snapshot)
            by_digest = {record.object_digest: record for record in records}
            lineages.append(
                {
                    "lineage_id": snapshot["lineage_id"],
                    "binding_ids": sorted(
                        {record.binding.binding_id for record in records}
                    ),
                    "versions": sorted(
                        {record.binding.binding_version for record in records}
                    ),
                    "lifecycle_states": sorted(
                        {
                            record.binding.lifecycle_status.value
                            for record in current_records
                        }
                    ),
                    "active_object_digest": (
                        active[0].object_digest if len(active) == 1 else None
                    ),
                    "records": [
                        {
                            "binding_id": record.binding.binding_id,
                            "binding_version": record.binding.binding_version,
                            "lifecycle_status": (record.binding.lifecycle_status.value),
                            "predecessor_binding_id": (
                                record.binding.predecessor_binding_id
                            ),
                            "predecessor_binding_version": (
                                record.binding.predecessor_binding_version
                            ),
                            "successor_binding_id": (
                                record.binding.supersession.successor_binding_id
                            ),
                            "successor_binding_version": (
                                record.binding.supersession.successor_binding_version
                            ),
                            "governance_event_ids": [
                                event.event_id
                                for event in record.binding.governance_provenance
                            ],
                            "object_digest": record.object_digest,
                        }
                        for record in sorted(
                            records,
                            key=lambda item: (
                                item.binding.binding_id,
                                _version_number(item.binding.binding_version),
                                item.object_digest,
                            ),
                        )
                    ],
                    "declared_active_object_digest": (snapshot["active_object_digest"]),
                }
            )
            if len(active) == 1:
                expected = by_digest.get(snapshot["active_object_digest"])
                if expected is None or expected.binding.lifecycle_status is not (
                    PersonaSelfBindingLifecycle.ADMITTED_ACTIVE
                ):
                    raise PersonaSelfBindingContractError(
                        PersonaSelfBindingErrorCode.PSB_STORE_CORRUPT,
                        "active index does not identify the current active record",
                    )
        if len(active_digests) > 1:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_DUPLICATE_ACTIVE_BINDING,
                "multiple active PersonaSelfBinding records exist",
            )
        lineages.sort(key=lambda item: item["lineage_id"])
        return PersonaSelfBindingInventory(
            tuple(lineages), active_digests[0] if active_digests else None
        )

    def quarantine_evidence(
        self,
        *,
        relative_path: str,
        observed_digest: str,
        expected_digest: str | None,
        reason: str,
    ) -> Path:
        evidence = {
            "schema_version": DURABLE_SCHEMA_VERSION,
            "relative_path": relative_path,
            "observed_digest": observed_digest,
            "expected_digest": expected_digest,
            "reason": reason,
            "executable": False,
            "repaired": False,
            "synthetic_replacement_created": False,
        }
        name = hashlib.sha256(
            json.dumps(
                evidence, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ).encode("utf-8")
        ).hexdigest()
        path = self.root / "quarantine" / f"{name}.json"
        self._atomic_write(path, evidence)
        return path

    def _require_store(self) -> None:
        marker = self.root / STORE_MARKER
        if not self.root.is_dir() or not marker.is_file():
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_STORE_MISSING,
                "PersonaSelfBinding store marker is missing",
                path=str(self.root),
            )
        for directory in ("lineages", "quarantine"):
            if not (self.root / directory).is_dir():
                raise PersonaSelfBindingContractError(
                    PersonaSelfBindingErrorCode.PSB_STORE_CORRUPT,
                    f"PersonaSelfBinding store directory is missing: {directory}",
                    path=str(self.root / directory),
                )
        marker_data = self._read_json(marker)
        if marker_data != {"schema_version": DURABLE_SCHEMA_VERSION}:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_SCHEMA_VERSION_UNSUPPORTED,
                "PersonaSelfBinding store marker schema is unsupported",
                path=str(marker),
            )
        partial = sorted(
            [*(self.root / "lineages").glob("*.tmp")],
            key=lambda item: item.name,
        )
        if partial:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_PARTIAL_WRITE_DETECTED,
                "partial PersonaSelfBinding lineage write detected",
                path=str(partial[0]),
            )

    def _require_unique_lineage(self, binding: PersonaSelfBinding) -> None:
        for snapshot in self._load_all_snapshots():
            if snapshot["lineage_id"] == binding.lineage_id:
                raise PersonaSelfBindingContractError(
                    PersonaSelfBindingErrorCode.PSB_LINEAGE_BROKEN,
                    "lineage ID already exists",
                )
            if any(
                record.binding.binding_id == binding.binding_id
                for record in self._snapshot_records(snapshot)
            ):
                raise PersonaSelfBindingContractError(
                    PersonaSelfBindingErrorCode.PSB_LINEAGE_BROKEN,
                    "binding ID already exists",
                )

    def _lineage_path(self, lineage_id: str) -> Path:
        digest = hashlib.sha256(lineage_id.encode("utf-8")).hexdigest()
        return self.root / "lineages" / f"{digest}.json"

    def _load_all_snapshots(self) -> tuple[dict[str, Any], ...]:
        self._require_store()
        directory = self.root / "lineages"
        snapshots = []
        for path in sorted(directory.iterdir(), key=lambda item: item.name):
            if not path.is_file() or path.suffix != ".json":
                raise PersonaSelfBindingContractError(
                    PersonaSelfBindingErrorCode.PSB_STORE_CORRUPT,
                    "unexpected file in lineage directory",
                    path=str(path),
                )
            snapshot = self._read_snapshot(path)
            snapshots.append(snapshot)
        return tuple(snapshots)

    def _read_snapshot(self, path: Path) -> dict[str, Any]:
        data = self._read_json(path)
        self._validate_snapshot(data, path)
        return data

    def _read_json(self, path: Path) -> Any:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_STORE_CORRUPT,
                "PersonaSelfBinding JSON is unreadable",
                path=str(path),
            ) from error
        if not isinstance(data, dict):
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_STORE_CORRUPT,
                "PersonaSelfBinding JSON root must be an object",
                path=str(path),
            )
        return data

    def _snapshot_records(
        self, snapshot: dict[str, Any]
    ) -> tuple[PersonaSelfBindingRecord, ...]:
        return tuple(
            PersonaSelfBindingRecord(
                PersonaSelfBinding.from_mapping(item["binding"]),
                item["object_digest"],
            )
            for item in snapshot["records"]
        )

    def _record_by_digest(
        self, object_digest: str
    ) -> tuple[PersonaSelfBindingRecord, dict[str, Any], Path]:
        for snapshot in self._load_all_snapshots():
            for record in self._snapshot_records(snapshot):
                if record.object_digest == object_digest:
                    return (
                        record,
                        snapshot,
                        self._lineage_path(snapshot["lineage_id"]),
                    )
        raise PersonaSelfBindingContractError(
            PersonaSelfBindingErrorCode.PSB_LINEAGE_BROKEN,
            "object digest is not present in the durable store",
            object_digest=object_digest,
        )

    def _validate_snapshot(self, snapshot: dict[str, Any], path: Path) -> None:
        if set(snapshot) != {
            "schema_version",
            "lineage_id",
            "records",
            "active_object_digest",
        }:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_STORE_CORRUPT,
                "lineage snapshot fields do not exactly match the schema",
                path=str(path),
            )
        if snapshot["schema_version"] != DURABLE_SCHEMA_VERSION:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_SCHEMA_VERSION_UNSUPPORTED,
                "lineage snapshot schema is unsupported",
                path=str(path),
            )
        if type(snapshot["lineage_id"]) is not str or not snapshot["lineage_id"]:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_STORE_CORRUPT,
                "lineage ID must be a nonempty string",
                path=str(path),
            )
        if type(snapshot["records"]) is not list or not snapshot["records"]:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_LINEAGE_BROKEN,
                "lineage snapshot requires records",
                path=str(path),
            )
        records: list[PersonaSelfBindingRecord] = []
        seen_digests: set[str] = set()
        for item in snapshot["records"]:
            if not isinstance(item, dict) or set(item) != {
                "binding",
                "object_digest",
            }:
                raise PersonaSelfBindingContractError(
                    PersonaSelfBindingErrorCode.PSB_STORE_CORRUPT,
                    "durable record fields do not exactly match the schema",
                    path=str(path),
                )
            binding = PersonaSelfBinding.from_mapping(item["binding"])
            object_digest = item["object_digest"]
            actual_digest = binding.digest()
            if object_digest != actual_digest:
                raise PersonaSelfBindingContractError(
                    PersonaSelfBindingErrorCode.PSB_OBJECT_DIGEST_MISMATCH,
                    "PersonaSelfBinding canonical digest does not match",
                    path=str(path),
                    object_digest=object_digest,
                )
            if object_digest in seen_digests:
                raise PersonaSelfBindingContractError(
                    PersonaSelfBindingErrorCode.PSB_LINEAGE_BROKEN,
                    "duplicate immutable record digest",
                    path=str(path),
                    object_digest=object_digest,
                )
            seen_digests.add(object_digest)
            if binding.lineage_id != snapshot["lineage_id"]:
                raise PersonaSelfBindingContractError(
                    PersonaSelfBindingErrorCode.PSB_LINEAGE_BROKEN,
                    "binding lineage ID does not match its snapshot",
                    path=str(path),
                    object_digest=object_digest,
                )
            records.append(PersonaSelfBindingRecord(binding, object_digest))
        self._validate_record_chain(records, path)
        active_digest = snapshot["active_object_digest"]
        current = self._current_records(snapshot, records)
        active = [
            record
            for record in current
            if record.binding.lifecycle_status
            is PersonaSelfBindingLifecycle.ADMITTED_ACTIVE
        ]
        if len(active) > 1:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_DUPLICATE_ACTIVE_BINDING,
                "lineage contains multiple current active versions",
                path=str(path),
            )
        if active_digest is not None:
            if active_digest not in seen_digests:
                raise PersonaSelfBindingContractError(
                    PersonaSelfBindingErrorCode.PSB_LINEAGE_BROKEN,
                    "active digest does not reference a retained record",
                    path=str(path),
                    object_digest=active_digest,
                )
            if len(active) != 1 or active[0].object_digest != active_digest:
                raise PersonaSelfBindingContractError(
                    PersonaSelfBindingErrorCode.PSB_LINEAGE_BROKEN,
                    "active index does not match governed lifecycle state",
                    path=str(path),
                    object_digest=active_digest,
                )
        elif active:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_LINEAGE_BROKEN,
                "active record exists without an active index",
                path=str(path),
                object_digest=active[0].object_digest,
            )

    def _validate_record_chain(
        self, records: list[PersonaSelfBindingRecord], path: Path
    ) -> None:
        latest_by_version: dict[str, PersonaSelfBindingRecord] = {}
        previous_for_version: dict[str, PersonaSelfBindingRecord | None] = {}
        for record in records:
            binding = record.binding
            version = binding.binding_version
            previous = previous_for_version.get(version)
            if previous is not None:
                if previous.binding.binding_id != binding.binding_id:
                    raise PersonaSelfBindingContractError(
                        PersonaSelfBindingErrorCode.PSB_LINEAGE_BROKEN,
                        "binding ID changed within a semantic version",
                        path=str(path),
                    )
                previous_events = previous.binding.governance_provenance
                current_events = binding.governance_provenance
                if current_events[: len(previous_events)] != previous_events:
                    raise PersonaSelfBindingContractError(
                        PersonaSelfBindingErrorCode.PSB_LINEAGE_BROKEN,
                        "governance history was not append-only",
                        path=str(path),
                    )
            previous_for_version[version] = record
            latest_by_version[version] = record
            if binding.predecessor_binding_version is not None:
                predecessor = latest_by_version.get(binding.predecessor_binding_version)
                if predecessor is None:
                    raise PersonaSelfBindingContractError(
                        PersonaSelfBindingErrorCode.PSB_PREDECESSOR_MISMATCH,
                        "predecessor version is missing from the lineage",
                        path=str(path),
                        object_digest=record.object_digest,
                    )
                if (
                    predecessor.binding.binding_id != binding.predecessor_binding_id
                    or predecessor.binding.lineage_id != binding.lineage_id
                ):
                    raise PersonaSelfBindingContractError(
                        PersonaSelfBindingErrorCode.PSB_PREDECESSOR_MISMATCH,
                        "predecessor identity does not match the successor",
                        path=str(path),
                        object_digest=record.object_digest,
                    )
            elif _version_number(version) != 1:
                raise PersonaSelfBindingContractError(
                    PersonaSelfBindingErrorCode.PSB_PREDECESSOR_MISMATCH,
                    "noninitial version has no predecessor",
                    path=str(path),
                    object_digest=record.object_digest,
                )
        for version, record in latest_by_version.items():
            successor_version = record.binding.supersession.successor_binding_version
            if (
                successor_version is not None
                and successor_version not in latest_by_version
            ):
                raise PersonaSelfBindingContractError(
                    PersonaSelfBindingErrorCode.PSB_LINEAGE_BROKEN,
                    "supersession successor is missing",
                    path=str(path),
                    object_digest=record.object_digest,
                )

    def _validate_successor(
        self,
        current: PersonaSelfBinding,
        successor: PersonaSelfBinding,
    ) -> None:
        if (
            successor.predecessor_binding_id != current.binding_id
            or successor.predecessor_binding_version != current.binding_version
            or successor.lineage_id != current.lineage_id
            or successor.binding_id != current.binding_id
            or _version_number(successor.binding_version)
            != _version_number(current.binding_version) + 1
        ):
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_PREDECESSOR_MISMATCH,
                "successor predecessor identity is invalid",
            )
        if successor.lifecycle_status not in {
            PersonaSelfBindingLifecycle.DRAFT,
            PersonaSelfBindingLifecycle.GOVERNANCE_REVIEW,
        }:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_ILLEGAL_TRANSITION,
                "successor must be a governed candidate before activation",
            )

    def _assert_no_conflicting_active(
        self, candidate: dict[str, Any], path: Path
    ) -> None:
        current = self._current_records(candidate)
        active = [
            record
            for record in current
            if record.binding.lifecycle_status
            is PersonaSelfBindingLifecycle.ADMITTED_ACTIVE
        ]
        if len(active) != 1:
            raise PersonaSelfBindingContractError(
                PersonaSelfBindingErrorCode.PSB_DUPLICATE_ACTIVE_BINDING,
                "candidate lineage must retain exactly one active record",
                path=str(path),
            )
        all_snapshots = [
            snapshot
            for snapshot in self._load_all_snapshots()
            if snapshot["lineage_id"] != candidate["lineage_id"]
        ]
        for snapshot in all_snapshots:
            for record in self._current_records(snapshot):
                if (
                    record.binding.lifecycle_status
                    is PersonaSelfBindingLifecycle.ADMITTED_ACTIVE
                    and record.binding.persona_self_id
                    == active[0].binding.persona_self_id
                ):
                    raise PersonaSelfBindingContractError(
                        PersonaSelfBindingErrorCode.PSB_DUPLICATE_ACTIVE_BINDING,
                        "persona already has an active governed binding",
                        path=str(path),
                    )

    def _current_records(
        self,
        snapshot: dict[str, Any],
        supplied: tuple[PersonaSelfBindingRecord, ...] | None = None,
    ) -> tuple[PersonaSelfBindingRecord, ...]:
        records = supplied or self._snapshot_records(snapshot)
        current: dict[str, PersonaSelfBindingRecord] = {}
        for record in records:
            current[record.binding.binding_version] = record
        return tuple(current[key] for key in sorted(current, key=_version_number))

    def _atomic_write(self, path: Path, value: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=path.name, suffix=".tmp", dir=path.parent
        )
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_path, path)
            directory_descriptor = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory_descriptor)
            finally:
                os.close(directory_descriptor)
            read_back = self._read_json(path)
            if read_back != value:
                raise PersonaSelfBindingContractError(
                    PersonaSelfBindingErrorCode.PSB_PARTIAL_WRITE_DETECTED,
                    "atomic replacement read-back did not match",
                    path=str(path),
                )
        finally:
            if temporary_path.exists():
                temporary_path.unlink()


_NORMAL_TRANSITIONS: dict[
    PersonaSelfBindingLifecycle, frozenset[GovernanceEventType]
] = {
    PersonaSelfBindingLifecycle.DRAFT: frozenset(
        {
            GovernanceEventType.REVIEW_BINDING,
            GovernanceEventType.REJECT_BINDING,
            GovernanceEventType.ADMIT_AND_ACTIVATE,
            GovernanceEventType.QUARANTINE_CORRUPTION,
        }
    ),
    PersonaSelfBindingLifecycle.GOVERNANCE_REVIEW: frozenset(
        {
            GovernanceEventType.REJECT_BINDING,
            GovernanceEventType.ADMIT_AND_ACTIVATE,
            GovernanceEventType.QUARANTINE_CORRUPTION,
        }
    ),
    PersonaSelfBindingLifecycle.ADMITTED_ACTIVE: frozenset(
        {
            GovernanceEventType.REVOKE_INVALID,
            GovernanceEventType.QUARANTINE_CORRUPTION,
        }
    ),
    PersonaSelfBindingLifecycle.ADMITTED_SUPERSEDED: frozenset(
        {
            GovernanceEventType.RETIRE_HISTORICAL,
            GovernanceEventType.QUARANTINE_CORRUPTION,
        }
    ),
}

_TARGET_BY_EVENT: dict[GovernanceEventType, PersonaSelfBindingLifecycle] = {
    GovernanceEventType.REVIEW_BINDING: (PersonaSelfBindingLifecycle.GOVERNANCE_REVIEW),
    GovernanceEventType.REJECT_BINDING: PersonaSelfBindingLifecycle.REJECTED,
    GovernanceEventType.ADMIT_AND_ACTIVATE: (
        PersonaSelfBindingLifecycle.ADMITTED_ACTIVE
    ),
    GovernanceEventType.REVOKE_INVALID: PersonaSelfBindingLifecycle.REVOKED_INVALID,
    GovernanceEventType.RETIRE_HISTORICAL: (
        PersonaSelfBindingLifecycle.RETIRED_HISTORICAL
    ),
    GovernanceEventType.QUARANTINE_CORRUPTION: (
        PersonaSelfBindingLifecycle.CORRUPT_QUARANTINED
    ),
}


def _version_number(value: str) -> int:
    return int(value[1:])


__all__ = [
    "DURABLE_SCHEMA_VERSION",
    "PersonaSelfBindingInventory",
    "PersonaSelfBindingRecord",
    "PersonaSelfBindingStore",
]
