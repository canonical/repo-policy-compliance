# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Tests for the target_branch_protection function."""

import itertools
from uuid import uuid4

import pytest

from repo_policy_compliance import Result, target_branch_protection

from .. import assert_
from .types_ import BranchWithProtection


@pytest.mark.parametrize(
    "github_branch, reason_string_array",
    [
        pytest.param(
            BranchWithProtection(
                name=f"target-branch/not-protected/{uuid4()}", branch_protection_enabled=False
            ),
            ("not enabled"),
            id="branch_protection disabled",
        ),
        pytest.param(
            BranchWithProtection(
                name=f"target-branch/no-code-owner-review/{uuid4()}",
                require_code_owner_reviews=False,
            ),
            ("codeowner", "pull request", "review", "not required"),
            id="code-owner missing",
        ),
        pytest.param(
            BranchWithProtection(
                name=f"target-branch/stale-review-not-dismissed/{uuid4()}",
                dismiss_stale_reviews_enabled=False,
            ),
            ("stale", "reviews", "not dismissed"),
            id="stale-review not-dismissed",
        ),
        pytest.param(
            BranchWithProtection(
                name=f"target-branch/pull-request-allowance-not-empty/{uuid4()}",
                bypass_pull_request_allowance_disabled=False,
            ),
            ("pull request", "reviews", "can be bypassed"),
            id="pull-request-allowance not empty",
        ),
        pytest.param(
            BranchWithProtection(
                name=f"target-branch/requires-signature/{uuid4()}",
                required_signatures_enabled=False,
            ),
            ("signed", "commits", "not required"),
            id="required-signature disabled",
        ),
    ],
    indirect=["github_branch"],
)
def test_fail(
    github_branch: BranchWithProtection,
    reason_string_array: tuple[str],
    github_repository_name: str,
):
    """
    arrange: given a branch that is not compliant.
    act: when target_branch_protection is called with the name of the branch.
    assert: then a fail report is returned.
    """
    # The github_client is injected
    report = target_branch_protection(  # pylint: disable=no-value-for-parameter
        repository_name=github_repository_name, branch_name=github_branch.name
    )

    assert_.substrings_in_string(
        itertools.chain(reason_string_array, github_branch.name), str(report.reason)
    )
    assert report.result == Result.FAIL


@pytest.mark.parametrize(
    "github_branch", [BranchWithProtection(name=f"protected/{uuid4()}")], indirect=True
)
def test_pass(
    github_branch: BranchWithProtection,
    github_repository_name: str,
):
    """
    arrange: given a branch that is compliant.
    act: when target_branch_protection is called with the name of the branch.
    assert: then a pass report is returned.
    """
    # The github_client is injected
    report = target_branch_protection(  # pylint: disable=no-value-for-parameter
        repository_name=github_repository_name, branch_name=github_branch.name
    )

    assert report.reason is None
    assert report.result == Result.PASS
