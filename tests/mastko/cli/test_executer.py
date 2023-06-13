import pytest

from mastko.cli.executer import cmd_executer


def test_cmd_executer_bruteforce(mocker):
    mock_parser = mocker.MagicMock()
    mock_parser.parse_args.return_value = mocker.MagicMock(command="bruteforce")
    mock_bruteforce_executer = mocker.patch("mastko.cli.executer.bruteforce_executer")
    cmd_executer(mock_parser)

    mock_parser.parse_args.assert_called_once()
    mock_bruteforce_executer.assert_called_once_with(mock_parser.parse_args.return_value)


def test_cmd_executer_validate_targets(mocker):
    mock_parser = mocker.MagicMock()
    mock_parser.parse_args.return_value = mocker.MagicMock(command="validate_targets")
    mock_validate_targets_executer = mocker.patch("mastko.cli.executer.validate_targets_executer")
    cmd_executer(mock_parser)

    mock_parser.parse_args.assert_called_once()
    mock_validate_targets_executer.assert_called_once_with(mock_parser.parse_args.return_value)


def test_cmd_executer_raise_exception(mocker):
    mock_parser = mocker.MagicMock()
    mock_parser.parse_args.side_effect = Exception("fake-exception")
    mock_parser.exit = mocker.MagicMock()

    mock_bruteforce_executer = mocker.patch("mastko.cli.executer.bruteforce_executer")
    mock_validate_targets_executer = mocker.patch("mastko.cli.executer.validate_targets_executer")

    cmd_executer(mock_parser)

    mock_parser.exit.assert_called_once_with(1)
    mock_bruteforce_executer.assert_not_called()
    mock_validate_targets_executer.assert_not_called()
