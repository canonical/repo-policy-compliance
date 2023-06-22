# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Tests for the source_branch_protection function."""

import itertools
from uuid import uuid4

import pytest
from github.Branch import Branch
from github.Repository import Repository

from repo_policy_compliance import Result, source_branch_protection

from .. import assert_
from .types_ import BranchWithProtection


@pytest.mark.parametrize(
    "github_branch, protected_github_branch, add_commit, reason_string_array",
    [
        pytest.param(
            f"test-branch/source-branch/not-protected/{uuid4()}",
            BranchWithProtection(branch_protection_enabled=False),
            False,
            ("not enabled"),
            id="branch_protection disabled",
        ),
        pytest.param(
            f"test-branch/source-branch/requires-signature/{uuid4()}",
            BranchWithProtection(required_signatures_enabled=False),
            False,
            ("signed", "commits", "not required"),
            id="required-signature disabled",
        ),
        pytest.param(
            f"test-branch/source-branch/unsigned-commits/{uuid4()}",
            BranchWithProtection(required_signatures_enabled=True),
            True,
            ("commit", "not signed"),
            id="required-signature enabled branch has unsigned commits",
        ),
    ],
    indirect=["github_branch", "protected_github_branch"],
)
@pytest.mark.usefixtures("protected_github_branch")
def test_fail(
    github_repository: Repository,
    github_branch: Branch,
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
        source_repository_name=github_repository_name,
        branch_name=github_branch.name,
        target_branch_name=github_repository.default_branch,
    )

    assert report.result == Result.FAIL
    assert report.reason, "expected a reason along with the fail result"
    assert_.substrings_in_string(
        itertools.chain(reason_string_array, github_branch.name), report.reason
    )


@pytest.mark.parametrize(
    "github_branch, protected_github_branch",
    [(f"test-branch/source-branch/protected/{uuid4()}", BranchWithProtection())],
    indirect=["github_branch", "protected_github_branch"],
)
def test_pass(
    github_repository: Repository,
    protected_github_branch_with_commit_in_ci: Branch,
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
        source_repository_name=github_repository_name,
        branch_name=protected_github_branch_with_commit_in_ci.name,
        target_branch_name=github_repository.default_branch,
    )

    assert report.reason is None
    assert report.result == Result.PASS


@pytest.mark.parametrize(
    "forked_github_branch",
    [f"test-branch/source-branch/forked/{uuid4()}"],
    indirect=True,
)
def test_pass_fork(
    forked_github_branch: Branch, forked_github_repository: Repository, github_repository_name: str
):
    """
    arrange: given a forked branch that is not compliant
    act: when source_branch_protection is called with the name of the branch.
    assert: then a pass report is returned.
    """
    # The github_client is injected
    report = source_branch_protection(  # pylint: disable=no-value-for-parameter
        repository_name=github_repository_name,
        source_repository_name=forked_github_repository.name,
        branch_name=forked_github_branch.name,
        target_branch_name=forked_github_repository.default_branch,
    )

    assert report.reason is None
    assert report.result == Result.PASS
