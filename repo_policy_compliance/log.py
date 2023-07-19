# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Module for logging."""

import logging
import sys
from typing import Callable, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


def check(func: Callable[P, R]) -> Callable[P, R]:
    """Log before check and result of check.

    Args:
        func: The function that executes a check.

    Returns:
        The function where the check is logged before it starts and the results are logged.
    """
    check_name = func.__name__

    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        """Replace function.

        Args:
            args: The positional arguments passed to the method
            kwargs: The keywords arguments passed to the method

        Returns:
            The return value after calling the wrapped function.
        """
        logging.info("start check '%s'", check_name)
        result = func(*args, **kwargs)
        logging.info("check '%s' finished, result: %s", check_name, result)
        return result

    return wrapper


def setup() -> None:
    """Initialise logging for check execution."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(message)s")
    handler.setFormatter(formatter)

    # Setup local logging
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    # Setup urllib3 logging
    urllib3_logger = logging.getLogger("urllib3")
    urllib3_logger.setLevel(logging.DEBUG)
    urllib3_logger.addHandler(handler)
