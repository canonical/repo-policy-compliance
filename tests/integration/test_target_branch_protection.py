# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""Tests for the target_branch_protection function."""


import pytest
from github import Branch, Repository

from repo_policy_compliance import Result, target_branch_protection


@pytest.mark.usefixtures("git_branch")
def test_fail(
    github_branch: Branch,
    github_repository_name: str,
    git_branch_name: str,
    github_repository: Repository,
):
    """
    arrange: given a branch that is not compliant
    act: when target_branch_protection is called with the name of the branch
    assert: then a fail report is returned.
    """
    # 1. branch protection not enabled
    report = target_branch_protection(
        repository_name=github_repository_name, branch_name=git_branch_name
    )

    assert report.result == Result.FAIL
    assert "not enabled" in report.reason
    assert git_branch_name in report.reason

    # 2. codeowner pull request review not required
    github_branch.edit_protection(require_code_owner_reviews=False)

    report = target_branch_protection(
        repository_name=github_repository_name, branch_name=git_branch_name
    )

    assert report.result == Result.FAIL
    assert "codeowner" in report.reason
    assert "pull request" in report.reason
    assert "review" in report.reason
    assert "not required" in report.reason
    assert git_branch_name in report.reason

    # 3. stale reviews not dismissed
    github_branch = github_repository.get_branch(git_branch_name)
    github_branch.edit_protection(require_code_owner_reviews=True)

    report = target_branch_protection(
        repository_name=github_repository_name, branch_name=git_branch_name
    )

    assert report.result == Result.FAIL
    assert "stale" in report.reason
    assert "reviews" in report.reason
    assert "not dismissed" in report.reason
    assert git_branch_name in report.reason

    # 4. pull requests allowances not empty
    github_branch.edit_protection(dismiss_stale_reviews=True)

    report = target_branch_protection(
        repository_name=github_repository_name, branch_name=git_branch_name
    )

    assert report.result == Result.FAIL
    assert "pull request" in report.reason
    assert "reviews" in report.reason
    assert "can be bypassed" in report.reason
    assert git_branch_name in report.reason
