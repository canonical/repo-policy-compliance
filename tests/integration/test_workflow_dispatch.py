# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Tests for the workflow_dispatch function."""

from uuid import uuid4

import pytest
from github.Branch import Branch
from github.Repository import Repository

from repo_policy_compliance import Result, WorkflowDispatchInput, policy, workflow_dispatch

from .types_ import BranchWithProtection, RequestedCollaborator


def test_invalid_policy():
    """
    arrange: given invalid policy
    act: when workflow_dispatch is called with the policy
    assert: then a fail report is returned.
    """
    policy_document = {"invalid": "value"}

    report = workflow_dispatch(
        input_=WorkflowDispatchInput(
            repository_name="repository 1",
            branch_name="branch 1",
            commit_sha="commit sha 1",
        ),
        policy_document=policy_document,
    )

    assert report.result == Result.FAIL, report.reason


@pytest.mark.parametrize(
    "github_branch, policy_enabled, expected_result",
    [
        pytest.param(
            f"test-branch/workflow_dispatch/branch-fail-enabled/{uuid4()}",
            True,
            Result.FAIL,
            id="policy enabled",
        ),
        pytest.param(
            f"test-branch/workflow_dispatch/branch-fail-disabled/{uuid4()}",
            False,
            Result.PASS,
            id="policy disabled",
        ),
    ],
    indirect=["github_branch"],
)
def test_fail_branch(
    github_branch: Branch,
    policy_enabled: bool,
    expected_result: Result,
    github_repository_name: str,
):
    """
    arrange: given a branch that is not compliant and whether the policy is enabled
    act: when workflow_dispatch is called with the policy
    assert: then the expected report is returned.
    """
    policy_document = {
        policy.JobType.WORKFLOW_DISPATCH: {
            policy.WorkflowDispatchProperty.BRANCH_PROTECTION: {policy.ENABLED_KEY: policy_enabled}
        }
    }

    report = workflow_dispatch(
        input_=WorkflowDispatchInput(
            repository_name=github_repository_name,
            branch_name=github_branch.name,
            commit_sha="sha 1",
        ),
        policy_document=policy_document,
    )

    assert report.result == expected_result, report.reason


@pytest.mark.parametrize(
    "github_branch, protected_github_branch, collaborators_with_permission, policy_enabled, "
    "expected_result",
    [
        pytest.param(
            f"test-branch/workflow_dispatch/collaborators-fail-enabled/{uuid4()}",
            BranchWithProtection(),
            RequestedCollaborator("admin", "admin"),
            True,
            Result.FAIL,
            id="policy enabled",
        ),
        pytest.param(
            f"test-branch/workflow_dispatch/collaborators-fail-disabled/{uuid4()}",
            BranchWithProtection(),
            RequestedCollaborator("admin", "admin"),
            False,
            Result.PASS,
            id="policy disabled",
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
    arrange: given a branch that are compliant and outside collaborators with more than read
        permission and whether the policy is enabled
    act: when workflow_dispatch is called with the policy
    assert: then the expected report is returned.
    """
    policy_document = {
        policy.JobType.WORKFLOW_DISPATCH: {
            policy.WorkflowDispatchProperty.COLLABORATORS: {policy.ENABLED_KEY: policy_enabled}
        }
    }

    report = workflow_dispatch(
        input_=WorkflowDispatchInput(
            repository_name=github_repository_name,
            branch_name=github_branch.name,
            commit_sha=github_branch.commit.sha,
        ),
        policy_document=policy_document,
    )

    assert report.result == expected_result


@pytest.mark.parametrize(
    "github_branch, protected_github_branch",
    [(f"test-branch/workflow_dispatch/pass/{uuid4()}", BranchWithProtection())],
    indirect=True,
)
@pytest.mark.usefixtures("protected_github_branch")
def test_pass(github_branch: Branch, github_repository_name: str):
    """
    arrange: given a branch and repository that is compliant
    act: when workflow_dispatch is called
    assert: then a pass report is returned.
    """
    report = workflow_dispatch(
        input_=WorkflowDispatchInput(
            repository_name=github_repository_name,
            branch_name=github_branch.name,
            commit_sha=github_branch.commit.sha,
        ),
    )

    assert report.result == Result.PASS
