# StockPilot AI

Local-first AI workspace для анализа продаж, запасов, прогнозирования и закупочного планирования.

StockPilot AI помогает локально загрузить CSV/XLSX с продажами и остатками, проверить структуру файла, построить анализ, получить закупочные рекомендации, оценить надёжность прогноза и объяснить результат через локальную Ollama.

## Что умеет

- CSV/XLSX upload
- Import Wizard
- column mapping
- local Ollama Copilot
- sales / inventory analytics
- forecast
- purchase recommendations
- supplier-aware procurement
- reliability metrics
- history
- reports / export

## Local-first принцип

- данные остаются локально;
- AI работает через Ollama;
- OpenAI API не используется;
- внешние AI providers не используются.

## Требования

- Python 3.12+  
  В проекте `ruff` настроен на `py312`, backend tests прогонялись через Python 3.12.
- Node.js 20+  
  Frontend собран на `Next.js 16`, для локального запуска разумный минимум сейчас `Node.js 20`.
- npm
- Ollama
- модель `qwen2.5:7b`

## Установка backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Установка frontend

```bash
cd frontend
npm install
```

Если нужен воспроизводимый install по lock-файлу:

```bash
cd frontend
npm ci
```

## Настройка env

Корневой `.env`:

```bash
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_TIMEOUT_SECONDS=60
```

Frontend `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Шаблоны:

- [/.env.example](/Users/bivaettttt/Desktop/stockpilot-ai/.env.example)
- [/Users/bivaettttt/Desktop/stockpilot-ai/frontend/.env.example](/Users/bivaettttt/Desktop/stockpilot-ai/frontend/.env.example)

## Запуск Ollama

Проверить локальные модели:

```bash
ollama list
```

Если модели нет:

```bash
ollama pull qwen2.5:7b
```

Быстрый smoke test:

```bash
ollama run qwen2.5:7b "Привет"
```

## Запуск backend

```bash
source .venv/bin/activate
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

## Запуск frontend

```bash
cd frontend
npm run dev
```

## URLs

- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Ollama: [http://localhost:11434](http://localhost:11434)

## Проверки

Backend:

```bash
./.venv/bin/python -m pytest -q
```

Frontend:

```bash
cd frontend
npm run lint
npm run typecheck
npm run build
```

## Demo scenario

1. Откройте [http://localhost:3000](http://localhost:3000).
2. На главной нажмите `Попробовать demo-файл`.
3. Проверьте preview файла.
4. Если нужно, проверьте mapping step.
5. Нажмите `Запустить анализ`.
6. На главной проверьте executive summary и action cards.
7. Откройте `Закупочный план`.
8. Измените статус, итоговое количество и комментарий по любой позиции.
9. Откройте `Надёжность анализа`.
10. Откройте `Copilot` и задайте вопрос: `Что нужно сделать в первую очередь?`
11. Перейдите в `Историю`.
12. Откройте сохранённый анализ повторно.
13. Перейдите в `Поставщики`.
14. Создайте поставщика.
15. Добавьте `lead time`, `MOQ`, `pack size`.
16. Привяжите SKU к поставщику через `Настройки товара`.
17. Вернитесь в `Закупочный план`.
18. Проверьте `С учётом поставщика`.
19. Экспортируйте CSV закупочного плана.

Короткая версия запуска — в [QUICKSTART.md](/Users/bivaettttt/Desktop/stockpilot-ai/QUICKSTART.md).  
Smoke checklist — в [docs/SMOKE_TEST.md](/Users/bivaettttt/Desktop/stockpilot-ai/docs/SMOKE_TEST.md).

## Формат входного файла

Обязательные колонки:

- `date`
- `sku`
- `product_name`
- `quantity_sold`
- `revenue`
- `stock_on_hand`

Полезные дополнительные:

- `category`
- `purchase_price`
- `selling_price`
- `supplier`
- `promotion_flag`

Пример CSV:

```csv
date,sku,product_name,category,quantity_sold,revenue,stock_on_hand,purchase_price,selling_price,supplier,promotion_flag
2026-01-01,COF-001,Кофе арабика 250г,Кофе,7,2940,183,250,420,Поставщик А,false
2026-01-02,COF-001,Кофе арабика 250г,Кофе,6,2520,177,250,420,Поставщик А,false
2026-01-01,TEA-001,Чай зелёный 100г,Чай,4,1320,96,160,330,Поставщик Б,true
```

Демо-файл в репозитории: [data/input/sample_sales.csv](/Users/bivaettttt/Desktop/stockpilot-ai/data/input/sample_sales.csv)

## Что уже готово

- inspect preview до анализа
- Import Wizard с deterministic mapping
- normalize + analyze flow
- локальный Copilot по import flow
- локальный Copilot по результатам анализа
- action-first overview
- закупочный workflow:
  - statuses
  - manual final qty
  - comments
  - grouped supplier view
  - CSV export
- reliability page:
  - data quality
  - WAPE / MAE / Bias
  - SKU-level reliability
- analysis history:
  - saved snapshots
  - reopen old analysis
  - restore active state after reload
- supplier / CRM-lite layer:
  - suppliers CRUD
  - SKU settings
  - MOQ / pack size / lead time
  - supplier-aware procurement enrichment

## Ограничения текущей версии

- локальный single-user режим;
- без auth;
- без SaaS;
- без cloud sync;
- без отправки заказов поставщикам;
- без purchase orders;
- без PDF-отчётов;
- Copilot отвечает только по переданному контексту;
- forecasting не гарантирует точность, а показывает reliability metrics;
- Docker Compose есть как локальный convenience-вариант, но основной рекомендуемый способ запуска сейчас — local dev через `uvicorn` + `npm run dev`;
- Ollama должна быть запущена отдельно, `docker-compose.yml` её не поднимает.

## Makefile

Быстрые локальные команды:

```bash
make backend
make frontend
make test
make lint
make build
```

Также доступны:

```bash
make dev
make check
make check-all
```

## Docker Compose

В репозитории есть [docker-compose.yml](/Users/bivaettttt/Desktop/stockpilot-ai/docker-compose.yml), но он сейчас ориентирован на локальный dev convenience.

Что важно:

- Compose не поднимает Ollama.
- Основной рекомендуемый запуск сейчас — вручную:
  - backend через `uvicorn`
  - frontend через `npm run dev`
  - Ollama отдельно локально

## Roadmap

- финальная UI polish
- purchase orders
- PDF / export improvements
- deeper forecast models
- optional desktop packaging
- optional multi-user / SaaS later
