# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Tests for the target_branch_protection function."""

import typing
from collections import namedtuple
from uuid import uuid4

import pytest
from github import Branch, Consts

from repo_policy_compliance import Result, target_branch_protection


def assert_substrings_in_string(substrings: typing.Iterable[str], string: str) -> None:
    """Assert that a string contains substrings.
    Args:
        string: The string to check.
        substrings: The sub strings that must be contained in the string.
    """
    for substring in substrings:
        assert substring in string, f"{substring!r} not in {string!r}"  # nosec


BranchProtectionParameters = namedtuple(
    "BranchProtectionParameters",
    [
        "branch_protection_enabled",
        "require_code_owner_reviews",
        "dismiss_stale_reviews_enabled",
        "bypass_pull_request_allowance_disabled",
        "required_signatures_enabled",
    ],
)


@pytest.mark.parametrize(
    "github_branch, reason_string_array, branch_protection_parameters",
    [
        pytest.param(
            f"not-protected/{uuid4()}",
            ["not enabled"],
            BranchProtectionParameters(
                branch_protection_enabled=False,
                require_code_owner_reviews=False,
                dismiss_stale_reviews_enabled=False,
                bypass_pull_request_allowance_disabled=False,
                required_signatures_enabled=False,
            ),
            id="branch_protection disabled",
        ),
        pytest.param(
            f"no-code-owner-review/{uuid4()}",
            ["codeowner", "pull request", "review", "not required"],
            BranchProtectionParameters(
                branch_protection_enabled=True,
                require_code_owner_reviews=False,
                dismiss_stale_reviews_enabled=False,
                bypass_pull_request_allowance_disabled=False,
                required_signatures_enabled=False,
            ),
            id="code-owner missing",
        ),
        pytest.param(
            f"stale-review-not-dismissed/{uuid4()}",
            ["stale", "reviews", "not dismissed"],
            BranchProtectionParameters(
                branch_protection_enabled=True,
                require_code_owner_reviews=True,
                dismiss_stale_reviews_enabled=False,
                bypass_pull_request_allowance_disabled=False,
                required_signatures_enabled=False,
            ),
            id="stale-review not-dismissed",
        ),
        pytest.param(
            f"pull-request-allowance-not-empty/{uuid4()}",
            ["pull request", "reviews", "can be bypassed"],
            BranchProtectionParameters(
                branch_protection_enabled=True,
                require_code_owner_reviews=True,
                dismiss_stale_reviews_enabled=True,
                bypass_pull_request_allowance_disabled=False,
                required_signatures_enabled=False,
            ),
            id="pull-request-allowance not emtpy",
        ),
        pytest.param(
            f"requires-signature/{uuid4()}",
            ["signed", "commits", "not required"],
            BranchProtectionParameters(
                branch_protection_enabled=True,
                require_code_owner_reviews=True,
                dismiss_stale_reviews_enabled=True,
                bypass_pull_request_allowance_disabled=True,
                required_signatures_enabled=False,
            ),
            id="required-signature disabled",
        ),
    ],
    indirect=["github_branch"],
)
def test_fail(
    github_branch: Branch,
    reason_string_array: str,
    branch_protection_parameters: BranchProtectionParameters,
    github_repository_name: str,
):
    """
    arrange: given a branch that is not compliant
    act: when target_branch_protection is called with the name of the branch
    assert: then a fail report is returned.
    """

    if branch_protection_parameters.branch_protection_enabled:
        edit_branch_protection(github_branch, branch_protection_parameters)

    report = target_branch_protection(
        repository_name=github_repository_name, branch_name=github_branch.name
    )

    if branch_protection_parameters.branch_protection_enabled:
        github_branch.remove_protection()

    assert_substrings_in_string(reason_string_array, report.reason)
    assert github_branch.name in report.reason
    assert report.result == Result.FAIL


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

    branch_protection_parameters = BranchProtectionParameters(
        branch_protection_enabled=True,
        require_code_owner_reviews=True,
        dismiss_stale_reviews_enabled=True,
        bypass_pull_request_allowance_disabled=True,
        required_signatures_enabled=True,
    )
    edit_branch_protection(github_branch, branch_protection_parameters)
    report = target_branch_protection(
        repository_name=github_repository_name, branch_name=github_branch.name
    )
    github_branch.remove_protection()

    assert report.reason == ""
    assert report.result == Result.PASS


def edit_branch_protection(
    github_branch: Branch, branch_protection_parameters: BranchProtectionParameters
) -> None:
    if not branch_protection_parameters.bypass_pull_request_allowance_disabled:
        post_parameters = {
            "required_status_checks": None,
            "enforce_admins": None,
            "required_pull_request_reviews": {
                "dismiss_stale_reviews": branch_protection_parameters.dismiss_stale_reviews_enabled,
                "require_code_owner_reviews": branch_protection_parameters.require_code_owner_reviews,
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

        return

    github_branch.edit_protection(
        require_code_owner_reviews=branch_protection_parameters.require_code_owner_reviews,
        dismiss_stale_reviews=branch_protection_parameters.dismiss_stale_reviews_enabled,
    )

    if branch_protection_parameters.required_signatures_enabled:
        github_branch._requester.requestJsonAndCheck(
            "POST",
            url=f"{github_branch.protection_url}/required_signatures",
            headers={"Accept": Consts.signaturesProtectedBranchesPreview},
        )
