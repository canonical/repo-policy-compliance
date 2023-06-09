# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Module for GitHub client."""

import functools
import os
from typing import Callable, Concatenate, Literal, ParamSpec, TypeVar
from urllib import parse

from github import BadCredentialsException, Github, GithubException, RateLimitExceededException
from github.Auth import Token
from github.Repository import Repository

from .exceptions import GithubClientError, InputError

P = ParamSpec("P")
R = TypeVar("R")

# Bandit thinks this constant is the real Github token
GITHUB_TOKEN_ENV_NAME = "GITHUB_TOKEN"  # nosec


def get() -> Github:
    """Get a GitHub client.

    Returns:
        A GitHub client that is configured with a token from the environment.

    Raises:
        InputError: If the GitHub token environment variable is not provided or empty.
    """
    github_token = os.getenv(GITHUB_TOKEN_ENV_NAME)
    if not github_token:
        raise InputError(
            f"The {GITHUB_TOKEN_ENV_NAME} environment variable was not provided or empty, "
            f"it is needed for interactions with GitHub, got: {github_token!r}"
        )
    return Github(auth=Token(github_token))


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
            GithubClientError: If the Github client encountered an error.

        Returns:
            The return value after calling the wrapped function with the injected GitHub client.

        """
        github_client = get()

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


def get_collaborators(
    affiliation: Literal["outside", "all"],
    permission: Literal["triage", "maintain", "admin", "pull"],
    repository: Repository,
) -> list[dict]:
    """Get collaborators with a given affiliation and permission.

    Args:
        affiliation: The relationship the collaborator has with the repository.
        permission: The permission the collaborator has on the repository.
        repository: The repository to get collaborators for.

    Returns:
        The logins of collaborators that match the criteria.
    """
    collaborators_url = repository.collaborators_url.replace("{/collaborator}", "")
    default_query = dict(parse.parse_qsl(parse.urlparse(collaborators_url).query))
    query: dict[str, str] = {**default_query, "permission": permission, "affiliation": affiliation}

    # mypy thinks the attribute doesn't exist when it actually does exist
    # need to use requester to send a raw API request
    # pylint: disable=protected-access
    (_, outside_collaborators) = repository._requester.requestJsonAndCheck(  # type: ignore
        "GET", f"{collaborators_url}?{parse.urlencode(query)}"
    )
    # pylint: enable=protected-access

    return outside_collaborators
