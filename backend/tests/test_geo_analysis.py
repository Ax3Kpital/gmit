"""Geo risk scoring from GDELT tone and volume."""
import pytest

from app.analysis.geo_analysis import _score_to_level, _tone_to_risk_score, compute_region_risk


def test_tone_maps_linearly_to_score():
    assert _tone_to_risk_score(-10, None) == 100
    assert _tone_to_risk_score(0, None) == 50
    assert _tone_to_risk_score(10, None) == 0
    assert _tone_to_risk_score(-30, None) == 100      # clamped
    assert _tone_to_risk_score(30, None) == 0         # clamped


def test_volume_boost_tiers_and_cap():
    assert _tone_to_risk_score(0, 1001) == 52
    assert _tone_to_risk_score(0, 5001) == 55
    assert _tone_to_risk_score(-10, 9999) == 100      # never above 100


def test_unknown_tone_is_neutral():
    assert _tone_to_risk_score(None, 5000) == 50


@pytest.mark.parametrize("score,level", [(0, "low"), (31.9, "low"), (32, "moderate"),
                                         (51.9, "moderate"), (52, "elevated"),
                                         (71.9, "elevated"), (72, "critical"), (100, "critical")])
def test_level_boundaries(score, level):
    assert _score_to_level(score) == level


def test_live_data_is_scored_and_keeps_status():
    r = compute_region_risk("middle_east", "Middle East", -6.0, 2000, "DELAYED")
    assert r.risk_level == "critical"
    assert r.avg_tone == -6.0
    assert r.data_status == "DELAYED"


def test_unavailable_data_is_flagged_and_has_no_tone():
    r = compute_region_risk("taiwan_strait", "Taiwan Strait", None, None, "UNAVAILABLE")
    assert r.data_status == "UNAVAILABLE"
    assert r.avg_tone is None and r.article_count is None
    assert "unavailable" in r.note.lower()


def test_unknown_region_without_data_is_unknown_level():
    r = compute_region_risk("atlantis", "Atlantis", None, None, "UNAVAILABLE")
    assert r.risk_level == "unknown"
