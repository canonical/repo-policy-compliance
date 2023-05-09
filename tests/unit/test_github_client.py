# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Tests for the github_client function."""
from unittest.mock import MagicMock

import pytest
from github import GithubException, RateLimitExceededException

from repo_policy_compliance import target_branch_protection
from repo_policy_compliance.exceptions import GithubClientError

GITHUB_REPOSITORY_NAME = "test/repository"
GITHUB_BRANCH_NAME = "arbitrary"


@pytest.mark.parametrize(
    "raised_exception, expected_message",
    [
        pytest.param(
            RateLimitExceededException("", "", {}),
            "Rate Limit Exceeded error",
            id="github_client rate limit error",
        ),
        pytest.param(
            GithubException("", "", {}), "encountered an error", id="git_client other error"
        ),
    ],
)
def test_github_error(
    raised_exception: GithubException,
    expected_message: str,
):
    """
    arrange: A github repository name and a github_client method that raises exception.
    act: when target_branch_protection method is called.
    assert: An expected error is raised with specific error message.
    """
    github_client = MagicMock()
    github_client.get_repo.side_effect = raised_exception

    with pytest.raises(GithubClientError) as error:
        # target_branch_protection is behind a decorator that injects github_client if not provided
        target_branch_protection(
            github_client, GITHUB_REPOSITORY_NAME, GITHUB_BRANCH_NAME  # type: ignore[call-arg]
        )
    assert expected_message in str(error.value)


def test_github_client_kwargs():
    """
    arrange: A github repository name and a mocked github_client.
    act: when target_branch_protection method is called using github_client named parameter.
    assert: the mocked github client is used.
    """
    github_client = MagicMock()

    target_branch_protection(
        repository_name=GITHUB_REPOSITORY_NAME,
        branch_name=GITHUB_BRANCH_NAME,
        github_client=github_client,  # type: ignore[call-arg]
    )
    github_client.get_repo.assert_called_once()
