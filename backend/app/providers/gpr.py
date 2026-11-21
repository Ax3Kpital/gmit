"""GPR Index provider — downloads Geopolitical Risk Index from Iacoviello (2026).

Source: https://www.matteoiacoviello.com/gpr.htm
File:   data_gpr_export_with_groups.xls (updated monthly)
License: free for academic/research use, citation required.
"""
import io
import logging
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Optional
import httpx

logger = logging.getLogger("gmit.gpr")

_GPR_URL = "https://www.matteoiacoviello.com/gpr_files/data_gpr_export_with_groups.xls"

# Fallback — the CSV export (sometimes available alongside the Excel)
_GPR_CSV_URL = "https://www.matteoiacoviello.com/gpr_files/data_gpr_export_with_groups.xlsx"


@dataclass
class GprPoint:
    period: date        # first day of the month
    gpr_value: Optional[float]   # overall GPR
    gpr_threat: Optional[float]  # GPRT — threat component
    gpr_act: Optional[float]     # GPRA — acts component


@dataclass
class GprResult:
    series: list[GprPoint]
    retrieved_at: datetime
    data_status: str
    source_url: str


def _safe_float(val) -> Optional[float]:
    try:
        f = float(val)
        return None if f != f else f  # NaN check
    except (TypeError, ValueError):
        return None


def _parse_excel(content: bytes) -> list[GprPoint]:
    """Parse GPR Excel file. Returns list sorted ascending by period."""
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    ws = wb.active

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []

    # Find header row — look for a row containing 'month' or 'MONTH' or 'date'
    header_idx = 0
    col_map: dict[str, int] = {}
    for i, row in enumerate(rows[:10]):
        row_lower = [str(c).lower().strip() if c is not None else "" for c in row]
        if any(k in row_lower for k in ("month", "date", "year")):
            header_idx = i
            for j, name in enumerate(row_lower):
                col_map[name] = j
            break

    # Column detection — GPR is often 'gpr', threat is 'gprt', act is 'gpra'
    gpr_col = col_map.get("gpr", col_map.get("gpr_index"))
    gprt_col = col_map.get("gprt")
    gpra_col = col_map.get("gpra")
    month_col = col_map.get("month", col_map.get("date", col_map.get("year", 0)))

    if gpr_col is None:
        # Fallback: scan header for column names containing 'gpr'
        for k, v in col_map.items():
            if "gpr" in k and "t" not in k and "a" not in k and "c" not in k:
                gpr_col = v
                break

    points: list[GprPoint] = []
    for row in rows[header_idx + 1:]:
        if not row or row[month_col] is None:
            continue

        # Period: may be a date object, a float (Excel serial), or "YYYY-MM" string
        raw = row[month_col]
        period: Optional[date] = None
        if isinstance(raw, (date, datetime)):
            period = raw.date() if isinstance(raw, datetime) else raw
        elif isinstance(raw, float):
            # Excel serial date → year/month extraction
            try:
                from datetime import timedelta
                epoch = date(1899, 12, 30)
                period = epoch + timedelta(days=int(raw))
                period = period.replace(day=1)
            except Exception:
                continue
        elif isinstance(raw, str):
            # "YYYY-MM" or "YYYY-MM-DD"
            try:
                parts = raw.strip().split("-")
                year, month = int(parts[0]), int(parts[1])
                period = date(year, month, 1)
            except Exception:
                continue

        if period is None:
            continue

        points.append(
            GprPoint(
                period=period.replace(day=1),
                gpr_value=_safe_float(row[gpr_col]) if gpr_col is not None else None,
                gpr_threat=_safe_float(row[gprt_col]) if gprt_col is not None else None,
                gpr_act=_safe_float(row[gpra_col]) if gpra_col is not None else None,
            )
        )

    points.sort(key=lambda p: p.period)
    return points


async def fetch_gpr_index(last_n_months: int = 48) -> GprResult:
    """Download GPR Excel and return last N months of data."""
    retrieved_at = datetime.now(timezone.utc)

    for url in (_GPR_CSV_URL, _GPR_URL):
        try:
            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                resp = await client.get(url)
                resp.raise_for_status()
            points = _parse_excel(resp.content)
            if points:
                logger.info("GPR: parsed %d months from %s", len(points), url)
                return GprResult(
                    series=points[-last_n_months:],
                    retrieved_at=retrieved_at,
                    data_status="PERIODIC_OFFICIAL_RELEASE",
                    source_url=url,
                )
        except Exception as exc:
            logger.warning("GPR fetch failed (%s): %s", url, exc)

    return GprResult(
        series=[],
        retrieved_at=retrieved_at,
        data_status="UNAVAILABLE",
        source_url=_GPR_URL,
    )
