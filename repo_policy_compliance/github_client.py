# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Module for GitHub client."""

import functools
import os
from typing import Callable, Concatenate, ParamSpec, TypeVar, cast

from github import BadCredentialsException, Github, GithubException, RateLimitExceededException

from .exceptions import GithubClientError, InputError

P = ParamSpec("P")
R = TypeVar("R")

# Bandit thinks this constant is the real Github token
GITHUB_TOKEN_ENV_NAME = "GITHUB_TOKEN"  # nosec


def inject(func: Callable[Concatenate[Github, P], R]) -> Callable[P, R]:
    """Injects a GitHub client as the first argument to a function.

    Args:
        func: The function that requires a GitHub client.

    Returns:
        The function where the GitHub client has been injected as the first argument.
    """

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        """Replace function.

        Args:
            args: The positional arguments passed to the method, github_client is prepended when
                calling the wrapped method
            kwargs: The keywords arguments passed to the method

        Raises:
            InputError: If the GitHub token environment variable is not provided or empty.
            GithubClientError: If the Github client encountered an error.

        Returns:
            The return value after calling the wrapped function with the injected GitHub client.

        """
        if len(args) < 3 and "github_client" not in kwargs:
            github_token = os.getenv(GITHUB_TOKEN_ENV_NAME)
            if not github_token:
                raise InputError(
                    f"The {GITHUB_TOKEN_ENV_NAME} environment variable was not provided or empty, "
                    f"it is needed for interactions with GitHub, got: {GITHUB_TOKEN_ENV_NAME!r}"
                )
            github_client: Github = Github(login_or_token=github_token)
        elif len(args) == 3:
            github_client = cast(Github, args[0])
            # We need to remove the first arg as we will pass it explicitly to func
            args = args[1:]  # type: ignore[assignment]
        else:
            github_client = cast(Github, kwargs["github_client"])
            kwargs.pop("github_client", None)

        try:
            return func(github_client, *args, **kwargs)
        except BadCredentialsException as exc:
            raise GithubClientError(
                f"The github client returned a Bad Credential error, "
                f"please ensure {GITHUB_TOKEN_ENV_NAME} is set with a valid value."
            ) from exc
        except RateLimitExceededException as exc:
            raise GithubClientError(
                "The github client is returning an Rate Limit Exceeded error, "
                "please wait before retrying."
            ) from exc
        except GithubException as exc:
            raise GithubClientError("The github client encountered an error.") from exc

    return wrapper
