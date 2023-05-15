# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Tests for the source_branch_protection function."""

import itertools
from uuid import uuid4

import pytest
from github import Github
from github.Repository import Repository

from repo_policy_compliance import Result, source_branch_protection

from .. import assert_
from .types_ import BranchWithProtection


@pytest.mark.parametrize(
    "github_branch, add_commit, reason_string_array",
    [
        pytest.param(
            BranchWithProtection(
                name=f"source-branch/not-protected/{uuid4()}", branch_protection_enabled=False
            ),
            False,
            ("not enabled"),
            id="branch_protection disabled",
        ),
        pytest.param(
            BranchWithProtection(
                name=f"source-branch/requires-signature/{uuid4()}",
                required_signatures_enabled=False,
            ),
            False,
            ("signed", "commits", "not required"),
            id="required-signature disabled",
        ),
        pytest.param(
            BranchWithProtection(
                name=f"source-branch/unsigned-commits/{uuid4()}",
                required_signatures_enabled=True,
            ),
            True,
            ("commit", "not signed"),
            id="required-signature enabled branch has unsigned commits",
        ),
    ],
    indirect=["github_branch"],
)
def test_fail(
    github_repository: Repository,
    github_branch: BranchWithProtection,
    add_commit: bool,
    reason_string_array: tuple[str],
    github_repository_name: str,
):
    """
    arrange: given a branch that is not compliant.
    act: when source_branch_protection is called with the name of the branch.
    assert: then a fail report is returned.
    """
    if add_commit:
        github_repository.create_file(
            "test.txt", "testing", "some content", branch=github_branch.name
        )

    # The github_client is injected
    report = source_branch_protection(  # pylint: disable=no-value-for-parameter
        repository_name=github_repository_name,
        branch_name=github_branch.name,
        target_branch_name=github_repository.default_branch,
    )

    assert_.substrings_in_string(
        itertools.chain(reason_string_array, github_branch.name), str(report.reason)
    )
    assert report.result == Result.FAIL


@pytest.mark.parametrize(
    "github_branch",
    [
        BranchWithProtection(
            name=f"protected/{uuid4()}",
            require_code_owner_reviews=False,
            dismiss_stale_reviews_enabled=False,
            bypass_pull_request_allowance_disabled=False,
        )
    ],
    indirect=True,
)
def test_pass(
    github_repository: Repository,
    ci_github_token: str | None,
    github_branch: BranchWithProtection,
    github_repository_name: str,
):
    """
    arrange: given a branch that is compliant including a signed commit only in CI.
    act: when source_branch_protection is called with the name of the branch.
    assert: then a pass report is returned.
    """
    # Use the CI GitHub token to create a signed commit only in CI
    if ci_github_token:
        ci_github_client = Github(login_or_token=ci_github_token)
        ci_repository = ci_github_client.get_repo(github_repository_name)
        ci_repository.create_file("test.txt", "testing", "some content", branch=github_branch.name)

    # The github_client is injected
    report = source_branch_protection(  # pylint: disable=no-value-for-parameter
        repository_name=github_repository_name,
        branch_name=github_branch.name,
        target_branch_name=github_repository.default_branch,
    )

    assert report.reason is None
    assert report.result == Result.PASS
