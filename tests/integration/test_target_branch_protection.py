# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""Tests for the target_branch_protection function."""

from uuid import uuid4

import pytest
from github import Branch, Consts

from repo_policy_compliance import Result, target_branch_protection

from .helpers import assert_substrings_in_string


@pytest.mark.parametrize(
    "github_branch, reason_string_array",
    [
        (f"not-protected/{uuid4()}", ["not enabled"]),
        (
            f"no-code-owner-review/{uuid4()}",
            ["codeowner", "pull request", "review", "not required"],
        ),
        (f"stale-review-not-dismissed/{uuid4()}", ["stale", "reviews", "not dismissed"]),
        (
            f"pull-request-allowance-not-empty/{uuid4()}",
            ["pull request", "reviews", "can be bypassed"],
        ),
    ],
    indirect=["github_branch"],
)
def test_fail(
    github_branch: Branch,
    reason_string_array: str,
    github_repository_name: str,
):
    """
    arrange: given a branch that is not compliant
    act: when target_branch_protection is called with the name of the branch
    assert: then a fail report is returned.
    """

    report = target_branch_protection(
        repository_name=github_repository_name, branch_name=github_branch.name
    )

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

    report = target_branch_protection(
        repository_name=github_repository_name, branch_name=github_branch.name
    )

    assert report.result == Result.PASS
    assert report.reason == ""
