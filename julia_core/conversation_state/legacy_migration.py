"""CM-R2-C — Legacy conversations.json → StorageV2 migration.

READ-ONLY source. WRITE-ONLY to staging target.
Deterministic. Verifiable. Source mutation: 0.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path

from julia_core.conversation_state.storage_v2_repository import StorageV2ConversationRepository


def _digest_normalized(convs: list[dict]) -> str:
    """Deterministic canonical digest for verification."""
    # Sort by conversation_id for deterministic output
    normalized = []
    for c in sorted(convs, key=lambda x: x["conversation_id"]):
        nc = {
            "conversation_id": c["conversation_id"],
            "title": c.get("title", ""),
            "created_at": c.get("created_at", ""),
            "updated_at": c.get("updated_at", ""),
            "message_count": len(c["messages"]),
            "messages": [],
        }
        for m in c["messages"]:
            nc["messages"].append({
                "message_id": m["message_id"],
                "turn_id": m["turn_id"],
                "role": m["role"],
                "modality": m.get("modality", "text"),
                "content": m["content"],
                "status": m.get("status", "completed"),
                "created_at": m.get("created_at", ""),
            })
        normalized.append(nc)
    payload = json.dumps(normalized, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def _normalize_legacy(source_path: Path) -> list[dict]:
    """Read legacy conversations.json into normalized form."""
    data = json.loads(source_path.read_text())
    if not isinstance(data, list):
        raise ValueError("Legacy source is not a conversation array")
    result = []
    for item in data:
        conv = {
            "conversation_id": item["id"],
            "title": item.get("title", ""),
            "created_at": item.get("created_at", ""),
            "updated_at": item.get("updated_at", ""),
            "message_count": len(item.get("messages", [])),
            "messages": [],
        }
        for m in item.get("messages", []):
            conv["messages"].append({
                "message_id": m.get("message_id", ""),
                "turn_id": m.get("turn_id", ""),
                "role": m.get("role", "user"),
                "modality": m.get("modality", "text"),
                "content": m.get("content", ""),
                "status": m.get("status", "completed"),
                "created_at": m.get("created_at", ""),
            })
        result.append(conv)
    return result


def _normalize_v2(repo: StorageV2ConversationRepository) -> list[dict]:
    """Read StorageV2 into same normalized form."""
    result = []
    for session in repo.list_all():
        conv = {
            "conversation_id": session.id,
            "title": session.title,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "message_count": len(session.messages),
            "messages": [],
        }
        for m in session.messages:
            conv["messages"].append({
                "message_id": m.message_id,
                "turn_id": m.turn_id,
                "role": m.role,
                "modality": m.modality,
                "content": m.content,
                "status": m.status,
                "created_at": m.created_at,
            })
        result.append(conv)
    return result


def migrate_legacy_conversations(
    source_path: str | Path,
    target_root: str | Path,
) -> dict:
    """Migrate legacy conversations.json to StorageV2.

    Returns a migration report dict. Source is read-only.
    Target is a staging directory (must not exist or be empty).
    """
    source = Path(source_path)
    target = Path(target_root)

    if not source.exists():
        return {"error": "source_not_found", "source": str(source)}

    # Source checksum before
    source_sha256_before = hashlib.sha256(source.read_bytes()).hexdigest()

    # Read legacy
    try:
        legacy_norm = _normalize_legacy(source)
    except (json.JSONDecodeError, ValueError, KeyError) as exc:
        return {"status": "REJECTED", "error": f"source_read_failed: {exc}",
                "source": str(source)}
    legacy_digest = _digest_normalized(legacy_norm)
    source_count = len(legacy_norm)
    source_msgs = sum(c["message_count"] for c in legacy_norm)

    # Migrate
    target.mkdir(parents=True, exist_ok=True)
    repo = StorageV2ConversationRepository(target)

    per_conv = []
    errors = []

    for conv in legacy_norm:
        cid = conv["conversation_id"]
        try:
            repo.create_with_id(cid, conv["title"])
            # Preserve legacy timestamps
            meta_path = repo._meta_path(cid)
            if meta_path.exists():
                meta = json.loads(meta_path.read_text())
                meta["created_at"] = conv.get("created_at", meta["created_at"])
                meta["updated_at"] = conv.get("updated_at", meta["updated_at"])
                meta_path.write_text(json.dumps(meta, indent=2))
            repo._cat.execute(
                "UPDATE conversations SET created_at=?, updated_at=? WHERE id=?",
                (conv.get("created_at", ""), conv.get("updated_at", ""), cid),
            )
            repo._cat.commit()
            for m in conv["messages"]:
                seq = repo._next_sequence(cid)
                msg = {
                    "schema_version": 2, "sequence": seq,
                    "message_id": m["message_id"], "conversation_id": cid,
                    "turn_id": m["turn_id"], "role": m["role"],
                    "modality": m["modality"], "content": m["content"],
                    "status": m["status"], "created_at": m["created_at"],
                }
                repo._write_canonical_message(cid, msg)
                repo._update_catalog_after_append(cid, msg)
            # Restore legacy timestamps (overwritten by append)
            repo._cat.execute(
                "UPDATE conversations SET created_at=?, updated_at=? WHERE id=?",
                (conv.get("created_at", ""), conv.get("updated_at", ""), cid),
            )
            repo._cat.commit()
            per_conv.append({"conversation_id": cid, "status": "migrated",
                             "message_count": conv["message_count"]})
        except Exception as exc:
            errors.append({"conversation_id": cid, "error": str(exc)})
            per_conv.append({"conversation_id": cid, "status": "failed",
                             "error": str(exc)})

    # If any errors, abort
    if errors:
        repo.close()
        return {
            "status": "REJECTED",
            "source": str(source),
            "source_sha256_before": source_sha256_before,
            "source_count": source_count,
            "source_messages": source_msgs,
            "errors": errors,
            "per_conversation": per_conv,
        }

    # Verify
    v2_norm = _normalize_v2(repo)
    v2_digest = _digest_normalized(v2_norm)
    target_count = len(v2_norm)
    target_msgs = sum(c["message_count"] for c in v2_norm)

    # Per-conversation detail check
    for c in per_conv:
        legacy_conv = next((x for x in legacy_norm if x["conversation_id"] == c["conversation_id"]), None)
        v2_conv = next((x for x in v2_norm if x["conversation_id"] == c["conversation_id"]), None)
        if legacy_conv and v2_conv:
            if legacy_conv["message_count"] == v2_conv["message_count"]:
                c["verify"] = "MATCH"
            else:
                c["verify"] = "MISMATCH"
                c["legacy_count"] = legacy_conv["message_count"]
                c["v2_count"] = v2_conv["message_count"]

    # Rebuild catalog test
    repo.close()
    cat_path = target / "catalog.sqlite"
    if cat_path.exists():
        os.remove(cat_path)
    repo2 = StorageV2ConversationRepository(target)
    v2_after_rebuild = _normalize_v2(repo2)
    rebuild_digest = _digest_normalized(v2_after_rebuild)
    repo2.close()

    # Source checksum after (must be unchanged)
    source_sha256_after = hashlib.sha256(source.read_bytes()).hexdigest()

    digest_match = legacy_digest == v2_digest
    rebuild_ok = legacy_digest == rebuild_digest
    source_unchanged = source_sha256_before == source_sha256_after

    return {
        "status": "CUTOVER_READY" if (digest_match and rebuild_ok and source_unchanged) else "REJECTED",
        "source": str(source),
        "target": str(target),
        "source_sha256": source_sha256_before,
        "source_unchanged": source_unchanged,
        "legacy_digest": legacy_digest,
        "v2_digest": v2_digest,
        "rebuild_digest": rebuild_digest,
        "digest_match": digest_match,
        "rebuild_ok": rebuild_ok,
        "source_count": source_count,
        "target_count": target_count,
        "source_messages": source_msgs,
        "target_messages": target_msgs,
        "per_conversation": per_conv,
    }
