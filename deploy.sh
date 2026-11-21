#!/usr/bin/env bash
# GMIT — production deploy script
# Usage: ./deploy.sh [--skip-build]
# Requires: Docker, .env file with production values

set -euo pipefail

COMPOSE="docker compose -f docker-compose.prod.yml"
SKIP_BUILD=${1:-""}

echo "==> GMIT deploy starting at $(date -u '+%Y-%m-%d %H:%M UTC')"

# Sanity checks
if [ ! -f .env ]; then
  echo "ERROR: .env not found. Copy .env.example and fill in values."
  exit 1
fi

if ! grep -q "POSTGRES_PASSWORD=" .env || grep -q "^POSTGRES_PASSWORD=$" .env; then
  echo "ERROR: POSTGRES_PASSWORD is not set in .env"
  exit 1
fi

if ! grep -q "DOMAIN=" .env || grep -q "^DOMAIN=$" .env; then
  echo "ERROR: DOMAIN is not set in .env (e.g. DOMAIN=gmit.yourdomain.com)"
  exit 1
fi

# Pull latest images (skip if building from source)
if [ "$SKIP_BUILD" != "--skip-build" ]; then
  echo "==> Building images..."
  $COMPOSE build --no-cache backend web
fi

# Start postgres first (healthcheck ensures it's ready)
echo "==> Starting postgres..."
$COMPOSE up -d postgres
echo "==> Waiting for postgres to be healthy..."
until $COMPOSE exec -T postgres pg_isready -U gmit > /dev/null 2>&1; do
  sleep 2
done

# Run migrations
echo "==> Running Alembic migrations..."
$COMPOSE run --rm backend alembic upgrade head

# Start everything
echo "==> Starting all services..."
$COMPOSE up -d --force-recreate

# Health check
sleep 5
if $COMPOSE exec -T backend curl -sf http://localhost:8000/api/health > /dev/null; then
  echo "==> Backend: OK"
else
  echo "WARNING: Backend health check failed — check logs with: docker compose -f docker-compose.prod.yml logs backend"
fi

echo ""
echo "==> Deploy complete!"
echo "    App:  https://$(grep '^DOMAIN=' .env | cut -d= -f2)"
echo "    Logs: docker compose -f docker-compose.prod.yml logs -f"
echo "    Stop: docker compose -f docker-compose.prod.yml down"
