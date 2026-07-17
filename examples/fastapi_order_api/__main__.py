import argparse
from collections.abc import Sequence

import uvicorn

from .application import create_app


def _port(value: str) -> int:
    try:
        port = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("port must be an integer") from error
    if not 1 <= port <= 65_535:
        raise argparse.ArgumentTypeError("port must be between 1 and 65535")
    return port


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the loopback FastAPI order example")
    parser.add_argument("--port", type=_port, default=8000)
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = _parser().parse_args(argv)
    uvicorn.run(
        create_app(),
        host="127.0.0.1",
        port=args.port,
        workers=1,
        reload=False,
        proxy_headers=False,
    )


if __name__ == "__main__":
    main()
