from mastko.cli.executer import cmd_executer
from mastko.cli.parser import get_parser
from mastko.lib.logger import get_logger

log = get_logger("mastko.main_handler")


def main() -> None:
    try:
        parser = get_parser()
        cmd_executer(parser)
    except Exception as ex:
        log.error(ex)
        parser.exit(1, str(ex))


if __name__ == "__main__":
    main()
