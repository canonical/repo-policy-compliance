# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Module for the policy document."""

from pathlib import Path
from typing import NamedTuple

import yaml
from jsonschema import ValidationError, validate


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
