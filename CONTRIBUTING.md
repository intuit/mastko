# Contributing

## Reporting Issues

Please use GitHub issues to report any conerns about the code.

## Contributions

All code contributions should be submitted through GitHub pull requests.

## Developing Locally

```shell
$ git clone path_to_git
$ cd mastko 
$ sh init.sh
```

This will create a python virtual environment using `venv`, install dependencies and runs `tox`.

## Code Quality

`tox` is currently configured to run `black`, `flake8`, `isort`, `mypy`, `pytest-cov`, and `pytest` in addition to the unit tests by default. You can run all these tools by running the tox command:

```
tox
```

Run only `mypy` command as specified in tox.ini file:

```
tox run -e mypy
```

Run only `flake8` command as specified in tox.ini file:

```
tox run -e flake8
```

## Code Formatting

Use the `black` and `isort` auto-formatter with line-length set to 160 to ensure consistent code formatting. This will run only `black` and `isort`.

```
tox run -e autoformat
```

Run only `isort` command as specified in tox.ini file:

```
tox run -e isort
```

Run only `black` command as specified in tox.ini file:

```
tox run -e black
```

## Code Coverage and Unit Tests

We are using the `pytest` and `pytest-cov` libraries for unit tests and code coverage analysis. Please add
sufficient code coverage for all new/modified functionality and verify that all tests are passing via `tox`.

To run all the unit tests and code coverage tool:

```
tox run -e py39
```

To run individual test files:

```
tox run -e py39 -- tests/stand/cli/test_get_args.py
```

To run individual test functions:

```
tox run -e py39 -- tests/stand/cli/test_get_args.py::test_getArgValue_withWrappedValue_shouldReturnValue
```

