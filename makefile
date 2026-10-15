.PHONY: install dev db-up db-down db-reset migrate api collect test lint

install:
	pip install -e ".[dev]"

db-up:
	docker compose up -d db

db-down:
	docker compose down

db-reset:
	docker compose down -v && docker compose up -d db

migrate:
	alembic upgrade head

api:
	uvicorn tracker.main:app --reload --host 0.0.0.0 --port 8000

collect:
	python -m scripts.coletar_agora

test:
	pytest -v

lint:
	ruff check src tests
	mypy src