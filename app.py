from __future__ import annotations

import argparse

from src.cli.cli_app import run_cli
from src.web.web_app import create_app

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Dialog interaction system with web and console interfaces v0.1 (in working)"
    )
    parser.add_argument(
        "-t",
        "--terminal",
        action="store_true",
        help="Run the console interface instead of the web interface.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.terminal:
        run_cli()
        return

    app = create_app()
    app.run(debug=True)


if __name__ == "__main__":
    main()