# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Tests for the pull_request_disallow_fork function."""

# The tests in this file have to rely on many fixtures, need access to private function to test it

from unittest.mock import MagicMock

import pytest
from github.Repository import Repository

import repo_policy_compliance
from repo_policy_compliance.check import JobMetadata, Result, pull_request_disallow_fork


def test_execute_job_same_repository():
    """
    arrange: given a repository that is not a fork.
    act: when execute_job is called.
    assert: a pass report is returned.
    """
    # The github_client is injected
    report = pull_request_disallow_fork(  # pylint: disable=no-value-for-parameter
        job_metadata=JobMetadata(
            repository_name="test_repository_disallow_fork",
            fork_or_branch_repository_name="test_repository_disallow_fork",
            branch_name="test/branchname",
            commit_sha="test_commit_sha",
        )
    )

    assert report.result == Result.PASS


@pytest.mark.parametrize(
    "is_collaborator",
    [
        pytest.param(False, id="Not a collaborator"),
        pytest.param(True, id="Collaborator"),
    ],
)
def test_pull_request_disallow_fork_collaborator_status(
    is_collaborator: bool,
    monkeypatch: pytest.MonkeyPatch,
    forked_github_repository: Repository,
    github_repository: Repository,
):
    """
    arrange: given a repository that is not a fork.
    act: when pull_request_disallow_fork is called.
    assert: a pass report is returned.
    """
    monkeypatch.setattr(
        repo_policy_compliance.check,
        "_check_fork_collaborator",
        MagicMock(return_value=is_collaborator),
    )
    # The github_client is injected
    report = pull_request_disallow_fork(  # pylint: disable=no-value-for-parameter
        job_metadata=JobMetadata(
            repository_name=github_repository.full_name,
            fork_or_branch_repository_name=forked_github_repository.full_name,
            branch_name="test/branchname",
            commit_sha="test_commit_sha",
        )
    )

    assert report.result == Result.PASS
