import sys
from argparse import ArgumentParser, _SubParsersAction

from mastko.cli.commands.bruteforce import bruteforce_parser
from mastko.cli.commands.validate_targets import validate_targets_parser
from mastko.version import __version__


def get_parser() -> ArgumentParser:
    parser = ArgumentParser(prog="mastko")

    subparsers: _SubParsersAction = parser.add_subparsers(
        description="Please select a subcommand. For more information run `mastko {sub-command} --help`.",
        help="sub-commands:",
        dest="command",
    )

    bruteforce_parser(subparsers)
    validate_targets_parser(subparsers)

    # global
    parser.add_argument(
        "--version", help="print out cli version", action="version", version=f"v{__version__}"
    )

    # handle no args
    parser.parse_args(args=None if sys.argv[1:] else ["--help"])

    return parser
