from dataclasses import dataclass


@dataclass
class MacroSignals:
    # Yield curve
    yield_10y: float | None
    yield_2y: float | None
    spread_10y2y: float | None
    yield_10y_delta30d: float | None   # pp change
    spread_delta30d: float | None      # pp change
    curve_shape: str  # "inverted" | "flat" | "normal" | "steep"

    # Commodities
    wti: float | None
    wti_delta30d_pct: float | None
    brent: float | None
    oil_trend: str  # "rising" | "falling" | "stable"

    # Equities
    sp500: float | None
    sp500_delta30d_pct: float | None
    nasdaq: float | None
    nasdaq_delta30d_pct: float | None
    equity_trend: str  # "bull" | "bear" | "sideways"

    # FX  (EURUSD: USD per EUR; DEXJPUS: JPY per USD)
    eurusd: float | None
    eurusd_delta30d_pct: float | None
    usdjpy: float | None
    usdjpy_delta30d_pct: float | None
    usd_trend: str  # "strengthening" | "weakening" | "stable"

    # Composite macro regime
    macro_regime: str  # "risk_on"|"risk_off"|"stagflation"|"goldilocks"|"tightening"|"easing"|"mixed"

    # Latest data date (most recent across all series)
    as_of: str


def _pct(current: float, prev: float) -> float:
    if prev == 0:
        return 0.0
    return (current - prev) / abs(prev) * 100


def _trend_pct(delta_pct: float | None, threshold: float = 3.0) -> str:
    if delta_pct is None:
        return "stable"
    if delta_pct > threshold:
        return "rising"
    if delta_pct < -threshold:
        return "falling"
    return "stable"


def compute_signals(snippets: list[dict]) -> MacroSignals:
    idx = {s["series_id"]: s for s in snippets}

    def val(sid: str) -> float | None:
        s = idx.get(sid)
        return s["latest_value"] if s else None

    def delta(sid: str) -> float | None:
        s = idx.get(sid)
        return s.get("delta30d") if s else None

    def delta_pct(sid: str) -> float | None:
        s = idx.get(sid)
        return s.get("delta30d_pct") if s else None

    def latest_date(sid: str) -> str | None:
        s = idx.get(sid)
        return s.get("latest_date") if s else None

    # Yield curve
    y10 = val("DGS10")
    y2 = val("DGS2")
    spread = val("T10Y2Y")
    spread_d = delta("T10Y2Y")
    y10_d = delta("DGS10")

    if spread is None:
        curve_shape = "unknown"
    elif spread < -0.10:
        curve_shape = "inverted"
    elif spread < 0.30:
        curve_shape = "flat"
    elif spread < 0.80:
        curve_shape = "normal"
    else:
        curve_shape = "steep"

    # Commodities
    wti = val("DCOILWTICO")
    wti_d_pct = delta_pct("DCOILWTICO")
    brent = val("DCOILBRENTEU")
    oil_trend = _trend_pct(wti_d_pct, threshold=4.0)

    # Equities
    sp = val("SP500")
    sp_d_pct = delta_pct("SP500")
    nq = val("NASDAQCOM")
    nq_d_pct = delta_pct("NASDAQCOM")
    equity_trend = _trend_pct(sp_d_pct, threshold=2.5)

    # FX — DEXUSEU = USD per EUR (EUR/USD), DEXJPUS = JPY per USD
    eurusd = val("DEXUSEU")
    eurusd_d_pct = delta_pct("DEXUSEU")
    # DEXJPUS = yen per dollar — higher = stronger USD
    jpy = val("DEXJPUS")
    jpy_d_pct = delta_pct("DEXJPUS")

    # USD strengthens when EUR/USD falls OR JPY/USD rises
    usd_score = 0
    if eurusd_d_pct is not None:
        if eurusd_d_pct < -1.5:
            usd_score += 1   # EUR/USD down → USD up
        elif eurusd_d_pct > 1.5:
            usd_score -= 1
    if jpy_d_pct is not None:
        if jpy_d_pct > 1.5:
            usd_score += 1   # more yen per dollar → USD up
        elif jpy_d_pct < -1.5:
            usd_score -= 1
    if usd_score >= 1:
        usd_trend = "strengthening"
    elif usd_score <= -1:
        usd_trend = "weakening"
    else:
        usd_trend = "stable"

    # Macro regime composite
    macro_regime = _classify_regime(
        curve_shape=curve_shape,
        y10_d=y10_d,
        oil_trend=oil_trend,
        equity_trend=equity_trend,
        usd_trend=usd_trend,
    )

    # Best as_of date
    dates = [latest_date(s) for s in ("DGS10", "SP500", "DCOILWTICO", "DEXUSEU") if latest_date(s)]
    as_of = max(dates) if dates else "N/A"

    return MacroSignals(
        yield_10y=y10,
        yield_2y=y2,
        spread_10y2y=spread,
        yield_10y_delta30d=y10_d,
        spread_delta30d=spread_d,
        curve_shape=curve_shape,
        wti=wti,
        wti_delta30d_pct=wti_d_pct,
        brent=brent,
        oil_trend=oil_trend,
        sp500=sp,
        sp500_delta30d_pct=sp_d_pct,
        nasdaq=nq,
        nasdaq_delta30d_pct=nq_d_pct,
        equity_trend=equity_trend,
        eurusd=eurusd,
        eurusd_delta30d_pct=eurusd_d_pct,
        usdjpy=jpy,
        usdjpy_delta30d_pct=jpy_d_pct,
        usd_trend=usd_trend,
        macro_regime=macro_regime,
        as_of=as_of,
    )


def _classify_regime(
    curve_shape: str,
    y10_d: float | None,
    oil_trend: str,
    equity_trend: str,
    usd_trend: str,
) -> str:
    yields_rising = y10_d is not None and y10_d > 0.20

    if oil_trend == "rising" and equity_trend == "bear":
        return "stagflation"

    if equity_trend == "bull" and oil_trend != "rising" and not yields_rising:
        return "goldilocks"

    if equity_trend == "bull" and oil_trend in ("rising", "stable"):
        return "risk_on"

    if equity_trend == "bear" and oil_trend == "falling":
        return "risk_off"

    if yields_rising and usd_trend == "strengthening":
        return "tightening"

    if y10_d is not None and y10_d < -0.20 and curve_shape in ("flat", "normal", "steep"):
        return "easing"

    return "mixed"
