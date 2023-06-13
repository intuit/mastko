from mastko.mastko import main


def test_main(mocker):
    mock_get_parser = mocker.patch("mastko.mastko.get_parser")
    mock_cmd_executer = mocker.patch("mastko.mastko.cmd_executer")

    main()

    mock_get_parser.assert_called_once()
    mock_cmd_executer.assert_called_once_with(mock_get_parser.return_value)


def test_main_raise_exception(mocker):
    mock_get_parser = mocker.patch("mastko.mastko.get_parser")
    mock_cmd_executer = mocker.patch("mastko.mastko.cmd_executer", side_effect=Exception("fake-exception"))
    mock_exit = mock_get_parser.return_value.exit = mocker.MagicMock()

    main()

    mock_get_parser.assert_called_once()
    mock_cmd_executer.assert_called_once_with(mock_get_parser.return_value)
    mock_exit.assert_called_once_with(1, "fake-exception")
