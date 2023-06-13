import os
from mastko.lib.logger import get_logger


def test_debug_setting():
    try:
        os.environ["DEBUG"] = "true"
        logger = get_logger("test_logger")
        assert "DEBUG" in str(logger)
    finally:
        os.environ.pop("DEBUG")
