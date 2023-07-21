# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Tests for the pull_request function."""

from uuid import uuid4

import pytest
from github.Branch import Branch
from github.Repository import Repository

from repo_policy_compliance import PullRequestInput, policy, pull_request
from repo_policy_compliance.check import Result

from .types_ import BranchWithProtection, RequestedCollaborator


def test_invalid_policy():
    """
    arrange: given invalid policy
    act: when pull_request is called with the policy
    assert: then a fail report is returned.
    """
    policy_document = {"invalid": "value"}

    report = pull_request(
        input_=PullRequestInput(
            repository_name="repository 1",
            source_repository_name="repository 2",
            target_branch_name="branch 1",
            source_branch_name="branch 2",
            commit_sha="commit sha 1",
        ),
        policy_document=policy_document,
    )

    assert report.result == Result.FAIL, report.reason


@pytest.mark.parametrize(
    "github_branch, policy_enabled, expected_result",
    [
        pytest.param(
            f"test-branch/pull_request/target-branch-fail-enabled/{uuid4()}",
            True,
            Result.FAIL,
            id="policy enabled",
        ),
        pytest.param(
            f"test-branch/pull_request/target-branch-fail-disabled/{uuid4()}",
            False,
            Result.PASS,
            id="policy disabled",
        ),
    ],
    indirect=["github_branch"],
)
def test_target_branch(
    github_branch: Branch,
    policy_enabled: bool,
    expected_result: Result,
    github_repository_name: str,
):
    """
    arrange: given a target branch that is not compliant and whether the policy is enabled
    act: when pull_request is called with the policy
    assert: then the expected report is returned.
    """
    policy_document = {
        policy.JobType.PULL_REQUEST: {
            policy.PullRequestProperty.TARGET_BRANCH_PROTECTION: {
                policy.ENABLED_KEY: policy_enabled
            }
        }
    }

    report = pull_request(
        input_=PullRequestInput(
            repository_name=github_repository_name,
            source_repository_name=github_repository_name,
            target_branch_name=github_branch.name,
            source_branch_name="branch 1",
            commit_sha="sha 1",
        ),
        policy_document=policy_document,
    )

    assert report.result == expected_result, report.reason


@pytest.mark.parametrize(
    "github_branch, protected_github_branch, another_github_branch, policy_enabled, "
    "expected_result",
    [
        pytest.param(
            f"test-branch/pull_request/source-branch-fail-enabled/target/{uuid4()}",
            BranchWithProtection(),
            f"test-branch/pull_request/source-branch-fail-enabled/source/{uuid4()}",
            True,
            Result.FAIL,
            id="policy enabled",
        ),
        pytest.param(
            f"test-branch/pull_request/source-branch-fail-disabled/target/{uuid4()}",
            BranchWithProtection(),
            f"test-branch/pull_request/source-branch-fail-disabled/source/{uuid4()}",
            False,
            Result.PASS,
            id="policy disabled",
        ),
    ],
    indirect=["github_branch", "protected_github_branch", "another_github_branch"],
)
@pytest.mark.usefixtures("protected_github_branch")
def test_source_branch(
    github_branch: Branch,
    github_repository_name: str,
    another_github_branch: Branch,
    policy_enabled: bool,
    expected_result: Result,
):
    """
    arrange: given a source branch that is not compliant and whether the policy is enabled
    act: when pull_request is called with the policy
    assert: then the expected report is returned.
    """
    policy_document = {
        policy.JobType.PULL_REQUEST: {
            policy.PullRequestProperty.SOURCE_BRANCH_PROTECTION: {
                policy.ENABLED_KEY: policy_enabled
            }
        }
    }

    report = pull_request(
        input_=PullRequestInput(
            repository_name=github_repository_name,
            source_repository_name=github_repository_name,
            target_branch_name=github_branch.name,
            source_branch_name=another_github_branch.name,
            commit_sha=another_github_branch.commit.sha,
        ),
        policy_document=policy_document,
    )

    assert report.result == expected_result


@pytest.mark.parametrize(
    "github_branch, protected_github_branch, collaborators_with_permission, policy_enabled, "
    "expected_result",
    [
        pytest.param(
            f"test-branch/pull_request/collaborators-fail-enabled/{uuid4()}",
            BranchWithProtection(),
            RequestedCollaborator("admin", "admin"),
            True,
            Result.FAIL,
            id="policy enabled",
        ),
        pytest.param(
            f"test-branch/pull_request/collaborators-fail-disabled/{uuid4()}",
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
def test_collaborators(
    github_branch: Branch,
    github_repository_name: str,
    policy_enabled: bool,
    expected_result: Result,
):
    """
    arrange: given a source and target branch that are compliant and outside collaborators with
        more than read permission and whether the policy is enabled
    act: when pull_request is called with the policy
    assert: then the expected report is returned.
    """
    policy_document = {
        policy.JobType.PULL_REQUEST: {
            policy.PullRequestProperty.COLLABORATORS: {policy.ENABLED_KEY: policy_enabled}
        }
    }

    report = pull_request(
        input_=PullRequestInput(
            repository_name=github_repository_name,
            source_repository_name=github_repository_name,
            target_branch_name=github_branch.name,
            source_branch_name=github_branch.name,
            commit_sha=github_branch.commit.sha,
        ),
        policy_document=policy_document,
    )

    assert report.result == expected_result


@pytest.mark.parametrize(
    "github_branch, protected_github_branch, forked_github_branch, policy_enabled, "
    "expected_result",
    [
        pytest.param(
            f"test-branch/pull_request/execute-job-fail/target/{uuid4()}",
            BranchWithProtection(),
            f"test-branch/pull_request/execute-job-fail/source/{uuid4()}",
            True,
            Result.FAIL,
            id="policy enabled",
        ),
        pytest.param(
            f"test-branch/pull_request/execute-job-fail/target/{uuid4()}",
            BranchWithProtection(),
            f"test-branch/pull_request/execute-job-fail/source/{uuid4()}",
            False,
            Result.PASS,
            id="policy disabled",
        ),
    ],
    indirect=["github_branch", "protected_github_branch", "forked_github_branch"],
)
@pytest.mark.usefixtures("protected_github_branch", "make_fork_branch_external")
# All the arguments are required for the test
def test_execute_job(  # pylint: disable=too-many-arguments
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
    act: when pull_request is called with the policy
    assert: then the expected report is returned.
    """
    policy_document = {
        policy.JobType.PULL_REQUEST: {
            policy.PullRequestProperty.EXECUTE_JOB: {policy.ENABLED_KEY: policy_enabled}
        }
    }

    report = pull_request(
        input_=PullRequestInput(
            repository_name=github_repository_name,
            source_repository_name=forked_github_repository.full_name,
            target_branch_name=github_branch.name,
            source_branch_name=forked_github_branch.name,
            commit_sha=forked_github_branch.commit.sha,
        ),
        policy_document=policy_document,
    )

    assert report.result == expected_result


@pytest.mark.parametrize(
    "github_branch, protected_github_branch",
    [(f"test-branch/pull_request/pass/{uuid4()}", BranchWithProtection())],
    indirect=True,
)
@pytest.mark.usefixtures("protected_github_branch")
def test_pass(
    github_branch: Branch, github_repository_name: str, caplog: pytest.LogCaptureFixture
):
    """
    arrange: given a source and target branch and repository that is compliant
    act: when pull_request is called
    assert: then a pass report is returned.
    """
    report = pull_request(
        input_=PullRequestInput(
            repository_name=github_repository_name,
            source_repository_name=github_repository_name,
            target_branch_name=github_branch.name,
            source_branch_name=github_branch.name,
            commit_sha=github_branch.commit.sha,
        ),
    )

    assert report.result == Result.PASS
    assert repr("pull_request") in caplog.text
    assert repr(report) in caplog.text
