# Copyright 2023 Canonical Ltd.
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
    """

    ALL = 1


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
    input_: PullRequestInput, policy_document: dict | UsedPolicy = UsedPolicy.ALL
) -> check.Report:
    """Run all the checks for pull request jobs.

    Args:
        input_: Data required for executing checks.
        policy_document: Describes the policies that should be run.

    Returns:
        Whether the run is authorized based on all the checks.
    """
    if policy_document == UsedPolicy.ALL:
        used_policy_document: MappingProxyType = policy.ALL
    else:
        # Guaranteed to be a dict due to initial if
        policy_document = cast(dict, policy_document)
        if not (policy_report := policy.check(document=policy_document)).result:
            return check.Report(result=check.Result.FAIL, reason=policy_report.reason)
        used_policy_document = MappingProxyType(policy_document)

    # The github_client argument is injected, disabling missing arguments check for this function
    # pylint: disable=no-value-for-parameter
    if (
        policy.enabled(
            job_type=policy.JobType.PULL_REQUEST,
            name=policy.PullRequestProperty.TARGET_BRANCH_PROTECTION,
            policy_document=used_policy_document,
        )
        and (
            target_branch_report := check.target_branch_protection(
                repository_name=input_.repository_name,
                branch_name=input_.target_branch_name,
                source_repository_name=input_.source_repository_name,
            )
        ).result
        == check.Result.FAIL
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

    if (
        policy.enabled(
            job_type=policy.JobType.PULL_REQUEST,
            name=policy.PullRequestProperty.EXECUTE_JOB,
            policy_document=used_policy_document,
        )
        and (
            execute_job_report := check.execute_job(
                repository_name=input_.repository_name,
                source_repository_name=input_.source_repository_name,
                branch_name=input_.source_branch_name,
                commit_sha=input_.commit_sha,
            )
        ).result
        == check.Result.FAIL
    ):
        return execute_job_report

    return check.Report(result=check.Result.PASS, reason=None)


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
    if policy_document == UsedPolicy.ALL:
        used_policy_document: MappingProxyType = policy.ALL
    else:
        # Guaranteed to be a dict due to initial if
        policy_document = cast(dict, policy_document)
        if not (policy_report := policy.check(document=policy_document)).result:
            return check.Report(result=check.Result.FAIL, reason=policy_report.reason)
        used_policy_document = MappingProxyType(policy_document)

    # The github_client argument is injected, disabling missing arguments check for this function
    # pylint: disable=no-value-for-parameter
    if (
        policy.enabled(
            job_type=policy.JobType.WORKFLOW_DISPATCH,
            name=policy.WorkflowDispatchProperty.COLLABORATORS,
            policy_document=used_policy_document,
        )
        and (
            collaborators_report := check.collaborators(repository_name=input_.repository_name)
        ).result
        == check.Result.FAIL
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
    if policy_document == UsedPolicy.ALL:
        used_policy_document: MappingProxyType = policy.ALL
    else:
        # Guaranteed to be a dict due to initial if
        policy_document = cast(dict, policy_document)
        if not (policy_report := policy.check(document=policy_document)).result:
            return check.Report(result=check.Result.FAIL, reason=policy_report.reason)
        used_policy_document = MappingProxyType(policy_document)

    # The github_client argument is injected, disabling missing arguments check for this function
    # pylint: disable=no-value-for-parameter
    if (
        policy.enabled(
            job_type=policy.JobType.PUSH,
            name=policy.PushProperty.COLLABORATORS,
            policy_document=used_policy_document,
        )
        and (
            collaborators_report := check.collaborators(repository_name=input_.repository_name)
        ).result
        == check.Result.FAIL
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
    if policy_document == UsedPolicy.ALL:
        used_policy_document: MappingProxyType = policy.ALL
    else:
        # Guaranteed to be a dict due to initial if
        policy_document = cast(dict, policy_document)
        if not (policy_report := policy.check(document=policy_document)).result:
            return check.Report(result=check.Result.FAIL, reason=policy_report.reason)
        used_policy_document = MappingProxyType(policy_document)

    # The github_client argument is injected, disabling missing arguments check for this function
    # pylint: disable=no-value-for-parameter
    if (
        policy.enabled(
            job_type=policy.JobType.SCHEDULE,
            name=policy.ScheduleProperty.COLLABORATORS,
            policy_document=used_policy_document,
        )
        and (
            collaborators_report := check.collaborators(repository_name=input_.repository_name)
        ).result
        == check.Result.FAIL
    ):
        return collaborators_report

    return check.Report(result=check.Result.PASS, reason=None)
