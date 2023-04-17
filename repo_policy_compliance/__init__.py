# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Library for checking that GitHub repos comply with policy."""

from enum import Enum
from typing import NamedTuple

from github import Github

from . import github_client


class Result(str, Enum):
    """The result of a check.

    Attrs:
        PASS: The check passed.
        FAIL: The check failed.
    """

    PASS = "pass"
    FAIL = "fail"


class Report(NamedTuple):
    """
    Reports the result of a check.

    Attrs:
        result: The check result.
        reason: If the check failed, the reason why it failed.
    """

    result: Result
    reason: str | None


@github_client.inject
def target_branch_protection(
    github_client: Github, repository_name: str, branch_name: str
) -> Report:
    """Check that the target branch has appropriate protections.

    Args:
        github_client: The client to be used for GitHub API interactions.
        repository_name: The name of the repository to run the check on.
        branch_name: The name of the branch to check.

    Returns:
        Whether the branch has appropriate protections.

    """
