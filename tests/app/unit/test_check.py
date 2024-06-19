# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Tests for the check module."""

# internal functions are being accessed for testing.
# pylint: disable=protected-access

from unittest.mock import MagicMock

import pytest
from github.Repository import Repository

import repo_policy_compliance
from repo_policy_compliance.check import Result
from repo_policy_compliance.exceptions import GithubClientError


def test_github_exceptions_to_fail_report():
    """
    arrange: given a function that raises a GithubClient error.
    act: when the function is called with github_exceptions_to_fail_report decorator.
    assert: a failed report with exception as reason is returned.
    """

    @repo_policy_compliance.check.github_exceptions_to_fail_report
    def github_client_error_raiser():
        """A mock function to raise github client error.

        Raises:
            GithubClientError: always.
        """
        raise GithubClientError("Exception message.")

    report = github_client_error_raiser()
    assert report.result == Result.ERROR
    assert "Something went wrong" in str(report.reason)


@pytest.mark.parametrize(
    "repository_name, source_repository_name, expected_user_permission, expected_result",
    [
        pytest.param(
            "repo-1/name-1",
            "user-1/name-1",
            "none",
            False,
            id="repo names don't match, owner none permission",
        ),
        pytest.param(
            "repo-1/name-1",
            "user-1/name-1",
            "read",
            False,
            id="repo names don't match, owner read permission",
        ),
        pytest.param(
            "repo-1/name-1",
            "user-1/name-1",
            "write",
            True,
            id="repo names don't match, owner write permissions",
        ),
        pytest.param(
            "repo-1/name-1",
            "user-1/name-1",
            "admin",
            True,
            id="repo names don't match, owner admin permissions",
        ),
    ],
)
def test__check_fork_collaborator(
    monkeypatch: pytest.MonkeyPatch,
    repository_name: str,
    source_repository_name: str,
    expected_user_permission: str,
    expected_result: bool,
):
    """
    arrange: given repository name, source repository name and push logins
    act: when repository name, source repository name and push logins are passed to
        _check_fork_collaborator
    assert: then the expected result is returned.
    """
    mocked_repository = MagicMock(spec=Repository)
    mocked_repository.full_name = repository_name
    monkeypatch.setattr(
        repo_policy_compliance.check,
        "get_collaborator_permission",
        lambda *_args, **_kwargs: expected_user_permission,
    )

    returned_result = repo_policy_compliance.check._check_fork_collaborator(
        repository=mocked_repository, fork_repository_name=source_repository_name
    )

    assert returned_result == expected_result
