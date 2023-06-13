from mastko.cli.parser import get_parser
from mastko.version import __version__


def test_get_parser(mocker):
    mock_argparse = mocker.patch("mastko.cli.parser.ArgumentParser")
    mock_add_subparsers = mock_argparse.return_value.add_subparsers
    mock_add_subparsers.return_value = mocker.MagicMock()

    mock_bruteforce_parser = mocker.patch("mastko.cli.parser.bruteforce_parser")
    mock_validate_targets_parser = mocker.patch("mastko.cli.parser.validate_targets_parser")

    mock_add_argument = mock_argparse.return_value.add_argument
    mock_parse_args = mock_argparse.return_value.parse_args

    expected_parser = get_parser()

    mock_argparse.assert_called_once_with(prog="mastko")
    mock_add_subparsers.assert_called_once_with(
        description="Please select a subcommand. For more information run `mastko {sub-command} --help`.",
        help="sub-commands:",
        dest="command",
    )

    mock_bruteforce_parser.assert_called_once_with(mock_add_subparsers.return_value)
    mock_validate_targets_parser.assert_called_once_with(mock_add_subparsers.return_value)

    mock_add_argument.assert_called_once_with(
        "--version", help="print out cli version", action="version", version=f"v{__version__}"
    )
    mock_parse_args.assert_called_once_with(args=None if mocker.ANY else ["--help"])

    assert expected_parser == mock_argparse.return_value
