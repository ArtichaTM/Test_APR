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
