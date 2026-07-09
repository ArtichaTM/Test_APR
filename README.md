# Test-APR
Сервис полнотекстового поиска документов (PostgreSQL + Elasticsearch).

## Быстрый старт

```bash
docker compose up -d
```

Импорт данных из CSV (колонки: `text`, `created_date`, `rubrics` — рубрики в виде Python-списка, например `"['тег1','тег2']"`):

```bash
docker compose exec app python -m test_apr.cli data/posts.csv
```

Переменные в `.env` можно не трогать в принципе - параметры по умолчанию позволяют пользоваться сайтом "as-is"

## Тесты
Для запуска тестов нужно закомментировать строчку 7 в [dockerignore](./.dockerignore#L7):

```gitignore
.git
.venv
__pycache__
*.pyc
.env
data/
# tests/  <-- Эту
.pytest_cache
```

[Добавить аргумент](./Dockerfile#L9) `--dev` к синхронизации проекта (для добавления зависимостей) и [убрать комментарий с папкой тестов](./Dockerfile#L13) в [Dockerfile](./Dockerfile):

```Dockerfile
FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

COPY pyproject.toml .python-version ./
RUN uv sync --dev --no-install-project  <-- --dev здесь

COPY README.md ./
COPY src ./src
COPY tests ./tests <- Убрать комментарий для добавления тестов в сборку
RUN uv sync

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["python", "-m", "test_apr"]
```

## API
- `GET /document/{id}` — получить документ.
- `DELETE /document/{id}` — удалить документ.
- `GET /search?q=<запрос>&limit=<n>&offset=<m>` — поиск

## Конфигурация
Переменные окружения (задаются в `.env`):

- `POSTGRES_*` — параметры подключения к БД.
- `ELASTICSEARCH_URL` — адрес Elasticsearch.
- `SEARCH_MAX_CANDIDATES` — сколько кандидатов забирать из ES перед сортировкой в БД (по умолчанию 10000).

## Примечания
- Дедупликация: строки с одинаковыми `text` и `rubrics` пропускаются при импорте (можно перезапускать без опасений).
- Сервис слушает порт `8000`.
