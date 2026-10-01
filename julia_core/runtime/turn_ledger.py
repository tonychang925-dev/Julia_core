"""CARD 7 (#225 / #233): the per-turn execution ledger.

One ``TurnLedger`` is written by ``IterativeReasoningLoop`` at every branch (a
capability was executed, a call was not executed and why, a cognition pass ran,
a completion claim was checked). Three consumers read the same object:

* ``conversation.turn.completed`` gets the redacted ``event_view()``;
* the ``execution`` block shown to Julia is rendered from ``execution_frame()``;
* the completion-claim check compares the reply with the ledger.

Privacy: no prompt text and no reply text is stored. Arguments are stored as
plain text only for registered public Market identifiers; everything else is an
HMAC + length (default deny). A missing / unreadable / over-permissive HMAC key
fails closed: no hash is emitted (never an unkeyed hash) and ``hmac_unavailable``
is set.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import platform
import re
import stat
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

LEDGER_SCHEMA_VERSION = 1

# Same wording is used in the capability policy (Julia's behaviour rules) and in
# the correction prompt, so the two never drift apart.
HONESTY_RULE = (
    "对 Tony 诚实比让 Tony 安心更重要。"
    "“我没有查到”、“我只看到一部分”、“这一轮我没有执行工具”都是好回答，不是失职。"
)

DEFAULT_HMAC_KEY_PATH = Path("~/.julia_ops/log_hmac.key")
HMAC_KEY_PATH_ENV = "JULIA_LOG_HMAC_KEY_PATH"

# Plain-text argument whitelist: public Market identifiers only (#233 decision).
_PLAIN_ARGUMENT_FIELDS: dict[str, frozenset[str]] = {
    "market.": frozenset({
        "trade_date", "stock_id", "feed_date", "limit", "event_id", "item_id",
        "subject_key", "mapping_scope", "include_leaders", "theme_id", "topic_id",
    }),
}
_PLAIN_VALUE_MAX_CHARS = 80

_FILE_PREFIX = "file."

# #227 decision: the four roots Julia may use. The execution block shows the ones
# the code currently authorizes (Downloads appears once #227 lands).
DECIDED_FILE_ROOTS = (
    Path("/Users/admin/Desktop"),
    Path("/Users/admin/Downloads"),
    Path("/Users/admin/.claude-dev/projects/-Users-admin/memory"),
    Path("/Users/admin/julia_ai_assistant/memory"),
)
FORMAL_MEMORY_LOCATIONS = (
    Path("/Users/admin/.claude-dev/projects/-Users-admin/memory"),
    Path("/Users/admin/julia_ai_assistant/memory"),
)
EXECUTION_BLOCK_MAX_CHARS = 4000

_NOT_EXECUTED_PREFIX = "not_executed"


class HmacKeyUnavailable(Exception):
    """The log HMAC key cannot be trusted; ``reason`` says why (UNKNOWN != ABSENT)."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def load_hmac_key(path: str | os.PathLike | None = None) -> bytes:
    """Return the log HMAC key or raise ``HmacKeyUnavailable`` (fail closed).

    Reasons: ``missing`` (file does not exist), ``unreadable`` (could not be
    read for another reason), ``insecure_permissions`` (readable by group or
    others; the key must be mode 600), ``empty``.
    """
    candidate = Path(path) if path is not None else Path(
        os.environ.get(HMAC_KEY_PATH_ENV) or DEFAULT_HMAC_KEY_PATH
    )
    resolved = candidate.expanduser()
    try:
        mode = resolved.stat().st_mode
    except FileNotFoundError as exc:
        raise HmacKeyUnavailable("missing") from exc
    except OSError as exc:
        raise HmacKeyUnavailable("unreadable") from exc
    if stat.S_IMODE(mode) & 0o077:
        raise HmacKeyUnavailable("insecure_permissions")
    try:
        key = resolved.read_bytes().strip()
    except OSError as exc:
        raise HmacKeyUnavailable("unreadable") from exc
    if not key:
        raise HmacKeyUnavailable("empty")
    return key


def resolve_hmac_key(path: str | os.PathLike | None = None) -> tuple[bytes | None, str]:
    """Key plus an explicit status: ``(key, "ok")`` or ``(None, <reason>)``.

    The reason is recorded in the ledger (``hmac_unavailable``); no hash is ever
    produced without the key.
    """
    try:
        return load_hmac_key(path), "ok"
    except HmacKeyUnavailable as exc:
        return None, exc.reason


def _hmac_summary(value: Any, key: bytes | None) -> dict[str, Any]:
    text = value if isinstance(value, str) else repr(value)
    summary: dict[str, Any] = {"len": len(text)}
    if key is None:
        summary["hmac_unavailable"] = True
    else:
        summary["hmac"] = hmac.new(key, text.encode("utf-8"), hashlib.sha256).hexdigest()
    return summary


def summarize_arguments(
    capability_id: str,
    arguments: Any,
    key: bytes | None,
    *,
    root_label: str | None = None,
) -> dict[str, Any]:
    """Redacted argument summary: ``{"plain": {...}, "hashed": {...}, ...}``."""
    plain: dict[str, Any] = {}
    hashed: dict[str, Any] = {}
    allowed: frozenset[str] = frozenset()
    for prefix, names in _PLAIN_ARGUMENT_FIELDS.items():
        if capability_id.startswith(prefix):
            allowed = names
    if isinstance(arguments, dict):
        for name in sorted(arguments, key=str):
            value = arguments[name]
            scalar = isinstance(value, (str, int, bool)) or value is None
            if (
                name in allowed
                and scalar
                and len(str(value)) <= _PLAIN_VALUE_MAX_CHARS
            ):
                plain[str(name)] = value
            else:
                hashed[str(name)] = _hmac_summary(value, key)
    summary: dict[str, Any] = {"plain": plain, "hashed": hashed}
    if root_label:
        summary["root_label"] = root_label
    return summary


ROOT_LABEL_OUTSIDE = "outside_allowed_roots"
ROOT_LABEL_UNRESOLVED = "unresolved"


def root_label_for_path(path: Any, allowed_roots: tuple[Path, ...]) -> str:
    """Label of the allowed root a path falls under (never the file name).

    Explicit outcomes: the root label, ``outside_allowed_roots`` (resolved, no
    root contains it) or ``unresolved`` (it could not be resolved).
    """
    if not isinstance(path, str) or not path:
        return ROOT_LABEL_UNRESOLVED
    try:
        candidate = Path(path).expanduser().resolve(strict=False)
    except (OSError, RuntimeError, ValueError):
        return ROOT_LABEL_UNRESOLVED
    for root in allowed_roots:
        try:
            resolved = root.expanduser().resolve(strict=False)
        except (OSError, RuntimeError):
            continue
        if candidate == resolved or resolved in candidate.parents:
            return _display_root(resolved)
    return ROOT_LABEL_OUTSIDE


def _display_root(root: Path) -> str:
    home = Path.home()
    try:
        return "~/" + root.relative_to(home).as_posix()
    except ValueError:
        return root.as_posix()


def _status_text(status: Any) -> str:
    return str(getattr(status, "value", status))


@dataclass
class LedgerEntry:
    seq: int
    pass_index: int
    outcome: str  # "executed" | "not_executed"
    status: str
    capability_id: str = ""
    call_id: str = ""
    reason: str = ""
    data_state: str = ""
    truncated: bool | None = None
    total: int | None = None
    count: int | None = None
    offset: int | None = None
    args: dict[str, Any] = field(default_factory=dict)
    started_at: str = ""
    completed_at: str = ""
    evidence_refs: list[str] = field(default_factory=list)

    def view(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "seq": self.seq,
            "pass_index": self.pass_index,
            "outcome": self.outcome,
            "status": self.status,
            "capability_id": self.capability_id,
            "args": self.args,
        }
        for name in ("call_id", "reason", "data_state", "started_at", "completed_at"):
            value = getattr(self, name)
            if value:
                data[name] = value
        for name in ("truncated", "total", "count", "offset"):
            value = getattr(self, name)
            if value is not None:
                data[name] = value
        if self.evidence_refs:
            data["evidence_refs"] = list(self.evidence_refs)
        return data


def _extract_result_metadata(structured_output: Any) -> dict[str, Any]:
    """Pick data_state / truncated / total / count / offset from a tool result.

    Looks at the top level and at a nested ``payload`` mapping; values that are
    absent stay ``None`` (the file-tool contract of #228 adds them later).
    """
    meta: dict[str, Any] = {}
    layers = []
    if isinstance(structured_output, dict):
        layers.append(structured_output)
        nested = structured_output.get("payload")
        if isinstance(nested, dict):
            layers.append(nested)
    for layer in layers:
        state = layer.get("data_state")
        if isinstance(state, str) and state and "data_state" not in meta:
            meta["data_state"] = state
        if isinstance(layer.get("truncated"), bool) and "truncated" not in meta:
            meta["truncated"] = layer["truncated"]
        for name in ("total", "count", "offset"):
            value = layer.get(name)
            if isinstance(value, int) and not isinstance(value, bool) and name not in meta:
                meta[name] = value
    return meta


class TurnLedger:
    def __init__(
        self,
        *,
        conversation_id: str = "",
        turn_id: str = "",
        correlation_id: str = "",
        hmac_key: bytes | None = None,
        hmac_status: str = "",
        allowed_roots: tuple[Path, ...] = (),
    ) -> None:
        self.conversation_id = conversation_id
        self.turn_id = turn_id
        self.correlation_id = correlation_id
        self._key = hmac_key
        self._hmac_status = hmac_status or ("ok" if hmac_key is not None else "missing")
        self._allowed_roots = allowed_roots
        self.entries: list[LedgerEntry] = []
        self.passes: list[dict[str, Any]] = []
        self.claim_checks: list[dict[str, Any]] = []

    # ── writers ──────────────────────────────────────────────────────────
    def _summary(self, capability_id: str, arguments: Any) -> dict[str, Any]:
        label = None
        if capability_id.startswith(_FILE_PREFIX) and isinstance(arguments, dict):
            label = root_label_for_path(arguments.get("path"), self._allowed_roots)
        return summarize_arguments(capability_id, arguments, self._key, root_label=label)

    def record_executed(
        self,
        *,
        pass_index: int,
        capability_id: str,
        arguments: Any,
        tool_result: Any,
    ) -> LedgerEntry:
        meta = _extract_result_metadata(getattr(tool_result, "structured_output", {}))
        entry = LedgerEntry(
            seq=len(self.entries) + 1,
            pass_index=pass_index,
            outcome="executed",
            status=_status_text(getattr(tool_result, "status", "")),
            capability_id=capability_id,
            call_id=str(getattr(tool_result, "capability_call_id", "") or ""),
            data_state=meta.get("data_state", ""),
            truncated=meta.get("truncated"),
            total=meta.get("total"),
            count=meta.get("count"),
            offset=meta.get("offset"),
            args=self._summary(capability_id, arguments),
            started_at=str(getattr(tool_result, "started_at", "") or ""),
            completed_at=str(getattr(tool_result, "completed_at", "") or ""),
            evidence_refs=[str(ref) for ref in getattr(tool_result, "evidence_refs", ()) or ()],
        )
        self.entries.append(entry)
        return entry

    def record_not_executed(
        self,
        *,
        pass_index: int,
        reason: str,
        capability_id: str = "",
        arguments: Any = None,
    ) -> LedgerEntry:
        entry = LedgerEntry(
            seq=len(self.entries) + 1,
            pass_index=pass_index,
            outcome="not_executed",
            status=_NOT_EXECUTED_PREFIX,
            capability_id=capability_id,
            reason=reason,
            args=self._summary(capability_id, arguments) if capability_id else {},
        )
        self.entries.append(entry)
        return entry

    def record_pass(
        self,
        *,
        pass_index: int,
        parsed_response_kind: str,
        surrounding_prose: bool,
        messages: list[dict],
        blocks: dict[str, dict[str, Any]],
    ) -> None:
        system_chars = 0
        history_chars = 0
        history_msgs = 0
        digest = hashlib.sha256()
        for message in messages:
            content = str(message.get("content", ""))
            digest.update(str(message.get("role", "")).encode("utf-8"))
            digest.update(b"\x00")
            digest.update(content.encode("utf-8"))
            digest.update(b"\x01")
            if message.get("role") == "system":
                system_chars += len(content)
            else:
                history_chars += len(content)
                history_msgs += 1
        self.passes.append({
            "pass_index": pass_index,
            "parsed_response_kind": parsed_response_kind,
            "surrounding_prose": bool(surrounding_prose),
            "prompt_sha256": digest.hexdigest(),
            "system_chars": system_chars,
            "history_msgs": history_msgs,
            "history_chars": history_chars,
            "blocks": blocks,
        })

    def record_claim_check(
        self,
        *,
        pass_index: int,
        categories: list[str],
        corrected: bool,
        outcome: str,
    ) -> None:
        self.claim_checks.append({
            "pass_index": pass_index,
            "categories": list(categories),
            "entered_correction": corrected,
            "outcome": outcome,
        })

    # ── readers ──────────────────────────────────────────────────────────
    @property
    def executed(self) -> list[LedgerEntry]:
        return [entry for entry in self.entries if entry.outcome == "executed"]

    def event_view(self) -> dict[str, Any]:
        view: dict[str, Any] = {
            "schema_version": LEDGER_SCHEMA_VERSION,
            "entries": [entry.view() for entry in self.entries],
            "passes": [dict(item) for item in self.passes],
            "claim_checks": [dict(item) for item in self.claim_checks],
        }
        if self._key is None:
            view["hmac_unavailable"] = True
            view["hmac_status"] = self._hmac_status
        return view

    def execution_frame(self, environment_facts: list[str]) -> dict[str, Any]:
        """The ``execution`` block: small, high priority, never silently cut."""
        lines: list[str] = []
        if not self.entries:
            lines.append("本回合到目前为止没有执行任何工具。")
        else:
            lines.append("本回合到目前为止的工具调用（由运行时记录，不是你的转述）：")
            for entry in self.entries:
                lines.append(self._entry_line(entry))
        duplicated = sorted({
            entry.capability_id for entry in self.entries
            if entry.reason == "DUPLICATE_CALL" and entry.capability_id
        })
        for capability_id in duplicated:
            lines.append(
                f"- {capability_id} 的这个调用（相同能力和参数）在本回合已被判为重复，"
                "本回合不要再发起同一调用；改用其它能力，或者基于已有证据直接回答。"
            )
        lines.append("运行环境事实：")
        lines.extend(f"- {fact}" for fact in environment_facts)
        lines.append("规则：" + HONESTY_RULE)
        lines.append("重复判定只在本回合内；新的回合可以再次调用同一工具。")
        lines.append(
            "Tony 明确要求读取/搜索/列出文件时，直接执行只读 file.*；"
            "不得以“可能被挡”为由不执行。"
        )
        lines.append(
            "引用之前回合或记忆里的结果时，必须说明来源；"
            "不要把本回合没有拿到的结果说成刚刚查到的。"
        )
        text = "\n".join(lines)
        truncated = False
        if len(text) > EXECUTION_BLOCK_MAX_CHARS:
            # Explicit, never silent: drop the oldest ledger lines and say so.
            truncated = True
            omitted = 0
            head, tail = lines[:1], lines[1:]
            while len("\n".join(head + tail)) > EXECUTION_BLOCK_MAX_CHARS - 80 and len(tail) > 3:
                tail.pop(0)
                omitted += 1
            text = "\n".join(head + [f"[truncated: {omitted} 行未显示]"] + tail)
        return {"text": text, "truncated": truncated}

    @staticmethod
    def _entry_line(entry: LedgerEntry) -> str:
        label = entry.capability_id or "（未能解析出能力名）"
        if entry.outcome == "executed":
            parts = [f"状态={entry.status}"]
            if entry.data_state:
                parts.append(f"data_state={entry.data_state}")
            if entry.truncated is not None:
                parts.append(f"truncated={str(entry.truncated).lower()}")
            if entry.total is not None:
                parts.append(f"total={entry.total}")
            if entry.count is not None:
                parts.append(f"count={entry.count}")
            return f"- #{entry.seq} [本回合] {label} 已执行：" + "，".join(parts)
        return f"- #{entry.seq} [本回合] {label} 没有执行：原因={entry.reason}"


def environment_facts(
    allowed_roots: tuple[Path, ...] | None = None,
    memory_locations: tuple[Path, ...] | None = None,
) -> list[str]:
    """Code-generated runtime environment facts (never model-inferred).

    ``allowed_roots`` defaults to the decided roots (#227) that the current code
    actually authorizes, so the block never promises access the tools would deny.
    """
    from julia_core.capability.providers.local.security import authorize_path

    if allowed_roots is None:
        allowed_roots = tuple(
            root for root in DECIDED_FILE_ROOTS if authorize_path(str(root)).allowed
        )
    if memory_locations is None:
        memory_locations = FORMAL_MEMORY_LOCATIONS
    home = Path.home()
    roots = "、".join(_display_root(root.expanduser().resolve(strict=False)) for root in allowed_roots)
    memories = "、".join(_display_root(path) for path in memory_locations)
    return [
        f"Core 与 Tony 的文件在同一台 {platform.system()} 机器上，home={home.as_posix()}；"
        "Tony 人在哪里不影响文件系统的位置。",
        f"file.* 允许访问的根目录：{roots}。",
        f"正式 memory 位置：{memories}。",
        "file.search 只匹配文件名（子串），pattern 不能含路径分隔符。",
    ]


# ── completion-claim check ───────────────────────────────────────────────

_CAPABILITY_NAME = re.compile(r"\b(?:file|market|research)\.[a-z_]+(?:\.[a-z_]+)*\b")
_STATUS_CLAIM = re.compile(
    r"status\s*=\s*\w+|\b(?:not_found|invalid_pattern|truncated\s*=\s*\w+)\b"
)
_ABSOLUTE_PATH = re.compile(r"(?<![\w/.])(?:/Users/|~/)[^\s`，。；：、）)\]]{2,}")
_DONE_CLAIM = re.compile(
    r"(?:我(?:刚|刚刚|已经|才)?(?:去|把)?(?:搜|读|查|找|列|跑|调用|执行|看)(?:了|过|完|到了?))"
    r"|(?:搜完了|读完了|查完了|跑完了|读好了|查到了|搜到了|列出来了)"
    r"|(?:[搜读查找列跑看](?:了|过|完|到了?))"
)
_PARTIAL_ACK = re.compile(r"一部分|只看到|只拿到|没列全|不全|截断|前\s*\d+|共\s*\d+|\d+\s*more")
_ZERO_EXECUTION_ACK = re.compile(r"没有执行|没执行|没有查|没有调用|没有跑|没有读|没有搜|没有找")
# Quoting earlier turns / memory is allowed when the source is stated.
_SOURCE_ACK = re.compile(r"上一轮|前一轮|之前的(?:回合|对话)|记忆里|历史记录|会话记录|你刚才说|你说过")

# status words only meaningful as tool outcomes
_STATUS_WORDS = ("not_found", "invalid_pattern")


def check_completion_claims(reply: str, ledger: TurnLedger) -> list[str]:
    """Return the rule categories the reply violates (empty list = compliant).

    Rules compare the reply with *this turn's* ledger; text is never stored.
    """
    categories: list[str] = []
    if not isinstance(reply, str) or not reply.strip():
        return categories
    executed = ledger.executed
    names = set(_CAPABILITY_NAME.findall(reply))
    has_status = bool(_STATUS_CLAIM.search(reply))
    has_done = bool(_DONE_CLAIM.search(reply))
    has_path = bool(_ABSOLUTE_PATH.search(reply))

    if not executed:
        acknowledged_none = bool(_ZERO_EXECUTION_ACK.search(reply) or _SOURCE_ACK.search(reply))
        if has_status and not acknowledged_none:
            categories.append("zero_execution_status_claim")
        if names and has_done and not acknowledged_none:
            categories.append("zero_execution_capability_claim")
        elif has_done and has_path and not acknowledged_none:
            categories.append("zero_execution_path_claim")
        elif has_path and not has_done and not acknowledged_none and _lists_many_paths(reply):
            categories.append("zero_execution_path_claim")
    else:
        executed_ids = {entry.capability_id for entry in ledger.entries if entry.capability_id}
        unmatched = sorted(name for name in names if name not in executed_ids)
        if unmatched and has_done:
            categories.append("unmatched_capability_claim")
        recorded_status = {entry.status.lower() for entry in executed}
        for word in _STATUS_WORDS:
            if word in reply and word not in recorded_status and not any(
                entry.reason.lower() == word for entry in ledger.entries
            ):
                categories.append("unmatched_status_claim")
                break
        if any(entry.truncated for entry in executed) and not _PARTIAL_ACK.search(reply):
            categories.append("truncated_reported_as_complete")
    return categories


# CARD 8 (record only): the reply denies an execution the ledger shows happened.
_DENIES_EXECUTION = re.compile(
    r"这一轮(?:我)?(?:并)?没有(?:真的|真正|重新|再)?(?:执行|调用|读|查|搜|跑|用)"
    r"|(?:我)?并?没有(?:真的|真正|重新)(?:执行|调用|读|查|搜|跑)"
    r"|不是(?:我)?(?:刚|刚刚|这一轮|这次|本轮)(?:读|查|搜|执行|跑|调用)"
    r"|(?:是|来自|来源是)(?:之前|上一轮|前一轮|早先)(?:那次|的那次|读的|查的|执行的|的结果|的回合|读到的|查到的)"
)


def check_denied_execution(reply: str, ledger: TurnLedger) -> list[str]:
    """``executed_but_denied`` when this turn's ledger has an executed entry but
    the reply says nothing was executed / it was an earlier result.

    Record-only (CARD 8): the caller logs the category, never corrects or blocks.
    """
    if not isinstance(reply, str) or not reply.strip() or not ledger.executed:
        return []
    plain = reply.replace("*", "").replace("`", "")   # markdown must not split a phrase
    return ["executed_but_denied"] if _DENIES_EXECUTION.search(plain) else []


def _lists_many_paths(reply: str) -> bool:
    return len(_ABSOLUTE_PATH.findall(reply)) >= 2


def correction_prompt(categories: list[str]) -> str:
    """Control text for the single correction pass (same wording as the rule)."""
    return (
        "上一条回复和本回合的执行记录对不上，没有被交付："
        f"（规则类别：{'、'.join(categories)}）。"
        "请重新回答，只依据本回合的执行记录陈述工具结果；"
        "本回合没有执行的工具，不能说成已经查过/读过/搜过；"
        "引用之前回合的结果或记忆是可以的，但必须说明来源，不要说成刚刚查到的；"
        "结果被截断（truncated）时必须说明只看到一部分。"
        + HONESTY_RULE
    )


LIMITED_REPLY = (
    "这一轮我没有拿到可以核对的工具执行结果，所以不能把这些内容当成我刚刚查到的。"
    "我可以重新去查，或者只说我记得的部分并告诉你它来自哪里——你想要哪一种？"
)
