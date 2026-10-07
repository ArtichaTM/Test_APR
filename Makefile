# `test` and `verify` call only docker and uv, so they work on Linux and Windows.
# Each target uses its own compose project, so they never touch `run` data.

export TEST_POSTGRES_PORT ?= 55432
export TEST_ELASTICSEARCH_PORT ?= 59200

TEST_COMPOSE := docker compose -p test_apr_test -f docker-compose.yml -f docker-compose.test.yml
VERIFY_COMPOSE := docker compose -p test_apr_verify -f docker-compose.yml -f docker-compose.verify.yml

.PHONY: test verify run

## Run all tests locally with uv; db and elasticsearch run in docker
test: export POSTGRES_HOST := localhost
test: export POSTGRES_PORT := $(TEST_POSTGRES_PORT)
test: export ELASTICSEARCH_URL := http://localhost:$(TEST_ELASTICSEARCH_PORT)
test:
	$(TEST_COMPOSE) up -d --wait db elasticsearch
	uv run pytest

## Run all tests and e2e checks in docker against a fresh stack
verify:
	$(VERIFY_COMPOSE) down -v
	$(VERIFY_COMPOSE) up --build --attach tests --exit-code-from tests
	$(VERIFY_COMPOSE) down -v

## Build and start the service at http://localhost:8000 (Linux)
run:
	docker compose up -d --build --wait
	@echo "Running at http://localhost:8000 (API docs: http://localhost:8000/docs)"
