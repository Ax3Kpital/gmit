"""
Alert engine — checks price threshold and COT extreme rules after each ingestion.
Deduplication: only fires once per rule per day to prevent spam.
"""
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models.smart_money import AlertRule, AlertEvent, CotInstrument, CotReport
from app.db.models.macro import MacroSeries

log = logging.getLogger("gmit.alerts")


def run_alert_checks() -> None:
    db = SessionLocal()
    try:
        rules = db.query(AlertRule).filter(AlertRule.enabled == True).all()
        fired = 0
        for rule in rules:
            if _already_fired_today(db, rule.id):
                continue
            if rule.rule_type == "price_threshold":
                fired += _check_price_threshold(db, rule)
            elif rule.rule_type == "cot_extreme":
                fired += _check_cot_extreme(db, rule)
        if fired:
            db.commit()
            log.info("Alerts: %d new events fired", fired)
    finally:
        db.close()


def _already_fired_today(db: Session, rule_id) -> bool:
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return db.query(AlertEvent).filter(
        AlertEvent.rule_id == rule_id,
        AlertEvent.triggered_at >= today_start,
    ).first() is not None


def _check_price_threshold(db: Session, rule: AlertRule) -> int:
    if not rule.series_id:
        return 0
    series = db.query(MacroSeries).filter(MacroSeries.series_id == rule.series_id).first()
    if not series:
        return 0
    from app.services.series_snapshot import resolve
    series, latest = resolve(db, series)
    if not latest or latest.value is None:
        return 0

    triggered = (
        (rule.condition == "above" and latest.value > rule.threshold_value) or
        (rule.condition == "below" and latest.value < rule.threshold_value)
    )
    if not triggered:
        return 0

    msg = (
        f"{rule.name}: {series.display_name or rule.series_id} is "
        f"{'above' if rule.condition == 'above' else 'below'} "
        f"{rule.threshold_value} — current value {latest.value:.4f} "
        f"as of {latest.date.isoformat()}"
    )
    db.add(AlertEvent(
        rule_id=rule.id,
        user_id=rule.user_id,
        message=msg,
        value_at_trigger=latest.value,
        threshold_value=rule.threshold_value,
    ))
    log.info("Alert fired: %s", msg)
    from app.services.notification_service import notify_alert
    from datetime import datetime, timezone
    notify_alert(msg, rule.name, datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
    return 1


def _check_cot_extreme(db: Session, rule: AlertRule) -> int:
    if not rule.cftc_code:
        return 0
    inst = db.query(CotInstrument).filter(CotInstrument.cftc_code == rule.cftc_code).first()
    if not inst:
        return 0

    # Get latest report's net_noncomm_pct_oi as percentile proxy (already normalised vs OI)
    reports = (
        db.query(CotReport)
        .filter(CotReport.instrument_id == inst.id, CotReport.net_noncomm.isnot(None))
        .order_by(CotReport.report_date.desc())
        .limit(52)
        .all()
    )
    if len(reports) < 4:
        return 0

    latest = reports[0]
    if latest.net_noncomm is None:
        return 0

    net_values = [r.net_noncomm for r in reports if r.net_noncomm is not None]
    min_net = min(net_values)
    max_net = max(net_values)
    if max_net == min_net:
        return 0

    percentile = (latest.net_noncomm - min_net) / (max_net - min_net) * 100

    triggered = (
        (rule.condition == "above" and percentile > rule.threshold_value) or
        (rule.condition == "below" and percentile < rule.threshold_value)
    )
    if not triggered:
        return 0

    direction = "extreme long" if percentile > 50 else "extreme short"
    msg = (
        f"{rule.name}: {inst.display_name} COT positioning is {direction} — "
        f"speculator net position at {percentile:.0f}th percentile (52-week), "
        f"net: {latest.net_noncomm:,} contracts as of {latest.report_date.isoformat()}"
    )
    db.add(AlertEvent(
        rule_id=rule.id,
        user_id=rule.user_id,
        message=msg,
        value_at_trigger=percentile,
        threshold_value=rule.threshold_value,
    ))
    log.info("Alert fired: %s", msg)
    from app.services.notification_service import notify_alert
    from datetime import datetime, timezone
    notify_alert(msg, rule.name, datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
    return 1
