"""Entrypoint for `python -m test_apr`: runs the API server."""

import uvicorn

from test_apr import config


def main() -> None:
    uvicorn.run("test_apr.app:app", host=config.APP_HOST, port=config.APP_PORT)


if __name__ == "__main__":
    main()
