# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""Tests for the target_branch_protection function."""


import pytest
from github import Branch, Consts

from repo_policy_compliance import Result, target_branch_protection


@pytest.mark.usefixtures("github_branch")
def test_fail(
    github_branch: Branch,
    github_repository_name: str,
    git_branch_name: str,
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
    github_branch.edit_protection(dismiss_stale_reviews=False, require_code_owner_reviews=True)

    report = target_branch_protection(
        repository_name=github_repository_name, branch_name=git_branch_name
    )

    assert report.result == Result.FAIL
    assert "stale" in report.reason
    assert "reviews" in report.reason
    assert "not dismissed" in report.reason
    assert git_branch_name in report.reason

    # 4. pull requests allowances not empty
    # The "bypass_pull_request_allowances" parameter is not available through the Github library
    post_parameters = {
        "required_status_checks": None,
        "enforce_admins": None,
        "required_pull_request_reviews": {
            "dismiss_stale_reviews": True,
            "require_code_owner_reviews": True,
        },
        "restrictions": None,
        "bypass_pull_request_allowances": {
            "users": ["gregory-schiano"],
            "teams": [],
            "apps": [],
        },
    }

    github_branch._requester.requestJsonAndCheck(
        "PUT",
        github_branch.protection_url,
        headers={"Accept": Consts.mediaTypeRequireMultipleApprovingReviews},
        input=post_parameters,
    )

    report = target_branch_protection(
        repository_name=github_repository_name, branch_name=git_branch_name
    )

    assert report.result == Result.FAIL
    assert "pull request" in report.reason
    assert "reviews" in report.reason
    assert "can be bypassed" in report.reason
    assert git_branch_name in report.reason


@pytest.mark.usefixtures("github_branch")
def test_pass(
    github_branch: Branch,
    github_repository_name: str,
    git_branch_name: str,
):
    """
    arrange: given a branch that is compliant
    act: when target_branch_protection is called with the name of the branch
    assert: then a pass report is returned.
    """

    github_branch.edit_protection(dismiss_stale_reviews=True, require_code_owner_reviews=True)

    report = target_branch_protection(
        repository_name=github_repository_name, branch_name=git_branch_name
    )

    assert report.result == Result.PASS
    assert report.reason == ""
