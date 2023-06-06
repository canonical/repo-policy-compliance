# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Module for the policy document."""

from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import NamedTuple

import yaml
from jsonschema import ValidationError, validate


class Property(str, Enum):
    """The result of a check.

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


_ENABLED_RULE = MappingProxyType({"enabled": True})
ALL = MappingProxyType({prop: _ENABLED_RULE for prop in Property})


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
        return Report(result=False, reason=f"invalid policy document,{exc=} ")
