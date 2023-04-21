# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""Tests for the target_branch_protection function."""

from uuid import uuid4

import pytest
from github import Branch, Consts, Github

from repo_policy_compliance import Result, target_branch_protection

from .helpers import assert_substrings_in_string


@pytest.mark.parametrize(
    "github_branch, reason_string_array, branch_protection, require_code_owner_reviews, dismiss_stale_reviews, bypass_pull_request_allowance_enabled",
    [
        (f"not-protected/{uuid4()}", ["not enabled"], False, False, False, False),
        (
            f"no-code-owner-review/{uuid4()}",
            ["codeowner", "pull request", "review", "not required"],
            True,
            False,
            False,
            False,
        ),
        (
            f"stale-review-not-dismissed/{uuid4()}",
            ["stale", "reviews", "not dismissed"],
            True,
            True,
            False,
            False,
        ),
        (
            f"pull-request-allowance-not-empty/{uuid4()}",
            ["pull request", "reviews", "can be bypassed"],
            True,
            True,
            True,
            True,
        ),
    ],
    indirect=["github_branch"],
)
def test_fail(
    github_branch: Branch,
    reason_string_array: str,
    branch_protection: bool,
    require_code_owner_reviews: bool,
    dismiss_stale_reviews: bool,
    bypass_pull_request_allowance_enabled: bool,
    github_repository_name: str,
):
    """
    arrange: given a branch that is not compliant
    act: when target_branch_protection is called with the name of the branch
    assert: then a fail report is returned.
    """

    if branch_protection:
        edit_branch_protection(
            github_branch,
            require_code_owner_reviews,
            dismiss_stale_reviews,
            bypass_pull_request_allowance_enabled,
        )

    report = target_branch_protection(
        repository_name=github_repository_name, branch_name=github_branch.name
    )

    if branch_protection:
        github_branch.remove_protection()

    assert report.result == Result.FAIL
    assert_substrings_in_string(reason_string_array, report.reason)
    assert github_branch.name in report.reason


@pytest.mark.parametrize("github_branch", [f"protected/{uuid4()}"], indirect=True)
def test_pass(
    github_branch: Branch,
    github_repository_name: str,
):
    """
    arrange: given a branch that is compliant
    act: when target_branch_protection is called with the name of the branch
    assert: then a pass report is returned.
    """

    edit_branch_protection(github_branch, True, True, False)
    report = target_branch_protection(
        repository_name=github_repository_name, branch_name=github_branch.name
    )
    github_branch.remove_protection()

    assert report.result == Result.PASS
    assert report.reason == ""


def edit_branch_protection(
    github_branch: Branch,
    require_code_owner_reviews: bool,
    dismiss_stale_reviews: bool,
    bypass_pull_request_allowance_enabled: bool,
) -> None:
    if bypass_pull_request_allowance_enabled:
        #pytest.set_trace()
        post_parameters = {
            "required_status_checks": None,
            "enforce_admins": None,
            "required_pull_request_reviews": {
                "dismiss_stale_reviews": dismiss_stale_reviews,
                "require_code_owner_reviews": require_code_owner_reviews,
                "bypass_pull_request_allowances": {
                    "users": ["gregory-schiano", "jdkanderson"],
                    "teams": ["is-charms"],
                    "apps": [],
                },
            },
            "restrictions": None,
        }

        github_branch._requester.requestJsonAndCheck(
            "PUT",
            github_branch.protection_url,
            headers={"Accept": Consts.mediaTypeRequireMultipleApprovingReviews},
            input=post_parameters,
        )
    else:
        github_branch.edit_protection(
            require_code_owner_reviews=require_code_owner_reviews,
            dismiss_stale_reviews=dismiss_stale_reviews,
        )
