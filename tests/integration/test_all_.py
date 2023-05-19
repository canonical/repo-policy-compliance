# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Tests for the all_ function."""

from uuid import uuid4

import pytest
from github.Branch import Branch
from github.Repository import Repository

from repo_policy_compliance import Result, all_

from .types_ import BranchWithProtection, RequestedCollaborator


@pytest.mark.parametrize(
    "github_branch",
    [f"test-branch/all/target-branch-fail/{uuid4()}"],
    indirect=["github_branch"],
)
def test_fail_target_branch(github_branch: Branch, github_repository_name: str):
    """
    arrange: given a target branch that is not complient
    act: when all_ is called
    assert: then a fail report is returned.
    """
    # The github_client is injected
    report = all_(  # pylint: disable=no-value-for-parameter
        repository_name=github_repository_name,
        source_repository_name=github_repository_name,
        target_branch_name=github_branch.name,
        source_branch_name="",
        commit_sha="",
    )

    assert report.result == Result.FAIL


@pytest.mark.parametrize(
    "github_branch, protected_github_branch, another_github_branch",
    [
        (
            f"test-branch/all/source-branch-fail/target/{uuid4()}",
            BranchWithProtection(),
            f"test-branch/all/source-branch-fail/source/{uuid4()}",
        )
    ],
    indirect=True,
)
@pytest.mark.usefixtures("protected_github_branch")
def test_fail_source_branch(
    github_branch: Branch, github_repository_name: str, another_github_branch: Branch
):
    """
    arrange: given a target branch that is not complient
    act: when all_ is called
    assert: then a fail report is returned.
    """
    # Create invalid source branch

    # The github_client is injected
    report = all_(  # pylint: disable=no-value-for-parameter
        repository_name=github_repository_name,
        source_repository_name=github_repository_name,
        target_branch_name=github_branch.name,
        source_branch_name=another_github_branch.name,
        commit_sha=another_github_branch.commit.sha,
    )

    assert report.result == Result.FAIL


@pytest.mark.parametrize(
    "github_branch, protected_github_branch, collaborators_with_permission",
    [
        (
            f"test-branch/all/collaborators-fail/{uuid4()}",
            BranchWithProtection(),
            RequestedCollaborator("admin", "admin"),
        )
    ],
    indirect=True,
)
@pytest.mark.usefixtures("protected_github_branch", "collaborators_with_permission")
def test_fail_collaborators(github_branch: Branch, github_repository_name: str):
    """
    arrange: given a source and target branch that are compliant and outside collaborators with
        more than read permission
    act: when all_ is called
    assert: then a fail report is returned.
    """
    # The github_client is injected
    report = all_(  # pylint: disable=no-value-for-parameter
        repository_name=github_repository_name,
        source_repository_name=github_repository_name,
        target_branch_name=github_branch.name,
        source_branch_name=github_branch.name,
        commit_sha=github_branch.commit.sha,
    )

    assert report.result == Result.FAIL


@pytest.mark.parametrize(
    "github_branch, protected_github_branch, forked_github_branch",
    [
        (
            f"test-branch/all/execute-job-fail/target/{uuid4()}",
            BranchWithProtection(),
            f"test-branch/all/execute-job-fail/source/{uuid4()}",
        )
    ],
    indirect=True,
)
@pytest.mark.usefixtures("protected_github_branch")
def test_fail_execute_job(
    github_branch: Branch,
    github_repository_name: str,
    forked_github_branch: Branch,
    forked_github_repository: Repository,
):
    """
    arrange: given a target and repository that is compliant and a source branch that is a fork
    act: when all_ is called
    assert: then a fail report is returned.
    """
    # The github_client is injected
    report = all_(  # pylint: disable=no-value-for-parameter
        repository_name=github_repository_name,
        source_repository_name=forked_github_repository.full_name,
        target_branch_name=github_branch.name,
        source_branch_name=forked_github_branch.name,
        commit_sha=forked_github_branch.commit.sha,
    )

    assert report.result == Result.FAIL


@pytest.mark.parametrize(
    "github_branch, protected_github_branch",
    [(f"test-branch/all/pass/{uuid4()}", BranchWithProtection())],
    indirect=True,
)
@pytest.mark.usefixtures("protected_github_branch")
def test_pass(github_branch: Branch, github_repository_name: str):
    """
    arrange: given a source and target branch and repository that is compliant
    act: when all_ is called
    assert: then a pass report is returned.
    """
    # The github_client is injected
    report = all_(  # pylint: disable=no-value-for-parameter
        repository_name=github_repository_name,
        source_repository_name=github_repository_name,
        target_branch_name=github_branch.name,
        source_branch_name=github_branch.name,
        commit_sha=github_branch.commit.sha,
    )

    assert report.result == Result.PASS
