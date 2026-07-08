# Test-APR
## Установка
### 1. Поднятие контейнера
Docker контейнер поднимается через `docker compose up -d`
### 2. Добавление тестовых данных
Тестовые данные добавляются через `docker compose exec app python -m test_apr.cli import-csv data/posts.csv`. Папка `/data` читается напрямую из контейнера, любые данные из этой папки попадают в контейнер. Можно закинуть в неё файл "test_debug.csv" и загрузить в базу данных в контейнере командой `docker compose exec app python -m test_apr.cli import-csv data/test_debug.csv`

## Примечания
- Команда `python -m test_apr.cli` предотвращает занесение дубликатов в таблицу по тексту+рубрики
- Добавлено поле "text_hash" для предотвращения дубликатов
