# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Individual checks used to compose job checks."""

from enum import Enum
from typing import NamedTuple

from github import Github
from github.Branch import Branch
from github.Repository import Repository

from repo_policy_compliance import log
from repo_policy_compliance.comment import remove_quote_lines
from repo_policy_compliance.github_client import get_branch, get_collaborators
from repo_policy_compliance.github_client import inject as inject_github_client

BYPASS_ALLOWANCES_KEY = "bypass_pull_request_allowances"
FAILURE_MESSAGE = (
    "\n"
    "This job has failed to pass a repository policy compliance check as defined in the "
    "https://github.com/canonical/repo-policy-compliance repository. "
    "The specific failure is listed "
    "below. Please update the settings on this project to fix the relevant policy."
    "\n"
)
AUTHORIZATION_STRING_PREFIX = "/canonical/self-hosted-runners/run-workflows"
# write permission in the UI is equivalent to push permission on the GitHub API
EXECUTE_JOB_MESSAGE = (
    "execution not authorized, a comment from a user with write permission or above on the "
    "repository approving the workflow was not found on a PR from a fork, the comment should "
    f"include the string '{AUTHORIZATION_STRING_PREFIX} <commit SHA>' where the commit SHA is the "
    "SHA of the latest commit on the branch"
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


log.setup()


@log.call
def branch_protected(branch: Branch) -> Report:
    """Check that the branch has protections enabled.

    Args:
        branch: The branch to check.

    Returns:
        Whether the branch has protections enabled.
    """
    if not branch.protected:
        return Report(
            result=Result.FAIL,
            reason=(f"{FAILURE_MESSAGE}branch protection not enabled, {branch.name=!r}"),
        )
    return Report(result=Result.PASS, reason=None)


@log.call
def signed_commits_required(branch: Branch) -> Report:
    """Check that the branch requires signed commits.

    Args:
        branch: The branch to check.

    Returns:
        Whether the branch requires signed commits.
    """
    if not branch.get_required_signatures():
        return Report(
            result=Result.FAIL,
            reason=(f"{FAILURE_MESSAGE}signed commits not required, {branch.name=!r}"),
        )
    return Report(result=Result.PASS, reason=None)


@log.call
def unique_commits_signed(
    branch_name: str, other_branch_name: str, repository: Repository
) -> Report:
    """Check that the commits unique to a branch are signed.

    Args:
        branch_name: The name of the branch to check.
        other_branch_name: The name of the branch which will be used to exclude commits.
        repository: The repository the branches are on.

    Returns:
        Whether the unique commits on the branch are signed.
    """
    other_branch_commit_shas = {
        commit.sha for commit in repository.get_commits(sha=other_branch_name)
    }
    branch_commits = repository.get_commits(sha=branch_name)
    unsigned_unique_branch_commits = (
        commit
        for commit in branch_commits
        if commit.sha not in other_branch_commit_shas
        and not commit.commit.raw_data["verification"]["verified"]
    )
    if first_unsigned_commit := next(unsigned_unique_branch_commits, None):
        return Report(
            result=Result.FAIL,
            reason=(
                f"{FAILURE_MESSAGE}"
                f"commit is not signed, {branch_name=!r}, {first_unsigned_commit.sha=!r}"
            ),
        )

    return Report(result=Result.PASS, reason=None)


@inject_github_client
@log.call
def target_branch_protection(
    github_client: Github, repository_name: str, branch_name: str, source_repository_name: str
) -> Report:
    """Check that the target branch has appropriate protections.

    Args:
        github_client: The client to be used for GitHub API interactions.
        repository_name: The name of the repository to run the check on.
        branch_name: The name of the branch to check.
        source_repository_name: The name of the repository that contains the source branch.

    Returns:
        Whether the branch has appropriate protections.
    """
    branch = get_branch(
        github_client=github_client, repository_name=repository_name, branch_name=branch_name
    )

    if (protected_report := branch_protected(branch=branch)).result == Result.FAIL:
        return protected_report

    # Only check for whether reviews are required for PRs from a fork or where the target branch is
    # the default branch
    repository = github_client.get_repo(repository_name)
    if branch_name == repository.default_branch or repository_name != source_repository_name:
        protection = branch.get_protection()
        pull_request_reviews = protection.required_pull_request_reviews
        if pull_request_reviews is None:
            return Report(
                result=Result.FAIL,
                reason=(
                    f"{FAILURE_MESSAGE}pull request reviews are not required, {branch_name=!r}"
                ),
            )
        if not pull_request_reviews.dismiss_stale_reviews:
            return Report(
                result=Result.FAIL,
                reason=(f"{FAILURE_MESSAGE}stale reviews are not dismissed, {branch_name=!r}"),
            )
        # Check for bypass allowances
        bypass_allowances = pull_request_reviews.raw_data.get(BYPASS_ALLOWANCES_KEY, {})
        if any(bypass_allowances.get(key, []) for key in ("users", "teams", "apps")):
            return Report(
                result=Result.FAIL,
                reason=(
                    f"{FAILURE_MESSAGE}pull request reviews can be bypassed, {branch_name=!r}"
                ),
            )

    if (signed_commits_report := signed_commits_required(branch=branch)).result == Result.FAIL:
        return signed_commits_report

    return Report(result=Result.PASS, reason=None)


@inject_github_client
@log.call
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

    branch = get_branch(
        github_client=github_client, repository_name=repository_name, branch_name=branch_name
    )

    if (protected_report := branch_protected(branch=branch)).result == Result.FAIL:
        return protected_report

    if (signed_commits_report := signed_commits_required(branch=branch)).result == Result.FAIL:
        return signed_commits_report

    repository = github_client.get_repo(repository_name)
    if (
        unique_commits_signed_report := unique_commits_signed(
            branch_name=branch_name,
            other_branch_name=target_branch_name,
            repository=repository,
        )
    ).result == Result.FAIL:
        return unique_commits_signed_report

    return Report(result=Result.PASS, reason=None)


@inject_github_client
@log.call
def branch_protection(
    github_client: Github,
    repository_name: str,
    branch_name: str,
    commit_sha: str,
) -> Report:
    """Check that the branch has appropriate protections.

    Args:
        github_client: The client to be used for GitHub API interactions.
        repository_name: The name of the repository to run the check on.
        branch_name: The name of the branch to check.
        commit_sha: The SHA of the commit that the workflow run is on.

    Returns:
        Whether the branch has appropriate protections.
    """
    branch = get_branch(
        github_client=github_client, repository_name=repository_name, branch_name=branch_name
    )

    if (protected_report := branch_protected(branch=branch)).result == Result.FAIL:
        return protected_report

    if (signed_commits_report := signed_commits_required(branch=branch)).result == Result.FAIL:
        return signed_commits_report

    # Check that the commit the job is running on is signed
    repository = github_client.get_repo(repository_name)
    commit = repository.get_commit(sha=commit_sha)
    if not commit.commit.raw_data["verification"]["verified"]:
        return Report(
            result=Result.FAIL,
            reason=(
                f"{FAILURE_MESSAGE}"
                f"commit the job is running on is not signed, {branch_name=!r}, {commit_sha=!r}"
            ),
        )

    return Report(result=Result.PASS, reason=None)


@inject_github_client
@log.call
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
                f"{FAILURE_MESSAGE}"
                "the repository includes outside collaborators with higher permissions than read,"
                f"{higher_permission_logins=!r}"
            ),
        )

    return Report(result=Result.PASS, reason=None)


def _branch_external_fork(
    repository_name: str, source_repository_name: str, push_logins: set[str]
) -> bool:
    """Check whether a branch is an external fork.

    A external fork is a fork that is not owned by a user who has push or above permission on the
    repository.

    Args:
        repository_name: The name of the repository to run the check on.
        source_repository_name: The name of the repository that contains the source branch.
        push_logins: The logins from users with push or above permission or above on the
            repository.

    Returns:
        Whether the branch is from a external fork.
    """
    if repository_name == source_repository_name:
        return False

    # Check if the owner of the fork also has push or higher permission
    if source_repository_name.split("/")[0] in push_logins:
        return False

    return True


@inject_github_client
@log.call
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
    repository = github_client.get_repo(repository_name)
    push_logins = {
        collaborator["login"]
        for collaborator in get_collaborators(
            repository=repository, permission="push", affiliation="all"
        )
    }
    if not _branch_external_fork(
        repository_name=repository_name,
        source_repository_name=source_repository_name,
        push_logins=push_logins,
    ):
        return Report(result=Result.PASS, reason=None)

    # Retrieve PR for the branch
    pulls = repository.get_pulls(state="open")
    pull_for_branch = next((pull for pull in pulls if pull.head.ref == branch_name), None)
    if not pull_for_branch:
        return Report(
            result=Result.FAIL,
            reason=(f"{FAILURE_MESSAGE}no open pull requests for branch {branch_name}"),
        )

    # Retrieve comments on the PR
    comments = pull_for_branch.get_issue_comments()
    if not comments.totalCount:
        return Report(
            result=Result.FAIL,
            reason=(
                f"{FAILURE_MESSAGE}"
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
                f"{FAILURE_MESSAGE}"
                f"authorization comment not found on PR, expected: {authorization_string} - "
                f"{EXECUTE_JOB_MESSAGE}, {branch_name=}, {commit_sha=}, {pull_for_branch.number=}"
            ),
        )

    # Check that the commenter has push or above permissions, this permission is called write in
    # the UI
    if not any(comment.user.login in push_logins for comment in authorization_comments):
        return Report(
            result=Result.FAIL,
            reason=(
                f"{FAILURE_MESSAGE}"
                "authorization comment from a user who does not have write permission or above - "
                f"{EXECUTE_JOB_MESSAGE}, {branch_name=}, {commit_sha=}, {pull_for_branch.number=}"
            ),
        )

    return Report(result=Result.PASS, reason=None)
