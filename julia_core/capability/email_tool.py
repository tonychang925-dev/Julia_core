"""v3.1 Communication Layer — Email integration.

LLM decides: check inbox, draft replies, summarize threads.
Runtime does: connect to email provider. Nothing more.

Action levels:
  READ:   search_email, read_email → auto-execute
  PROPOSE: draft_reply → show to Tony before sending
  APPROVAL: send_email → require explicit confirmation

Provider abstraction: Gmail API (MCP) or local simulation.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from julia_core.capability.approval import ApprovalGate, ActionLevel


class EmailTool:
    """Email capability. LLM decides when to check, what to surface."""

    _inbox_path = Path(os.environ.get(
        "JULIA_EMAIL_PATH",
        str(Path.home() / ".julia" / "inbox.json"),
    ))

    @classmethod
    def search(cls, query: str = "", max_results: int = 10) -> str:
        """Search inbox. Returns matching emails."""
        emails = cls._load_inbox()
        if not emails:
            return "收件箱为空。"

        if query:
            q = query.lower()
            emails = [e for e in emails
                      if q in e.get("subject", "").lower()
                      or q in e.get("from", "").lower()
                      or q in e.get("body", "").lower()]

        if not emails:
            return f"未找到匹配 '{query}' 的邮件"

        lines = [f"📧 收件箱 ({len(emails)} 封):"]
        for e in emails[-max_results:]:
            unread = "🔵" if e.get("unread", True) else "  "
            lines.append(
                f"{unread} {e.get('date', '')} | {e.get('from', '')}\n"
                f"   主题: {e.get('subject', '无主题')}"
            )
        return "\n".join(lines)

    @classmethod
    def read(cls, index: int = 0) -> str:
        """Read a specific email by index."""
        emails = cls._load_inbox()
        if not emails:
            return "收件箱为空。"
        if index < 0 or index >= len(emails):
            return f"邮件 #{index} 不存在。共 {len(emails)} 封。"
        e = emails[index]
        return (
            f"📧 邮件 #{index}\n"
            f"发件人: {e.get('from', '')}\n"
            f"日期: {e.get('date', '')}\n"
            f"主题: {e.get('subject', '无主题')}\n"
            f"\n{e.get('body', '')[:2000]}"
        )

    @classmethod
    def draft_reply(cls, index: int, reply_text: str) -> str:
        """Draft a reply. Returns draft text for Tony to review."""
        emails = cls._load_inbox()
        if not emails or index < 0 or index >= len(emails):
            return "无法创建草稿：邮件不存在。"
        e = emails[index]
        draft = (
            f"📝 草稿 (待确认)\n"
            f"回复: {e.get('subject', '')}\n"
            f"收件人: {e.get('from', '')}\n"
            f"\n{reply_text}\n"
            f"\n---\n以上是草稿。确认后发送。"
        )
        return draft

    @classmethod
    def _load_inbox(cls) -> List[dict]:
        if cls._inbox_path.exists():
            try:
                return json.loads(cls._inbox_path.read_text())
            except Exception:
                pass
        return []


def register_email_tools(registry):
    """Register email tools in capability registry."""
    from julia_core.capability.tool_protocol import ToolSchema, ToolCategory

    registry.register(
        ToolSchema(
            name="search_email",
            description="搜索收件箱。当Tony问'有没有新邮件'或想查看某个发件人的邮件时使用。",
            category=ToolCategory.SYSTEM,
            parameters={"query": "搜索关键词（可选，空则列出最近邮件）"},
            example="search_email(query='GitHub')",
        ),
        lambda query="", max_results=10: EmailTool.search(query, int(max_results)),
    )

    registry.register(
        ToolSchema(
            name="read_email",
            description="读取指定邮件全文。当Tony想了解某封邮件的详细内容时使用。",
            category=ToolCategory.SYSTEM,
            parameters={"index": "邮件序号（0开始）"},
            example="read_email(index=0)",
        ),
        lambda index=0: EmailTool.read(int(index)),
    )

    registry.register(
        ToolSchema(
            name="draft_email_reply",
            description="起草邮件回复。生成草稿供Tony审核，不会自动发送。",
            category=ToolCategory.SYSTEM,
            parameters={"index": "要回复的邮件序号", "reply_text": "回复内容"},
            example="draft_email_reply(index=0, reply_text='感谢您的邮件...')",
        ),
        lambda index=0, reply_text="": EmailTool.draft_reply(int(index), reply_text),
    )
