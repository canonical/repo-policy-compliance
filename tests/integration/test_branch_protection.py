# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Tests for the branch_protection function."""

import itertools
from uuid import uuid4

import pytest
from github.Branch import Branch
from github.Repository import Repository

from repo_policy_compliance import Result, branch_protection

from .. import assert_
from . import branch_protection as test_branch_protection
from .types_ import BranchWithProtection


@pytest.mark.parametrize(
    "github_branch, protected_github_branch, add_commit, reason_string_array",
    [
        pytest.param(
            f"test-branch/branch/not-protected/{uuid4()}",
            BranchWithProtection(branch_protection_enabled=False),
            False,
            ("not enabled"),
            id="branch_protection disabled",
        ),
        pytest.param(
            f"test-branch/branch/requires-signature/{uuid4()}",
            BranchWithProtection(required_signatures_enabled=False),
            False,
            ("signed", "commits", "not required"),
            id="required-signature disabled",
        ),
        pytest.param(
            f"test-branch/branch/unsigned-commits/{uuid4()}",
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
    act: when branch_protection is called with the name of the branch.
    assert: then a fail report is returned.
    """
    if add_commit:
        github_repository.create_file(
            "test.txt", "testing", "some content", branch=github_branch.name
        )

    # The github_client is injected
    report = branch_protection(  # pylint: disable=no-value-for-parameter
        repository_name=github_repository_name,
        branch_name=github_branch.name,
        commit_sha="commit sha 1",
    )

    assert report.result == Result.FAIL
    assert report.reason, "expected a reason along with the fail result"
    assert_.substrings_in_string(
        itertools.chain(reason_string_array, (github_branch.name,)), report.reason
    )


@pytest.fixture(name="branch_for_commit_not_signed_fail")
def fixture_branch_for_commit_not_signed_fail(
    forked_github_branch: Branch, forked_github_repository: Repository
):
    """Create branch for the test_commit_not_signed_fail test.

    Makes the branch the default branch for the repository and makes the latest commit unsigned.
    """
    # Make an unsigned commit
    forked_github_repository.create_file(
        "test.txt", "testing", "some content", branch=forked_github_branch.name
    )

    # Change default branch so that the commit is ignored by the check for unique commits being
    # signed
    forked_github_repository.edit(default_branch=forked_github_branch.name)

    branch_with_protection = BranchWithProtection(
        require_code_owner_reviews=False,
        dismiss_stale_reviews_enabled=False,
        bypass_pull_request_allowance_disabled=True,
    )

    test_branch_protection.edit(
        branch=forked_github_branch, branch_with_protection=branch_with_protection
    )

    yield forked_github_branch

    forked_github_branch.remove_protection()


@pytest.mark.parametrize(
    "forked_github_branch", [f"test-branch/branch/unsigned-commit/{uuid4()}"], indirect=True
)
def test_commit_not_signed_fail(
    branch_for_commit_not_signed_fail: Branch,
    forked_github_repository: Repository,
):
    """
    arrange: given a default branch where the last commit is not signed.
    act: when branch_protection is called with the name of the branch.
    assert: then a fail report is returned.
    """
    # Can't use branch_for_commit_not_signed_fail branch since it doesn't know about the latest
    # commit
    commit_sha = forked_github_repository.get_commit(
        sha=branch_for_commit_not_signed_fail.name
    ).sha

    # The github_client is injected
    report = branch_protection(  # pylint: disable=no-value-for-parameter
        repository_name=forked_github_repository.full_name,
        branch_name=branch_for_commit_not_signed_fail.name,
        commit_sha=commit_sha,
    )

    assert report.result == Result.FAIL
    assert report.reason, "expected a reason along with the fail result"
    assert_.substrings_in_string(
        ("commit", "not signed", commit_sha, branch_for_commit_not_signed_fail.name), report.reason
    )


@pytest.mark.parametrize(
    "github_branch", [f"test-branch/branch/protected/{uuid4()}"], indirect=["github_branch"]
)
def test_pass(protected_github_branch_with_commit_in_ci: Branch, github_repository_name: str):
    """
    arrange: given a branch that is compliant including a signed commit only in CI (on local runs
        the branch has no unique commits and hence the check for unsigned commits will pass).
    act: when branch_protection is called with the name of the branch.
    assert: then a pass report is returned.
    """
    # The github_client is injected
    report = branch_protection(  # pylint: disable=no-value-for-parameter
        repository_name=github_repository_name,
        branch_name=protected_github_branch_with_commit_in_ci.name,
        commit_sha=protected_github_branch_with_commit_in_ci.commit.sha,
    )

    assert report.reason is None
    assert report.result == Result.PASS
