from argparse import ArgumentParser, Namespace, _SubParsersAction

from mastko.data.target import Target
from mastko.lib.bruteforcer import Bruteforcer
from mastko.lib.exceptions import BruteforceCommandException
from mastko.lib.logger import get_logger

log = get_logger("mastko.cli.commands.bruteforce")


def bruteforce_parser(subparser: _SubParsersAction) -> None:
    bruteforce_parser: ArgumentParser = subparser.add_parser(
        name="bruteforce", help="runs subdomain takeover bruteforce service"
    )
    bruteforce_parser.add_argument(
        "--iterations",
        help="Specify the number of bruteforce iterations",
        metavar="iterations",
        dest="iterations",
        type=int,
        required=True,
    )
    bruteforce_parser.add_argument(
        "--elastic-ip",
        help="Specify the Elastic IP to use for bruteforcing",
        metavar="eip_ip",
        dest="eip_ip",
        type=str,
        required=True,
    )
    bruteforce_parser.add_argument(
        "--ec2-instance-id",
        help="Specify the EC2 instance-id to use for bruteforcing",
        metavar="instance_id",
        dest="instance_id",
        type=str,
        required=True,
    )
    bruteforce_parser.add_argument(
        "--region",
        help="Specify the AWS region to use for bruteforcing",
        metavar="region",
        dest="region",
        type=str,
        required=True,
    )


def bruteforce_executer(args: Namespace) -> None:
    log.info(f"Initiating bruteforce for {args.iterations} iterations")

    if not Target.target_available():
        raise BruteforceCommandException(
            "Prequisite for bruteforce not met, there are no targets available in DB. "
            "Please run `mastko validate_targets --help` for more infromation."
        )

    bruteforcer = Bruteforcer(
        targets=Target.get_all_targets_from_db(),
        region=args.region,
        instance_id=args.instance_id,
        eip_ip=args.eip_ip,
    )
    bruteforcer.run(iterations=args.iterations)
