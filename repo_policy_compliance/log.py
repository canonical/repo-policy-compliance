# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Module for logging."""

import logging
import sys
from typing import Callable, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


def call(func: Callable[P, R]) -> Callable[P, R]:
    """Log before func and result of func.

    Args:
        func: The function that executes a func.

    Returns:
        The function where the func is logged before it starts and the results are logged.
    """
    func_name = func.__name__

    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        """Replace function.

        Args:
            args: The positional arguments passed to the method
            kwargs: The keywords arguments passed to the method

        Returns:
            The return value after calling the wrapped function.
        """
        logging.info("start func '%s'", func_name)
        result = func(*args, **kwargs)
        logging.info("func '%s' finished, result: %s", func_name, result)
        return result

    return wrapper


def setup() -> None:
    """Initialise logging for check execution."""
    _setup_root_logger()
    _setup_urllib3_logger()


def _setup_root_logger() -> None:
    """Set up the root logger."""
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        # Setup logging handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(message)s")
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)

    root_logger.setLevel(logging.DEBUG)


def _setup_urllib3_logger() -> None:
    """Set up the urllib3 logger."""
    # urllib3 logger propagates logs to the root logger, no need to add a handler
    urllib_logger = logging.getLogger("urllib3")
    urllib_logger.setLevel(logging.DEBUG)
