# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Module for the policy document."""

from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import NamedTuple

import yaml
from jsonschema import ValidationError, validate


class JobType(str, Enum):
    """The names of the properties for the policy document.

    Attributes:
        PULL_REQUEST: Policies for pull requests.
        WORKFLOW_DISPATCH: Policies for workflow dispatch jobs.
        PUSH: Policies for push jobs.
        SCHEDULE: Policies for scheduled jobs.
    """

    PULL_REQUEST = "pull_request"
    WORKFLOW_DISPATCH = "workflow_dispatch"
    PUSH = "push"
    SCHEDULE = "schedule"


class PullRequestProperty(str, Enum):
    """The names of the properties for the pull request portion of the policy document.

    Attributes:
        TARGET_BRANCH_PROTECTION: Branch protection for the target branch.
        COLLABORATORS: Participants on a repository.
        DISALLOW_FORK: Whether a forked repository should not be allowed to run jobs.
        EXECUTE_JOB: Whether a job should be executed.
    """

    TARGET_BRANCH_PROTECTION = "target_branch_protection"
    COLLABORATORS = "collaborators"
    DISALLOW_FORK = "disallow_fork"
    EXECUTE_JOB = "execute_job"


class BranchJobProperty(str, Enum):
    """The names of the properties for jobs running on a branch portion of the policy document.

    Attributes:
        COLLABORATORS: Participants on a repository.
    """

    COLLABORATORS = "collaborators"


WorkflowDispatchProperty = BranchJobProperty
PushProperty = BranchJobProperty
ScheduleProperty = BranchJobProperty


# Using MappingProxyType to make these immutable
ENABLED_KEY = "enabled"
ENABLED_RULE = MappingProxyType({ENABLED_KEY: True})
DISABLED_RULE = MappingProxyType({ENABLED_KEY: False})
_DEFAULT_POLICY_MAP = {
    JobType.WORKFLOW_DISPATCH: {prop: ENABLED_RULE for prop in WorkflowDispatchProperty},
    JobType.PUSH: {prop: ENABLED_RULE for prop in PushProperty},
    JobType.SCHEDULE: {prop: ENABLED_RULE for prop in ScheduleProperty},
}
ALL = MappingProxyType(
    {
        JobType.PULL_REQUEST: {prop: ENABLED_RULE for prop in PullRequestProperty},
        **_DEFAULT_POLICY_MAP,
    }
)
ALLOW_FORKS = MappingProxyType(
    {
        JobType.PULL_REQUEST: {
            prop: (ENABLED_RULE if prop != PullRequestProperty.DISALLOW_FORK else DISABLED_RULE)
            for prop in PullRequestProperty
        },
        **_DEFAULT_POLICY_MAP,
    }
)


class Report(NamedTuple):
    """Reports the result of checking whether a policy document is valid.

    Attributes:
        result: The check result.
        reason: If the check failed, the reason why it failed.
    """

    result: bool
    reason: str | None


def check(document: dict) -> Report:
    """Check that a policy document is valid.

    Args:
        document: The dictionary containing the policy to check.

    Returns:
        Whether the policy document is valid.
    """
    schema = yaml.safe_load(
        (Path(__file__).parent / Path("policy_schema.yaml")).read_text(encoding="utf-8")
    )

    try:
        validate(instance=document, schema=schema)
        return Report(result=True, reason=None)
    except ValidationError as exc:
        return Report(result=False, reason=f"invalid policy document, {exc=}")


def enabled(
    job_type: JobType,
    name: PullRequestProperty | WorkflowDispatchProperty | PushProperty | ScheduleProperty,
    policy_document: MappingProxyType,
) -> bool:
    """Check whether a given policy is enabled.

    Args:
        job_type: The type of the job to check.
        name: The property name of the policy.
        policy_document: Describes the policies that should be run.

    Returns:
        Whether the policy is enabled in the document.
    """
    if job_type not in policy_document or name not in policy_document[job_type]:
        return True
    return (
        job_type in policy_document
        and name in policy_document[job_type]
        and policy_document[job_type][name][ENABLED_KEY]
    )
