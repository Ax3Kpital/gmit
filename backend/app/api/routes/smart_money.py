from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Cookie, HTTPException
from sqlalchemy.orm import Session
from app.core.freshness import classify_cot, cot_release_time, next_cot_release
from app.db.session import get_db
from app.services import auth_service
from app.db.models.smart_money import CotInstrument, CotReport

router = APIRouter(prefix="/smart-money")
_SESSION_COOKIE = "gmit_session"


def _require_auth(
    db: Session = Depends(get_db),
    token: str | None = Cookie(default=None, alias=_SESSION_COOKIE),
):
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not auth_service.get_session(db, token):
        raise HTTPException(status_code=401, detail="Session expired")


@router.get("/cot")
def get_cot_overview(
    _auth=Depends(_require_auth),
    db: Session = Depends(get_db),
):
    instruments = db.query(CotInstrument).filter(CotInstrument.enabled == True).all()
    result = []

    for inst in instruments:
        reports = (
            db.query(CotReport)
            .filter(CotReport.instrument_id == inst.id, CotReport.net_noncomm.isnot(None))
            .order_by(CotReport.report_date.desc())
            .limit(52)
            .all()
        )
        if not reports:
            result.append({
                "cftc_code": inst.cftc_code,
                "display_name": inst.display_name,
                "category": inst.category,
                "exchange": inst.exchange,
                "related_series_id": inst.related_series_id,
                "data_status": "UNAVAILABLE",
                "latest_report_date": None,
                "net_noncomm": None,
                "net_noncomm_pct_oi": None,
                "percentile_52w": None,
                "sentiment": None,
                "change_net_wow": None,
                "open_interest": None,
                "history": [],
            })
            continue

        latest = reports[0]
        net_values = [r.net_noncomm for r in reports if r.net_noncomm is not None]
        min_net = min(net_values)
        max_net = max(net_values)
        percentile = None
        if max_net != min_net and latest.net_noncomm is not None:
            percentile = round((latest.net_noncomm - min_net) / (max_net - min_net) * 100, 1)

        sentiment = None
        if percentile is not None:
            if percentile >= 80:
                sentiment = "extreme_long"
            elif percentile >= 60:
                sentiment = "long"
            elif percentile <= 20:
                sentiment = "extreme_short"
            elif percentile <= 40:
                sentiment = "short"
            else:
                sentiment = "neutral"

        change_wow = None
        if len(reports) >= 2 and reports[0].net_noncomm is not None and reports[1].net_noncomm is not None:
            change_wow = reports[0].net_noncomm - reports[1].net_noncomm

        history = [
            {
                "date": r.report_date.isoformat(),
                "net_noncomm": r.net_noncomm,
                "open_interest": r.open_interest,
            }
            for r in reversed(reports[:26])
        ]

        result.append({
            "cftc_code": inst.cftc_code,
            "display_name": inst.display_name,
            "category": inst.category,
            "exchange": inst.exchange,
            "related_series_id": inst.related_series_id,
            "data_status": classify_cot(latest.report_date, datetime.now(timezone.utc)),
            "latest_report_date": latest.report_date.isoformat(),
            "net_noncomm": latest.net_noncomm,
            "net_noncomm_pct_oi": round(latest.net_noncomm_pct_oi, 2) if latest.net_noncomm_pct_oi is not None else None,
            "percentile_52w": percentile,
            "sentiment": sentiment,
            "change_net_wow": change_wow,
            "open_interest": latest.open_interest,
            "history": history,
        })

    now = datetime.now(timezone.utc)
    newest = max((i["latest_report_date"] for i in result if i.get("latest_report_date")), default=None)
    release = None
    if newest:
        from datetime import date as _date
        nd = _date.fromisoformat(newest)
        nxt_report, nxt_release = next_cot_release(now)
        release = {
            "positions_as_of": newest,
            "published_at": cot_release_time(nd).isoformat(),
            "next_positions_as_of": nxt_report.isoformat(),
            "next_release_at": nxt_release.isoformat(),
            "data_status": classify_cot(nd, now),
            "cadence": "Weekly: CFTC publishes every Friday ~15:30 ET for the preceding Tuesday.",
        }
    return {"items": result, "source": "CFTC Commitments of Traders — Legacy Futures Only",
            "lag_note": "Data reflects Tuesday positions, published Friday.", "release": release}
