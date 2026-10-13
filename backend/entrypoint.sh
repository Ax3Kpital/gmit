#!/bin/bash
set -e

echo "==> Running database migrations..."
alembic upgrade head

echo "==> Seeding dev user (skipped if already exists)..."
python scripts/seed_dev.py || true

echo "==> Starting GMIT API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
