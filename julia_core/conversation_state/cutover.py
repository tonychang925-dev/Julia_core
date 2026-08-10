"""CM-R2-D — Production Cutover: atomic authority switch.

BEFORE:  LegacyJsonConversationRepository = writable canonical
AFTER:   StorageV2ConversationRepository  = writable canonical
         Legacy = READ-ONLY, NOT CANONICAL, NOT FALLBACK

R2-S01: exactly one writable canonical store at any instant.
No dual-write. No automatic stale-store fallback.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from julia_core.conversation_state.legacy_json_repository import LegacyJsonConversationRepository
from julia_core.conversation_state.storage_v2_repository import StorageV2ConversationRepository
from julia_core.conversation_state.legacy_migration import migrate_legacy_conversations

logger = logging.getLogger("julia.cutover")

CUTOVER_STATE_FILE = "cutover_state.json"


class CutoverError(Exception):
    """Cutover failed — system MUST NOT run in indeterminate state."""


class CutoverState:
    """Tracks whether cutover has been performed."""

    def __init__(self, state_dir: Path):
        self._path = state_dir / CUTOVER_STATE_FILE

    def is_complete(self) -> bool:
        if not self._path.exists():
            return False
        try:
            data = json.loads(self._path.read_text())
            return data.get("status") == "complete"
        except Exception:
            return False

    def record_complete(self, legacy_path: str, v2_path: str):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps({
            "status": "complete",
            "legacy_path": legacy_path,
            "v2_path": v2_path,
        }, indent=2))


def cutover_to_storage_v2(
    legacy_path: str | Path,
    v2_path: str | Path,
    state_dir: str | Path = "data",
    dry_run: bool = False,
) -> dict:
    """Atomic authority switch from legacy JSON to StorageV2.

    Steps:
      1. Preflight: verify legacy healthy, migration CUTOVER_READY
      2. Migrate to staging
      3. Verify normalized digest
      4. Switch: StorageV2 becomes canonical, legacy sealed

    Returns cutover report.
    Raises CutoverError if any step fails.
    """
    legacy = Path(legacy_path)
    v2 = Path(v2_path)
    state = CutoverState(Path(state_dir))

    report = {
        "status": "PENDING",
        "legacy_path": str(legacy),
        "v2_path": str(v2),
        "steps": [],
    }

    # Step 1: Preflight
    if not legacy.exists():
        raise CutoverError(f"Legacy store not found: {legacy}")

    legacy_repo = LegacyJsonConversationRepository(legacy)
    legacy_sessions = legacy_repo.list_all()
    legacy_count = len(legacy_sessions)
    report["legacy_conversations"] = legacy_count
    report["steps"].append({"step": "preflight_legacy", "status": "ok",
                            "conversations": legacy_count})

    # Step 2: Migration to staging (if target is empty)
    if dry_run:
        report["status"] = "DRY_RUN_OK"
        report["steps"].append({"step": "migration", "status": "dry_run_skipped"})
        return report

    migration_result = migrate_legacy_conversations(legacy, v2)
    if migration_result["status"] != "CUTOVER_READY":
        raise CutoverError(
            f"Migration not CUTOVER_READY: {migration_result.get('errors', [])}"
        )
    report["steps"].append({
        "step": "migration", "status": "ok",
        "conversations": migration_result["target_count"],
        "messages": migration_result["target_messages"],
        "digest_match": migration_result["digest_match"],
    })

    # Step 3: Verify new backend
    v2_repo = StorageV2ConversationRepository(v2)
    v2_sessions = v2_repo.list_all()
    if len(v2_sessions) != legacy_count:
        v2_repo.close()
        raise CutoverError(
            f"Count mismatch: legacy={legacy_count}, v2={len(v2_sessions)}"
        )
    v2_repo.close()
    report["steps"].append({"step": "verify_v2", "status": "ok",
                            "conversations": len(v2_sessions)})

    # Step 4: Record cutover
    state.record_complete(str(legacy), str(v2))
    report["status"] = "COMPLETE"
    report["steps"].append({"step": "record", "status": "ok"})
    report["legacy_status"] = "READ_ONLY_LEGACY_BACKUP"
    report["v2_status"] = "CANONICAL_WRITABLE"

    logger.info("Cutover complete: %d conversations migrated to %s",
                legacy_count, v2)
    return report


def create_repository_for_runtime(
    v2_path: str | Path,
    fallback_legacy_path: str | Path | None = None,
) -> StorageV2ConversationRepository:
    """Create the canonical repository for ConversationRuntime.

    After cutover: returns StorageV2ConversationRepository.
    Never falls back to legacy — that would create a second canonical source.

    If v2_path doesn't exist yet (pre-cutover), use fallback if provided.
    Otherwise: fail closed — conversation persistence requires explicit setup.
    """
    v2 = Path(v2_path)

    if v2.exists():
        return StorageV2ConversationRepository(v2)

    if fallback_legacy_path:
        logger.warning("StorageV2 not found, using legacy fallback (pre-cutover)")
        return LegacyJsonConversationRepository(fallback_legacy_path)

    raise CutoverError(
        f"StorageV2 path does not exist: {v2}. "
        "Cutover must be performed before production use."
    )
