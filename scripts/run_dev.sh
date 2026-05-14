#!/bin/bash

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$PROJECT_ROOT"

echo "StockPilot AI — dev launcher"
echo "======================================"
echo "Project root: $PROJECT_ROOT"
echo

if [ ! -d ".venv" ]; then
  echo ".venv не найден — создаю виртуальное окружение..."
  python3 -m venv .venv
fi

source "$PROJECT_ROOT/.venv/bin/activate"

if ! python -c "import fastapi" 2>/dev/null; then
  echo "Зависимости не установлены — выполняю pip install -r requirements.txt..."
  pip install -r "$PROJECT_ROOT/requirements.txt"
fi

if [ ! -d "frontend" ]; then
  echo "Ошибка: папка frontend не найдена."
  exit 1
fi

if [ ! -d "frontend/node_modules" ]; then
  echo "frontend/node_modules не найден."
  echo "Устанавливаю frontend-зависимости..."
  cd "$PROJECT_ROOT/frontend"
  npm install
  cd "$PROJECT_ROOT"
fi

echo "Запускаю backend API на http://127.0.0.1:8000"
echo "Запускаю frontend на http://localhost:3000"
echo
echo "Для остановки нажмите Ctrl + C"
echo "======================================"
echo

cleanup() {
  echo
  echo "Останавливаю процессы..."
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  echo "Готово."
}

trap cleanup EXIT INT TERM

uvicorn src.api.main:app --reload &
BACKEND_PID=$!

cd "$PROJECT_ROOT/frontend"
npm run dev &
FRONTEND_PID=$!

wait "$BACKEND_PID" "$FRONTEND_PID"
