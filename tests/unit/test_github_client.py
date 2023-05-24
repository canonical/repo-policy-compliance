# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Tests for the github_client function."""

from unittest.mock import MagicMock

import pytest
from github import Github, GithubException, RateLimitExceededException

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

    with pytest.raises(GithubClientError) as error:
        # The github_client is injected
        target_branch_protection(  # pylint: disable=no-value-for-parameter
            GITHUB_REPOSITORY_NAME, GITHUB_BRANCH_NAME
        )
    assert expected_message in str(error.value)
