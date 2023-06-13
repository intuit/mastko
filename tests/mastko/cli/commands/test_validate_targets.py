from argparse import Namespace

from mastko.cli.commands.validate_targets import validate_targets_executer, validate_targets_parser
from mastko.data.target import Target
from mastko.lib.target_generator import TargetGenerator


def test_validate_targets_parser(mocker):
    mock_subparsers = mocker.MagicMock()
    validate_targets_parser(mock_subparsers)

    mock_subparsers.add_parser.assert_called_once_with(
        name="validate_targets", help="validates and loads targets to DB"
    )


def return_targets(mocker):
    return [Target(domain="example.com", ip_address="1.2.3.4", region="us-west-2")]


def test_validate_targets_executer_with_region(mocker):
    mock_args = Namespace(hosts_file="fake-file", region="us-west-2")
    mocker.patch.object(TargetGenerator, "generate", return_targets)
    mocker.patch.object(TargetGenerator, "import_hosts_from_file")
    mock_target_generator_filter_targets_to_aws_region = mocker.patch.object(
        TargetGenerator, "filter_targets_to_aws_region"
    )
    validate_targets_executer(args=mock_args)
    mock_target_generator_filter_targets_to_aws_region.assert_called_once_with(
        [Target(domain="example.com", ip_address="1.2.3.4", region="us-west-2")]
    )


def test_validate_targets_executer_without_region(mocker):
    mock_args = Namespace(hosts_file="fake-file", region=None)
    mocker.patch.object(TargetGenerator, "generate", return_targets)
    mocker.patch.object(TargetGenerator, "import_hosts_from_file")
    mock_target_generator_filter_targets_to_aws_region = mocker.patch.object(
        TargetGenerator, "filter_targets_to_aws_region"
    )
    validate_targets_executer(args=mock_args)
    mock_target_generator_filter_targets_to_aws_region.assert_not_called()
