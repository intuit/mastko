from mastko.version import __version__


def test_version():
    assert type(__version__) is str
