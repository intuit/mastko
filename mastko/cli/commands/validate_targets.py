from argparse import ArgumentParser, Namespace, _SubParsersAction

from mastko.data.target import Target
from mastko.lib.logger import get_logger
from mastko.lib.target_generator import TargetGenerator

log = get_logger("mastko.cli.commands.validate_targets")


def validate_targets_parser(subparser: _SubParsersAction) -> None:
    validate_targets_parser: ArgumentParser = subparser.add_parser(
        name="validate_targets", help="validates and loads targets to DB"
    )
    validate_targets_parser.add_argument(
        "--hosts-file",
        help="A newline delimited file with all interested domains.",
        metavar="hosts_file",
        dest="hosts_file",
        type=str,
        required=True,
    )
    validate_targets_parser.add_argument(
        "--region",
        help="Filter target for a given AWS Region.",
        metavar="region",
        dest="region",
        type=str,
        required=False,
    )


def validate_targets_executer(args: Namespace) -> None:
    generator = TargetGenerator(hosts_file=args.hosts_file, region=args.region)
    targets = generator.generate()
    filtered_targets = []
    if args.region is not None:
        filtered_targets = generator.filter_targets_to_aws_region(targets)
    else:
        filtered_targets = targets

    if len(filtered_targets) > 0:
        generator.load_targets(filtered_targets)
        output_file_name = "mastko_targets.csv"
        Target.to_csv(targets, output_file_name)
        log.info(
            f"Target Validation Complete. Targets loaded to Database and also written to {output_file_name}"
        )
    else:
        log.warning(
            "NO TARGETS FOUND for given criteria. Please rerun with more Hosts or remove the AWS region"
            " filter."
        )
