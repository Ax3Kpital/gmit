"""
Dev seed: creates a default user if it does not exist.
Credentials are printed at startup — change them before any public deployment.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.services.auth_service import get_user_by_email, create_user

DEV_EMAIL = "admin@gmit.local"
DEV_PASSWORD = "gmit_dev_2026"


def seed():
    db = SessionLocal()
    try:
        if get_user_by_email(db, DEV_EMAIL):
            print(f"[seed] User {DEV_EMAIL} already exists — skipping")
            return
        create_user(db, DEV_EMAIL, DEV_PASSWORD)
        print("=" * 60)
        print("[seed] Dev user created")
        print(f"  Email:    {DEV_EMAIL}")
        print(f"  Password: {DEV_PASSWORD}")
        print("  Change these credentials before any public deployment!")
        print("=" * 60)
    finally:
        db.close()


if __name__ == "__main__":
    seed()
