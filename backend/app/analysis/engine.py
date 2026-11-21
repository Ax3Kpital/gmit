"""
Rules-based macro thesis engine.
Produces ThesisResult from MacroSignals + topic string — no LLM required.
"""
import time
from app.analysis.signals import MacroSignals
from app.llm.base import ThesisResult, EvidenceDTO, ScenarioDTO, CounterArgumentDTO

_TOPIC_KEYWORDS: dict[str, list[str]] = {
    "gold":     ["gold", "aur", "xau", "precious", "bullion"],
    "oil":      ["oil", "crude", "wti", "brent", "petrol", "energie", "energy", "opec", "gaz natural", "natural gas", "henry hub"],
    "bonds":    ["bond", "yield", "treasury", "obligatiune", "randament", "rates", "dobanda", "curve", "courba", "10y", "2y"],
    "equities": ["stock", "equity", "equities", "s&p", "sp500", "nasdaq", "actiuni", "market", "piata", "bursa", "equit"],
    "dollar":   ["dollar", "usd", "dolar", "dxy", "greenback", "dolarul"],
    "fx":       ["forex", "eur", "euro", "jpy", "yen", "gbp", "sterling", "yuan", "cnh", "currency", "valuta"],
}


def detect_topic(topic: str) -> str:
    t = topic.lower()
    for topic_type, keywords in _TOPIC_KEYWORDS.items():
        if any(kw in t for kw in keywords):
            return topic_type
    return "macro"


def _fmt(v: float | None, decimals: int = 2) -> str:
    if v is None:
        return "N/A"
    return f"{v:.{decimals}f}"


def _fmt_delta(v: float | None, decimals: int = 2, suffix: str = "") -> str:
    if v is None:
        return "N/A"
    sign = "+" if v >= 0 else ""
    return f"{sign}{v:.{decimals}f}{suffix}"


def _regime_label(regime: str) -> str:
    return {
        "risk_on": "risk-on",
        "risk_off": "risk-off",
        "stagflation": "stagflationary",
        "goldilocks": "goldilocks",
        "tightening": "tightening",
        "easing": "easing",
        "mixed": "mixed",
    }.get(regime, "mixed")


# ---------------------------------------------------------------------------
# Topic builders
# ---------------------------------------------------------------------------

def _gold_thesis(s: MacroSignals, topic: str) -> tuple[str, int, str, str, list[str], list[str], list[ScenarioDTO], list[CounterArgumentDTO], list[EvidenceDTO]]:
    usd = s.usd_trend
    curve = s.curve_shape
    regime = s.macro_regime
    y10 = _fmt(s.yield_10y)
    y10_d = _fmt_delta(s.yield_10y_delta30d, suffix="pp")
    spread = _fmt(s.spread_10y2y)
    eurusd = _fmt(s.eurusd, 4)

    if usd == "weakening" and s.yield_10y_delta30d is not None and s.yield_10y_delta30d < 0:
        confidence = 68
        time_horizon = "3M"
        claim = (
            f"Gold is positioned for meaningful upside as real yields fall and the dollar weakens, "
            f"with the 10Y at {y10}% ({y10_d} over 30 days) and EUR/USD at {eurusd}."
        )
        rationale = (
            f"Gold's primary macro drivers — real interest rates and dollar strength — are both moving in its favour. "
            f"The U.S. 10-year yield stands at {y10}%, having moved {y10_d} over the past 30 days, "
            f"while the dollar is in a weakening trend (EUR/USD: {eurusd}). "
            f"A falling-rate environment reduces the opportunity cost of holding a non-yielding asset like gold, "
            f"historically one of the strongest bull catalysts.\n\n"
            f"The yield curve ({curve}, spread: {spread}%) also suggests a macro environment where "
            f"central bank credibility is being tested. In past {curve} curve episodes, gold has outperformed "
            f"over 3-6 month windows as investors reassess duration risk.\n\n"
            f"Current macro regime is assessed as {_regime_label(regime)}, which historically correlates "
            f"with increased safe-haven and inflation-hedge demand."
        )
        catalysts = [
            f"Further decline in 10Y real yields below current {y10}% level",
            "Continued dollar weakness accelerating capital flows into commodities",
            "Central bank reserve diversification away from USD-denominated assets",
            "Geopolitical risk premium re-pricing",
        ]
        invalidations = [
            f"Sustained 10Y yield recovery above {_fmt(s.yield_10y + 0.5 if s.yield_10y else None)}% would pressure gold",
            "Dollar reversal driven by strong U.S. data surprise",
            "Risk-on rally reducing safe-haven demand",
        ]
        scenarios = [
            ScenarioDTO("Base", 55, f"Gradual gold appreciation as yields stabilise near {y10}% and dollar remains soft.", "Fed holds rates, dollar drift continues."),
            ScenarioDTO("Bull", 30, "Accelerated rally if yields break lower and institutional flows pile in.", "Fed signals rate cuts or yield curve control measures."),
            ScenarioDTO("Bear", 15, "Pullback on dollar reversal or risk-on rotation out of safe havens.", "U.S. labour data surprises to the upside, pushing yields higher."),
        ]
        counter_args = [
            CounterArgumentDTO("High real yields in other G10 economies may cap USD weakness and by extension gold upside.", "moderate"),
            CounterArgumentDTO("Stretched speculative positioning in gold futures could trigger a sharp short-term correction.", "moderate"),
            CounterArgumentDTO("A global risk-on rotation may favour equities over gold despite weak dollar.", "weak"),
        ]

    elif usd == "strengthening" and s.yield_10y_delta30d is not None and s.yield_10y_delta30d > 0:
        confidence = 62
        time_horizon = "3M"
        claim = (
            f"Gold faces headwinds from dollar strength and rising nominal yields ({y10}%, {y10_d} over 30d), "
            f"though structural demand provides a floor."
        )
        rationale = (
            f"Gold is navigating a difficult near-term environment: the dollar is strengthening (EUR/USD: {eurusd}), "
            f"and U.S. 10-year yields have risen {y10_d} over the past 30 days to {y10}%. "
            f"Rising nominal yields increase the opportunity cost of gold, typically a headwind for the metal.\n\n"
            f"The yield curve is currently {curve} (spread: {spread}%), and the macro regime reads as "
            f"{_regime_label(regime)}. In tightening cycles, gold has historically underperformed until "
            f"the terminal rate becomes visible.\n\n"
            f"Central bank physical demand and geopolitical reserve diversification provide structural support "
            f"that may prevent a deep drawdown, but momentum is unfavourable near-term."
        )
        catalysts = [
            "Fed pivot signal or pause in rate hike cycle",
            "Geopolitical escalation driving safe-haven demand regardless of yield environment",
            "Inflation data surprising to the upside, boosting gold's inflation-hedge appeal",
        ]
        invalidations = [
            f"Yields continuing to rise above {_fmt(s.yield_10y + 0.75 if s.yield_10y else None)}% would extend gold weakness",
            "Dollar index breaking to new cycle highs on strong U.S. data",
        ]
        scenarios = [
            ScenarioDTO("Base", 50, f"Gold consolidates in a range as yields stabilise near {y10}% and dollar upside is limited.", "Fed signals approaching terminal rate."),
            ScenarioDTO("Bull", 20, "Reversal on Fed pivot or inflation spike reignites gold demand.", "CPI surprise or Fed guidance shift."),
            ScenarioDTO("Bear", 30, "Continued yield rise and dollar strength push gold to retest key support.", "Hot labour or inflation data forces further Fed tightening."),
        ]
        counter_args = [
            CounterArgumentDTO("Central bank gold buying (especially EM) has been at multi-decade highs, providing structural demand.", "strong"),
            CounterArgumentDTO("Historically gold has eventually rallied after the last Fed hike — timing the turn is the challenge.", "moderate"),
        ]

    else:
        confidence = 48
        time_horizon = "3M"
        claim = (
            f"Gold's near-term outlook is mixed with macro signals in flux — 10Y yield at {y10}%, "
            f"yield curve {curve}, macro regime {_regime_label(regime)}."
        )
        rationale = (
            f"The macro backdrop for gold is currently ambiguous. The 10-year yield stands at {y10}% "
            f"(30d change: {y10_d}), the yield curve is {curve} (spread: {spread}%), and the dollar "
            f"is broadly {usd}. None of these individually provide a clear directional signal for gold.\n\n"
            f"The current macro regime ({_regime_label(regime)}) does not historically map cleanly to "
            f"either strong bull or bear gold outcomes. In mixed environments, gold tends to track "
            f"real yield movements closely — monitoring the 10Y-CPI relationship is key."
        )
        catalysts = [
            "Break in either direction in real yields would provide directional catalyst",
            "Dollar trend clarification (sustained move in either direction)",
            "Geopolitical or financial system stress event",
        ]
        invalidations = [
            "Sharp dollar rally combined with yield spike",
            "Sustained risk-on regime reducing safe-haven flows",
        ]
        scenarios = [
            ScenarioDTO("Base", 55, "Gold trades sideways in current range pending clearer macro direction.", "No significant catalyst in either direction."),
            ScenarioDTO("Bull", 25, "Macro signal clarifies in gold's favour as yields/dollar both soften.", "Fed dovish pivot or geopolitical shock."),
            ScenarioDTO("Bear", 20, "Dollar and yield strength assert themselves, pressuring gold.", "Strong U.S. data pushes yields and dollar higher."),
        ]
        counter_args = [
            CounterArgumentDTO("Mixed signals often resolve to the downside in the near-term as uncertainty premia compress.", "moderate"),
            CounterArgumentDTO("Gold's high correlation with real yields means a surprise rate move could quickly change the picture.", "moderate"),
        ]

    evidence = [
        EvidenceDTO("U.S. 10-Year Treasury Yield", "DGS10", s.yield_10y, s.as_of,
                    f"Primary gold headwind/tailwind. Currently at {y10}%, 30d change {y10_d}. Falling yields reduce opportunity cost of gold."),
        EvidenceDTO("10Y-2Y Yield Spread", "T10Y2Y", s.spread_10y2y, s.as_of,
                    f"Curve shape ({curve}, {spread}%) signals macro stress level and rate-cycle positioning."),
        EvidenceDTO("EUR/USD Exchange Rate", "DEXUSEU", s.eurusd, s.as_of,
                    f"Dollar proxy: EUR/USD at {eurusd}, 30d change {_fmt_delta(s.eurusd_delta30d_pct, 2, '%')}. USD trend: {usd}."),
    ]

    return claim, confidence, time_horizon, rationale, catalysts, invalidations, scenarios, counter_args, evidence


def _oil_thesis(s: MacroSignals, topic: str) -> tuple:
    wti = _fmt(s.wti)
    brent = _fmt(s.brent)
    wti_d = _fmt_delta(s.wti_delta30d_pct, 1, "%")
    regime = _regime_label(s.macro_regime)
    sp = _fmt(s.sp500, 0)

    if s.oil_trend == "rising" and s.equity_trend in ("bull", "sideways"):
        confidence = 63
        time_horizon = "3M"
        claim = (
            f"Oil maintains a constructive bias at WTI ${wti}/bbl ({wti_d} over 30d) "
            f"supported by demand resilience in an {regime} macro environment."
        )
        rationale = (
            f"WTI crude is trading at ${wti}/bbl with Brent at ${brent}/bbl, up {wti_d} over the past 30 days. "
            f"The prevailing {regime} macro regime — with equities {s.equity_trend} — implies demand-side "
            f"resilience that supports the current price floor.\n\n"
            f"Supply dynamics remain a key variable: OPEC+ production discipline, U.S. rig count trajectory, "
            f"and geopolitical risk premiums are all active factors. Historically, oil has sustained upward "
            f"momentum in {regime} environments when demand signals are confirmed by equity market strength.\n\n"
            f"Energy sector margins at current levels remain attractive for producers, which may incentivise "
            f"incremental supply — the primary risk to the bullish case."
        )
        catalysts = [
            "OPEC+ production cut extension or surprise additional cuts",
            f"Global demand pickup sustaining S&P 500 above {sp}",
            "Supply disruption from geopolitical event in key producing region",
            "U.S. dollar weakening reducing oil price pressure for non-USD buyers",
        ]
        invalidations = [
            f"WTI breaking below ${_fmt(s.wti - 10 if s.wti else None)}/bbl on demand destruction",
            "Sharp macro deterioration flipping equity market to bear territory",
            "Large surprise U.S. inventory build signalling demand weakness",
        ]
        scenarios = [
            ScenarioDTO("Base", 55, f"Oil consolidates near current levels with moderate upside. WTI range ${_fmt(s.wti)}–${_fmt(s.wti + 8 if s.wti else None)}/bbl.", "OPEC+ discipline holds, demand stable."),
            ScenarioDTO("Bull", 25, "Supply shock or demand acceleration pushes WTI materially higher.", "Geopolitical disruption or inventory draw surprise."),
            ScenarioDTO("Bear", 20, "Macro slowdown or supply surge breaks support.", "Recession signal or OPEC+ compliance breakdown."),
        ]
        counter_args = [
            CounterArgumentDTO("High oil prices are self-limiting — they eventually suppress demand and incentivise alternative energy adoption.", "strong"),
            CounterArgumentDTO("U.S. shale producers can rapidly increase output at current prices, capping the upside.", "moderate"),
        ]

    elif s.oil_trend == "falling":
        confidence = 61
        time_horizon = "3M"
        claim = (
            f"Oil is under pressure at WTI ${wti}/bbl ({wti_d} over 30d), "
            f"reflecting {regime} macro conditions and demand-side concerns."
        )
        rationale = (
            f"WTI crude has declined {wti_d} over the past 30 days to ${wti}/bbl, with Brent at ${brent}/bbl. "
            f"The falling trend coincides with a {regime} macro backdrop: equities are {s.equity_trend}, "
            f"suggesting demand concerns rather than pure supply-driven weakness.\n\n"
            f"The yield curve is {s.curve_shape} (spread: {_fmt(s.spread_10y2y)}%), which "
            f"{'historically precedes demand slowdowns that negatively impact oil' if s.curve_shape == 'inverted' else 'adds uncertainty to the demand outlook'}.\n\n"
            f"At current levels, marginal U.S. shale production becomes less economic, which may provide "
            f"a natural floor — but OPEC+ response timing is the critical swing factor."
        )
        catalysts = [
            "OPEC+ emergency cuts in response to price weakness",
            "Macro improvement flipping equity sentiment positive",
            "Supply disruption reducing available barrels",
        ]
        invalidations = [
            f"WTI breaking ${_fmt(s.wti - 8 if s.wti else None)}/bbl signals deeper demand destruction",
            "Global recession confirmation removing the demand recovery case",
        ]
        scenarios = [
            ScenarioDTO("Base", 50, f"Oil stabilises near current levels as OPEC+ adjusts supply. WTI ~${wti}/bbl.", "OPEC+ production cut response."),
            ScenarioDTO("Bull", 25, "Sharper-than-expected production cuts drive recovery.", "OPEC+ emergency meeting + cut announcement."),
            ScenarioDTO("Bear", 25, "Demand destruction accelerates; WTI breaks to new lows.", "Global recession data confirmed."),
        ]
        counter_args = [
            CounterArgumentDTO("OPEC+ has demonstrated willingness to defend price floors, limiting downside duration.", "strong"),
            CounterArgumentDTO("Energy transition investments reducing long-run demand may structurally cap recovery.", "moderate"),
        ]

    else:
        confidence = 47
        time_horizon = "3M"
        claim = f"Oil is in a stable range at WTI ${wti}/bbl, with no strong directional catalyst evident in a {regime} macro environment."
        rationale = (
            f"WTI crude is trading at ${wti}/bbl (Brent: ${brent}/bbl) with a 30-day price change of {wti_d}. "
            f"The market appears balanced near current levels, with macro conditions ({regime}) neither "
            f"strongly supportive nor pressuring.\n\n"
            f"Directional catalysts — OPEC+ policy changes, significant demand data surprises, or "
            f"geopolitical supply disruptions — are the key swing factors to monitor."
        )
        catalysts = ["OPEC+ policy change", "Significant demand data surprise", "Geopolitical supply disruption"]
        invalidations = ["Range break in either direction on macro data", "Large inventory build or draw"]
        scenarios = [
            ScenarioDTO("Base", 60, f"Oil remains range-bound near ${wti}/bbl pending clearer macro direction.", "No major supply/demand catalyst."),
            ScenarioDTO("Bull", 20, "Supply tightens unexpectedly.", "Geopolitical event or OPEC+ cut."),
            ScenarioDTO("Bear", 20, "Demand data disappoints.", "Macro slowdown confirmed."),
        ]
        counter_args = [
            CounterArgumentDTO("Stable price regimes often precede sharp moves — direction risk is elevated.", "moderate"),
        ]

    evidence = [
        EvidenceDTO("WTI Crude Oil", "DCOILWTICO", s.wti, s.as_of,
                    f"Spot price ${wti}/bbl, 30d change {wti_d}. Primary oil price benchmark for U.S. crude."),
        EvidenceDTO("Brent Crude Oil", "DCOILBRENTEU", s.brent, s.as_of,
                    f"International benchmark at ${brent}/bbl. Brent-WTI spread indicates logistical/quality differentials."),
        EvidenceDTO("S&P 500 Index", "SP500", s.sp500, s.as_of,
                    f"Equity market at {sp} ({_fmt_delta(s.sp500_delta30d_pct, 1, '%')} 30d) — proxy for global demand expectations."),
    ]
    return claim, confidence, time_horizon, rationale, catalysts, invalidations, scenarios, counter_args, evidence


def _bonds_thesis(s: MacroSignals, topic: str) -> tuple:
    y10 = _fmt(s.yield_10y)
    y2 = _fmt(s.yield_2y)
    spread = _fmt(s.spread_10y2y)
    y10_d = _fmt_delta(s.yield_10y_delta30d, suffix="pp")
    spread_d = _fmt_delta(s.spread_delta30d, suffix="pp")
    regime = _regime_label(s.macro_regime)

    if s.curve_shape == "inverted":
        confidence = 70
        time_horizon = "6M"
        claim = (
            f"The inverted U.S. yield curve (10Y: {y10}%, 2Y: {y2}%, spread: {spread}%) "
            f"continues to signal elevated recession risk over a 6-12 month horizon."
        )
        rationale = (
            f"The U.S. Treasury yield curve is currently inverted at {spread}% (10Y at {y10}%, 2Y at {y2}%), "
            f"a configuration with a strong historical track record as a leading recession indicator — "
            f"every U.S. recession since 1955 was preceded by a yield curve inversion.\n\n"
            f"The spread has changed {spread_d} over the past 30 days, and the 10Y yield has moved {y10_d}. "
            f"Duration of the inversion matters: inversions persisting beyond 6 months have historically "
            f"been particularly reliable recession predictors.\n\n"
            f"The macro regime ({regime}) combined with an inverted curve implies that short-duration "
            f"Treasuries offer attractive risk-adjusted returns while long-duration bonds may benefit "
            f"from a flight-to-quality bid if the recession scenario materialises."
        )
        catalysts = [
            "Economic data deterioration confirming the recessionary signal",
            "Fed pivot/pause allowing the front end to rally (curve steepening)",
            "Credit spread widening validating the risk-off thesis",
            "Labour market softening confirming demand destruction",
        ]
        invalidations = [
            f"Curve normalising above {_fmt((s.spread_10y2y or 0) + 0.50)}% would reduce recession probability",
            "Strong GDP and employment data sustaining a no-landing scenario",
            "Inflation re-acceleration forcing the curve to remain inverted for non-recessionary reasons",
        ]
        scenarios = [
            ScenarioDTO("Soft landing", 40, "Curve gradually steepens as Fed cuts without triggering recession. Duration rally.", "Fed cuts while unemployment stays below 5%."),
            ScenarioDTO("Hard landing", 35, "Inversion followed by sharp steepening as short rates collapse in recession. Long bonds outperform.", "Unemployment spikes, credit spreads blow out."),
            ScenarioDTO("Higher for longer", 25, "Inversion persists as inflation remains sticky. Front end stays elevated.", "CPI re-acceleration above 3.5%."),
        ]
        counter_args = [
            CounterArgumentDTO("The 'this time is different' argument: structural factors (QE, foreign demand) may have broken the yield curve's predictive signal.", "moderate"),
            CounterArgumentDTO("Long inversion with no recession yet suggests the lag may be even longer than historical averages.", "moderate"),
            CounterArgumentDTO("Strong labour market and consumer spending continuously push out the recession timeline.", "strong"),
        ]

    elif s.curve_shape in ("flat", "normal"):
        confidence = 55
        time_horizon = "3M"
        claim = (
            f"The {s.curve_shape} yield curve (10Y: {y10}%, 2Y: {y2}%, spread: {spread}%) "
            f"reflects policy uncertainty in a {regime} macro environment."
        )
        rationale = (
            f"The U.S. Treasury curve is currently {s.curve_shape} at {spread}% spread "
            f"(10Y: {y10}%, 2Y: {y2}%). The 10Y has moved {y10_d} over the past 30 days.\n\n"
            f"A {s.curve_shape} curve historically signals that markets are pricing in policy "
            f"{'uncertainty about the rate path' if s.curve_shape == 'flat' else 'normalisation'}. "
            f"In {regime} macro environments, this configuration tends to precede "
            f"{'further flattening or brief inversion' if s.curve_shape == 'flat' else 'gradual steepening as growth stabilises'}.\n\n"
            f"Duration positioning in this environment favours an intermediate-term barbell: "
            f"short-end yields remain attractive on a carry basis while long-end provides "
            f"convexity protection against macro deterioration."
        )
        catalysts = [
            "Fed guidance shift altering rate path expectations",
            f"Economic data print causing significant repricing at the {'2Y' if s.yield_2y and s.yield_2y > (s.yield_10y or 0) else '10Y'}",
            "Foreign central bank buying shifting term premium dynamics",
        ]
        invalidations = [
            "Inflation data surprise forcing further front-end repricing",
            "Strong growth data reducing rate cut expectations",
        ]
        scenarios = [
            ScenarioDTO("Steepening", 45, "Curve steepens as front end rallies on rate cut pricing. Duration benefits.", "Fed signals cuts as labour market softens."),
            ScenarioDTO("Stable", 35, "Curve holds current shape with limited movement pending data.", "No major data or policy surprise."),
            ScenarioDTO("Inversion", 20, "Curve inverts on inflation resurgence forcing more hikes.", "CPI re-accelerates above 3.5%."),
        ]
        counter_args = [
            CounterArgumentDTO("Term premium has been structurally suppressed by QE — curve signals may be less reliable in the current cycle.", "moderate"),
            CounterArgumentDTO(f"The absolute level of 10Y at {y10}% provides limited historical context for current valuations.", "weak"),
        ]

    else:  # steep
        confidence = 57
        time_horizon = "6M"
        claim = (
            f"A steep yield curve (10Y: {y10}%, 2Y: {y2}%, spread: {spread}%) "
            f"suggests reflationary dynamics or term premium expansion in a {regime} environment."
        )
        rationale = (
            f"The U.S. yield curve has steepened to {spread}% (10Y: {y10}%, 2Y: {y2}%), "
            f"a level historically associated with either early economic recovery or rising inflation expectations. "
            f"The 10Y has moved {y10_d} over the past month.\n\n"
            f"In the current {regime} macro context, steep curves typically signal that markets are pricing "
            f"growth recovery and/or inflation persistence. Long-duration bonds face headwinds from "
            f"rising term premium, while the short end may begin to price rate cuts if growth has already peaked.\n\n"
            f"Credit and equities tend to outperform duration in steep curve environments — "
            f"the risk-reward for long duration is asymmetrically unfavourable until the curve re-flattens."
        )
        catalysts = [
            "Continued growth/inflation data supporting the reflationary thesis",
            "Central bank bond purchases (QE) compressing long-end yields",
            "Fiscal expansion increasing bond supply and pushing long yields higher",
        ]
        invalidations = [
            "Sharp slowdown in economic data causing bull flattening",
            f"10Y breaking above {_fmt(s.yield_10y + 0.50 if s.yield_10y else None)}% triggering forced selling",
        ]
        scenarios = [
            ScenarioDTO("Bear steepening continues", 40, "Long yields rise further on fiscal/inflation concerns. Duration underperforms.", "Fiscal expansion or inflation resurgence."),
            ScenarioDTO("Bull flattening", 40, "Growth disappoints; curve flattens as front end stays sticky and long end rallies.", "GDP/employment data miss."),
            ScenarioDTO("Parallel shift", 20, "Curve moves in parallel on global macro repricing.", "Coordinated central bank guidance change."),
        ]
        counter_args = [
            CounterArgumentDTO("Foreign demand for U.S. Treasuries may absorb supply and cap long-end yields despite steep curve.", "moderate"),
            CounterArgumentDTO("Steep curves in late-cycle have historically been poor timing signals — growth can remain strong for extended periods.", "moderate"),
        ]

    evidence = [
        EvidenceDTO("U.S. 10-Year Treasury Yield", "DGS10", s.yield_10y, s.as_of,
                    f"Long-end benchmark at {y10}%, 30d change {y10_d}. Key rate for mortgage, credit and equity discount rates."),
        EvidenceDTO("U.S. 2-Year Treasury Yield", "DGS2", s.yield_2y, s.as_of,
                    f"Policy-sensitive front end at {y2}%. Closely tracks Fed funds rate expectations."),
        EvidenceDTO("10Y-2Y Yield Spread", "T10Y2Y", s.spread_10y2y, s.as_of,
                    f"Spread at {spread}% ({s.curve_shape} curve), 30d change {spread_d}. Canonical recession indicator."),
    ]
    return claim, confidence, time_horizon, rationale, catalysts, invalidations, scenarios, counter_args, evidence


def _equities_thesis(s: MacroSignals, topic: str) -> tuple:
    sp = _fmt(s.sp500, 0)
    sp_d = _fmt_delta(s.sp500_delta30d_pct, 1, "%")
    nq_d = _fmt_delta(s.nasdaq_delta30d_pct, 1, "%")
    regime = _regime_label(s.macro_regime)
    y10 = _fmt(s.yield_10y)
    spread = _fmt(s.spread_10y2y)

    if s.equity_trend == "bull":
        confidence = 62
        time_horizon = "3M"
        claim = (
            f"U.S. equities maintain bullish momentum (S&P 500: {sp}, {sp_d} over 30d) "
            f"in a {regime} macro regime, though valuation and yield dynamics warrant monitoring."
        )
        rationale = (
            f"The S&P 500 stands at {sp} with a 30-day return of {sp_d}, and the Nasdaq has moved {nq_d}. "
            f"The {regime} macro backdrop supports risk asset performance in the near term.\n\n"
            f"The 10-year yield at {y10}% and yield curve at {spread}% ({s.curve_shape}) represent "
            f"the primary macro headwind to monitor: rising yields compress equity valuations through "
            f"higher discount rates, particularly in growth-heavy Nasdaq constituents.\n\n"
            f"Dollar trend ({s.usd_trend}) has implications for S&P 500 earnings: approximately 40% of "
            f"S&P 500 revenues are international, making USD strength a moderate earnings headwind.\n\n"
            f"Breadth and sector rotation are key technical signals — a narrow rally concentrated in "
            f"mega-cap names is less sustainable than broad participation."
        )
        catalysts = [
            "Earnings growth exceeding analyst estimates in upcoming reporting season",
            "Fed pivot or rate cut signal reducing the discount rate headwind",
            f"10Y yield declining from current {y10}% expanding equity P/E multiples",
            "Risk-on rotation from bonds to equities on improving macro data",
        ]
        invalidations = [
            f"10Y yield break above {_fmt(s.yield_10y + 0.75 if s.yield_10y else None)}% triggering multiple compression",
            "Earnings recession with two consecutive quarters of declining S&P 500 EPS",
            "Credit spread widening signalling financial stress",
        ]
        scenarios = [
            ScenarioDTO("Continuation", 50, f"S&P 500 grinds higher on earnings growth. Target: {_fmt(s.sp500 * 1.08 if s.sp500 else None, 0)}.", "Soft landing confirmed, yields stable."),
            ScenarioDTO("Consolidation", 30, "Sideways market as yield uncertainty limits multiple expansion.", "Mixed macro data, Fed holds."),
            ScenarioDTO("Correction", 20, "10-15% pullback on yield spike or earnings miss.", "Hot inflation data or credit event."),
        ]
        counter_args = [
            CounterArgumentDTO("Equity valuations (P/E) remain elevated relative to historical averages given current yield levels.", "strong"),
            CounterArgumentDTO("Inverted or flat yield curve historically precedes earnings deterioration with a 6-12 month lag.", "moderate"),
            CounterArgumentDTO("Narrow market breadth with rally concentrated in a few mega-cap names is a historically bearish signal.", "moderate"),
        ]

    elif s.equity_trend == "bear":
        confidence = 64
        time_horizon = "3M"
        claim = (
            f"U.S. equities are in a corrective phase (S&P 500: {sp}, {sp_d} over 30d), "
            f"with a {regime} macro backdrop and {s.curve_shape} yield curve adding to headwinds."
        )
        rationale = (
            f"The S&P 500 has declined {sp_d} over the past 30 days to {sp}, with Nasdaq down {nq_d}. "
            f"The current {regime} macro regime, characterised by "
            f"{'falling equities and oil simultaneously' if s.oil_trend == 'falling' else 'deteriorating risk sentiment'}, "
            f"supports a cautious near-term equity outlook.\n\n"
            f"The 10-year yield at {y10}% and a {s.curve_shape} yield curve ({spread}%) "
            f"{'historically precede demand slowdowns that pressure corporate earnings' if s.curve_shape == 'inverted' else 'reflect macro uncertainty'}. "
            f"Credit spreads and earnings guidance revisions are the key indicators to monitor for "
            f"signs of a bottom or further deterioration.\n\n"
            f"Positioning and sentiment indicators typically reach extremes (high VIX, elevated put/call ratios, "
            f"oversold breadth) before meaningful bounces — these metrics should be tracked alongside "
            f"the macro signals."
        )
        catalysts = [
            "Fed pivot or pause providing a relief rally",
            "Oversold technical conditions triggering short-covering bounce",
            "Earnings beats resetting expectations lower than feared",
        ]
        invalidations = [
            f"S&P 500 breaking below {_fmt(s.sp500 * 0.90 if s.sp500 else None, 0)} would confirm deeper bear market",
            "Credit event or financial stress spreading beyond equities",
            "Earnings recession materialising beyond current estimates",
        ]
        scenarios = [
            ScenarioDTO("Bounce then fade", 40, "Technical bounce followed by retest of lows as fundamentals remain weak.", "Oversold bounce, then macro deterioration."),
            ScenarioDTO("Bear market rally", 30, "Sustained 10-20% rally on Fed pivot hopes, then new lows later.", "Fed signals pause or cut."),
            ScenarioDTO("Continued decline", 30, f"S&P 500 breaks to {_fmt(s.sp500 * 0.85 if s.sp500 else None, 0)} on recession confirmation.", "Hard landing data confirms."),
        ]
        counter_args = [
            CounterArgumentDTO("Historically, equity bear markets in non-recessionary environments are shallower and shorter than feared.", "moderate"),
            CounterArgumentDTO("Strong labour market and consumer balance sheets suggest earnings resilience not yet priced in.", "moderate"),
        ]

    else:
        confidence = 48
        time_horizon = "3M"
        claim = (
            f"U.S. equities (S&P 500: {sp}, {sp_d} 30d) are in a holding pattern "
            f"in a {regime} macro environment, awaiting a directional catalyst."
        )
        rationale = (
            f"The S&P 500 is at {sp} with a modest 30-day change of {sp_d}. The {regime} macro regime "
            f"and {s.curve_shape} yield curve ({spread}%) do not provide a strong directional bias.\n\n"
            f"At this juncture, earnings visibility and Fed guidance are the key catalysts to watch. "
            f"The 10Y at {y10}% provides an equity valuation anchor — movements here will be the "
            f"primary driver of P/E multiple expansion or compression."
        )
        catalysts = ["Earnings growth surprise", "Fed guidance shift", "Macro data break in either direction"]
        invalidations = ["Yield spike above 50bp from current levels", "Earnings miss cycle beginning"]
        scenarios = [
            ScenarioDTO("Mild upside", 40, f"Equities drift to {_fmt(s.sp500 * 1.05 if s.sp500 else None, 0)} on stable macro.", "Goldilocks data continues."),
            ScenarioDTO("Sideways", 35, "Range-bound market pending clearer catalysts.", "Mixed data, Fed holds."),
            ScenarioDTO("Pullback", 25, f"S&P 500 drops to {_fmt(s.sp500 * 0.93 if s.sp500 else None, 0)} on yield spike or earnings miss.", "Hot CPI or guidance cuts."),
        ]
        counter_args = [
            CounterArgumentDTO("Sideways markets often resolve to the downside when macro uncertainty is elevated.", "moderate"),
        ]

    evidence = [
        EvidenceDTO("S&P 500 Index", "SP500", s.sp500, s.as_of,
                    f"U.S. large-cap benchmark at {sp}, 30d performance {sp_d}. Broad equity market health indicator."),
        EvidenceDTO("Nasdaq Composite", "NASDAQCOM", s.nasdaq, s.as_of,
                    f"Growth/tech-heavy index, 30d change {nq_d}. High sensitivity to real yield movements."),
        EvidenceDTO("U.S. 10-Year Treasury Yield", "DGS10", s.yield_10y, s.as_of,
                    f"Equity discount rate proxy at {y10}%. Rising yields compress P/E multiples, especially in Nasdaq."),
    ]
    return claim, confidence, time_horizon, rationale, catalysts, invalidations, scenarios, counter_args, evidence


def _dollar_thesis(s: MacroSignals, topic: str) -> tuple:
    eurusd = _fmt(s.eurusd, 4)
    eurusd_d = _fmt_delta(s.eurusd_delta30d_pct, 2, "%")
    usdjpy = _fmt(s.usdjpy, 2)
    y10 = _fmt(s.yield_10y)
    regime = _regime_label(s.macro_regime)
    usd = s.usd_trend

    if usd == "strengthening":
        confidence = 63
        time_horizon = "3M"
        claim = (
            f"The U.S. dollar is in a strengthening trend (EUR/USD: {eurusd}, {eurusd_d} 30d) "
            f"driven by yield differentials and {regime} macro conditions."
        )
        rationale = (
            f"The dollar index is strengthening: EUR/USD is at {eurusd} ({eurusd_d} 30d), "
            f"and USD/JPY at {usdjpy} reflects relative yield differentials. "
            f"With the U.S. 10-year yield at {y10}%, the interest rate differential versus major G10 "
            f"economies continues to attract capital flows into dollar-denominated assets.\n\n"
            f"The {regime} macro backdrop reinforces dollar demand: "
            f"{'risk-off environments typically drive safe-haven USD flows' if s.macro_regime == 'risk_off' else 'tightening cycles have historically been USD-supportive'}. "
            f"Dollar strength has significant cross-asset implications: it pressures EM currencies, "
            f"commodity prices (oil, gold), and U.S. multinational earnings.\n\n"
            f"The key risk to sustained dollar strength is a Fed pivot that narrows yield differentials "
            f"or a sharp improvement in growth outside the U.S. that boosts foreign currencies."
        )
        catalysts = [
            f"U.S. yield differential versus G10 remaining wide (10Y at {y10}%)",
            "Risk-off episodes driving safe-haven dollar demand",
            "U.S. data outperformance versus other major economies",
            "EM stress events triggering dollar funding demand",
        ]
        invalidations = [
            "Fed pivot signal narrowing the U.S. yield advantage",
            "Strong growth data outside the U.S. boosting EUR or JPY",
            f"EUR/USD recovering above {_fmt(s.eurusd + 0.03 if s.eurusd else None, 4)} on ECB hawkishness",
        ]
        scenarios = [
            ScenarioDTO("Continued strength", 45, f"Dollar grinds higher; EUR/USD tests {_fmt(s.eurusd - 0.03 if s.eurusd else None, 4)}.", "U.S. data outperforms, Fed holds."),
            ScenarioDTO("Consolidation", 35, "Dollar pauses as market digests yield dynamics.", "Mixed global data, no clear catalyst."),
            ScenarioDTO("Reversal", 20, "Dollar weakens sharply on Fed pivot or external growth surprise.", "Fed signals cuts; ECB stays hawkish."),
        ]
        counter_args = [
            CounterArgumentDTO("Dollar is overvalued on PPP measures versus most G10 and EM currencies — mean reversion pressure builds.", "strong"),
            CounterArgumentDTO("Sustained dollar strength historically triggers coordinated intervention from trading partners.", "moderate"),
        ]

    elif usd == "weakening":
        confidence = 61
        time_horizon = "3M"
        claim = (
            f"The dollar is in a weakening trend (EUR/USD: {eurusd}, {eurusd_d} 30d) "
            f"as yield differential dynamics shift in a {regime} macro environment."
        )
        rationale = (
            f"The dollar is weakening: EUR/USD has risen to {eurusd} ({eurusd_d} 30d). "
            f"The 10-year yield at {y10}% and macro regime of {regime} suggest that the "
            f"interest rate differential supporting dollar strength is narrowing.\n\n"
            f"Dollar weakness has historically been supportive for commodities (especially gold and oil), "
            f"EM assets, and U.S. multinational earnings (currency translation boost). "
            f"EUR/USD at {eurusd} is the primary cross to monitor — the ECB/Fed policy divergence "
            f"is the key driver of this pair near-term."
        )
        catalysts = [
            "Fed rate cut signal reducing yield advantage",
            "Stronger-than-expected European or Asian growth data",
            "Risk-on rotation away from dollar safe-haven into risk assets",
        ]
        invalidations = [
            "Hot U.S. inflation data reversing rate cut expectations",
            f"EUR/USD break back below {_fmt(s.eurusd - 0.02 if s.eurusd else None, 4)} on European growth disappointment",
        ]
        scenarios = [
            ScenarioDTO("Continued weakness", 45, f"EUR/USD extends to {_fmt(s.eurusd + 0.03 if s.eurusd else None, 4)} on Fed pivot pricing.", "Fed signals cuts, ECB holds."),
            ScenarioDTO("Stabilisation", 35, "Dollar finds support as yield differential remains wide.", "No clear Fed pivot signal."),
            ScenarioDTO("Reversal", 20, "Dollar rebounds on strong U.S. data or geopolitical shock.", "CPI surprise or risk-off event."),
        ]
        counter_args = [
            CounterArgumentDTO("Dollar weakness may be premature if the Fed maintains higher-for-longer stance.", "strong"),
            CounterArgumentDTO("European growth outlook remains fragile — EUR/USD upside may be capped.", "moderate"),
        ]

    else:
        confidence = 46
        time_horizon = "3M"
        claim = f"The dollar is in a neutral range (EUR/USD: {eurusd}) with macro signals mixed in a {regime} environment."
        rationale = (
            f"EUR/USD at {eurusd} ({eurusd_d} 30d) reflects balanced macro forces. "
            f"The U.S. 10-year at {y10}% and {regime} macro regime do not strongly bias the dollar either way. "
            f"Fed vs ECB policy divergence remains the key near-term driver to monitor."
        )
        catalysts = ["Fed or ECB policy surprise", "Major U.S. data miss or beat", "Geopolitical shock"]
        invalidations = ["Range break in either direction on policy surprise"]
        scenarios = [
            ScenarioDTO("USD mild strength", 35, f"Dollar edges up; EUR/USD tests {_fmt(s.eurusd - 0.02 if s.eurusd else None, 4)}.", "U.S. data outperforms marginally."),
            ScenarioDTO("Range-bound", 40, f"EUR/USD stays near {eurusd} pending clearer catalysts.", "Data mixed, central banks hold."),
            ScenarioDTO("USD weakness", 25, f"EUR/USD breaks to {_fmt(s.eurusd + 0.03 if s.eurusd else None, 4)} on Fed pivot.", "Fed signals cuts earlier than expected."),
        ]
        counter_args = [
            CounterArgumentDTO("Neutral range regimes often precede sharp directional breaks — event risk is elevated.", "moderate"),
        ]

    evidence = [
        EvidenceDTO("EUR/USD Exchange Rate", "DEXUSEU", s.eurusd, s.as_of,
                    f"Dollar vs euro at {eurusd}, 30d change {eurusd_d}. Primary USD strength indicator."),
        EvidenceDTO("USD/JPY Exchange Rate", "DEXJPUS", s.usdjpy, s.as_of,
                    f"Yen at {usdjpy} per dollar. JPY weakness reflects carry trade and BoJ/Fed policy divergence."),
        EvidenceDTO("U.S. 10-Year Treasury Yield", "DGS10", s.yield_10y, s.as_of,
                    f"10Y at {y10}% drives yield differential — the primary engine of dollar demand."),
    ]
    return claim, confidence, time_horizon, rationale, catalysts, invalidations, scenarios, counter_args, evidence


def _macro_thesis(s: MacroSignals, topic: str) -> tuple:
    regime = _regime_label(s.macro_regime)
    y10 = _fmt(s.yield_10y)
    spread = _fmt(s.spread_10y2y)
    sp = _fmt(s.sp500, 0)
    wti = _fmt(s.wti)
    eurusd = _fmt(s.eurusd, 4)
    sp_d = _fmt_delta(s.sp500_delta30d_pct, 1, "%")

    confidence = {
        "risk_on": 60, "risk_off": 65, "stagflation": 62,
        "goldilocks": 58, "tightening": 63, "easing": 60, "mixed": 48,
    }.get(s.macro_regime, 48)

    time_horizon = "3M"

    regime_descriptions = {
        "risk_on": "Global risk appetite is constructive, supporting equities and commodities while safe-haven assets underperform.",
        "risk_off": "Risk aversion is dominant — equities and commodities are under pressure while Treasuries and the dollar attract safe-haven flows.",
        "stagflation": "A stagflationary dynamic is emerging with oil rising and equities under pressure — the most challenging macro environment for balanced portfolios.",
        "goldilocks": "A goldilocks environment: equities are trending higher with contained inflation and moderate growth — the ideal backdrop for risk assets.",
        "tightening": "Monetary tightening pressures dominate: yields are rising and the dollar is strengthening, headwinds for duration and commodities.",
        "easing": "An easing cycle is signalled by falling yields and a steepening curve — typically supportive for duration and growth assets.",
        "mixed": "Mixed macro signals without a dominant regime — elevated uncertainty favours diversified positioning and reduced sizing.",
    }

    claim = (
        f"The current macro regime reads as {regime.upper()}: "
        f"yield curve {s.curve_shape} at {spread}%, "
        f"equities {s.equity_trend} (S&P {sp}, {sp_d} 30d), "
        f"oil {s.oil_trend} (WTI ${wti}), dollar {s.usd_trend}."
    )

    rationale = (
        f"{regime_descriptions.get(s.macro_regime, 'Mixed signals.')}\n\n"
        f"Yield curve analysis: the 10Y-2Y spread is at {spread}% ({s.curve_shape}), "
        f"with the 10Y at {y10}% and 2Y at {_fmt(s.yield_2y)}%. "
        f"30d yield change: {_fmt_delta(s.yield_10y_delta30d, suffix='pp')}. "
        f"{'An inverted curve is historically the most reliable leading recession indicator.' if s.curve_shape == 'inverted' else f'A {s.curve_shape} curve implies the market is pricing ' + ('a policy pause or normalisation' if s.curve_shape in ('flat','normal') else 'reflationary dynamics or term premium expansion') + '.'}\n\n"
        f"Equity market signal: S&P 500 at {sp} ({sp_d} 30d), Nasdaq {_fmt_delta(s.nasdaq_delta30d_pct, 1, '%')} 30d. "
        f"Equity trend is {s.equity_trend}, consistent with a {regime} macro read.\n\n"
        f"Commodity signal: WTI crude at ${wti} ({_fmt_delta(s.wti_delta30d_pct, 1, '%')} 30d). "
        f"Oil {s.oil_trend} — "
        f"{'a demand-destruction signal' if s.oil_trend == 'falling' and s.equity_trend == 'bear' else 'supply dynamics dominant' if s.oil_trend == 'rising' else 'balanced supply/demand'}.\n\n"
        f"FX: EUR/USD at {eurusd} ({_fmt_delta(s.eurusd_delta30d_pct, 2, '%')} 30d), dollar {s.usd_trend}. "
        f"Dollar trend has cross-asset implications for EM, commodities, and U.S. multinational earnings."
    )

    regime_catalysts = {
        "risk_on": ["Continued earnings growth", "Fed pivot accelerating", "Geopolitical de-escalation"],
        "risk_off": ["Fed pivot/rate cut materialising", "Inflation normalising", "Policy coordination"],
        "stagflation": ["OPEC+ supply increase breaking oil rally", "Productivity surprise reducing inflation", "Fiscal consolidation"],
        "goldilocks": ["Earnings growth sustaining current valuations", "Soft landing confirmed by labour data", "Inflation continuing to normalise"],
        "tightening": ["Terminal rate becoming visible", "Inflation breaking lower", "Dollar rally slowing"],
        "easing": ["Rate cuts materialising", "Growth stabilisation at lower yields", "Credit spreads tightening"],
        "mixed": ["Macro data clarifying regime", "Central bank guidance shift", "Geopolitical resolution"],
    }

    regime_invalidations = {
        "risk_on": ["Inflation resurgence forcing Fed reversal", "Credit event", "Earnings recession"],
        "risk_off": ["Strong macro data reversing risk aversion", "Fed emergency cut", "Geopolitical resolution"],
        "stagflation": ["Oil supply shock ending", "Recession arriving before stagflation entrenches", "Demand destruction breaking inflation"],
        "goldilocks": ["Inflation re-accelerating above 3.5%", "Labour market deterioration beyond soft-landing scenario", "Yield spike on fiscal concerns"],
        "tightening": ["Fed pivot earlier than expected", "Dollar reversal on external growth surprise", "Inflation breaking sharply lower"],
        "easing": ["Inflation resurgence forcing hawkish reversal", "Growth stronger than expected, reducing cut necessity", "Term premium expansion limiting long-end rally"],
        "mixed": ["Data breaks regime clarity in either direction", "Central bank surprise"],
    }

    catalysts = regime_catalysts.get(s.macro_regime, ["Macro data clarity", "Central bank guidance"])
    invalidations = regime_invalidations.get(s.macro_regime, ["Data surprise in opposite direction"])

    regime_scenarios = {
        "risk_on": [
            ScenarioDTO("Risk rally extends", 50, "Equities and risk assets continue higher. Bonds underperform.", "Earnings beats + stable inflation."),
            ScenarioDTO("Consolidation", 30, "Risk-on pauses; sideways markets, yields stable.", "Mixed data, Fed holds."),
            ScenarioDTO("Risk reversal", 20, "Unexpected shock triggers risk-off. Equities correct 10-15%.", "Geopolitical or credit event."),
        ],
        "risk_off": [
            ScenarioDTO("Continued risk-off", 40, "Equities and oil remain under pressure; Treasuries and dollar outperform.", "No catalyst for reversal."),
            ScenarioDTO("Fed rescue rally", 35, "Sharp reversal on Fed pivot or emergency action.", "Fed signals cuts or QE."),
            ScenarioDTO("Hard landing", 25, "Risk-off deepens into recession. Credit spreads blow out.", "Unemployment spikes + GDP contracts."),
        ],
        "stagflation": [
            ScenarioDTO("Stagflation entrenches", 35, "Oil stays high, equities grind lower, bonds lose on both ends.", "OPEC+ holds cuts, inflation sticky."),
            ScenarioDTO("Oil breaks lower", 40, "Supply shock ends; oil falls, regime shifts to risk-off or goldilocks.", "OPEC+ compliance breaks."),
            ScenarioDTO("Recession clears inflation", 25, "Hard landing destroys demand; inflation falls sharply but growth collapses.", "Unemployment surges."),
        ],
    }

    default_scenarios = [
        ScenarioDTO("Base case", 50, f"Current {regime} regime persists for 3 months with moderate cross-asset performance.", "No major macro catalyst."),
        ScenarioDTO("Regime shift positive", 30, "Data improves and macro shifts towards goldilocks or risk-on.", "Growth + inflation normalisation."),
        ScenarioDTO("Regime deterioration", 20, "Macro data worsens and regime shifts to risk-off or stagflation.", "Recession signal or inflation spike."),
    ]

    scenarios = regime_scenarios.get(s.macro_regime, default_scenarios)

    counter_args = [
        CounterArgumentDTO(
            f"Regime classifications are simplifications — the current {regime} read could shift quickly on a single data print.",
            "moderate",
        ),
        CounterArgumentDTO(
            "Lagged effects of prior monetary tightening may not yet be fully visible in current data, biasing the regime read.",
            "strong",
        ),
        CounterArgumentDTO(
            "Geopolitical risks (outside the model's data inputs) represent unquantified tail risk to any macro regime call.",
            "moderate",
        ),
    ]

    evidence = [
        EvidenceDTO("U.S. 10-Year Treasury Yield", "DGS10", s.yield_10y, s.as_of,
                    f"Long-end at {y10}%, 30d: {_fmt_delta(s.yield_10y_delta30d, suffix='pp')}. Primary macro anchor."),
        EvidenceDTO("10Y-2Y Yield Spread", "T10Y2Y", s.spread_10y2y, s.as_of,
                    f"{s.curve_shape.capitalize()} curve at {spread}%. Recession leading indicator."),
        EvidenceDTO("S&P 500 Index", "SP500", s.sp500, s.as_of,
                    f"Equities at {sp} ({sp_d} 30d). Risk appetite barometer."),
        EvidenceDTO("WTI Crude Oil", "DCOILWTICO", s.wti, s.as_of,
                    f"Oil at ${wti} ({_fmt_delta(s.wti_delta30d_pct, 1, '%')} 30d). Growth/inflation signal."),
        EvidenceDTO("EUR/USD", "DEXUSEU", s.eurusd, s.as_of,
                    f"Dollar proxy at {eurusd} ({_fmt_delta(s.eurusd_delta30d_pct, 2, '%')} 30d). Cross-asset implications."),
    ]

    return claim, confidence, time_horizon, rationale, catalysts, invalidations, scenarios, counter_args, evidence


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

_BUILDERS = {
    "gold":     _gold_thesis,
    "oil":      _oil_thesis,
    "bonds":    _bonds_thesis,
    "equities": _equities_thesis,
    "dollar":   _dollar_thesis,
    "fx":       _dollar_thesis,
    "macro":    _macro_thesis,
}


def build_thesis(topic: str, signals: MacroSignals) -> ThesisResult:
    t0 = time.monotonic()
    topic_type = detect_topic(topic)
    builder = _BUILDERS.get(topic_type, _macro_thesis)
    claim, confidence, time_horizon, rationale, catalysts, invalidations, scenarios, counter_args, evidence = builder(signals, topic)

    return ThesisResult(
        claim=claim,
        confidence=confidence,
        time_horizon=time_horizon,
        rationale=rationale,
        catalysts=catalysts,
        invalidation_conditions=invalidations,
        evidence=evidence,
        scenarios=scenarios,
        counter_arguments=counter_args,
        model_name="rules-engine-v1",
        provider="rules",
        input_tokens=None,
        output_tokens=None,
        generation_ms=int((time.monotonic() - t0) * 1000),
    )
