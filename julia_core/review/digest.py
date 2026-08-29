"""Stable digest helpers for review artifacts.

Digests bind review_id / candidate_id / candidate_sha to the exact ReviewBundle
payload end-to-end. A bundle digest mismatch is a Core-side semantic rejection
(no silent carry-over, no stale continuation).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def compute_text_digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def compute_bundle_digest(bundle: Any) -> str:
    payload = bundle.to_dict() if hasattr(bundle, "to_dict") else bundle
    return compute_text_digest(_canonical_json(payload))


def digests_equal(a: str, b: str) -> bool:
    """Constant-ish string equality for digest comparison."""
    if not isinstance(a, str) or not isinstance(b, str):
        return False
    return hashlib.sha256(a.encode("utf-8")).digest() == hashlib.sha256(b.encode("utf-8")).digest()


__all__ = ["compute_bundle_digest", "compute_text_digest", "digests_equal"]
