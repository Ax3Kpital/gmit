"""Rule-based daily macro briefing builder — zero LLM cost."""
from dataclasses import dataclass, field
from app.analysis.signals import MacroSignals


@dataclass
class DailyBriefingData:
    date: str
    macro_regime: str
    headline: str
    key_moves: list[str]
    cot_highlights: list[str]
    alert_summary: list[str]
    watchlist: list[str]


_REGIME_HEADLINES: dict[str, str] = {
    "risk_on": (
        "Markets in risk-on mode: equities advancing, safe havens underperforming. "
        "Macro backdrop supports risk assets in the near term."
    ),
    "risk_off": (
        "Risk aversion dominates: equities under pressure, safe havens bid. "
        "Elevated uncertainty; monitor for potential trend reversal signals."
    ),
    "stagflation": (
        "Stagflationary pressures build: energy elevated while equities struggle. "
        "Difficult environment for traditional 60/40 portfolios."
    ),
    "goldilocks": (
        "Goldilocks conditions: equity trend intact with contained macro headwinds. "
        "Supportive backdrop for risk assets; watch for complacency."
    ),
    "tightening": (
        "Tightening cycle dynamics in focus: yields elevated and rising. "
        "Fixed income under pressure; watch USD strength and credit spreads."
    ),
    "easing": (
        "Easing cycle underway: yields declining, credit conditions loosening. "
        "Supportive for duration and equities; watch pace of cuts."
    ),
    "mixed": (
        "Mixed signals across asset classes — no clear directional conviction. "
        "Elevated uncertainty; position sizing and risk management critical."
    ),
}

_REGIME_WATCHLIST: dict[str, list[str]] = {
    "risk_off": [
        "Fed pivot signals: watch for dovish language in Fed communications",
        "Credit markets: monitor high-yield spreads for systemic stress",
        "VIX term structure: contango vs backwardation as fear gauge",
    ],
    "stagflation": [
        "Energy supply data: monitor oil inventory builds/draws weekly",
        "Real yields: TIPS breakevens key for inflation expectations",
        "Commodity basket: broad strength may extend stagflationary pressures",
    ],
    "tightening": [
        "Fed terminal rate: market pricing for peak funds rate",
        "Dollar index: DXY strength could pressure EM and commodities",
        "Mortgage rates: housing market as key tightening transmission channel",
    ],
    "easing": [
        "Rate cut pace: forward guidance crucial for duration positioning",
        "Credit spreads: watch IG/HY for risk-on confirmation",
        "USD weakness: commodity and EM tailwind if dollar softens",
    ],
    "risk_on": [
        "Valuation stretch: monitor P/E multiples vs earnings revision trend",
        "Momentum: watch for breadth deterioration under surface strength",
    ],
    "goldilocks": [
        "Soft landing durability: labor market data key to regime persistence",
        "Earnings quality: revenue vs margin expansion — which is driving gains",
    ],
    "mixed": [
        "Regime catalyst: next major data release could resolve current uncertainty",
        "Positioning: extreme COT readings may signal near-term mean reversion",
    ],
}


def build_briefing(
    signals: MacroSignals,
    cot_items: list[dict],
    alert_events: list[dict],
) -> DailyBriefingData:
    headline = _REGIME_HEADLINES.get(signals.macro_regime, _REGIME_HEADLINES["mixed"])
    key_moves = _build_key_moves(signals)
    cot_highlights = _build_cot_highlights(cot_items)
    alert_summary = [ev.get("message", "") for ev in alert_events[:5] if ev.get("message")]
    watchlist = _build_watchlist(signals)

    return DailyBriefingData(
        date=signals.as_of,
        macro_regime=signals.macro_regime,
        headline=headline,
        key_moves=key_moves,
        cot_highlights=cot_highlights,
        alert_summary=alert_summary,
        watchlist=watchlist,
    )


def _build_key_moves(s: MacroSignals) -> list[str]:
    moves = []

    if s.yield_10y is not None:
        d = f"{s.yield_10y_delta30d:+.2f}pp/30d" if s.yield_10y_delta30d is not None else ""
        moves.append(
            f"10Y Treasury: {s.yield_10y:.2f}% {d} — {s.curve_shape} curve "
            f"(spread {s.spread_10y2y:+.2f}%)" if s.spread_10y2y is not None
            else f"10Y Treasury: {s.yield_10y:.2f}% {d} — {s.curve_shape} curve"
        )

    if s.wti is not None:
        d = f"{s.wti_delta30d_pct:+.1f}%/30d" if s.wti_delta30d_pct is not None else ""
        moves.append(f"WTI Crude: ${s.wti:.2f} {d} — oil {s.oil_trend}")

    if s.sp500 is not None:
        d = f"{s.sp500_delta30d_pct:+.1f}%/30d" if s.sp500_delta30d_pct is not None else ""
        moves.append(f"S&P 500: {s.sp500:,.0f} {d} — equities {s.equity_trend}")

    if s.eurusd is not None:
        d = f"{s.eurusd_delta30d_pct:+.2f}%/30d" if s.eurusd_delta30d_pct is not None else ""
        moves.append(f"EUR/USD: {s.eurusd:.4f} {d} — USD {s.usd_trend}")

    return moves


def _build_cot_highlights(cot_items: list[dict]) -> list[str]:
    highlights = []
    for item in cot_items:
        pct = item.get("percentile_52w")
        name = item.get("display_name", "?")
        net = item.get("net_noncomm")
        net_str = f"{net:+,}" if net is not None else "N/A"
        if pct is None:
            continue
        if pct >= 80:
            highlights.append(
                f"{name}: EXTREME LONG ({pct:.0f}th pct, net {net_str}) — "
                "elevated speculative longs; contrarian positioning risk"
            )
        elif pct <= 20:
            highlights.append(
                f"{name}: EXTREME SHORT ({pct:.0f}th pct, net {net_str}) — "
                "specs heavily short; potential squeeze risk"
            )
    return highlights


def _build_watchlist(s: MacroSignals) -> list[str]:
    items = list(_REGIME_WATCHLIST.get(s.macro_regime, _REGIME_WATCHLIST["mixed"]))

    if s.curve_shape == "inverted":
        items.append(
            "Yield curve: sustained inversion — watch for un-inversion as recession signal"
        )
    if s.oil_trend == "rising" and s.macro_regime not in ("risk_on", "goldilocks"):
        items.append("Oil supply premium: elevated energy costs risk margin compression")

    return items[:5]
