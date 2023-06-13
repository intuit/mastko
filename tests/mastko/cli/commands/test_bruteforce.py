from argparse import Namespace

from mastko.cli.commands.bruteforce import bruteforce_executer, bruteforce_parser
from mastko.lib.exceptions import BruteforceCommandException


import pytest


def test_bruteforce_parser(mocker):
    mock_subparsers = mocker.MagicMock()
    bruteforce_parser(mock_subparsers)

    mock_subparsers.add_parser.assert_called_once_with(
        name="bruteforce", help="runs subdomain takeover bruteforce service"
    )


def test_bruteforce_executer(mocker):
    mock_args = Namespace(iterations=1, eip_ip="0.0.0.0", instance_id="test-id", region="us-west-2")
    mock_target_available = mocker.patch(
        "mastko.cli.commands.bruteforce.Target.target_available", return_value=True
    )
    mock_target_gat_all_targets_from_db = mocker.patch(
        "mastko.cli.commands.bruteforce.Target.get_all_targets_from_db", return_value=["fake-target"]
    )
    mock_bruteforcer = mocker.patch("mastko.cli.commands.bruteforce.Bruteforcer")
    bruteforce_executer(args=mock_args)

    mock_target_available.assert_called_once()
    mock_target_gat_all_targets_from_db.assert_called_once()
    mock_bruteforcer.assert_called_once_with(
        targets=["fake-target"], region="us-west-2", instance_id="test-id", eip_ip="0.0.0.0"
    )
    mock_bruteforcer().run.assert_called_once_with(iterations=1)


def test_bruteforce_executer_exception(mocker):
    mock_args = Namespace(iterations=1, eip_ip="0.0.0.0", instance_id="test-id", region="us-west-2")
    mock_target_available = mocker.patch(
        "mastko.cli.commands.bruteforce.Target.target_available", return_value=False
    )

    with pytest.raises(Exception) as ex:
        bruteforce_executer(args=mock_args)

    mock_target_available.assert_called_once()
    assert ex.type is BruteforceCommandException
