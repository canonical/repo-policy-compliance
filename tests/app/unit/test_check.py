# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Tests for the check module."""
import secrets
from unittest.mock import MagicMock

import pytest
from github import Github, GithubException
from github.Branch import Branch
from github.Repository import Repository

import repo_policy_compliance
from repo_policy_compliance.check import Report, Result
from repo_policy_compliance.exceptions import GithubClientError

# internal functions are being accessed for testing.
# pylint: disable=protected-access


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


def test_target_branch_protection_get_protections_raises_non_404_error(
    monkeypatch: pytest.MonkeyPatch,
):
    """
    arrange: that branch.get_protection raises an error (non 404 status code)
    act: call target_branch_protection
    assert: a report with error result is returned.
    """
    branch_mock = MagicMock(spec=Branch)
    branch_mock.get_protection = MagicMock(side_effect=GithubException(status=500))
    monkeypatch.setattr(
        repo_policy_compliance.check, "get_branch", lambda *_args, **_kwargs: branch_mock
    )
    monkeypatch.setattr(
        repo_policy_compliance.check,
        "branch_protected",
        lambda *_args, **_kwargs: Report(Result.PASS, "Branch is protected"),
    )

    repo_mock = MagicMock(spec=Repository)
    repo_mock.default_branch = secrets.token_hex(16)
    github_client_mock = MagicMock(spec=Github)
    github_client_mock.get_repo.return_value = repo_mock
    monkeypatch.setattr(
        "repo_policy_compliance.github_client.get", lambda *_args, **_kwargs: github_client_mock
    )

    # github_client is injected, therefore we don't need to pass it.
    report = repo_policy_compliance.check.target_branch_protection(  # pylint: disable=no-value-for-parameter
        repository_name="this/test",
        branch_name=secrets.token_hex(16),
        source_repository_name="other/test",
    )

    assert report.result == Result.ERROR
    assert "Something went wrong" in str(report.reason)


@pytest.mark.parametrize(
    "rulesets, expected_result, expected_reason_substring",
    [
        pytest.param(
            [],
            Result.FAIL,
            "branch protection not enabled via rulesets",
            id="no rulesets",
        ),
        pytest.param(
            [
                {
                    "id": 1,
                    "rules": [{"type": "deletion"}],
                }
            ],
            Result.FAIL,
            "pull request reviews are not required in rulesets",
            id="no pull_request rule",
        ),
        pytest.param(
            [
                {
                    "id": 1,
                    "rules": [
                        {
                            "type": "pull_request",
                            "parameters": {
                                "bypass_pull_request_allowances": {
                                    "users": [{"user_id": 1}],
                                }
                            },
                        }
                    ],
                }
            ],
            Result.FAIL,
            "pull request reviews can be bypassed",
            id="pull_request rule with bypass allowances",
        ),
        pytest.param(
            [
                {
                    "id": 1,
                    "rules": [
                        {
                            "type": "pull_request",
                        }
                    ],
                }
            ],
            Result.PASS,
            None,
            id="pull_request rule without bypass allowances",
        ),
    ],
)
def test__check_rulesets_for_pull_request_reviews(
    monkeypatch: pytest.MonkeyPatch,
    rulesets: list,
    expected_result: Result,
    expected_reason_substring: str | None,
):
    """
    arrange: given a repository with rulesets.
    act: when _check_rulesets_for_pull_request_reviews is called.
    assert: the expected result is returned.
    """
    mock_repository = MagicMock(spec=Repository)
    monkeypatch.setattr(
        repo_policy_compliance.check,
        "get_rulesets_for_branch",
        lambda *_args, **_kwargs: rulesets,
    )

    report = repo_policy_compliance.check._check_rulesets_for_pull_request_reviews(
        mock_repository, "main"
    )

    assert report.result == expected_result
    if expected_reason_substring:
        assert expected_reason_substring in str(report.reason)
    else:
        assert report.reason is None
