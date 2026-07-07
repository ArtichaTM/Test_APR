FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Install dependencies first (separate layer, cached as long as
# pyproject.toml doesn't change).
COPY pyproject.toml .python-version ./
RUN uv sync --no-install-project

# Now add the actual source and finish the sync (installs the project itself).
COPY README.md ./
COPY src ./src
RUN uv sync

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["python", "-m", "test_apr"]
