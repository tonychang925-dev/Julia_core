"""Market Evidence Formatter — single reusable boundary between Market Brain raw output and Julia LLM context.

Principle:
  Market Brain raw result → ONE formatter → human-readable Julia context.
  NOT: JuliaSession one formatter, :18089 another formatter.

Used by BOTH:
  - JuliaSession._format_market_context() (ContextBlocks path)
  - :18089 market tool handler (raw capability result path)

ai_theme_app owns facts. Julia owns understanding. This formatter just translates.
"""

from __future__ import annotations

from typing import Any


def _status_line(data: dict[str, Any]) -> str:
    """Extract status + reason from Market Brain response envelope."""
    status = data.get("status", "")
    reason = data.get("reason", "")
    if status and status != "ok":
        return f"状态: {status}" + (f" ({reason})" if reason else "")
    if reason and status == "ok":
        return f"({reason})"
    return ""


def _date_line(data: dict[str, Any]) -> str:
    """Extract trade_date from response."""
    date = data.get("trade_date", data.get("as_of", ""))
    if date:
        return f"数据日期: {date}"
    return ""


def format_market_snapshot(data: dict[str, Any]) -> str:
    """Format market.snapshot.read / review_market_snapshot result → readable context.

    Real schema (analyst-workbench.intelligence.v1):
      {status, reason, trade_date, market_view: {sentiment?, themes?, risks?}, claims: [...]}
    """
    parts = ["[市场全景 — 来自 Market Brain 实时数据]"]

    status_line = _status_line(data)
    date_line = _date_line(data)

    if status_line:
        parts.append(status_line)
    if date_line:
        parts.append(date_line)

    # Extract from market_view (nested dict)
    mv = data.get("market_view", {})
    if isinstance(mv, dict) and mv:
        sentiment = mv.get("sentiment", mv.get("market_sentiment", ""))
        if sentiment:
            parts.append(f"市场情绪: {sentiment}")

        themes = mv.get("themes", mv.get("active_themes", ()))
        if isinstance(themes, (list, tuple)) and themes:
            themes_str = ", ".join(str(t) for t in themes[:8])
            parts.append(f"活跃题材({len(themes)}): {themes_str}")

        risks = mv.get("risks", mv.get("risk_alerts", ()))
        if isinstance(risks, (list, tuple)) and risks:
            parts.append(f"风险: {'; '.join(str(r) for r in risks[:5])}")

        # Generic: render any remaining keys
        rendered = {"sentiment", "market_sentiment", "themes", "active_themes", "risks", "risk_alerts"}
        for k, v in mv.items():
            if k not in rendered and not isinstance(v, (dict, list)):
                parts.append(f"  {k}: {v}")

    # Extract from claims (top-level list)
    claims = data.get("claims", ())
    if isinstance(claims, (list, tuple)) and claims:
        parts.append(f"研判({len(claims)}条):")
        for c in claims[:5]:
            if isinstance(c, dict):
                parts.append(f"  - {c.get('text', c.get('claim', str(c)))}")
            else:
                parts.append(f"  - {c}")

    # If status is not_ready and no data at all, tell Julia clearly
    if not status_line or status_line.startswith("状态: not_ready"):
        if not any(p for p in parts[1:] if not p.startswith("状态:") and not p.startswith("数据日期:")):
            parts.append("(当前暂无已核准的市场快照数据。请基于已有知识和以下可用的其他数据源回答。)")

    return "\n".join(parts)


def format_market_alerts(data: dict[str, Any] | list) -> str:
    """Format market.alert.query / list_active_alerts result → readable context.

    Can be:
      - list of DecisionEnvelope objects (when data available)
      - empty list (no active alerts)
      - dict with status envelope
    """
    parts = ["[市场风险警报 — 来自 Market Brain]"]

    if isinstance(data, list):
        if not data:
            parts.append("当前无活跃风险警报。")
        else:
            for i, alert in enumerate(data[:5]):
                if isinstance(alert, dict):
                    level = alert.get("level", alert.get("type", "?"))
                    impact = alert.get("impact", "")
                    src = alert.get("source", "")
                    parts.append(f"  {i+1}. [{level}] {impact}" + (f" (来源: {src})" if src else ""))
                else:
                    parts.append(f"  {i+1}. {alert}")
            if len(data) > 5:
                parts.append(f"  ... 还有 {len(data)-5} 条")
    elif isinstance(data, dict):
        status_line = _status_line(data)
        if status_line:
            parts.append(status_line)
        items = data.get("alerts", data.get("items", data.get("claims", [])))
        for item in (items if isinstance(items, list) else [])[:5]:
            parts.append(f"  - {item}")

    return "\n".join(parts)


def format_market_regime(data: dict[str, Any]) -> str:
    """Format market.regime.read / market_regime_read result → readable context.

    Real schema: {status, reason, tool, as_of, ...regime_data}
    """
    parts = ["[市场阶段评估 — 来自 Market Brain]"]

    status_line = _status_line(data)
    date_line = _date_line(data)

    if status_line:
        parts.append(status_line)
    if date_line:
        parts.append(date_line)

    regime = data.get("regime", data.get("market_regime", ""))
    if regime:
        parts.append(f"当前阶段: {regime}")

    # Generic rendering for any other scalar fields
    skip = {"status", "reason", "tool", "as_of", "trade_date", "regime", "market_regime", "schema_version", "provider"}
    for k, v in data.items():
        if k not in skip and not isinstance(v, (dict, list)):
            parts.append(f"  {k}: {v}")

    evidence = data.get("evidence", data.get("signals", ()))
    if isinstance(evidence, (list, tuple)) and evidence:
        for e in evidence[:5]:
            if isinstance(e, dict):
                parts.append(f"  - {e.get('text', str(e))}")
            else:
                parts.append(f"  - {e}")

    if status_line and status_line.startswith("状态: unavailable"):
        parts.append("(当前市场阶段数据不可用。请告知 Tony 你无法提供实时阶段评估。)")

    return "\n".join(parts)


def format_stock_history(data: dict[str, Any], stock_code: str = "") -> str:
    """Format market.stock.history / market_stock_history result → readable context.

    Real schema: {status, reason, tool, stock_code, as_of, ...history_data}
    """
    stock_label = f" {stock_code} " if stock_code else " "
    parts = [f"[股票{stock_label}历史数据 — 来自 Market Brain]"]

    status_line = _status_line(data)
    if status_line:
        parts.append(status_line)

    date_line = _date_line(data)
    if date_line:
        parts.append(date_line)

    if isinstance(data, dict):
        if data.get("status") in ("unavailable", "not_ready"):
            parts.append("(该股票历史数据当前不可用。不要编造价格数据。)")
            return "\n".join(parts)

        # Try to extract OHLCV data
        bars = data.get("bars", data.get("data", data.get("history", ())))
        if isinstance(bars, (list, tuple)) and bars:
            parts.append(f"  近{len(bars)}个交易日:")
            for item in bars[-5:]:
                if isinstance(item, dict):
                    date = item.get("date", "?")
                    close = item.get("close", item.get("收盘价", "?"))
                    change = item.get("change_pct", item.get("涨跌幅", ""))
                    parts.append(f"    {date}: 收{close}" + (f" 涨跌{change}%" if change else ""))
        else:
            # Generic render
            skip = {"status", "reason", "tool", "stock_code", "as_of", "trade_date",
                    "schema_version", "provider", "bars", "data", "history"}
            for k, v in data.items():
                if k not in skip and not isinstance(v, (dict, list)):
                    parts.append(f"  {k}: {v}")

    return "\n".join(parts)


def format_stock_auction(data: dict[str, Any], stock_code: str = "") -> str:
    """Format market.stock.auction / market_stock_auction result → readable context.

    Real schema: {status, reason, tool, stock_code, as_of, ...auction_data}
    """
    stock_label = f" {stock_code} " if stock_code else " "
    parts = [f"[股票{stock_label}竞价数据 — 来自 Market Brain]"]

    status_line = _status_line(data)
    if status_line:
        parts.append(status_line)

    if isinstance(data, dict):
        if data.get("status") in ("unavailable", "not_ready"):
            parts.append("(该股票竞价数据当前不可用。不要编造竞价信息。)")
            return "\n".join(parts)

        direction = data.get("direction", data.get("gap_direction", ""))
        strength = data.get("strength", data.get("auction_strength", ""))
        if direction:
            parts.append(f"  竞价方向: {direction}")
        if strength:
            parts.append(f"  竞价强度: {strength}")

        skip = {"status", "reason", "tool", "stock_code", "as_of", "trade_date",
                "direction", "strength", "gap_direction", "auction_strength",
                "schema_version", "provider"}
        for k, v in data.items():
            if k not in skip and not isinstance(v, (dict, list)):
                parts.append(f"  {k}: {v}")

    return "\n".join(parts)


def format_theme_constituents(data: dict[str, Any]) -> str:
    """Format market.theme.constituents → readable context."""
    parts = ["[题材成分股 — 来自 Market Brain]"]

    status_line = _status_line(data)
    if status_line:
        parts.append(status_line)

    stocks = data.get("stocks", data.get("constituents", ()))
    if isinstance(stocks, list) and stocks:
        parts.append(f"  成分股({len(stocks)}):")
        for s in stocks[:10]:
            if isinstance(s, dict):
                code = s.get("code", s.get("stock_code", "?"))
                name = s.get("name", "")
                label = f"{code} {name}" if name else code
                parts.append(f"    {label}")
            else:
                parts.append(f"    {s}")
    else:
        if data.get("status") in ("unavailable", "not_ready"):
            parts.append("(成分股数据当前不可用。)")
        else:
            skip = {"status", "reason", "stocks", "constituents", "schema_version", "provider"}
            for k, v in data.items():
                if k not in skip and not isinstance(v, (dict, list)):
                    parts.append(f"  {k}: {v}")

    return "\n".join(parts)


def format_theme_capital(data: dict[str, Any]) -> str:
    """Format market.theme.capital → readable context."""
    parts = ["[题材资金流 — 来自 Market Brain]"]

    status_line = _status_line(data)
    if status_line:
        parts.append(status_line)

    if isinstance(data, dict):
        flow = data.get("flow", data.get("capital_flow", ""))
        trend = data.get("trend", data.get("persistence", ""))
        if flow:
            parts.append(f"  资金方向: {flow}")
        if trend:
            parts.append(f"  持续性: {trend}")
        skip = {"status", "reason", "flow", "trend", "capital_flow", "persistence",
                "schema_version", "provider"}
        for k, v in data.items():
            if k not in skip and not isinstance(v, (dict, list)):
                parts.append(f"  {k}: {v}")

    if not status_line or status_line.startswith("状态: unavailable"):
        parts.append("(资金流数据当前不可用。)")

    return "\n".join(parts)


def format_intelligence_observe(data: dict[str, Any]) -> str:
    """Format market.intelligence.observe result → readable context.

    Can receive composed results from multiple sub-calls, or a single
    market_workbench_review / intelligence observation envelope.
    """
    parts = ["[市场综合情报 — 来自 Market Brain 多维度分析]"]

    status_line = _status_line(data)
    date_line = _date_line(data)

    if status_line:
        parts.append(status_line)
    if date_line:
        parts.append(date_line)

    if isinstance(data, dict):
        # Detect which envelope we got
        if "market_view" in data:
            parts.append(format_market_snapshot(data))

        if "market_judgment" in data:
            judgment = data["market_judgment"]
            if isinstance(judgment, dict) and judgment:
                for k, v in judgment.items():
                    if not isinstance(v, (dict, list)):
                        parts.append(f"  {k}: {v}")

        # Claims at top level
        claims = data.get("claims", ())
        if isinstance(claims, (list, tuple)) and claims:
            parts.append(f"研判要点({len(claims)}):")
            for c in claims[:5]:
                if isinstance(c, dict):
                    parts.append(f"  - {c.get('text', c.get('claim', str(c)))}")
                else:
                    parts.append(f"  - {c}")

        # approval info
        approval = data.get("approval", {})
        if isinstance(approval, dict) and approval.get("status"):
            parts.append(f"核准状态: {approval['status']}")

        # Generic scalar fallback for unrecognized envelopes
        view_keys = {"market_view", "market_judgment", "claims", "approval",
                     "status", "reason", "trade_date", "as_of", "generated_at",
                     "schema_version", "provider", "opinion_mode"}
        for k, v in data.items():
            if k not in view_keys and not isinstance(v, (dict, list)):
                parts.append(f"  {k}: {v}")

    return "\n".join(parts)


# ── Dispatch ──────────────────────────────────────────────────────────────────

FORMATTERS = {
    "market.snapshot.read": format_market_snapshot,
    "market.alert.query": format_market_alerts,
    "market.regime.read": format_market_regime,
    "market.stock.history": format_stock_history,
    "market.stock.auction": format_stock_auction,
    "market.theme.constituents": format_theme_constituents,
    "market.theme.capital": format_theme_capital,
    "market.intelligence.observe": format_intelligence_observe,
}


def format_market_evidence(capability_name: str, result: dict[str, Any], **kwargs) -> str:
    """Single entry point: capability name + raw result → readable LLM context.

    Args:
        capability_name: e.g. "market.snapshot.read"
        result: raw dict from MCP tool execution
        **kwargs: extra context (e.g. stock_code for stock history)

    Returns:
        Human-readable string suitable for LLM context injection.
    """
    formatter = FORMATTERS.get(capability_name)
    if formatter is None:
        return _format_generic(capability_name, result)

    import inspect
    sig = inspect.signature(formatter)
    extra = {k: v for k, v in kwargs.items() if k in sig.parameters}

    try:
        return formatter(result, **extra)
    except Exception:
        return _format_generic(capability_name, result)


def _format_generic(capability_name: str, data: dict[str, Any]) -> str:
    """Fallback generic formatting."""
    parts = [f"[{capability_name} — 来自 Market Brain]"]
    if isinstance(data, dict):
        # Check for status envelope
        status = data.get("status", "")
        if status and status != "ok":
            parts.append(f"状态: {status}")
            reason = data.get("reason", "")
            if reason:
                parts.append(f"原因: {reason}")
        for k, v in data.items():
            if k in ("status", "reason", "schema_version", "provider"):
                continue
            if not isinstance(v, (dict, list)):
                parts.append(f"  {k}: {v}")
            elif isinstance(v, list):
                parts.append(f"  {k}: {', '.join(str(x) for x in v[:5])}")
    elif isinstance(data, list):
        for item in data[:10]:
            parts.append(f"  - {item}")
    else:
        parts.append(f"  {data}")
    return "\n".join(parts)


__all__ = [
    "format_market_evidence",
    "format_market_snapshot",
    "format_market_alerts",
    "format_market_regime",
    "format_stock_history",
    "format_stock_auction",
    "format_theme_constituents",
    "format_theme_capital",
    "format_intelligence_observe",
    "FORMATTERS",
]
