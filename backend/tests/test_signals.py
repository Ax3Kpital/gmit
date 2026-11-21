"""Deterministic macro signals and regime classification."""
import pytest

from app.analysis.signals import _classify_regime, _trend_pct, compute_signals


def snip(sid, value, delta=None, pct=None, date="2026-11-20"):
    return {"series_id": sid, "latest_value": value, "delta30d": delta,
            "delta30d_pct": pct, "latest_date": date}


@pytest.mark.parametrize("spread,shape", [
    (-0.5, "inverted"), (-0.11, "inverted"), (0.0, "flat"), (0.29, "flat"),
    (0.30, "normal"), (0.79, "normal"), (0.80, "steep"), (1.5, "steep"),
])
def test_curve_shape_thresholds(spread, shape):
    assert compute_signals([snip("T10Y2Y", spread)]).curve_shape == shape


def test_missing_data_is_unknown_not_invented():
    s = compute_signals([])
    assert s.curve_shape == "unknown"
    assert s.yield_10y is None and s.wti is None and s.sp500 is None
    assert s.oil_trend == "stable" and s.equity_trend == "stable" and s.usd_trend == "stable"
    assert s.macro_regime == "mixed"
    assert s.as_of == "N/A"


@pytest.mark.parametrize("pct,expected", [(None, "stable"), (4.01, "rising"), (-4.01, "falling"),
                                          (4.0, "stable"), (-4.0, "stable"), (0.0, "stable")])
def test_trend_threshold_edges(pct, expected):
    assert _trend_pct(pct, threshold=4.0) == expected


def test_usd_strengthening_when_eur_falls_and_yen_weakens():
    s = compute_signals([snip("DEXUSEU", 1.05, pct=-2.0), snip("DEXJPUS", 155, pct=2.0)])
    assert s.usd_trend == "strengthening"


def test_usd_weakening_when_eur_rises():
    s = compute_signals([snip("DEXUSEU", 1.15, pct=2.0)])
    assert s.usd_trend == "weakening"


def test_as_of_uses_latest_of_key_series():
    s = compute_signals([snip("DGS10", 4.0, date="2026-11-18"), snip("SP500", 6000, date="2026-11-20")])
    assert s.as_of == "2026-11-20"


@pytest.mark.parametrize("kwargs,regime", [
    (dict(oil_trend="rising", equity_trend="bear"), "stagflation"),
    (dict(oil_trend="stable", equity_trend="bull"), "goldilocks"),
    (dict(oil_trend="falling", equity_trend="bull"), "goldilocks"),
    (dict(oil_trend="rising", equity_trend="bull"), "risk_on"),
    (dict(oil_trend="rising", equity_trend="bull", y10_d=0.5), "risk_on"),
    (dict(oil_trend="falling", equity_trend="bear"), "risk_off"),
    (dict(oil_trend="stable", equity_trend="sideways", y10_d=0.3, usd_trend="strengthening"), "tightening"),
    (dict(oil_trend="stable", equity_trend="sideways", y10_d=-0.3, curve_shape="normal"), "easing"),
    (dict(oil_trend="stable", equity_trend="sideways"), "mixed"),
])
def test_regime_classification(kwargs, regime):
    base = dict(curve_shape="normal", y10_d=None, oil_trend="stable",
                equity_trend="sideways", usd_trend="stable")
    base.update(kwargs)
    assert _classify_regime(**base) == regime


def test_easing_requires_non_inverted_curve():
    assert _classify_regime("inverted", -0.5, "stable", "sideways", "stable") == "mixed"
