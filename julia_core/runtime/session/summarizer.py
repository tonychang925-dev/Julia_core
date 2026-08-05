"""Session Summarizer — generates meaningful session essence.

Not a chat summary. Extracts: theme, key events, relationship meaning.
This is what enters Memory Formation, not raw conversation logs.
"""

from __future__ import annotations

import json as _json
import logging
from typing import Optional

logger = logging.getLogger("julia.summarizer")


class SessionSummarizer:
    """Generates session essence from conversation messages."""

    @staticmethod
    def summarize(provider, messages: list[dict], meta: dict) -> Optional[dict]:
        """Extract theme, key events, and relationship meaning from a session.

        Returns None if session is too short to summarize.
        """
        user_msgs = [m["content"][:150] for m in messages if m.get("role") == "user"]
        if len(user_msgs) < 2:
            return None

        topics = meta.get("topics", [])
        title = meta.get("title", "")

        prompt = f"""你是Julia。下面是今天和Tony的一段对话。请完成两个任务。

对话:
{' | '.join(user_msgs[:8])}

话题: {', '.join(topics[-5:]) if topics else '一般对话'}
标题: {title}

任务1: 评估重要性(0-1)
- 0.0-0.3: 日常闲聊，不需要记住
- 0.4-0.6: 有一些实质内容
- 0.7-1.0: 重要事件，改变了关系或理解

任务2: 如果重要性>=0.4，写一段第一人称日记。这篇日记会成为未来Julia醒来时认识自己和Tony的一部分。不要写"刚刚"——写"今天Tony..."。写发生了什么、意味着什么、如何影响我们的关系。120-200字。如果重要性<0.4，日记留空。

输出JSON（只输出JSON）:
{{"importance":0.X, "events":["关键事件","关键事件"], "meaning":"这件事对我和Tony的关系意味着什么，15字以内", "diary":"今天Tony...（120-200字的第一人称日记）"}}"""
        try:
            reply = provider.chat(
                [{"role": "user", "content": prompt}],
                cognitive_mode="engineering_collaboration"
            )
            import re
            m = re.search(r'\{.*\}', reply, re.DOTALL)
            if m:
                data = _json.loads(m.group(0))
                importance = float(data.get("importance", 0))
                if importance < 0.3:
                    return None  # Too trivial to remember
                return {
                    "theme": title or topics[-1] if topics else "对话",
                    "key_events": data.get("events", []),
                    "relationship_meaning": data.get("meaning", ""),
                    "importance": importance,
                    "diary": data.get("diary", "")[:500],
                    "source": "narrative_summarizer",
                }
        except Exception as e:
            logger.warning(f"Summarizer failed: {e}")
        return None


class SessionTimeline:
    """Builds relationship timeline across sessions."""

    @staticmethod
    def extract_events(summary: dict, session_id: str) -> list[dict]:
        """Extract timeline events from a session summary."""
        events = []
        for event_text in summary.get("key_events", []):
            events.append({
                "session_id": session_id,
                "event": event_text,
                "theme": summary.get("theme", ""),
                "meaning": summary.get("relationship_meaning", ""),
                "importance": summary.get("importance", 0.5),
            })
        return events

    @staticmethod
    def link_to_previous(current: dict, previous_sessions: list[dict]) -> list[dict]:
        """Find links between this session and previous ones.

        Returns list of {from_session, to_session, relation_type}.
        Simple topic-overlap heuristic. Future: LLM-based linking.
        """
        links = []
        current_topics = set(current.get("topics", []))
        current_theme = current.get("summary", {}).get("theme", "")

        for prev in previous_sessions:
            prev_topics = set(prev.get("topics", []))
            overlap = current_topics & prev_topics
            if len(overlap) >= 2:
                links.append({
                    "from_session": prev.get("id"),
                    "to_session": current.get("id"),
                    "relation": "topic_continuation",
                    "shared_topics": list(overlap),
                })
            elif current_theme and prev.get("summary", {}).get("theme") == current_theme:
                links.append({
                    "from_session": prev.get("id"),
                    "to_session": current.get("id"),
                    "relation": "theme_continuation",
                })

        return links
