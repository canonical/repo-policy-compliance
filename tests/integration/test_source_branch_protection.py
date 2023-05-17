# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Tests for the source_branch_protection function."""

import itertools
from uuid import uuid4

import pytest
from github import Github
from github.Branch import Branch
from github.Repository import Repository

from repo_policy_compliance import Result, source_branch_protection

from .. import assert_
from . import branch_protection
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

    assert report.reason
    assert_.substrings_in_string(
        itertools.chain(reason_string_array, github_branch.name), report.reason
    )
    assert report.result == Result.FAIL


@pytest.fixture(name="source_branch_for_test_pass")
def fixture_source_branch_for_test_pass(
    github_repository: Repository,
    ci_github_token: str | None,
    github_repository_name: str,
):
    """Create branch for the test_pass test."""
    branch_name = f"source-branch/protected/{uuid4()}"
    main_branch = github_repository.get_branch(github_repository.default_branch)
    branch_ref = github_repository.create_git_ref(
        ref=f"refs/heads/{branch_name}", sha=main_branch.commit.sha
    )
    branch = github_repository.get_branch(branch_name)

    # Use the CI GitHub token to create a signed commit only in CI
    if ci_github_token:
        ci_github_client = Github(login_or_token=ci_github_token)
        ci_repository = ci_github_client.get_repo(github_repository_name)
        ci_repository.create_file("test.txt", "testing", "some content", branch=branch_name)

    branch_with_protection = BranchWithProtection(
        name=branch_name,
        require_code_owner_reviews=False,
        dismiss_stale_reviews_enabled=False,
        bypass_pull_request_allowance_disabled=True,
    )

    branch_protection.edit(branch=branch, branch_with_protection=branch_with_protection)

    yield branch

    branch.remove_protection()
    branch_ref.delete()


def test_pass(
    github_repository: Repository,
    source_branch_for_test_pass: Branch,
    github_repository_name: str,
):
    """
    arrange: given a branch that is compliant including a signed commit only in CI (on local runs
        the source branch has no unique commits and hence the check for unsigned commits will
        pass).
    act: when source_branch_protection is called with the name of the branch.
    assert: then a pass report is returned.
    """
    # The github_client is injected
    report = source_branch_protection(  # pylint: disable=no-value-for-parameter
        repository_name=github_repository_name,
        branch_name=source_branch_for_test_pass.name,
        target_branch_name=github_repository.default_branch,
    )

    assert report.reason is None
    assert report.result == Result.PASS
