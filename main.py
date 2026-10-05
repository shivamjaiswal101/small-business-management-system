"""Launch the Business Manager desktop application or configuration CLI."""

import sys

import cli


def main() -> int:
    if len(sys.argv) > 1:
        return cli.run_cli(sys.argv[1:])
    from ui import run_app
    run_app()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
