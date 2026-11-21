"""
Dev seed: creates default user and all series/instrument metadata.
Credentials printed at startup — change before any public deployment.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.services.auth_service import get_user_by_email, create_user
from app.db.models.macro import MacroSeries
from app.db.models.smart_money import CotInstrument

DEV_EMAIL = "admin@gmit.local"
DEV_PASSWORD = "gmit_dev_2026"

ALL_SERIES = [
    # ── Macro (Phase 2) ───────────────────────────────────────────────
    {
        "series_id": "DGS10",
        "display_name": "10Y UST",
        "category": "macro",
        "title": "Market Yield on U.S. Treasury Securities at 10-Year Constant Maturity",
        "units": "Percent",
        "frequency": "Daily, 7-Day",
        "seasonal_adjustment": "Not Seasonally Adjusted",
        "provider": "fred",
        "source_url": "https://fred.stlouisfed.org/series/DGS10",
        "data_status": "UNAVAILABLE",
        "stale_after_hours": 72,
    },
    {
        "series_id": "DGS2",
        "display_name": "2Y UST",
        "category": "macro",
        "title": "Market Yield on U.S. Treasury Securities at 2-Year Constant Maturity",
        "units": "Percent",
        "frequency": "Daily, 7-Day",
        "seasonal_adjustment": "Not Seasonally Adjusted",
        "provider": "fred",
        "source_url": "https://fred.stlouisfed.org/series/DGS2",
        "data_status": "UNAVAILABLE",
        "stale_after_hours": 72,
    },
    {
        "series_id": "T10Y2Y",
        "display_name": "10Y-2Y Spread",
        "category": "macro",
        "title": "10-Year Treasury Constant Maturity Minus 2-Year Treasury Constant Maturity",
        "units": "Percent",
        "frequency": "Daily, 7-Day",
        "seasonal_adjustment": "Not Seasonally Adjusted",
        "provider": "fred",
        "source_url": "https://fred.stlouisfed.org/series/T10Y2Y",
        "data_status": "UNAVAILABLE",
        "stale_after_hours": 72,
    },
    # ── Commodities (Phase 3) ─────────────────────────────────────────
    # Gold/Silver: FRED discontinued spot price series.
    # Source pending: LBMA or Kitco API verification required before adding.
    {
        "series_id": "DCOILWTICO",
        "display_name": "WTI Crude",
        "category": "commodity",
        "title": "Crude Oil Prices: West Texas Intermediate (WTI) - Cushing, Oklahoma",
        "units": "USD/Barrel",
        "frequency": "Daily",
        "seasonal_adjustment": "Not Seasonally Adjusted",
        "provider": "fred",
        "source_url": "https://fred.stlouisfed.org/series/DCOILWTICO",
        "data_status": "UNAVAILABLE",
        "stale_after_hours": 72,
    },
    {
        "series_id": "DCOILBRENTEU",
        "display_name": "Brent Crude",
        "category": "commodity",
        "title": "Crude Oil Prices: Brent - Europe",
        "units": "USD/Barrel",
        "frequency": "Daily",
        "seasonal_adjustment": "Not Seasonally Adjusted",
        "provider": "fred",
        "source_url": "https://fred.stlouisfed.org/series/DCOILBRENTEU",
        "data_status": "UNAVAILABLE",
        "stale_after_hours": 72,
    },
    {
        "series_id": "DHHNGSP",
        "display_name": "Henry Hub",
        "category": "commodity",
        "title": "Henry Hub Natural Gas Spot Price",
        "units": "USD/MMBTU",
        "frequency": "Daily",
        "seasonal_adjustment": "Not Seasonally Adjusted",
        "provider": "fred",
        "source_url": "https://fred.stlouisfed.org/series/DHHNGSP",
        "data_status": "UNAVAILABLE",
        "stale_after_hours": 72,
    },
    # ── Equities (Phase 3) ────────────────────────────────────────────
    {
        "series_id": "SP500",
        "display_name": "S&P 500",
        "category": "equity",
        "title": "S&P 500",
        "units": "Index",
        "frequency": "Daily",
        "seasonal_adjustment": "Not Seasonally Adjusted",
        "provider": "fred",
        "source_url": "https://fred.stlouisfed.org/series/SP500",
        "data_status": "UNAVAILABLE",
        "stale_after_hours": 72,
    },
    {
        "series_id": "NASDAQCOM",
        "display_name": "Nasdaq",
        "category": "equity",
        "title": "NASDAQ Composite Index",
        "units": "Index",
        "frequency": "Daily",
        "seasonal_adjustment": "Not Seasonally Adjusted",
        "provider": "fred",
        "source_url": "https://fred.stlouisfed.org/series/NASDAQCOM",
        "data_status": "UNAVAILABLE",
        "stale_after_hours": 72,
    },
    # ── FX (Phase 3) ──────────────────────────────────────────────────
    {
        "series_id": "DEXUSEU",
        "display_name": "EUR/USD",
        "category": "fx",
        "title": "U.S. Dollars to Euro Spot Exchange Rate",
        "units": "USD per EUR",
        "frequency": "Daily",
        "seasonal_adjustment": "Not Seasonally Adjusted",
        "provider": "fred",
        "source_url": "https://fred.stlouisfed.org/series/DEXUSEU",
        "data_status": "UNAVAILABLE",
        "stale_after_hours": 72,
    },
    {
        "series_id": "DEXJPUS",
        "display_name": "USD/JPY",
        "category": "fx",
        "title": "Japanese Yen to U.S. Dollar Spot Exchange Rate",
        "units": "JPY per USD",
        "frequency": "Daily",
        "seasonal_adjustment": "Not Seasonally Adjusted",
        "provider": "fred",
        "source_url": "https://fred.stlouisfed.org/series/DEXJPUS",
        "data_status": "UNAVAILABLE",
        "stale_after_hours": 72,
    },
    {
        "series_id": "DEXUSUK",
        "display_name": "GBP/USD",
        "category": "fx",
        "title": "U.S. Dollars to U.K. Pound Sterling Spot Exchange Rate",
        "units": "USD per GBP",
        "frequency": "Daily",
        "seasonal_adjustment": "Not Seasonally Adjusted",
        "provider": "fred",
        "source_url": "https://fred.stlouisfed.org/series/DEXUSUK",
        "data_status": "UNAVAILABLE",
        "stale_after_hours": 72,
    },
    {
        "series_id": "DEXCHUS",
        "display_name": "USD/CNH",
        "category": "fx",
        "title": "Chinese Yuan Renminbi to U.S. Dollar Spot Exchange Rate",
        "units": "CNY per USD",
        "frequency": "Daily",
        "seasonal_adjustment": "Not Seasonally Adjusted",
        "provider": "fred",
        "source_url": "https://fred.stlouisfed.org/series/DEXCHUS",
        "data_status": "UNAVAILABLE",
        "stale_after_hours": 72,
    },
]


COT_INSTRUMENTS = [
    {"cftc_code": "088691", "name": "GOLD - COMMODITY EXCHANGE INC.", "display_name": "Gold", "category": "commodity", "exchange": "COMEX", "related_series_id": None},
    {"cftc_code": "067651", "name": "CRUDE OIL, LIGHT SWEET - NEW YORK MERCANTILE EXCHANGE", "display_name": "WTI Crude Oil", "category": "commodity", "exchange": "NYMEX", "related_series_id": "DCOILWTICO"},
    {"cftc_code": "13874A", "name": "E-MINI S&P 500 - CHICAGO MERCANTILE EXCHANGE", "display_name": "S&P 500 E-mini", "category": "equity", "exchange": "CME", "related_series_id": "SP500"},
    {"cftc_code": "099741", "name": "EURO FX - CHICAGO MERCANTILE EXCHANGE", "display_name": "Euro FX", "category": "fx", "exchange": "CME", "related_series_id": "DEXUSEU"},
    {"cftc_code": "043602", "name": "10-YEAR U.S. TREASURY NOTES - CHICAGO BOARD OF TRADE", "display_name": "10-Year T-Note", "category": "rates", "exchange": "CBOT", "related_series_id": "DGS10"},
    {"cftc_code": "023651", "name": "NATURAL GAS - NEW YORK MERCANTILE EXCHANGE", "display_name": "Natural Gas", "category": "commodity", "exchange": "NYMEX", "related_series_id": "DHHNGSP"},
]


def seed():
    db = SessionLocal()
    try:
        if get_user_by_email(db, DEV_EMAIL):
            print(f"[seed] User {DEV_EMAIL} already exists — skipping")
        else:
            create_user(db, DEV_EMAIL, DEV_PASSWORD)
            print("=" * 60)
            print("[seed] Dev user created")
            print(f"  Email:    {DEV_EMAIL}")
            print(f"  Password: {DEV_PASSWORD}")
            print("  Change these credentials before any public deployment!")
            print("=" * 60)

        for meta in ALL_SERIES:
            existing = db.query(MacroSeries).filter(MacroSeries.series_id == meta["series_id"]).first()
            if existing:
                # Update display_name and category in case they were seeded before Phase 3
                changed = False
                if existing.display_name != meta.get("display_name"):
                    existing.display_name = meta.get("display_name")
                    changed = True
                if existing.category != meta.get("category", "macro"):
                    existing.category = meta.get("category", "macro")
                    changed = True
                if changed:
                    print(f"[seed] MacroSeries {meta['series_id']} updated (display_name/category)")
                else:
                    print(f"[seed] MacroSeries {meta['series_id']} already exists — skipping")
                continue
            db.add(MacroSeries(**meta))
            print(f"[seed] MacroSeries {meta['series_id']} inserted")

        for cot in COT_INSTRUMENTS:
            existing = db.query(CotInstrument).filter(CotInstrument.cftc_code == cot["cftc_code"]).first()
            if existing:
                print(f"[seed] CotInstrument {cot['cftc_code']} already exists — skipping")
                continue
            db.add(CotInstrument(**cot))
            print(f"[seed] CotInstrument {cot['cftc_code']} ({cot['display_name']}) inserted")

        db.commit()

    finally:
        db.close()


if __name__ == "__main__":
    seed()
