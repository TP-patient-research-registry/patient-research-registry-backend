.PHONY: help deps dev migrate migrations test lint format schema superuser seed worker

COMPOSE_DEV := docker compose -f deploy/docker-compose.dev.yml
MANAGE := uv run python manage.py

help:  ## Show available targets
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F ':.*## ' '{printf "  %-12s %s\n", $$1, $$2}'

deps:  ## Start PostgreSQL + Redis for local development
	$(COMPOSE_DEV) up -d --wait

dev: deps  ## Start dependencies and the Django dev server on :8000
	$(MANAGE) runserver 0.0.0.0:8000

worker:  ## Run a Celery worker locally
	uv run celery -A config worker --loglevel=info

migrate:  ## Apply database migrations
	$(MANAGE) migrate

migrations:  ## Create new migrations
	$(MANAGE) makemigrations

test:  ## Run the test suite (needs `make deps`)
	uv run pytest

lint:  ## Ruff lint + format check + missing migrations check
	uv run ruff check .
	uv run ruff format --check .
	$(MANAGE) makemigrations --check --dry-run

format:  ## Auto-format and fix lint issues
	uv run ruff check --fix .
	uv run ruff format .

schema:  ## Export the OpenAPI schema to schema.yml
	$(MANAGE) spectacular --file schema.yml --validate

superuser:  ## Create an admin user
	$(MANAGE) createsuperuser

seed:  ## Fill the database with fake demo data
	$(MANAGE) seed_demo
