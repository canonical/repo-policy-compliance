# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Tests for the all_ function."""

from uuid import uuid4

import pytest
from github.Branch import Branch
from github.Repository import Repository

from repo_policy_compliance import Result, all_, policy

from .types_ import BranchWithProtection, RequestedCollaborator


def test_invalid_policy():
    """
    arrange: given invalid policy
    act: when all_ is called with the policy
    assert: then a fail report is returned.
    """
    policy_document = {"invalid": {"enabled": True}}

    report = all_(
        repository_name="repository 1",
        source_repository_name="repository 2",
        target_branch_name="branch 1",
        source_branch_name="",
        commit_sha="",
        policy_document=policy_document,
    )

    assert report.result == Result.FAIL, report.reason


@pytest.mark.parametrize(
    "github_branch, policy_enabled, expected_result",
    [
        pytest.param(
            f"test-branch/all/target-branch-fail-enabled/{uuid4()}",
            True,
            Result.FAIL,
            id="policy enabled",
        ),
        pytest.param(
            f"test-branch/all/target-branch-fail-disabled/{uuid4()}",
            False,
            Result.PASS,
            id="policy disabled",
        ),
    ],
    indirect=["github_branch"],
)
def test_fail_target_branch(
    github_branch: Branch,
    policy_enabled: bool,
    expected_result: Result,
    github_repository_name: str,
):
    """
    arrange: given a target branch that is not compliant and whether the policy is enabled
    act: when all_ is called with the policy
    assert: then the expected report is returned.
    """
    policy_document = {policy.Property.TARGET_BRANCH_PROTECTION: {"enabled": policy_enabled}}

    report = all_(
        repository_name=github_repository_name,
        source_repository_name=github_repository_name,
        target_branch_name=github_branch.name,
        source_branch_name="",
        commit_sha="",
        policy_document=policy_document,
    )

    assert report.result == expected_result, report.reason


@pytest.mark.parametrize(
    "github_branch, protected_github_branch, another_github_branch, policy_enabled, "
    "expected_result",
    [
        pytest.param(
            f"test-branch/all/source-branch-fail-enabled/target/{uuid4()}",
            BranchWithProtection(),
            f"test-branch/all/source-branch-fail-enabled/source/{uuid4()}",
            True,
            Result.FAIL,
            id="policy enabled",
        ),
        pytest.param(
            f"test-branch/all/source-branch-fail-disabled/target/{uuid4()}",
            BranchWithProtection(),
            f"test-branch/all/source-branch-fail-disabled/source/{uuid4()}",
            False,
            Result.PASS,
            id="policy disabled",
        ),
    ],
    indirect=["github_branch", "protected_github_branch", "another_github_branch"],
)
@pytest.mark.usefixtures("protected_github_branch")
def test_fail_source_branch(
    github_branch: Branch,
    github_repository_name: str,
    another_github_branch: Branch,
    policy_enabled: bool,
    expected_result: Result,
):
    """
    arrange: given a source branch that is not compliant and whether the policy is enabled
    act: when all_ is called with the policy
    assert: then the expected report is returned.
    """
    policy_document = {policy.Property.SOURCE_BRANCH_PROTECTION: {"enabled": policy_enabled}}

    report = all_(
        repository_name=github_repository_name,
        source_repository_name=github_repository_name,
        target_branch_name=github_branch.name,
        source_branch_name=another_github_branch.name,
        commit_sha=another_github_branch.commit.sha,
        policy_document=policy_document,
    )

    assert report.result == expected_result


@pytest.mark.parametrize(
    "github_branch, protected_github_branch, collaborators_with_permission, policy_enabled, "
    "expected_result",
    [
        pytest.param(
            f"test-branch/all/collaborators-fail-enabled/{uuid4()}",
            BranchWithProtection(),
            RequestedCollaborator("admin", "admin"),
            True,
            Result.FAIL,
            id="policy enabled",
        ),
        pytest.param(
            f"test-branch/all/collaborators-fail-disabled/{uuid4()}",
            BranchWithProtection(),
            RequestedCollaborator("admin", "admin"),
            False,
            Result.PASS,
            id="policy enabled",
        ),
    ],
    indirect=["github_branch", "protected_github_branch", "collaborators_with_permission"],
)
@pytest.mark.usefixtures("protected_github_branch", "collaborators_with_permission")
def test_fail_collaborators(
    github_branch: Branch,
    github_repository_name: str,
    policy_enabled: bool,
    expected_result: Result,
):
    """
    arrange: given a source and target branch that are compliant and outside collaborators with
        more than read permission and whether the policy is enabled
    act: when all_ is called with the policy
    assert: then the expected report is returned.
    """
    policy_document = {policy.Property.COLLABORATORS: {"enabled": policy_enabled}}

    report = all_(
        repository_name=github_repository_name,
        source_repository_name=github_repository_name,
        target_branch_name=github_branch.name,
        source_branch_name=github_branch.name,
        commit_sha=github_branch.commit.sha,
        policy_document=policy_document,
    )

    assert report.result == expected_result


@pytest.mark.parametrize(
    "github_branch, protected_github_branch, forked_github_branch, policy_enabled, "
    "expected_result",
    [
        pytest.param(
            f"test-branch/all/execute-job-fail/target/{uuid4()}",
            BranchWithProtection(),
            f"test-branch/all/execute-job-fail/source/{uuid4()}",
            True,
            Result.FAIL,
            id="policy enabled",
        ),
        pytest.param(
            f"test-branch/all/execute-job-fail/target/{uuid4()}",
            BranchWithProtection(),
            f"test-branch/all/execute-job-fail/source/{uuid4()}",
            False,
            Result.PASS,
            id="policy disabled",
        ),
    ],
    indirect=["github_branch", "protected_github_branch", "forked_github_branch"],
)
@pytest.mark.usefixtures("protected_github_branch")
def test_fail_execute_job(
    github_branch: Branch,
    github_repository_name: str,
    forked_github_branch: Branch,
    forked_github_repository: Repository,
    policy_enabled: bool,
    expected_result: Result,
):
    """
    arrange: given a target and repository that is compliant and a source branch that is a fork and
        whether the policy is enabled
    act: when all_ is called with the policy
    assert: then the expected report is returned.
    """
    policy_document = {policy.Property.EXECUTE_JOB: {"enabled": policy_enabled}}

    report = all_(
        repository_name=github_repository_name,
        source_repository_name=forked_github_repository.full_name,
        target_branch_name=github_branch.name,
        source_branch_name=forked_github_branch.name,
        commit_sha=forked_github_branch.commit.sha,
        policy_document=policy_document,
    )

    assert report.result == expected_result


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
    report = all_(
        repository_name=github_repository_name,
        source_repository_name=github_repository_name,
        target_branch_name=github_branch.name,
        source_branch_name=github_branch.name,
        commit_sha=github_branch.commit.sha,
    )

    assert report.result == Result.PASS
