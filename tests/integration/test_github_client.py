# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Tests for the github_client module."""

import pytest

from repo_policy_compliance.check import Result, target_branch_protection
from repo_policy_compliance.exceptions import ConfigurationError, GithubClientError
from repo_policy_compliance.github_client import GITHUB_TOKEN_ENV_NAME

from .. import assert_


@pytest.mark.parametrize(
    "github_token_value, fail_reason",
    [
        pytest.param(
            "", pytest.raises(ConfigurationError), "was not provided", id="github_token empty"
        ),
        pytest.param(
            None, pytest.raises(GithubClientError), "Bad Credential error", id="github_token none"
        ),
        pytest.param(
            "abcd",
            pytest.raises(GithubClientError),
            "Bad Credential error",
            id="github_token wrong",
        ),
    ],
)
def test_github_token(
    github_token_value: str | None,
    fail_reason: str,
    github_repository_name: str,
    monkeypatch: pytest.MonkeyPatch,
):
    """
    arrange: A github repository name and a missing or invalid github token.
    act: when the github client is injected to target_branch_protection.
    assert: An expected error is raised with a specific error message.
    """
    monkeypatch.setenv(GITHUB_TOKEN_ENV_NAME, str(github_token_value))
    # The github_client is injected
    report = target_branch_protection(  # pylint: disable=no-value-for-parameter
        repository_name=github_repository_name,
        branch_name="arbitrary",
        source_repository_name="arbitrary",
    )

    assert report.result == Result.FAIL
    assert_.substrings_in_string([GITHUB_TOKEN_ENV_NAME, fail_reason], str(report.reason))
