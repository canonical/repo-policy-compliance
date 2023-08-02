# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Tests for the target_branch_protection function."""

import itertools
from uuid import uuid4

import pytest
from github.Branch import Branch

from repo_policy_compliance.check import Result, target_branch_protection

from .. import assert_
from .types_ import BranchWithProtection


@pytest.mark.parametrize(
    "github_branch, protected_github_branch, reason_string_array",
    [
        pytest.param(
            f"test-branch/target-branch/not-protected/{uuid4()}",
            BranchWithProtection(branch_protection_enabled=False),
            ("not enabled"),
            id="branch_protection disabled",
        ),
        pytest.param(
            f"test-branch/target-branch/stale-review-not-dismissed/{uuid4()}",
            BranchWithProtection(dismiss_stale_reviews_enabled=False),
            ("stale", "reviews", "not dismissed"),
            id="stale-review not-dismissed",
        ),
        pytest.param(
            f"test-branch/target-branch/pull-request-allowance-not-empty/{uuid4()}",
            BranchWithProtection(bypass_pull_request_allowance_disabled=False),
            ("pull request", "reviews", "can be bypassed"),
            id="pull-request-allowance not empty",
        ),
        pytest.param(
            f"test-branch/target-branch/requires-signature/{uuid4()}",
            BranchWithProtection(required_signatures_enabled=False),
            ("signed", "commits", "not required"),
            id="required-signature disabled",
        ),
    ],
    indirect=["github_branch", "protected_github_branch"],
)
@pytest.mark.usefixtures("protected_github_branch")
def test_fail(github_branch: Branch, reason_string_array: tuple[str], github_repository_name: str):
    """
    arrange: given a branch that is not compliant.
    act: when target_branch_protection is called with the name of the branch.
    assert: then a fail report is returned.
    """
    # The github_client is injected
    report = target_branch_protection(  # pylint: disable=no-value-for-parameter
        repository_name=github_repository_name,
        branch_name=github_branch.name,
        source_repository_name="other repo",
    )

    assert report.result == Result.FAIL
    assert report.reason, "expected a reason along with the fail result"
    assert_.substrings_in_string(
        itertools.chain(reason_string_array, github_branch.name), report.reason
    )


@pytest.mark.parametrize(
    "github_branch",
    [
        pytest.param(
            f"test-branch/target-branch/review-not-required/{uuid4()}",
            id="branch_protection disabled",
        )
    ],
    indirect=["github_branch"],
)
def test_fail_pull_request_review_not_required(
    pull_request_review_not_required: Branch, github_repository_name: str
):
    """
    arrange: given a branch that has protections enabled but does not require reviews
    act: when target_branch_protection is called with the name of the branch
    assert: then a fail report is returned.
    """
    pull_request_review_not_required.edit_protection(allow_force_pushes=False)

    # The github_client is injected
    report = target_branch_protection(  # pylint: disable=no-value-for-parameter
        repository_name=github_repository_name,
        branch_name=pull_request_review_not_required.name,
        source_repository_name="other repository",
    )

    assert report.result == Result.FAIL
    assert report.reason, "expected a reason along with the fail result"
    assert_.substrings_in_string(
        ("pull request", "review", "not required", pull_request_review_not_required.name),
        report.reason,
    )


@pytest.mark.parametrize(
    "github_branch, protected_github_branch",
    [(f"test-branch/target-branch/protected/{uuid4()}", BranchWithProtection())],
    indirect=["github_branch", "protected_github_branch"],
)
@pytest.mark.usefixtures("protected_github_branch")
def test_pass(
    github_branch: Branch, github_repository_name: str, caplog: pytest.LogCaptureFixture
):
    """
    arrange: given a branch that is compliant.
    act: when target_branch_protection is called with the name of the branch.
    assert: then a pass report is returned.
    """
    # The github_client is injected
    report = target_branch_protection(  # pylint: disable=no-value-for-parameter
        repository_name=github_repository_name,
        branch_name=github_branch.name,
        source_repository_name="other repository",
    )

    assert report.reason is None
    assert report.result == Result.PASS
    assert repr("target_branch_protection") in caplog.text
    assert repr(report) in caplog.text


@pytest.mark.parametrize(
    "github_branch, protected_github_branch",
    [
        (
            f"test-branch/target-branch/protected-on-repo/{uuid4()}",
            BranchWithProtection(
                required_signatures_enabled=True,
                branch_protection_enabled=True,
                dismiss_stale_reviews_enabled=False,
                bypass_pull_request_allowance_disabled=False,
            ),
        )
    ],
    indirect=["github_branch", "protected_github_branch"],
)
@pytest.mark.usefixtures("protected_github_branch")
def test_pass_branch_on_source_repo(
    github_branch: Branch, github_repository_name: str, caplog: pytest.LogCaptureFixture
):
    """
    arrange: given a branch that is compliant where both the source and destination branch are on
        the same repo.
    act: when target_branch_protection is called with the name of the branch.
    assert: then a pass report is returned.
    """
    github_branch.remove_required_pull_request_reviews()

    # The github_client is injected
    report = target_branch_protection(  # pylint: disable=no-value-for-parameter
        repository_name=github_repository_name,
        branch_name=github_branch.name,
        source_repository_name=github_repository_name,
    )

    assert report.reason is None
    assert report.result == Result.PASS
    assert repr("target_branch_protection") in caplog.text
    assert repr(report) in caplog.text
