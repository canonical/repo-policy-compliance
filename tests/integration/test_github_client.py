# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Tests for the github_client module."""

import typing

import pytest

from repo_policy_compliance.check import target_branch_protection
from repo_policy_compliance.exceptions import ConfigurationError, GithubClientError
from repo_policy_compliance.github_client import GITHUB_TOKEN_ENV_NAME

from .. import assert_


@pytest.mark.parametrize(
    "github_token_value, exception_context, exception_message",
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
    exception_context: typing.ContextManager,
    exception_message: str,
    github_repository_name: str,
    monkeypatch: pytest.MonkeyPatch,
):
    """
    arrange: A github repository name and a missing or invalid github token.
    act: when the github client is injected to target_branch_protection.
    assert: An expected error is raised with a specific error message.
    """
    monkeypatch.setenv(GITHUB_TOKEN_ENV_NAME, str(github_token_value))
    with exception_context as error:
        # The github_client is injected
        target_branch_protection(  # pylint: disable=no-value-for-parameter
            repository_name=github_repository_name,
            branch_name="arbitrary",
            source_repository_name="arbitrary",
        )
    assert_.substrings_in_string([GITHUB_TOKEN_ENV_NAME, exception_message], str(error.value))
