FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

COPY pyproject.toml .python-version ./
# add `--dev` after sync to enable testing (includes dev packages for testing)
RUN uv sync --no-install-project


COPY README.md ./
COPY src ./src
# COPY tests ./tests
RUN uv sync

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["python", "-m", "test_apr"]
