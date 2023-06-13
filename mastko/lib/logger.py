import logging
import os
from typing import Any, MutableMapping, Tuple

__handler = logging.StreamHandler()


def set_process_name(process_name: str) -> None:
    __handler.setFormatter(logging.Formatter(f"%(levelname)s {process_name} %(name)s %(message)s"))


set_process_name("mastko")


class MemoryLoggingAdapter(logging.LoggerAdapter):
    def process(self, msg: Any, kwargs: MutableMapping[str, Any]) -> Tuple[Any, MutableMapping[str, Any]]:
        import psutil  # type: ignore

        process = psutil.Process(os.getpid())
        return (f"{msg} [{process.memory_info().rss / 1024 ** 2} MB used]", kwargs)


def get_logger(name: str) -> logging.Logger:
    """Get the pre-configured logger object

    Returns:
        logging.Logger: pre-configured logging object
    """

    # configure the logger
    logger = logging.getLogger(name)

    if not logger.hasHandlers():
        logger.addHandler(__handler)

    if os.environ.get("DEBUG"):
        logger.level = logging.DEBUG
        # mypy is uppity about this interface.
        return MemoryLoggingAdapter(logger, {})  # type: ignore

    logger.level = logging.INFO
    return logger
