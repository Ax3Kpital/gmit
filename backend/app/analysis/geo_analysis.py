"""Geo risk analysis — compute risk level per region from GDELT tone + volume."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class RegionRisk:
    region_key: str
    region_label: str
    risk_level: str          # critical | elevated | moderate | low | unknown
    risk_score: float        # 0-100, higher = more risk
    avg_tone: Optional[float]
    article_count: Optional[int]
    note: str
    data_status: str


# Tone scale: GDELT tone ranges roughly -10 (very negative) to +10 (positive)
# Article volume: high volume + very negative tone → elevated risk
def _tone_to_risk_score(avg_tone: Optional[float], article_count: Optional[int]) -> float:
    """Map GDELT tone + volume to a 0-100 risk score."""
    if avg_tone is None:
        return 50.0  # neutral unknown

    # Tone component: map [-10, +10] → [100, 0]
    tone_score = max(0.0, min(100.0, ((-avg_tone + 10.0) / 20.0) * 100.0))

    # Volume modifier: high coverage amplifies the signal slightly
    volume_boost = 0.0
    if article_count is not None:
        if article_count > 5000:
            volume_boost = 5.0
        elif article_count > 1000:
            volume_boost = 2.0

    return min(100.0, tone_score + volume_boost)


def _score_to_level(score: float) -> str:
    if score >= 72:
        return "critical"
    if score >= 52:
        return "elevated"
    if score >= 32:
        return "moderate"
    return "low"


def _build_note(region_key: str, avg_tone: Optional[float],
                article_count: Optional[int], data_status: str) -> str:
    if data_status == "UNAVAILABLE" or avg_tone is None:
        return "Live data unavailable — showing last cached assessment."

    tone_desc = (
        "strongly negative coverage" if avg_tone < -4
        else "negative coverage" if avg_tone < -2
        else "neutral coverage" if avg_tone < 1
        else "positive coverage"
    )
    vol_desc = (
        f"{article_count:,} articles/week" if article_count else "volume unknown"
    )
    return f"GDELT: {tone_desc} (tone {avg_tone:+.1f}), {vol_desc}."


# Fallback manual assessments (shown when GDELT unavailable)
_FALLBACK: dict[str, dict] = {
    "eastern_europe":      {"level": "critical",  "note": "Active conflict — energy supply, sanctions, NATO posture"},
    "middle_east":         {"level": "elevated",  "note": "Regional escalation risk — oil supply premium, Red Sea disruptions"},
    "taiwan_strait":       {"level": "elevated",  "note": "Semiconductor supply chain, US-China strategic competition"},
    "sub_saharan_africa":  {"level": "moderate",  "note": "Coup cycle in Sahel, resource nationalism"},
    "latin_america":       {"level": "moderate",  "note": "Political volatility in key economies"},
    "north_america_europe":{"level": "low",       "note": "Elevated political polarization but no active conflict"},
}

_FALLBACK_SCORES = {"critical": 80.0, "elevated": 60.0, "moderate": 40.0, "low": 20.0}


def compute_region_risk(
    region_key: str,
    region_label: str,
    avg_tone: Optional[float],
    article_count: Optional[int],
    data_status: str,
) -> RegionRisk:
    if data_status == "UNAVAILABLE" or avg_tone is None:
        fb = _FALLBACK.get(region_key, {"level": "unknown", "note": "No data available"})
        return RegionRisk(
            region_key=region_key,
            region_label=region_label,
            risk_level=fb["level"],
            risk_score=_FALLBACK_SCORES.get(fb["level"], 50.0),
            avg_tone=None,
            article_count=None,
            note=fb["note"] + " (manual fallback — live data unavailable)",
            data_status="UNAVAILABLE",
        )

    score = _tone_to_risk_score(avg_tone, article_count)
    level = _score_to_level(score)
    note = _build_note(region_key, avg_tone, article_count, data_status)

    return RegionRisk(
        region_key=region_key,
        region_label=region_label,
        risk_level=level,
        risk_score=round(score, 1),
        avg_tone=round(avg_tone, 2),
        article_count=article_count,
        note=note,
        data_status=data_status,
    )
