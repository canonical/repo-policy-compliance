# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Library for checking that GitHub repos comply with policy."""

from enum import Enum
from types import MappingProxyType
from typing import NamedTuple

from github import Github
from github.Branch import Branch

from . import policy
from .comment import remove_quote_lines
from .github_client import get_collaborators
from .github_client import inject as inject_github_client

BYPASS_ALLOWANCES_KEY = "bypass_pull_request_allowances"
AUTHORIZATION_STRING_PREFIX = "/canonical/self-hosted-runners/run-workflows"
EXECUTE_JOB_MESSAGE = (
    "execution not authorized, a comment from a maintainer or above on the repository approving "
    "the workflow was not found on a PR from a fork, the comment should include the string "
    f"'{AUTHORIZATION_STRING_PREFIX} <commit SHA>' where the commit SHA is the SHA of the latest "
    "commit on the branch"
)


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


class All:
    """Indicate that all policies should be checked."""


ALL = All()


def all_(
    repository_name: str,
    source_repository_name: str,
    target_branch_name: str,
    source_branch_name: str,
    commit_sha: str,
    policy_document: dict | All = ALL,
) -> Report:
    """Run all the checks.

    Args:
        repository_name: The name of the repository to run the check on.
        source_repository_name: The name of the repository that has the source branch.
        target_branch_name: The name of the branch that is targeted by the PR.
        source_branch_name: The name of the branch that contains the commits to be merged.
        commit_sha: The SHA of the commit that the workflow run is on.

    Returns:
        Whether the run is authorized based on all the checks.
    """
    if isinstance(policy_document, All):
        used_policy_document: MappingProxyType = policy.ALL
    else:
        if not (policy_report := policy.check(document=policy_document)).result:
            return Report(result=Result.FAIL, reason=policy_report.reason)
        used_policy_document = MappingProxyType(policy_document)

    # The github_client argument is injected, disabling missing arguments check for this function
    # pylint: disable=no-value-for-parameter
    if (
        policy.Property.TARGET_BRANCH_PROTECTION in used_policy_document
        and used_policy_document[policy.Property.TARGET_BRANCH_PROTECTION]["enabled"]
        and (
            target_branch_report := target_branch_protection(
                repository_name=repository_name, branch_name=target_branch_name
            )
        ).result
        == Result.FAIL
    ):
        return target_branch_report

    if (
        policy.Property.SOURCE_BRANCH_PROTECTION in used_policy_document
        and used_policy_document[policy.Property.SOURCE_BRANCH_PROTECTION]["enabled"]
        and (
            source_branch_report := source_branch_protection(
                repository_name=repository_name,
                source_repository_name=source_repository_name,
                branch_name=source_branch_name,
                target_branch_name=target_branch_name,
            )
        ).result
        == Result.FAIL
    ):
        return source_branch_report

    if (
        policy.Property.COLLABORATORS in used_policy_document
        and used_policy_document[policy.Property.COLLABORATORS]["enabled"]
        and (collaborators_report := collaborators(repository_name=repository_name)).result
        == Result.FAIL
    ):
        return collaborators_report

    if (
        policy.Property.EXECUTE_JOB in used_policy_document
        and used_policy_document[policy.Property.EXECUTE_JOB]["enabled"]
        and (
            execute_job_report := execute_job(
                repository_name=repository_name,
                source_repository_name=source_repository_name,
                branch_name=source_branch_name,
                commit_sha=commit_sha,
            )
        ).result
        == Result.FAIL
    ):
        return execute_job_report

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
    github_client: Github,
    repository_name: str,
    source_repository_name: str,
    branch_name: str,
    target_branch_name: str,
) -> Report:
    """Check that the source branch has appropriate protections.

    Args:
        github_client: The client to be used for GitHub API interactions.
        repository_name: The name of the repository to run the check on.
        source_repository_name: The name of the repository that contains the source branch.
        branch_name: The name of the branch to check.
        target_branch_name: The name of the branch that the source branch is proposed to be merged
            into.

    Returns:
        Whether the branch has appropriate protections.
    """
    # Check for fork
    if source_repository_name != repository_name:
        return Report(result=Result.PASS, reason=None)

    branch = _get_branch(
        github_client=github_client, repository_name=repository_name, branch_name=branch_name
    )

    if (protected_report := _check_branch_protected(branch=branch)).result == Result.FAIL:
        return protected_report

    if (
        signed_commits_report := _check_signed_commits_required(branch=branch)
    ).result == Result.FAIL:
        return signed_commits_report

    # Check that all commits unique to the source branch are signed
    repository = github_client.get_repo(repository_name)
    target_branch_commit_shas = {
        commit.sha for commit in repository.get_commits(sha=target_branch_name)
    }
    source_branch_commits = repository.get_commits(sha=branch_name)
    unique_source_branch_commits = (
        commit for commit in source_branch_commits if commit.sha not in target_branch_commit_shas
    )
    unsigned_unique_source_branch_commits = (
        commit
        for commit in unique_source_branch_commits
        if not commit.commit.raw_data["verification"]["verified"]
    )
    if first_unsigned_commit := next(unsigned_unique_source_branch_commits, None):
        return Report(
            result=Result.FAIL,
            reason=f"commit is not signed, {branch.name=!r}, {first_unsigned_commit.sha=!r}",
        )

    return Report(result=Result.PASS, reason=None)


@inject_github_client
def collaborators(github_client: Github, repository_name: str) -> Report:
    """Check that no outside contributors have higher access than read.

    Args:
        github_client: The client to be used for GitHub API interactions.
        repository_name: The name of the repository to run the check on.

    Returns:
        Whether there are any outside collaborators with higher than read permissions.
    """
    repository = github_client.get_repo(repository_name)
    outside_collaborators = get_collaborators(
        repository=repository, permission="triage", affiliation="outside"
    )

    higher_permission_logins = tuple(
        collaborator["login"]
        for collaborator in outside_collaborators
        if collaborator["role_name"] != "read"
    )

    if higher_permission_logins:
        return Report(
            result=Result.FAIL,
            reason=(
                "the repository includes outside collaborators with higher permissions than read,"
                f"{higher_permission_logins=!r}"
            ),
        )

    return Report(result=Result.PASS, reason=None)


@inject_github_client
def execute_job(
    github_client: Github,
    repository_name: str,
    source_repository_name: str,
    branch_name: str,
    commit_sha: str,
) -> Report:
    """Check that the execution of the workflow for a SHA has been granted for a PR from a fork.

    Args:
        github_client: The client to be used for GitHub API interactions.
        repository_name: The name of the repository to run the check on.
        source_repository_name: The name of the repository that contains the source branch.
        branch_name: The name of the branch that has the PR.
        commit_sha: The SHA of the commit that the workflow run is on.

    Returns:
        Whether the workflow run has been approved for the commit SHA.
    """
    # Not from a forked repository
    if repository_name == source_repository_name:
        return Report(result=Result.PASS, reason=None)

    # Retrieve PR for the branch
    repository = github_client.get_repo(repository_name)
    pulls = repository.get_pulls(state="open")
    pull_for_branch = next((pull for pull in pulls if pull.head.ref == branch_name), None)
    if not pull_for_branch:
        return Report(result=Result.FAIL, reason=f"no open pull requests for branch {branch_name}")

    # Retrieve comments on the PR
    comments = pull_for_branch.get_issue_comments()
    if not comments.totalCount:
        return Report(
            result=Result.FAIL,
            reason=(
                f"no comment found on PR - {EXECUTE_JOB_MESSAGE}, {branch_name=}, {commit_sha=} "
                f"{pull_for_branch.number=}"
            ),
        )

    # Check for authroization comment
    authorization_string = f"{AUTHORIZATION_STRING_PREFIX} {commit_sha}"
    authorization_comments = tuple(
        comment for comment in comments if authorization_string in remove_quote_lines(comment.body)
    )
    if not authorization_comments:
        return Report(
            result=Result.FAIL,
            reason=(
                f"authorization comment not found on PR, expected: {authorization_string} - "
                f"{EXECUTE_JOB_MESSAGE}, {branch_name=}, {commit_sha=}, {pull_for_branch.number=}"
            ),
        )

    # Check that the commenter has maintain or above permissions
    maintain_logins = {
        collaborator["login"]
        for collaborator in get_collaborators(
            repository=repository, permission="maintain", affiliation="all"
        )
    }
    if not any(comment.user.login in maintain_logins for comment in authorization_comments):
        return Report(
            result=Result.FAIL,
            reason=(
                f"authorization comment from a user that is not a maintainer or above - "
                f"{EXECUTE_JOB_MESSAGE}, {branch_name=}, {commit_sha=}, {pull_for_branch.number=}"
            ),
        )

    return Report(result=Result.PASS, reason=None)
