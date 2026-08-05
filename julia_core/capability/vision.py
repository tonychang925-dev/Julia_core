"""Vision Capability Tool — Julia's eyes.

LLM decides: whether to look at an image, what to ask about it.
Runtime does: call vision model, return raw description. Nothing more.

Architecture:
  Image → Vision Model → visual description → LLM → memory association → response

Key principle: Vision provides FACTS (what's in the image).
LLM provides MEANING (why it matters, how it connects to memory).
"""

from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Optional


class VisionTool:
    """Image understanding capability. LLM decides when to look."""

    tool_name = "vision_analyze"
    tool_description = (
        "查看和理解图片内容。当Tony给你看照片、截图、图表时使用。"
        "返回图片中的视觉信息——物体、场景、文字、氛围。"
        "LLM负责将视觉信息与记忆关联，产生意义。"
    )

    @staticmethod
    def analyze(image_path: str, question: str = "") -> str:
        """Analyze an image. Currently uses base64 fallback.
        In production: connect to GPT-4V, Claude Vision, or local VLM.
        """
        path = Path(image_path).expanduser()
        if not path.exists():
            return f"图片不存在: {image_path}"

        size = path.stat().st_size
        suffix = path.suffix.lower()

        # For now: return image metadata + visual context
        # Production: call vision model API
        result_parts = [
            f"[图片信息]",
            f"文件: {path.name}",
            f"大小: {size/1024:.0f}KB",
            f"格式: {suffix}",
        ]

        # Try to get basic image dimensions via PIL if available
        try:
            from PIL import Image
            img = Image.open(path)
            result_parts.append(f"尺寸: {img.size[0]}×{img.size[1]}")
            result_parts.append(f"模式: {img.mode}")
            img.close()
        except ImportError:
            result_parts.append("[需要 PIL 获取尺寸: pip install Pillow]")
        except Exception:
            pass

        # Encode as base64 for vision API
        try:
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            result_parts.append(f"base64: {b64[:50]}...({len(b64)} chars)")
        except Exception:
            pass

        if question:
            result_parts.append(f"问题: {question}")

        return "\n".join(result_parts)

    @staticmethod
    def is_available() -> bool:
        """Check if vision capabilities are available."""
        try:
            from PIL import Image
            return True
        except ImportError:
            return False


# ── Tool Registration ───────────────────────────────────────────────────────

def register_vision_tool(registry):
    """Register vision tool in capability registry."""
    from julia_core.capability.tool_protocol import ToolSchema, ToolCategory

    available = VisionTool.is_available()

    registry.register(
        ToolSchema(
            name="vision_analyze",
            description=VisionTool.tool_description + (" (可用)" if available else " (需安装Pillow)"),
            category=ToolCategory.INTERFACE,
            parameters={
                "image_path": "图片文件路径",
                "question": "关于这张图片的问题（可选）",
            },
            example="vision_analyze(image_path='/Users/admin/photo.jpg', question='这是哪里？')",
        ),
        lambda image_path="", question="": VisionTool.analyze(image_path, question),
    )
