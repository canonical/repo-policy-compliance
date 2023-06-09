# Copyright 2023 Canonical Ltd.
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

    Attrs:
        PULL_REQUEST: Policies for pull requests.
        WORKFLOW_DISPATCH: Policies for workflow dispatch jobs.
    """

    PULL_REQUEST = "pull_request"
    WORKFLOW_DISPATCH = "workflow_dispatch"


class PullRequestProperty(str, Enum):
    """The names of the properties for the pull request portion of the policy document.

    Attrs:
        TARGET_BRANCH_PROTECTION: Branch protection for the target branch.
        SOURCE_BRANCH_PROTECTION: Branch protection for the source branch.
        COLLABORATORS: Particupants on a repository.
        EXECUTE_JOB: Whether a job should be executed.
    """

    TARGET_BRANCH_PROTECTION = "target_branch_protection"
    SOURCE_BRANCH_PROTECTION = "source_branch_protection"
    COLLABORATORS = "collaborators"
    EXECUTE_JOB = "execute_job"


class WorkflowDispatchProperty(str, Enum):
    """The names of the properties for the workflow dispatch portion of the policy document.

    Attrs:
        BRANCH_PROTECTION: Branch protection for the branch.
        COLLABORATORS: Particupants on a repository.
    """

    BRANCH_PROTECTION = "branch_protection"
    COLLABORATORS = "collaborators"


# Using MappingProxyType to make these immutable
ENABLED_KEY = "enabled"
ENABLED_RULE = MappingProxyType({ENABLED_KEY: True})
ALL = MappingProxyType(
    {
        JobType.PULL_REQUEST: {prop: ENABLED_RULE for prop in PullRequestProperty},
        JobType.WORKFLOW_DISPATCH: {prop: ENABLED_RULE for prop in WorkflowDispatchProperty},
    }
)


class Report(NamedTuple):
    """Reports the result of checking whether a policy document is valid.

    Attrs:
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
    name: PullRequestProperty | WorkflowDispatchProperty,
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
    return (
        job_type in policy_document
        and name in policy_document[job_type]
        and policy_document[job_type][name][ENABLED_KEY]
    )
