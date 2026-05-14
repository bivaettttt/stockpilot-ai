.PHONY: help dev api backend frontend frontend-build build demo-data analyze-demo validate-demo test lint format check check-all docker-build docker-up docker-down docker-logs install install-frontend clean

help:
	@echo "StockPilot AI — доступные команды"
	@echo "--------------------------------"
	@echo "make dev              - запустить backend и frontend вместе локально"
	@echo "make api              - запустить FastAPI backend локально"
	@echo "make backend          - alias для make api"
	@echo "make frontend         - запустить Next.js frontend локально"
	@echo "make frontend-build   - проверить production-сборку frontend"
	@echo "make build            - alias для make frontend-build"
	@echo "make demo-data        - сгенерировать демо-датасет"
	@echo "make analyze-demo     - запустить анализ демо-датасета через CLI"
	@echo "make validate-demo    - проверить демо-файл через API"
	@echo "make test             - запустить Python-тесты"
	@echo "make lint             - проверить Python-код через ruff"
	@echo "make format           - отформатировать Python-код через ruff"
	@echo "make check            - запустить Python lint + test"
	@echo "make check-all        - запустить Python check + frontend build"
	@echo "make docker-build     - собрать Docker-образы"
	@echo "make docker-up        - запустить проект через Docker Compose"
	@echo "make docker-down      - остановить Docker Compose"
	@echo "make docker-logs      - показать Docker-логи"
	@echo "make install          - установить Python-зависимости"
	@echo "make install-frontend - установить frontend-зависимости"
	@echo "make clean            - удалить временные результаты"

dev:
	./scripts/run_dev.sh

api:
	. .venv/bin/activate && uvicorn src.api.main:app --reload

backend: api

frontend:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

build: frontend-build

demo-data:
	. .venv/bin/activate && python scripts/generate_demo_data.py

analyze-demo:
	. .venv/bin/activate && python main.py \
		--input data/input/demo_sales_90_days.csv \
		--output data/output/demo_report.xlsx \
		--dashboard data/output/demo_dashboard.html \
		--horizon 30 \
		--safety-stock 0.25 \
		--lead-time 5

validate-demo:
	curl -X POST "http://127.0.0.1:8000/validate-file" \
		-F "file=@data/input/demo_sales_90_days.csv"

test:
	. .venv/bin/activate && pytest -q

lint:
	. .venv/bin/activate && ruff check .

format:
	. .venv/bin/activate && ruff format .
	. .venv/bin/activate && ruff check . --fix

check: lint test

check-all: check frontend-build

docker-build:
	docker compose build

docker-up:
	docker compose up

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

install:
	@test -d .venv || python3 -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt

install-frontend:
	cd frontend && npm install

clean:
	rm -rf data/output/*
	rm -rf data/uploads/*
	rm -rf logs/*
	rm -rf frontend/.next
