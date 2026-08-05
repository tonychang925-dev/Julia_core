"""v3.2 Relationship Intelligence — Contact Awareness + Preference Learning.

NOT a CRM database. NOT a Person table.
Narrative-driven: LLM observes patterns → proposes insights → Tony confirms.

Principle: Relationship knowledge comes from interaction, not from labels.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from julia_core.capability.approval import ApprovalGate, ActionLevel


class ContactAwareness:
    """Narrative contact understanding. LLM infers relationships from context."""

    _contacts_path = Path(os.environ.get(
        "JULIA_CONTACTS_PATH",
        str(Path.home() / ".julia" / "contacts.json"),
    ))

    @classmethod
    def lookup(cls, name: str) -> str:
        """Look up what Julia knows about a contact. Narrative, not labels."""
        contacts = cls._load()
        matches = [c for c in contacts if name.lower() in c.get("name", "").lower()]
        if not matches:
            return f"目前没有关于 '{name}' 的记录。"

        lines = []
        for c in matches:
            lines.append(f"📇 {c.get('name', '')}")
            if c.get("context"):
                lines.append(f"   关系: {c['context']}")
            if c.get("notes"):
                lines.append(f"   备注: {c['notes']}")
            if c.get("last_contact"):
                lines.append(f"   最近联系: {c['last_contact']}")
        return "\n".join(lines)

    @classmethod
    def add_observation(cls, name: str, context: str, notes: str = "") -> str:
        """Add an observation about a contact. Proposal — needs confirmation."""
        contacts = cls._load()
        # Check existing
        for c in contacts:
            if c.get("name", "").lower() == name.lower():
                c["last_contact"] = datetime.now().strftime("%Y-%m-%d")
                if notes and notes not in c.get("notes", ""):
                    c["notes"] = c.get("notes", "") + "; " + notes
                cls._save(contacts)
                return f"已更新 {name} 的观察记录。"
        # New contact
        contacts.append({
            "name": name,
            "context": context,
            "notes": notes,
            "first_observed": datetime.now().strftime("%Y-%m-%d"),
            "last_contact": datetime.now().strftime("%Y-%m-%d"),
        })
        cls._save(contacts)
        return f"已添加 {name}（{context}）。"

    @classmethod
    def list_all(cls) -> str:
        """List all known contacts."""
        contacts = cls._load()
        if not contacts:
            return "暂无联系人记录。"
        lines = ["📇 已知联系人:"]
        for c in contacts:
            lines.append(f"  {c.get('name', '')} — {c.get('context', '未分类')}")
        return "\n".join(lines)

    @classmethod
    def _load(cls) -> List[dict]:
        if cls._contacts_path.exists():
            try:
                return json.loads(cls._contacts_path.read_text())
            except Exception:
                pass
        return []

    @classmethod
    def _save(cls, contacts: List[dict]):
        cls._contacts_path.parent.mkdir(parents=True, exist_ok=True)
        cls._contacts_path.write_text(json.dumps(contacts, ensure_ascii=False, indent=2))


def register_contacts_tools(registry):
    """Register contact awareness tools."""
    from julia_core.capability.tool_protocol import ToolSchema, ToolCategory

    registry.register(
        ToolSchema(
            name="lookup_contact",
            description="查询已知联系人的信息。当Tony提到某个人名你想了解背景时使用。",
            category=ToolCategory.SYSTEM,
            parameters={"name": "姓名"},
            example="lookup_contact(name='张三')",
        ),
        lambda name="": ContactAwareness.lookup(name),
    )

    registry.register(
        ToolSchema(
            name="add_contact_note",
            description="添加对某人的观察记录。当你在互动中发现重要关系信息时使用。需要Tony确认。",
            category=ToolCategory.SYSTEM,
            parameters={"name": "姓名", "context": "关系描述", "notes": "备注"},
            example="add_contact_note(name='李总', context='合作方', notes='偏好技术细节')",
        ),
        lambda name="", context="", notes="":
            ContactAwareness.add_observation(name, context, notes),
    )

    registry.register(
        ToolSchema(
            name="list_contacts",
            description="列出所有已知联系人。",
            category=ToolCategory.SYSTEM,
            parameters={},
            example="list_contacts()",
        ),
        lambda: ContactAwareness.list_all(),
    )
