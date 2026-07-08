import os

from dotenv import load_dotenv

load_dotenv()


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value else default


# --- Postgres ---------------------------------------------------------------
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = _get_int("POSTGRES_PORT", 5432)
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "test_apr")

DATABASE_URL = (
    f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

# --- Elasticsearch ------------------------------------------------------------
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
ELASTICSEARCH_INDEX = os.getenv("ELASTICSEARCH_INDEX", "documents")

# --- Search ---------------------------------------------------------------------
# Default/limit for GET /search pagination.
SEARCH_DEFAULT_LIMIT = _get_int("SEARCH_DEFAULT_LIMIT", 20)
SEARCH_MAX_LIMIT = _get_int("SEARCH_MAX_LIMIT", 100)

# How many candidate ids to pull from Elasticsearch before the final
# ordering/pagination by `created_date` is applied in Postgres. The index
# only stores `id`/`text` (per spec), so relevance filtering happens in ES
# and date ordering happens in the DB.
SEARCH_MAX_CANDIDATES = _get_int("SEARCH_MAX_CANDIDATES", 10000)

# --- App ----------------------------------------------------------------------
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = _get_int("APP_PORT", 8000)
