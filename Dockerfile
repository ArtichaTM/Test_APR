FROM python:3.14-slim AS base

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --locked --no-dev --no-install-project

COPY README.md ./
COPY src ./src
RUN uv sync --locked --no-dev

ENV PATH="/app/.venv/bin:$PATH"


# Test suite image, used by `make verify`
FROM base AS test

RUN uv sync --locked
COPY tests ./tests

CMD ["pytest"]


FROM base AS app

EXPOSE 8000

CMD ["python", "-m", "test_apr"]
