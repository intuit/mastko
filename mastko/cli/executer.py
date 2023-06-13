from argparse import ArgumentParser

from mastko.cli.commands.bruteforce import bruteforce_executer
from mastko.cli.commands.validate_targets import validate_targets_executer
from mastko.lib.logger import get_logger

log = get_logger("mastko.cli.executer")


def cmd_executer(parser: ArgumentParser) -> None:
    try:
        args = parser.parse_args()
        if args.command == "bruteforce":
            bruteforce_executer(args)

        if args.command == "validate_targets":
            validate_targets_executer(args)
    except Exception as ex:
        log.error(ex)
        parser.exit(1)
