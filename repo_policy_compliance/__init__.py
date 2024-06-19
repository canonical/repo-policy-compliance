# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Library for checking that GitHub repos comply with policy."""

from enum import Enum
from types import MappingProxyType
from typing import cast

from pydantic import BaseModel, Field

from repo_policy_compliance import check, log, policy


class UsedPolicy(Enum):
    """Sentinel to indicate which policy to use.

    Attributes:
        ALL: Use all policies.
        PULL_REQUEST_ALLOW_FORK: Use policy that lets forked repositories run jobs (default).
    """

    ALL = 1
    PULL_REQUEST_ALLOW_FORK = 2


class PullRequestInput(BaseModel):
    """Input arguments for pull request checks.

    Attributes:
        repository_name: The name of the repository to run the check on.
        source_repository_name: The name of the repository that has the source branch.
        target_branch_name: The name of the branch that is targeted by the PR.
        source_branch_name: The name of the branch that contains the commits to be merged.
        commit_sha: The SHA of the commit that the job is running on.
    """

    repository_name: str = Field(min_length=1)
    source_repository_name: str = Field(min_length=1)
    target_branch_name: str = Field(min_length=1)
    source_branch_name: str = Field(min_length=1)
    commit_sha: str = Field(min_length=1)


@log.call
def pull_request(
    input_: PullRequestInput,
    policy_document: dict | UsedPolicy = UsedPolicy.PULL_REQUEST_ALLOW_FORK,
) -> check.Report:
    """Run all the checks for pull request jobs.

    Args:
        input_: Data required for executing checks.
        policy_document: Describes the policies that should be run.

    Returns:
        Whether the run is authorized based on all the checks.
    """
    try:
        used_policy_document = _retrieve_policy_document(policy_document=policy_document)
    except ValueError as exc:
        return check.Report(result=check.Result.FAIL, reason=exc.args[0])

    # The github_client argument is injected, disabling missing arguments check for this function
    # pylint: disable=no-value-for-parameter
    if policy.enabled(
        job_type=policy.JobType.PULL_REQUEST,
        name=policy.PullRequestProperty.TARGET_BRANCH_PROTECTION,
        policy_document=used_policy_document,
    ) and (
        (
            target_branch_report := check.target_branch_protection(
                repository_name=input_.repository_name,
                branch_name=input_.target_branch_name,
                source_repository_name=input_.source_repository_name,
            )
        ).result
        == check.Result.FAIL
        or target_branch_report.result == check.Result.ERROR
    ):
        return target_branch_report

    if (
        policy.enabled(
            job_type=policy.JobType.PULL_REQUEST,
            name=policy.PullRequestProperty.COLLABORATORS,
            policy_document=used_policy_document,
        )
        and (
            collaborators_report := check.collaborators(repository_name=input_.repository_name)
        ).result
        == check.Result.FAIL
    ):
        return collaborators_report

    is_pull_request_disallow_fork_policy_enabled = policy.enabled(
        job_type=policy.JobType.PULL_REQUEST,
        name=policy.PullRequestProperty.PULL_REQUEST_DISALLOW_FORK,
        policy_document=used_policy_document,
    )

    if (
        policy.enabled(
            job_type=policy.JobType.PULL_REQUEST,
            name=policy.PullRequestProperty.EXECUTE_JOB,
            policy_document=used_policy_document,
        )
        and (
            execute_job_report := check.execute_job(
                job_metadata=check.JobMetadata(
                    branch_name=input_.source_branch_name,
                    commit_sha=input_.commit_sha,
                    repository_name=input_.repository_name,
                    source_repository_name=input_.source_repository_name,
                ),
                disable_third_party_fork=is_pull_request_disallow_fork_policy_enabled,
            )
        ).result
        == check.Result.FAIL
    ):
        return execute_job_report

    return check.Report(result=check.Result.PASS, reason=None)


def _retrieve_policy_document(
    policy_document: dict | UsedPolicy = UsedPolicy.PULL_REQUEST_ALLOW_FORK,
) -> MappingProxyType:
    """Get policy document from predefined UsedPolicy or custom document mapping.

    Args:
        policy_document: The predefined used policy enum or custom mapping dict.

    Raises:
        ValueError: If an invalid policy document mapping was given.

    Returns:
        Mapped policy document.
    """
    if policy_document == UsedPolicy.ALL:
        return policy.ALL
    if policy_document == UsedPolicy.PULL_REQUEST_ALLOW_FORK:
        return policy.ALLOW_FORK
    # Guaranteed to be a dict due to initial if
    policy_document = cast(dict, policy_document)
    if not (policy_report := policy.check(document=policy_document)).result:
        raise ValueError(policy_report.reason)
    return MappingProxyType(policy_document)


class BranchInput(BaseModel):
    """Input arguments to check jobs running on a branch.

    Attributes:
        repository_name: The name of the repository to run the check on.
    """

    repository_name: str = Field(min_length=1)


WorkflowDispatchInput = BranchInput


@log.call
def workflow_dispatch(
    input_: WorkflowDispatchInput, policy_document: dict | UsedPolicy = UsedPolicy.ALL
) -> check.Report:
    """Run all the checks for workflow dispatch jobs.

    Args:
        input_: Data required for executing checks.
        policy_document: Describes the policies that should be run.

    Returns:
        Whether the run is authorized based on all the checks.
    """
    try:
        used_policy_document = _retrieve_policy_document(policy_document=policy_document)
    except ValueError as exc:
        return check.Report(result=check.Result.FAIL, reason=exc.args[0])

    # The github_client argument is injected, disabling missing arguments check for this function
    # pylint: disable=no-value-for-parameter
    if policy.enabled(
        job_type=policy.JobType.WORKFLOW_DISPATCH,
        name=policy.WorkflowDispatchProperty.COLLABORATORS,
        policy_document=used_policy_document,
    ) and (
        (
            collaborators_report := check.collaborators(repository_name=input_.repository_name)
        ).result
        == check.Result.FAIL
        or collaborators_report.result == check.Result.ERROR
    ):
        return collaborators_report

    return check.Report(result=check.Result.PASS, reason=None)


PushInput = BranchInput


@log.call
def push(input_: PushInput, policy_document: dict | UsedPolicy = UsedPolicy.ALL) -> check.Report:
    """Run all the checks for on push jobs.

    Args:
        input_: Data required for executing checks.
        policy_document: Describes the policies that should be run.

    Returns:
        Whether the run is authorized based on all the checks.
    """
    try:
        used_policy_document = _retrieve_policy_document(policy_document=policy_document)
    except ValueError as exc:
        return check.Report(result=check.Result.FAIL, reason=exc.args[0])

    # The github_client argument is injected, disabling missing arguments check for this function
    # pylint: disable=no-value-for-parameter
    if policy.enabled(
        job_type=policy.JobType.PUSH,
        name=policy.PushProperty.COLLABORATORS,
        policy_document=used_policy_document,
    ) and (
        (
            collaborators_report := check.collaborators(repository_name=input_.repository_name)
        ).result
        == check.Result.FAIL
        or collaborators_report.result == check.Result.ERROR
    ):
        return collaborators_report

    return check.Report(result=check.Result.PASS, reason=None)


ScheduleInput = BranchInput


@log.call
def schedule(
    input_: ScheduleInput, policy_document: dict | UsedPolicy = UsedPolicy.ALL
) -> check.Report:
    """Run all the checks for on schedule jobs.

    Args:
        input_: Data required for executing checks.
        policy_document: Describes the policies that should be run.

    Returns:
        Whether the run is authorized based on all the checks.
    """
    try:
        used_policy_document = _retrieve_policy_document(policy_document=policy_document)
    except ValueError as exc:
        return check.Report(result=check.Result.FAIL, reason=exc.args[0])

    # The github_client argument is injected, disabling missing arguments check for this function
    # pylint: disable=no-value-for-parameter
    if policy.enabled(
        job_type=policy.JobType.SCHEDULE,
        name=policy.ScheduleProperty.COLLABORATORS,
        policy_document=used_policy_document,
    ) and (
        (
            collaborators_report := check.collaborators(repository_name=input_.repository_name)
        ).result
        == check.Result.FAIL
        or collaborators_report.result == check.Result.ERROR
    ):
        return collaborators_report

    return check.Report(result=check.Result.PASS, reason=None)
