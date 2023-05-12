# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Library for checking that GitHub repos comply with policy."""

from enum import Enum
from typing import NamedTuple

from github import Github
from github.Branch import Branch

from .github_client import inject as inject_github_client

BYPASS_ALLOWANCES_KEY = "bypass_pull_request_allowances"


class Result(str, Enum):
    """The result of a check.

    Attrs:
        PASS: The check passed.
        FAIL: The check failed.
    """

    # Bandit thinks pass is for password
    PASS = "pass"  # nosec
    FAIL = "fail"


class Report(NamedTuple):
    """Reports the result of a check.

    Attrs:
        result: The check result.
        reason: If the check failed, the reason why it failed.
    """

    result: Result
    reason: str | None


def _get_branch(github_client: Github, repository_name: str, branch_name: str) -> Branch:
    """Get the branch for the check.

    Args:
        github_client: The client to be used for GitHub API interactions.
        repository_name: The name of the repository to run the check on.
        branch_name: The name of the branch to check.

    Returns:
        The requested branch.
    """
    repository = github_client.get_repo(repository_name)
    return repository.get_branch(branch_name)


def _check_branch_protected(branch: Branch) -> Report:
    """Check that the branch has protections enabled.

    Args:
        branch: The branch to check.

    Returns:
        Whether the branch has protections enabled.
    """
    if not branch.protected:
        return Report(
            result=Result.FAIL, reason=f"branch protection not enabled, {branch.name=!r}"
        )
    return Report(result=Result.PASS, reason=None)


def _check_signed_commits_required(branch: Branch) -> Report:
    """Check that the branch requires signed commits.

    Args:
        branch: The branch to check.

    Returns:
        Whether the branch requires signed commits.
    """
    if not branch.get_required_signatures():
        return Report(result=Result.FAIL, reason=f"signed commits not required, {branch.name=!r}")
    return Report(result=Result.PASS, reason=None)


@inject_github_client
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
    branch = _get_branch(
        github_client=github_client, repository_name=repository_name, branch_name=branch_name
    )

    if (protected_report := _check_branch_protected(branch=branch)).result == Result.FAIL:
        return protected_report

    protection = branch.get_protection()

    pull_request_reviews = protection.required_pull_request_reviews
    if not pull_request_reviews.require_code_owner_reviews:
        return Report(
            result=Result.FAIL,
            reason=f"codeowner pull request reviews are not required, {branch_name=!r}",
        )
    if not pull_request_reviews.dismiss_stale_reviews:
        return Report(
            result=Result.FAIL,
            reason=f"stale reviews are not dismissed, {branch_name=!r}",
        )
    # Check for bypass allowances
    bypass_allowances = pull_request_reviews.raw_data.get(BYPASS_ALLOWANCES_KEY, {})
    if any(bypass_allowances.get(key, []) for key in ("users", "teams", "apps")):
        return Report(
            result=Result.FAIL,
            reason=f"pull request reviews can be bypassed, {branch_name=!r}",
        )

    if (
        signed_commits_report := _check_signed_commits_required(branch=branch)
    ).result == Result.FAIL:
        return signed_commits_report

    return Report(result=Result.PASS, reason=None)


@inject_github_client
def source_branch_protection(
    github_client: Github, repository_name: str, branch_name: str
) -> Report:
    """Check that the source branch has appropriate protections.

    Args:
        github_client: The client to be used for GitHub API interactions.
        repository_name: The name of the repository to run the check on.
        branch_name: The name of the branch to check.

    Returns:
        Whether the branch has appropriate protections.
    """
    branch = _get_branch(
        github_client=github_client, repository_name=repository_name, branch_name=branch_name
    )

    if (protected_report := _check_branch_protected(branch=branch)).result == Result.FAIL:
        return protected_report

    if (
        signed_commits_report := _check_signed_commits_required(branch=branch)
    ).result == Result.FAIL:
        return signed_commits_report

    return Report(result=Result.PASS, reason=None)
