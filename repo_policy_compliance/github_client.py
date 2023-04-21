# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Module for GitHub client."""

import functools
import os
from typing import Callable, Concatenate, ParamSpec, TypeVar

from github import Github

from .exceptions import InputError

P = ParamSpec("P")
R = TypeVar("R")


GITHUB_TOKEN_ENV_NAME = "GITHUB_TOKEN"


def inject(func: Callable[Concatenate[Github, P], R]) -> Callable[P, R]:
    """Injects a GitHub client as the first argument to a function.

    Args:
        func: The function that requires a GitHub client.

    Returns:
        The function where the GitHub client has been injected as the first argument.
    """

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        """Replacement function.

        Raises:
            InputError: If the GitHub token environment variable is not provided or empty.

        Returns;
            The return value after calling the wrapped function with the injected GitHub client.

        """
        github_token = os.getenv(GITHUB_TOKEN_ENV_NAME)
        if not github_token:
            raise InputError(
                f"The {GITHUB_TOKEN_ENV_NAME} environment variable was not provided or empty, it "
                f"is needed for interactions with GitHub, got: {GITHUB_TOKEN_ENV_NAME!r}"
            )
        github_client = Github(login_or_token=github_token)

        return func(github_client, *args, **kwargs)

    return wrapper
