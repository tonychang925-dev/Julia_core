"""M3.2.7.4 Deterministic Hypothesis Evaluator — EvidenceBundle → Evaluation.

No scores. No LLM. No 0.83 confidence.
SUPPORTED / PARTIAL / CONTRADICTED / INSUFFICIENT_EVIDENCE + decisive flag.
Reads typed L3 predicates from StrategyCard.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


class EvalStatus:
    SUPPORTED = "SUPPORTED"
    PARTIAL = "PARTIAL"
    CONTRADICTED = "CONTRADICTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


@dataclass
class PredicateResult:
    requirement_id: str
    metric: str
    expected: Any
    actual: Any
    satisfied: bool
    role: str = "core"


@dataclass
class HypothesisEvaluation:
    state: str
    status: str
    supported_by: list[str] = field(default_factory=list)
    contradicted_by: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    decisive: bool = False


class HypothesisEvaluator:
    """Evaluates StrategyCard hypotheses against EvidenceBundle."""

    def evaluate(self, state_entry: dict, evidence: dict[str, Any]) -> HypothesisEvaluation:
        state_name = state_entry["state"]
        predicates = state_entry.get("predicates", [])

        if not predicates:
            return HypothesisEvaluation(
                state=state_name,
                status="CARD_NOT_EXECUTABLE",
                missing=["no typed L3 predicates in StrategyCard"],
            )

        ev = HypothesisEvaluation(state=state_name, status=EvalStatus.SUPPORTED)

        for pred in predicates:
            req_id = pred["requirement_id"]
            item = evidence.get(req_id)
            if item is None:
                ev.missing.append(f"{req_id}: no evidence")
                continue

            if item.status in ("unavailable", "error"):
                ev.missing.append(f"{req_id}: {item.status}")
                continue
            if item.status == "insufficient_evidence":
                ev.missing.append(f"{req_id}: insufficient")
                continue

            actual = item.derived_value
            expected = pred.get("value")
            operator = pred.get("operator", "eq")
            role = pred.get("role", "core")
            path = pred.get("path")
            is_list_count = pred.get("is_list_count", False)

            # Check
            if is_list_count and isinstance(actual, list):
                result = _cmp(operator, len(actual), expected)
            elif path and isinstance(actual, dict):
                val = _resolve(actual, path)
                result = val is not None and _cmp(operator, val, expected)
            else:
                result = _cmp(operator, actual, expected)

            desc = f"{req_id}: {_fmt(actual)} {operator} {expected}"
            if result:
                ev.supported_by.append(desc)
            else:
                ev.contradicted_by.append(f"{desc} (got {_fmt(_resolve(actual, path) if path and isinstance(actual, dict) else actual)})")

        n_s, n_c, n_m = len(ev.supported_by), len(ev.contradicted_by), len(ev.missing)
        has_decisive = any(
            p.get("role") == "decisive" and _eval_pred(p, evidence) is False
            for p in predicates
        )

        if has_decisive or (n_c >= 2 and n_s == 0):
            ev.status = EvalStatus.CONTRADICTED
            ev.decisive = has_decisive
        elif n_c >= 1 and n_s == 0:
            ev.status = EvalStatus.CONTRADICTED
        elif n_c >= 2:
            ev.status = EvalStatus.CONTRADICTED
        elif n_c >= 1 and n_s >= 2:
            ev.status = EvalStatus.PARTIAL
        elif n_s >= 2 and n_m >= 2:
            ev.status = EvalStatus.PARTIAL
        elif n_s >= 2:
            ev.status = EvalStatus.SUPPORTED
        elif n_s >= 1 and n_c == 0:
            ev.status = EvalStatus.PARTIAL
        elif n_s == 0 and n_c == 0:
            ev.status = EvalStatus.INSUFFICIENT_EVIDENCE
        else:
            ev.status = EvalStatus.PARTIAL

        return ev

# ── Helpers ──

def _resolve(data, path):
    for part in path.split("."):
        if isinstance(data, dict) and part in data:
            data = data[part]
        else:
            return None
    return data

def _cmp(op, v, e):
    try:
        if op == "eq": return str(v) == str(e)
        if op == ">=": return float(v) >= float(e)
        if op == "<=": return float(v) <= float(e)
        if op == ">": return float(v) > float(e)
        if op == "<": return float(v) < float(e)
        if op == "in": return v in e
        if op == "!=": return str(v) != str(e)
    except (TypeError, ValueError):
        return False
    return False

def _eval_pred(pred, evidence) -> bool | None:
    """Evaluate one predicate. Returns: True(satisfied), False(contradicted), None(unknown/missing)."""
    item = evidence.get(pred["requirement_id"])
    if not item:
        return None
    if item.status in ("unavailable", "error", "insufficient_evidence"):
        return None
    actual = item.derived_value
    path = pred.get("path")
    if path and isinstance(actual, dict):
        actual = _resolve(actual, path)
        if actual is None:
            return None
    if pred.get("is_list_count") and isinstance(actual, list):
        actual = len(actual)
    return _cmp(pred.get("operator", "eq"), actual, pred.get("value"))

def _fmt(v):
    if isinstance(v, float): return f"{v:.3f}"
    return str(v)[:40]


__all__ = ["HypothesisEvaluator", "HypothesisEvaluation", "EvalStatus"]
