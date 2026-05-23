# StockPilot AI

AI workspace для анализа продаж, запасов, прогнозирования и закупочного планирования.

StockPilot AI помогает загрузить CSV/XLSX с продажами и остатками, проверить структуру файла, построить анализ, получить закупочные рекомендации, оценить надёжность прогноза и объяснить результат через YandexGPT по агрегированному контексту анализа.

## Что умеет

- CSV/XLSX upload
- Import Wizard
- column mapping
- YandexGPT Copilot
- sales / inventory analytics
- forecast
- purchase recommendations
- supplier-aware procurement
- reliability metrics
- history
- reports / export

## Принцип обработки данных и AI

- аналитика считается backend-сервером StockPilot;
- в YandexGPT отправляется только компактный агрегированный контекст анализа;
- исходный CSV/XLSX целиком в модель не отправляется;
- API-ключ YandexGPT хранится только на backend в `.env`;
- OpenAI API не используется.

## Требования

- Python 3.12+  
  В проекте `ruff` настроен на `py312`, backend tests прогонялись через Python 3.12.
- Node.js 20+  
  Frontend собран на `Next.js 16`, для локального запуска разумный минимум сейчас `Node.js 20`.
- npm
- Yandex Cloud service account API key
- `YANDEX_GPT_FOLDER_ID`
- модель по умолчанию `yandexgpt-5-lite`

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
AI_PROVIDER=yandex
YANDEX_GPT_API_KEY=
YANDEX_GPT_FOLDER_ID=
YANDEX_GPT_MODEL=yandexgpt-5-lite
YANDEX_GPT_BASE_URL=https://llm.api.cloud.yandex.net/foundationModels/v1/completion
YANDEX_GPT_TIMEOUT_SECONDS=30
YANDEX_GPT_TEMPERATURE=0.2
YANDEX_GPT_MAX_TOKENS=1200
```

Frontend `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Шаблоны:

- [/.env.example](/Users/bivaettttt/Desktop/stockpilot-ai/.env.example)
- [/Users/bivaettttt/Desktop/stockpilot-ai/frontend/.env.example](/Users/bivaettttt/Desktop/stockpilot-ai/frontend/.env.example)

## Настройка YandexGPT

Создайте API key для сервисного аккаунта Yandex Cloud и укажите `YANDEX_GPT_API_KEY` и `YANDEX_GPT_FOLDER_ID` в корневом `.env`.

Проверить статус backend-конфигурации:

```bash
curl http://127.0.0.1:8000/system/ai-status
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
- Copilot по import flow через YandexGPT
- Copilot по результатам анализа через YandexGPT
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

- single-user режим;
- без auth;
- без SaaS;
- без cloud sync;
- без отправки заказов поставщикам;
- без purchase orders;
- без PDF-отчётов;
- Copilot отвечает только по переданному контексту;
- forecasting не гарантирует точность, а показывает reliability metrics;
- Docker Compose есть как локальный convenience-вариант, но основной рекомендуемый способ запуска сейчас — local dev через `uvicorn` + `npm run dev`;
- YandexGPT API key настраивается отдельно в `.env` и не попадает во frontend.

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

- Compose не настраивает YandexGPT credentials.
- Основной рекомендуемый запуск сейчас — вручную:
  - backend через `uvicorn`
  - frontend через `npm run dev`
  - YandexGPT credentials в `.env`

## Roadmap

- финальная UI polish
- purchase orders
- PDF / export improvements
- deeper forecast models
- optional desktop packaging
- optional multi-user / SaaS later
