# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Tests for the github_client function."""

from unittest.mock import MagicMock

import pytest
from github import BadCredentialsException, Github, GithubException, RateLimitExceededException
from github.Repository import Repository

import repo_policy_compliance.github_client
from repo_policy_compliance.check import Result, target_branch_protection
from repo_policy_compliance.exceptions import ConfigurationError, GithubClientError

GITHUB_REPOSITORY_NAME = "test/repository"
GITHUB_BRANCH_NAME = "arbitrary"


@pytest.mark.parametrize(
    "raised_exception, expected_message",
    [
        pytest.param(
            BadCredentialsException(0, "", {}), "Something went wrong", id="bad credentials error"
        ),
        pytest.param(
            RateLimitExceededException(0, "", {}),
            "Please wait before retrying",
            id="github_client rate limit error",
        ),
        pytest.param(
            GithubException(0, "", {}), "Something went wrong", id="git_client other error"
        ),
    ],
)
def test_github_error(
    raised_exception: GithubException, expected_message: str, monkeypatch: pytest.MonkeyPatch
):
    """
    arrange: A github repository name and a github_client method that raises exception.
    act: when target_branch_protection method is called.
    assert: An expected error is raised with specific error message.
    """
    github_client = MagicMock(spec=Github)
    github_client.get_repo.side_effect = raised_exception

    monkeypatch.setattr(
        "repo_policy_compliance.github_client.Github", lambda *_args, **_kwargs: github_client
    )
    monkeypatch.setattr(
        repo_policy_compliance.github_client, "get", lambda *_args, **_kwargs: github_client
    )

    # The github_client is injected
    report = target_branch_protection(  # pylint: disable=no-value-for-parameter
        GITHUB_REPOSITORY_NAME, GITHUB_BRANCH_NAME, GITHUB_REPOSITORY_NAME
    )
    assert report.result == Result.ERROR
    assert expected_message in str(report.reason)


def test_get_collaborator_permission_error():
    """
    arrange: Given a mocked get_collaborator_permission function that returns invalid value.
    act: when get_collaborator_permission is called.
    assert: GithubClientError is raised.
    """
    mock_repository = MagicMock(spec=Repository)
    mock_repository.get_collaborator_permission.return_value = "invalid"

    with pytest.raises(GithubClientError) as error:
        # The github_client is injected
        repo_policy_compliance.github_client.get_collaborator_permission(
            mock_repository, "test_user"
        )
    assert "Invalid collaborator permission" in str(error.value)


@pytest.mark.parametrize(
    "github_app_id, github_app_installation_id, github_app_private_key, github_token, "
    "expected_message",
    [
        pytest.param(
            "123",
            "456",
            "private",
            "github_token",
            repo_policy_compliance.github_client.PROVIDED_GITHUB_TOKEN_AND_APP_CONFIG_ERR_MSG,
            id="github app config and github token",
        ),
        pytest.param(
            None,
            None,
            None,
            None,
            repo_policy_compliance.github_client.MISSING_GITHUB_CONFIG_ERR_MSG,
            id="no github app config or github token",
        ),
        pytest.param(
            "eda",
            "no int",
            "private",
            None,
            "Invalid github app installation id",
            id="invalid github app installation id",
        ),
        pytest.param(
            "eda",
            "123",
            None,
            None,
            repo_policy_compliance.github_client.NOT_ALL_GITHUB_APP_CONFIG_ERR_MSG,
            id="not all github app config provided",
        ),
    ],
)  # we use a lot of arguments but it seems not worth to introduce a capsulating object for this
def test_get_client_configuration_error(  # pylint: disable=too-many-arguments
    github_app_id: str,
    github_app_installation_id: str,
    github_app_private_key: str,
    github_token: str,
    expected_message: str,
    monkeypatch: pytest.MonkeyPatch,
):
    """
    arrange: Given a mocked get_client_configuration function that returns invalid value.
    act: when get_client_configuration is called.
    assert: GithubClientError is raised.
    """
    if github_app_id:
        monkeypatch.setenv("GITHUB_APP_ID", github_app_id)
    if github_app_installation_id:
        monkeypatch.setenv("GITHUB_APP_INSTALLATION_ID", github_app_installation_id)
    if github_app_private_key:
        monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY", github_app_private_key)
    if github_token:
        monkeypatch.setenv("GITHUB_TOKEN", github_token)

    with pytest.raises(ConfigurationError) as error:
        # The github_client is injected
        repo_policy_compliance.github_client.get()
    assert expected_message in str(error.value)
