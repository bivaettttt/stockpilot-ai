# QUICKSTART

## 1. Install

Backend:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Frontend:

```bash
cd frontend
npm install
```

## 2. Env

Root `.env`:

```bash
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_TIMEOUT_SECONDS=60
```

Frontend `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 3. Run Ollama

```bash
ollama list
ollama pull qwen2.5:7b
ollama run qwen2.5:7b "Привет"
```

## 4. Run backend

```bash
source .venv/bin/activate
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

## 5. Run frontend

```bash
cd frontend
npm run dev
```

## 6. Open browser

- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## 7. Demo flow

1. Откройте главную страницу.
2. Нажмите `Попробовать demo-файл`.
3. Проверьте preview и mapping.
4. Запустите анализ.
5. Откройте `Закупочный план`.
6. Измените статус, количество и комментарий.
7. Откройте `Надёжность анализа`.
8. Задайте вопрос в `Copilot`.
9. Откройте `Историю`.
10. Повторно откройте старый анализ.
11. Создайте поставщика и привяжите SKU.
12. Проверьте `С учётом поставщика`.
13. Экспортируйте CSV закупочного плана.
