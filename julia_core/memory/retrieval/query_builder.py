from __future__ import annotations

from .retrieval_context import MemoryQuery, MemoryRetrievalContext


class MemoryQueryBuilder:
    """Builds a cognitive memory query from JuliaContext-derived retrieval context."""

    def build(self, context: MemoryRetrievalContext) -> MemoryQuery:
        text = context.user_input.strip()
        lower = text.lower()
        topics = self._topics(context, lower)
        priority = self._priority(context, lower)
        memory_types = self._memory_types(priority, lower)
        return MemoryQuery(text=text, topics=topics, memory_types=memory_types, priority=priority)

    def _topics(self, context: MemoryRetrievalContext, lower: str) -> list[str]:
        topics = list(context.active_topics)
        checks = [
            ("Julia Runtime", ["julia", "runtime", "运行时"]),
            ("Context Compiler", ["context compiler", "contextcompiler", "上下文", "compiler", "编译"]),
            ("Cognitive Architecture", ["cognitive", "认知", "架构", "projection", "arbitration"]),
            ("Identity Continuity", ["为什么", "初心", "身份", "存在", "连续", "迁移", "记得"]),
            ("Project Pressure", ["压力", "做不完", "没完成", "怎么办", "累"]),
            ("Memory Runtime", ["memory", "记忆", "召回", "检索"]),
        ]
        for topic, needles in checks:
            if any(needle in lower for needle in needles):
                topics.append(topic)
        return self._dedupe(topics)

    @staticmethod
    def _priority(context: MemoryRetrievalContext, lower: str) -> dict[str, float]:
        relationship_terms = ["为什么", "初心", "关系", "身份", "存在", "连续", "迁移", "记得"]
        technical_terms = ["架构", "设计", "context", "compiler", "runtime", "模块", "代码", "怎么"]
        pressure_terms = ["压力", "做不完", "没完成", "怎么办", "累"]
        priority = {"relationship": 0.3, "technical": 0.3, "emotional": 0.2, "recurrence": 0.2}
        if any(term in lower for term in relationship_terms):
            priority.update({"relationship": 0.9, "recurrence": 0.75, "emotional": 0.65, "technical": 0.35})
        if any(term in lower for term in technical_terms):
            priority.update({"technical": max(priority["technical"], 0.9), "recurrence": max(priority["recurrence"], 0.55)})
        if context.current_arc == "project_pressure" or any(term in lower for term in pressure_terms):
            priority.update({"emotional": max(priority["emotional"], 0.75), "relationship": max(priority["relationship"], 0.65), "recurrence": max(priority["recurrence"], 0.7)})
        if context.cognitive_mode == "engineering_collaboration":
            priority["technical"] = max(priority["technical"], 0.7)
        if context.cognitive_mode == "emotional_support":
            priority["emotional"] = max(priority["emotional"], 0.8)
        return priority

    @staticmethod
    def _memory_types(priority: dict[str, float], lower: str) -> list[str]:
        if priority.get("relationship", 0.0) >= 0.8 and "怎么" not in lower:
            return ["relationship", "episodic", "semantic", "working"]
        if priority.get("technical", 0.0) >= 0.8:
            return ["semantic", "episodic", "working", "relationship"]
        return ["working", "episodic", "relationship", "semantic"]

    @staticmethod
    def _dedupe(items: list[str]) -> list[str]:
        result: list[str] = []
        for item in items:
            value = str(item).strip()
            if value and value not in result:
                result.append(value)
        return result
