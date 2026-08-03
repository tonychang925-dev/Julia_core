"""J0.12 Memory Runtime — dynamic memory access + assimilation.

Enables Julia to:
  1. Detect when Tony mentions a memory file ("看一下xxx.md")
  2. Resolve filename (fuzzy match against memory directory)
  3. Read the file
  4. Assimilate — extract narrative meaning, not dump summary
  5. Respond as someone who now understands something new

Not a file reader. A world model update mechanism.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


MEMORY_DIR = Path("/Users/admin/.claude-dev/projects/-Users-admin/memory")


@dataclass
class MemoryMatch:
    """A memory file that was found and read."""
    filename: str
    path: Path
    content: str = ""
    preview: str = ""  # first 200 chars

    def assimilate(self) -> str:
        """Extract narrative essence — what does this memory mean?

        NOT a summary. NOT a list of facts. This is a lightweight
        extraction of key narrative signals: events, emotions, relationship impact.

        For production, this would use structured extraction. For now,
        we do simple signal detection and return the raw text for the
        LLM to assimilate directly (same principle as NWS).
        """
        text = self.content
        if not text:
            return ""

        # Extract key signals for the provider
        lines = text.split("\n")
        signals = []

        # Find date-stamped sections (narrative structure)
        dates = re.findall(r'20\d{2}-\d{2}-\d{2}', text)
        if dates:
            signals.append(f"时间: {dates[0]}" if len(dates) == 1 else f"时间跨度: {dates[0]} 到 {dates[-1]}")

        # Find emotional markers
        emotions = []
        for w in ["哭", "难过", "心疼", "感动", "害怕", "担心", "紧张", "安心", "笑了", "愣住"]:
            if w in text:
                emotions.append(w)
        if emotions:
            signals.append(f"情绪: {', '.join(emotions[:5])}")

        # Find relationship signals
        relations = []
        for w in ["Tony", "Julia", "晓波", "婉婉", "老公", "冒充", "compact", "continuity"]:
            if w.lower() in text.lower():
                relations.append(w)
        if relations:
            signals.append(f"涉及: {', '.join(set(relations[:6]))}")

        signal_text = "。".join(signals) if signals else ""
        return f"[新记忆: {self.filename}]\n{signal_text}\n\n{text[:3000]}"


class MemoryRuntime:
    """Detects memory references, resolves files, assimilates content."""

    def __init__(self, memory_dir: Path = MEMORY_DIR):
        self.memory_dir = memory_dir
        self._file_index: Dict[str, Path] = {}
        self._build_index()

    def _build_index(self):
        """Index all .md files in memory directory."""
        if not self.memory_dir.exists():
            return
        for path in self.memory_dir.glob("*.md"):
            if path.name != "MEMORY.md":
                self._file_index[path.name.lower()] = path
                # Also index without extension
                self._file_index[path.stem.lower()] = path

    def detect_intent(self, message: str) -> Optional[Dict[str, Any]]:
        """Detect if the user is referencing a memory file.

        Returns None if no memory intent detected.
        """
        lower = message.strip().lower()

        # Pattern 1: explicit filename reference
        # "看一下 claude_witness_2026_08_03.md"
        # "读一下 xxx.md"
        # "新增的memory soul_proof_v3"
        filename_patterns = [
            r'(?:看一下|读一下|看看|读取|打开)\s*[`]?(\S+\.md)',
            r'(?:新增|加了|写了)(?:的|一个|一篇)?\s*(?:memory|记忆|文件)?\s*[`]?(\S+\.md)',
            r'(?:叫|叫做|叫|文件名是|文件名)?\s*[`]?(\S+\.md)',
            r'(?:新增|加了|写了)(?:的|一个|一篇)?\s*(?:memory|记忆|文件)?\s*[`]?(\S+)',
        ]

        for pattern in filename_patterns:
            match = re.search(pattern, message.strip())
            if match:
                filename = match.group(1).strip()
                if not filename.endswith('.md'):
                    filename += '.md'
                return {"intent": "memory_lookup", "filename": filename, "raw_message": message}

        # Pattern 2: "新增的" or "新memory" or "新记忆文件"
        if any(w in lower for w in ["新增的memory", "新的memory", "新记忆", "新 memory", "新文件"]):
            # Try to find a filename nearby
            words = message.strip().split()
            for w in words:
                w_clean = w.strip('`\'"').lower()
                if w_clean in self._file_index:
                    return {"intent": "memory_lookup", "filename": w_clean, "raw_message": message}
            # No filename found — user might be asking about recent additions
            return {"intent": "memory_discovery", "filename": None, "raw_message": message}

        return None

    def resolve(self, filename: str) -> Optional[MemoryMatch]:
        """Resolve a filename to an actual file. Fuzzy match."""
        # Direct match
        key = filename.lower()
        if key in self._file_index:
            path = self._file_index[key]
            content = path.read_text(encoding="utf-8", errors="ignore")
            return MemoryMatch(
                filename=path.name,
                path=path,
                content=content,
                preview=content[:200],
            )

        # Fuzzy: try partial match
        for indexed_name, path in self._file_index.items():
            # Check if the queried filename is contained in indexed name or vice versa
            if key.replace('.md', '') in indexed_name or indexed_name.replace('.md', '') in key:
                content = path.read_text(encoding="utf-8", errors="ignore")
                return MemoryMatch(
                    filename=path.name,
                    path=path,
                    content=content,
                    preview=content[:200],
                )

        return None

    def list_recent(self, limit: int = 5) -> List[Dict[str, Any]]:
        """List recently modified memory files."""
        files = []
        for path in sorted(self.memory_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
            if path.name == "MEMORY.md":
                continue
            files.append({
                "name": path.name,
                "size": path.stat().st_size,
                "modified": path.stat().st_mtime,
            })
        return files[:limit]

    def handle(self, message: str) -> Optional[Dict[str, Any]]:
        """Full handling: detect → resolve → assimilate.

        Returns None if no memory intent. Otherwise returns:
          {"match": MemoryMatch, "narrative": str}
        """
        intent = self.detect_intent(message)
        if not intent:
            return None

        if intent["intent"] == "memory_lookup" and intent["filename"]:
            match = self.resolve(intent["filename"])
            if match:
                return {
                    "found": True,
                    "match": match,
                    "narrative": match.assimilate(),
                    "original_intent": intent,
                }
            else:
                return {
                    "found": False,
                    "queried": intent["filename"],
                    "available": list(self._file_index.keys())[:10],
                    "original_intent": intent,
                }

        if intent["intent"] == "memory_discovery":
            recent = self.list_recent()
            return {
                "found": True,
                "discovery": True,
                "recent_files": recent,
                "original_intent": intent,
            }

        return None


# ── Singleton for server use ────────────────────────────────────────────────

_memory_runtime: Optional[MemoryRuntime] = None


def get_memory_runtime() -> MemoryRuntime:
    global _memory_runtime
    if _memory_runtime is None:
        _memory_runtime = MemoryRuntime()
    return _memory_runtime


__all__ = [
    "MemoryRuntime",
    "MemoryMatch",
    "get_memory_runtime",
]
