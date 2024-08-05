# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Module for GitHub client."""
import enum
import functools
import logging
import os
from enum import Enum
from typing import Callable, Concatenate, Literal, ParamSpec, TypeVar, cast
from urllib import parse

from github import BadCredentialsException, Github, GithubException, RateLimitExceededException
from github.Auth import AppAuth, AppInstallationAuth, Auth, Token
from github.Branch import Branch
from github.Repository import Repository
from urllib3 import Retry

from repo_policy_compliance.exceptions import (
    ConfigurationError,
    GithubApiNotFoundError,
    GithubClientError,
    RetryableGithubClientError,
)

P = ParamSpec("P")
R = TypeVar("R")

# Bandit thinks this constant is the real Github token
GITHUB_TOKEN_ENV_NAME = "GITHUB_TOKEN"  # nosec
GITHUB_APP_ID_ENV_NAME = "GITHUB_APP_ID"
GITHUB_APP_INSTALLATION_ID_ENV_NAME = "GITHUB_APP_INSTALLATION_ID"
GITHUB_APP_PRIVATE_KEY_ENV_NAME = "GITHUB_APP_PRIVATE_KEY"

MISSING_GITHUB_CONFIG_ERR_MSG = (
    f"Either the {GITHUB_TOKEN_ENV_NAME} or not all of {GITHUB_APP_ID_ENV_NAME},"
    f" {GITHUB_APP_INSTALLATION_ID_ENV_NAME}, {GITHUB_APP_PRIVATE_KEY_ENV_NAME} "
    f"environment variables were provided or are empty, "
    "the variables are needed for interactions with GitHub, "
)
NOT_ALL_GITHUB_APP_CONFIG_ERR_MSG = (
    f"Not all of {GITHUB_APP_ID_ENV_NAME}, {GITHUB_APP_INSTALLATION_ID_ENV_NAME},"
    f" {GITHUB_APP_PRIVATE_KEY_ENV_NAME} environment variables were provided, "
)
# the following is no hardcoded password
PROVIDED_GITHUB_TOKEN_AND_APP_CONFIG_ERR_MSG = (  # nosec
    "Provided github app config and github token, only one of them should be provided, "
)


class _AuthMode(Enum):
    """Enum to represent the auth mode to use.

    Attributes:
        TOKEN: Using GitHub token auth.
        APP: Using GitHub App auth.
    """

    TOKEN = enum.auto()
    APP = enum.auto()


def get() -> Github:
    """Get a GitHub client.

    Returns:
        A GitHub client that is configured with a token or GitHub app from the environment.

    Raises:
        ConfigurationError: If the GitHub auth config is not valid.
    """  # noqa: DCO051 error raised is useful to know for the user of the public interface
    auth = _get_auth()

    # Only retry on 5xx and only retry once after 20 secs
    retry_config = Retry(
        total=1,
        backoff_factor=20,
        status_forcelist=list(range(500, 600)),
        respect_retry_after_header=False,
        raise_on_status=False,
        raise_on_redirect=False,
    )
    return Github(auth=auth, retry=retry_config)


def _get_auth() -> Auth:
    """Get a GitHub auth object.

    Returns:
        A GitHub auth object that is configured with a token from the environment.
    """
    github_token = os.getenv(GITHUB_TOKEN_ENV_NAME) or os.getenv(f"FLASK_{GITHUB_TOKEN_ENV_NAME}")
    github_app_id = os.getenv(GITHUB_APP_ID_ENV_NAME) or os.getenv(
        f"FLASK_{GITHUB_APP_ID_ENV_NAME}"
    )
    github_app_installation_id_str = os.getenv(GITHUB_APP_INSTALLATION_ID_ENV_NAME) or os.getenv(
        f"FLASK_{GITHUB_APP_INSTALLATION_ID_ENV_NAME}"
    )
    github_app_private_key = os.getenv(GITHUB_APP_PRIVATE_KEY_ENV_NAME) or os.getenv(
        f"FLASK_{GITHUB_APP_PRIVATE_KEY_ENV_NAME}"
    )

    auth_mode = _get_auth_mode(
        github_token=github_token,
        github_app_id=github_app_id,
        github_app_installation_id_str=github_app_installation_id_str,
        github_app_private_key=github_app_private_key,
    )

    auth: Auth
    if auth_mode == _AuthMode.APP:
        auth = _get_github_app_installation_auth(
            github_app_id=cast(str, github_app_id),
            github_app_installation_id_str=cast(str, github_app_installation_id_str),
            github_app_private_key=cast(str, github_app_private_key),
        )
    else:
        assert github_token is not None  # nosec
        auth = Token(github_token)

    return auth


def _get_auth_mode(
    github_token: str | None,
    github_app_id: str | None,
    github_app_installation_id_str: str | None,
    github_app_private_key: str | None,
) -> _AuthMode:
    """Get the auth mode to use.

    Args:
        github_token: The GitHub token.
        github_app_id: The GitHub App ID or Client ID.
        github_app_installation_id_str: The GitHub App Installation ID as a string.
        github_app_private_key: The GitHub App private key.

    Raises:
        ConfigurationError: If the configuration is not valid, e.g. if both a token and app config
            are provided.

    Returns:
        The auth mode to use.
    """
    if not github_token and not (
        github_app_id or github_app_installation_id_str or github_app_private_key
    ):
        raise ConfigurationError(
            f"{MISSING_GITHUB_CONFIG_ERR_MSG}"
            f"got: {github_token!r}, {github_app_id!r},"
            f" {github_app_installation_id_str!r}, {github_app_private_key!r}"
        )
    if github_token and (
        github_app_id or github_app_installation_id_str or github_app_private_key
    ):
        raise ConfigurationError(
            f"{PROVIDED_GITHUB_TOKEN_AND_APP_CONFIG_ERR_MSG}"
            f"got: {github_token!r}, {github_app_id!r}, {github_app_installation_id_str!r},"
            f" {github_app_private_key!r}"
        )

    if github_app_id or github_app_installation_id_str or github_app_private_key:
        if not (github_app_id and github_app_installation_id_str and github_app_private_key):
            raise ConfigurationError(
                f"{NOT_ALL_GITHUB_APP_CONFIG_ERR_MSG}"
                f"got: {github_app_id!r}, {github_app_installation_id_str!r}, "
                f"{github_app_private_key!r}"
            )

    if github_token:
        return _AuthMode.TOKEN
    return _AuthMode.APP


def _get_github_app_installation_auth(
    github_app_id: str, github_app_installation_id_str: str, github_app_private_key: str
) -> AppInstallationAuth:
    """Get a GitHub App Installation Auth object.

    Args:
        github_app_id: The GitHub App ID or Client ID.
        github_app_installation_id_str: The GitHub App Installation ID as a string.
        github_app_private_key: The GitHub App private key.

    Returns:
        A GitHub App Installation Auth object.

    Raises:
        ConfigurationError: If the GitHub App Installation Auth config is not valid.
    """
    try:
        github_app_installation_id = int(github_app_installation_id_str)
    except ValueError as exc:
        raise ConfigurationError(
            f"Invalid github app installation id {github_app_installation_id_str!r}, "
            f"it should be an integer."
        ) from exc
    app_auth = AppAuth(app_id=github_app_id, private_key=github_app_private_key)
    return AppInstallationAuth(app_auth=app_auth, installation_id=github_app_installation_id)


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
            GithubApiNotFoundError: If the GitHub API returns a 404.
            GithubClientError: If the Github client encountered an error.
            RetryableGithubClientError: If the error raised is retryable on the users's end.

        Returns:
            The return value after calling the wrapped function with the injected GitHub client.

        """
        github_client = get()

        try:
            return func(github_client, *args, **kwargs)
        except BadCredentialsException as exc:
            logging.error("Github client credentials error: %s", exc, exc_info=exc)
            raise GithubClientError(
                "The github client returned a Bad Credential error, "
                f"please ensure {GITHUB_TOKEN_ENV_NAME} is set with a valid value."
            ) from exc
        except RateLimitExceededException as exc:
            logging.error("Github rate limit exceeded error: %s", exc, exc_info=exc)
            raise RetryableGithubClientError(
                "The github client is returning a Rate Limit Exceeded error, "
                "please wait before retrying."
            ) from exc
        except GithubException as exc:
            if exc.status == 404:
                raise GithubApiNotFoundError(api_message=exc.data.get("message")) from exc
            logging.error("Github client error: %s", exc, exc_info=exc)
            raise GithubClientError("The github client encountered an error.") from exc

    return wrapper


def get_collaborators(
    affiliation: Literal["outside", "all"],
    permission: Literal["triage", "maintain", "admin", "pull", "push"],
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
    query: dict[str, str] = {
        **default_query,
        "permission": permission,
        "affiliation": affiliation,
        "per_page": "100",
    }

    # mypy thinks the attribute doesn't exist when it actually does exist
    # need to use requester to send a raw API request
    # pylint: disable=protected-access
    (_, outside_collaborators) = repository._requester.requestJsonAndCheck(  # type: ignore
        "GET", f"{collaborators_url}?{parse.urlencode(query)}"
    )
    # pylint: enable=protected-access

    return outside_collaborators


def get_branch(github_client: Github, repository_name: str, branch_name: str) -> Branch:
    """Get the branch for the check.

    Args:
        github_client: The client to be used for GitHub API interactions.
        repository_name: The name of the repository to run the check on.
        branch_name: The name of the branch to check.

    Returns:
        The requested branch.
    """
    repository = github_client.get_repo(repository_name)
    return repository.get_branch(branch_name)


def get_collaborator_permission(
    repository: Repository, username: str
) -> Literal["admin", "write", "read", "none"]:
    """Get user permission for a given repository.

    Args:
        repository: The repository to get collaborators for.
        username: The github login to check for permission.

    Raises:
        GithubClientError: if an invalid user permission is returned from the API call.

    Returns:
        The collaborator permission.
    """
    user_permission = repository.get_collaborator_permission(username)
    if user_permission not in ("admin", "write", "read", "none"):
        raise GithubClientError(
            f"Invalid collaborator permission {user_permission} received, "
            'expected one of "admin", "write", "read", "none"'
        )
    return cast(Literal["admin", "write", "read", "none"], user_permission)
