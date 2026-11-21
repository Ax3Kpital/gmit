"""
Notification service — email (SMTP) and Telegram.
Both implementations are synchronous (smtplib + httpx.Client)
so they work safely from APScheduler threads.
"""
import logging
import smtplib
import textwrap
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import httpx

from app.core.config import settings

log = logging.getLogger("gmit.notify")

_REGIME_EMOJI: dict[str, str] = {
    "risk_on":     "🟢",
    "risk_off":    "🔴",
    "stagflation": "🟡",
    "goldilocks":  "🟢",
    "tightening":  "🟡",
    "easing":      "🔵",
    "mixed":       "⚪",
}


# ── Email ─────────────────────────────────────────────────────────────────────

def _send_email_raw(subject: str, html: str, plain: str) -> bool:
    if not settings.email_configured:
        log.debug("Email not configured — skipping")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.smtp_from_address or settings.smtp_user
        msg["To"] = settings.notification_email
        msg.attach(MIMEText(plain, "plain"))
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as s:
            s.ehlo()
            s.starttls()
            s.login(settings.smtp_user, settings.smtp_password)
            s.send_message(msg)
        log.info("Email sent: %s → %s", subject, settings.notification_email)
        return True
    except Exception as exc:
        log.error("Email failed: %s", exc)
        return False


def _email_html_wrapper(title: str, body_html: str) -> str:
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  body{{font-family:'IBM Plex Sans',Arial,sans-serif;background:#0e1116;color:#e8edf4;margin:0;padding:0}}
  .wrap{{max-width:600px;margin:0 auto;padding:24px}}
  .header{{border-bottom:1px solid #2a3340;padding-bottom:16px;margin-bottom:20px}}
  .logo{{font-family:monospace;font-size:11px;color:#3d9cf0;letter-spacing:0.1em;text-transform:uppercase}}
  h1{{font-size:18px;font-weight:600;margin:8px 0 4px;color:#e8edf4}}
  .regime{{display:inline-block;padding:2px 10px;border-radius:99px;font-size:11px;font-family:monospace;margin-bottom:16px}}
  .section-title{{font-size:10px;letter-spacing:0.08em;text-transform:uppercase;color:#8b98a8;margin:16px 0 8px;font-weight:600}}
  .item{{padding:6px 0;font-size:13px;border-bottom:1px solid #2a3340;color:#e8edf4;line-height:1.4}}
  .muted{{color:#8b98a8;font-size:12px}}
  .footer{{margin-top:24px;padding-top:16px;border-top:1px solid #2a3340;font-size:11px;color:#8b98a8}}
</style></head>
<body><div class="wrap">
  <div class="header">
    <div class="logo">GMIT — Global Macro Intelligence Terminal</div>
    <h1>{title}</h1>
  </div>
  {body_html}
  <div class="footer">
    Not financial advice. For research purposes only.
    <br>GMIT · Automated by rules-engine-v1
  </div>
</div></body></html>"""


def send_alert_email(alert_message: str, rule_name: str, triggered_at: str) -> bool:
    subject = f"[GMIT Alert] {rule_name}"
    body_html = f"""
<div class="section-title">Alert triggered</div>
<div class="item">{alert_message}</div>
<div class="item muted">Triggered: {triggered_at}</div>
"""
    plain = f"GMIT Alert: {rule_name}\n\n{alert_message}\nTriggered: {triggered_at}"
    return _send_email_raw(subject, _email_html_wrapper(f"⚠ {rule_name}", body_html), plain)


def send_briefing_email(
    date: str,
    regime: str,
    headline: str,
    key_moves: list[str],
    cot_highlights: list[str],
    watchlist: list[str],
) -> bool:
    emoji = _REGIME_EMOJI.get(regime, "⚪")
    regime_label = regime.upper().replace("_", " ")
    subject = f"[GMIT] Daily Briefing — {date} · {regime_label}"

    def section(title: str, items: list[str]) -> str:
        if not items:
            return ""
        rows = "".join(f'<div class="item">› {item}</div>' for item in items)
        return f'<div class="section-title">{title}</div>{rows}'

    body_html = f"""
<div class="regime" style="color:#3d9cf0;border:1px solid #3d9cf0">{emoji} {regime_label}</div>
<p style="color:#8b98a8;font-size:13px;line-height:1.5">{headline}</p>
{section("Key Moves", key_moves)}
{section("COT Highlights", cot_highlights)}
{section("Watchlist", watchlist)}
"""
    plain_items = "\n".join(f"  › {m}" for m in key_moves)
    plain = textwrap.dedent(f"""
        GMIT Daily Briefing — {date}
        Regime: {regime_label}

        {headline}

        KEY MOVES:
        {plain_items}
    """).strip()
    return _send_email_raw(
        subject,
        _email_html_wrapper(f"Daily Briefing — {date}", body_html),
        plain,
    )


# ── Telegram ──────────────────────────────────────────────────────────────────

def _send_telegram(text: str) -> bool:
    if not settings.telegram_configured:
        log.debug("Telegram not configured — skipping")
        return False
    try:
        url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
        with httpx.Client(timeout=10) as client:
            resp = client.post(url, json={
                "chat_id": settings.telegram_chat_id,
                "text": text,
                "parse_mode": "HTML",
            })
            resp.raise_for_status()
        log.info("Telegram message sent (%d chars)", len(text))
        return True
    except Exception as exc:
        log.error("Telegram failed: %s", exc)
        return False


def send_alert_telegram(alert_message: str, rule_name: str) -> bool:
    text = f"🚨 <b>GMIT Alert</b>\n<b>{rule_name}</b>\n\n{alert_message}"
    return _send_telegram(text)


def send_briefing_telegram(
    date: str,
    regime: str,
    headline: str,
    key_moves: list[str],
    cot_highlights: list[str],
    watchlist: list[str],
) -> bool:
    emoji = _REGIME_EMOJI.get(regime, "⚪")
    regime_label = regime.upper().replace("_", " ")
    lines = [
        f"📊 <b>GMIT Daily Briefing</b> — {date}",
        f"Regime: {emoji} <b>{regime_label}</b>",
        "",
        headline,
    ]
    if key_moves:
        lines += ["", "<b>Key Moves</b>"]
        lines += [f"› {m}" for m in key_moves[:4]]
    if cot_highlights:
        lines += ["", "<b>COT Highlights</b>"]
        lines += [f"› {m}" for m in cot_highlights[:3]]
    if watchlist:
        lines += ["", "<b>Watchlist</b>"]
        lines += [f"› {m}" for m in watchlist[:3]]
    return _send_telegram("\n".join(lines))


# ── Convenience wrappers ──────────────────────────────────────────────────────

def notify_alert(alert_message: str, rule_name: str, triggered_at: str) -> None:
    send_alert_email(alert_message, rule_name, triggered_at)
    send_alert_telegram(alert_message, rule_name)


def notify_briefing(
    date: str, regime: str, headline: str,
    key_moves: list[str], cot_highlights: list[str], watchlist: list[str],
) -> None:
    send_briefing_email(date, regime, headline, key_moves, cot_highlights, watchlist)
    send_briefing_telegram(date, regime, headline, key_moves, cot_highlights, watchlist)
