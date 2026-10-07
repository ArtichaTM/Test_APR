# Test-APR
Сервис полнотекстового поиска документов (PostgreSQL + Elasticsearch).

## Быстрый старт
Нужны Docker и GNU make (на Windows: `winget install ezwinports.make`, `scoop install make` или `choco install make`).

```bash
make run
```

Сервис поднимется на http://localhost:8000 (документация API: http://localhost:8000/docs).
`make run` рассчитан на Linux; `make test` и `make verify` работают и на Linux, и на Windows.

Импорт данных из CSV (колонки: `text`, `created_date`, `rubrics` — рубрики в виде Python-списка, например `"['тег1','тег2']"`):

```bash
docker compose exec app python -m test_apr.cli import-csv data/posts.csv
```

Переиндексация всех документов из PostgreSQL в Elasticsearch (например, после обновления ES):

```bash
docker compose exec app python -m test_apr.cli reindex
```

Переменные в `.env` можно не трогать в принципе - параметры по умолчанию позволяют пользоваться сайтом "as-is"

## Тесты
- `make test` — все тесты локально через `uv`. PostgreSQL и Elasticsearch поднимаются в Docker
  (отдельный проект `test_apr_test`, порты `55432` и `59200`; меняются через
  `TEST_POSTGRES_PORT` и `TEST_ELASTICSEARCH_PORT`). E2E-тесты пропускаются.
- `make verify` — все тесты, включая e2e (CLI-импорт, поиск, получение и удаление через HTTP, `reindex`),
  внутри Docker на чистом окружении (проект `test_apr_verify`). После успешного прогона окружение удаляется;
  при ошибке контейнеры остаются остановленными для разбора и пересоздаются при следующем запуске.

Остановить окружение `make test`: `docker compose -p test_apr_test down -v`.

## API
- `GET /document/{id}` — получить документ.
- `DELETE /document/{id}` — удалить документ.
- `GET /search?q=<запрос>&limit=<n>&offset=<m>` — поиск

## Конфигурация
Переменные окружения (задаются в `.env`):

- `POSTGRES_*` — параметры подключения к БД.
- `ELASTICSEARCH_URL` — адрес Elasticsearch.
- `SEARCH_MAX_CANDIDATES` — сколько кандидатов забирать из ES перед сортировкой в БД (по умолчанию 10000).

## Обновление с PostgreSQL 16 / Elasticsearch 7
Данные старых версий несовместимы с PostgreSQL 18 и Elasticsearch 9, поэтому
новые версии используют новые тома (`pg18-data`, `es9-data`). Старые тома
(`<project>_db-data`, `<project>_es-data`, см. `docker volume ls`) не удаляются.

Перенос данных PostgreSQL:

```bash
docker compose down
docker run -d --name pg16-dump -v test_apr_db-data:/var/lib/postgresql/data postgres:16-alpine
until docker exec pg16-dump pg_isready -U postgres; do sleep 1; done
docker exec pg16-dump pg_dump -U postgres -d test_apr --clean --if-exists > dump.sql
docker rm -f pg16-dump
docker compose up -d --wait db
docker compose exec -T db psql -U postgres -d test_apr -v ON_ERROR_STOP=1 < dump.sql
docker compose up -d --build --wait
docker compose exec app python -m test_apr.cli reindex
```

Индекс Elasticsearch не переносится, а строится заново из PostgreSQL командой `reindex`.
После проверки старые тома можно удалить: `docker volume rm test_apr_db-data test_apr_es-data`.

## Примечания
- Дедупликация: строки с одинаковыми `text` и `rubrics` пропускаются при импорте (можно перезапускать без опасений).
- Сервис слушает порт `8000`.
