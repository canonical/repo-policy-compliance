# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Tests for the github_client module."""

import pytest

from repo_policy_compliance.check import Result, target_branch_protection
from repo_policy_compliance.github_client import GITHUB_TOKEN_ENV_NAME

from .. import assert_


@pytest.mark.parametrize(
    "github_token_value, fail_reason",
    [
        pytest.param(
            "",
            "Something went wrong while configuring repository compliance policy check.",
            id="github_token empty",
        ),
        pytest.param(
            None,
            "Something went wrong while checking repository compliance policy.",
            id="github_token none",
        ),
        pytest.param(
            "abcd",
            "Something went wrong while checking repository compliance policy.",
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

    assert report.result == Result.ERROR
    assert fail_reason in str(report.reason)
