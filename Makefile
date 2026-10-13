.PHONY: up down build logs shell-backend shell-db \
        test-backend lint-backend typecheck-backend \
        test-frontend typecheck-frontend \
        migrate seed

up:
	docker compose up --build

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

shell-backend:
	docker compose exec backend bash

shell-db:
	docker compose exec postgres psql -U gmit -d gmit

migrate:
	docker compose exec backend alembic upgrade head

seed:
	docker compose exec backend python scripts/seed_dev.py

test-backend:
	cd backend && pytest -v

lint-backend:
	cd backend && ruff check .

typecheck-backend:
	cd backend && mypy app/

test-frontend:
	cd apps/web && npm run test

typecheck-frontend:
	cd apps/web && npx tsc --noEmit

lint-frontend:
	cd apps/web && npm run lint
