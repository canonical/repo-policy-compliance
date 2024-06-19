# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Individual checks used to compose job checks."""

import dataclasses
import functools
from enum import Enum
from typing import Callable, NamedTuple, ParamSpec, TypeVar

from github import Github
from github.Branch import Branch
from github.Repository import Repository

from repo_policy_compliance import log
from repo_policy_compliance.comment import remove_quote_lines
from repo_policy_compliance.exceptions import (
    ConfigurationError,
    GithubClientError,
    RetryableGithubClientError,
)
from repo_policy_compliance.github_client import (
    get_branch,
    get_collaborator_permission,
    get_collaborators,
)
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

    Attributes:
        PASS: The check passed.
        FAIL: The check failed.
        ERROR: There was an error while performing the check.
    """

    # Bandit thinks pass is for password
    PASS = "pass"  # nosec
    FAIL = "fail"
    ERROR = "error"


class Report(NamedTuple):
    """Reports the result of a check.

    Attributes:
        result: The check result.
        reason: If the check failed, the reason why it failed.
    """

    result: Result
    reason: str | None


log.setup()

P = ParamSpec("P")
R = TypeVar("R")


def github_exceptions_to_fail_report(func: Callable[P, R]) -> Callable[P, R | Report]:
    """Catch exceptions and convert to failed report with reason.

    Args:
        func: The function to catch the GithubClient exceptions for.

    Returns:
        The function where any exceptions raised would be converted to a failed result.
    """

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R | Report:
        """Replace function.

        Args:
            args: The positional arguments passed to the original method.
            kwargs: The keywords arguments passed to the original method.

        Returns:
            Failed result report if any exceptions were raised. The return value after calling the
            wrapped function otherwise.
        """
        try:
            return func(*args, **kwargs)
        except RetryableGithubClientError:
            return Report(
                result=Result.ERROR,
                reason="Checking repository compliance policy failed due to Github rate limit "
                "exceeded. Please wait before retrying",
            )
        except GithubClientError:
            return Report(
                result=Result.ERROR,
                reason="Something went wrong while checking repository compliance policy. "
                "Please contact the operator.",
            )
        except ConfigurationError:
            return Report(
                result=Result.ERROR,
                reason="Something went wrong while configuring repository compliance policy "
                "check. Please contact the operator.",
            )

    return wrapper


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


@github_exceptions_to_fail_report
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
        # Check for bypass allowances
        bypass_allowances = pull_request_reviews.raw_data.get(BYPASS_ALLOWANCES_KEY, {})
        if any(bypass_allowances.get(key, []) for key in ("users", "teams", "apps")):
            return Report(
                result=Result.FAIL,
                reason=(
                    f"{FAILURE_MESSAGE}pull request reviews can be bypassed, {branch_name=!r}"
                ),
            )

    return Report(result=Result.PASS, reason=None)


@github_exceptions_to_fail_report
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


@dataclasses.dataclass
class JobMetadata:
    """Information about the target job run to check for authorization.

    Attrs:
        branch_name: The branch name of the target repository.
        commit_sha: The commit SHA of the job run.
        repository_name: The repository running the check.
        fork_or_branch_repository_name: The repository of the branch/fork.
    """

    branch_name: str
    commit_sha: str
    repository_name: str
    fork_or_branch_repository_name: str


@github_exceptions_to_fail_report
@inject_github_client
@log.call
def execute_job(github_client: Github, job_metadata: JobMetadata) -> Report:
    """Check that the execution of the workflow for a SHA has been granted for a PR from a fork.

    Args:
        github_client: The client to be used for GitHub API interactions.
        job_metadata: Information about the target job run to check for authorization.

    Returns:
        Whether the workflow run has been approved for the commit SHA.
    """
    # Not a fork (is a branch) if source and target repositories are the same. Users that can
    # create branches already have write permissions or above.
    if job_metadata.repository_name == job_metadata.fork_or_branch_repository_name:
        return Report(result=Result.PASS, reason=None)

    if _check_fork_collaborator(
        repository=(repository := github_client.get_repo(job_metadata.repository_name)),
        fork_repository_name=job_metadata.fork_or_branch_repository_name,
    ):
        return Report(result=Result.PASS, reason=None)

    return _check_authorization_comment(
        repository=repository,
        branch_name=job_metadata.branch_name,
        commit_sha=job_metadata.commit_sha,
    )


def _check_fork_collaborator(repository: Repository, fork_repository_name: str) -> bool:
    """Check whether the fork's owner is authorized as a collaborator.

    A user is authorized if he is a collaborator with write permissions and above.

    Args:
        repository: The repository to run the check on.
        fork_repository_name: The name of the forked repository.

    Returns:
        Whether the fork owner has write or above privileges as a collaborator.
    """
    fork_username = fork_repository_name.split("/")[0]

    # Check if owner of the fork already has push or higher permission (not an external user)
    fork_user_permission = get_collaborator_permission(repository, fork_username)
    return fork_user_permission in ("admin", "write")


def _check_authorization_comment(
    repository: Repository, branch_name: str, commit_sha: str
) -> Report:
    """Check whether a comment from a person with collaborator status has authorized a run with \
        an authorization comment for a particular commit.

    Args:
        repository: The repository to run the check on.
        branch_name: The name of the branch that has the PR.
        commit_sha: The SHA of the commit that the workflow run is on.

    Returns:
        A report whether the check has succeeded or failed.
    """
    push_logins = {
        collaborator["login"]
        for collaborator in get_collaborators(
            repository=repository, permission="push", affiliation="all"
        )
    }

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

    # Check for authorization comment
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


@github_exceptions_to_fail_report
@inject_github_client
@log.call
def pull_request_disallow_fork(github_client: Github, job_metadata: JobMetadata) -> Report:
    """Check that the pull request from 3rd party is disallowed.

    Args:
        github_client: The client to be used for GitHub API interactions.
        job_metadata: Information about the target job run to check for authorization.

    Returns:
        Whether the pull_request run is authorized as a non-3rd party fork or source repository \
        run.
    """
    if job_metadata.repository_name == job_metadata.fork_or_branch_repository_name:
        return Report(result=Result.PASS, reason=None)

    if _check_fork_collaborator(
        repository=github_client.get_repo(job_metadata.repository_name),
        fork_repository_name=job_metadata.fork_or_branch_repository_name,
    ):
        return Report(result=Result.PASS, reason=None)

    return Report(
        result=Result.FAIL,
        reason=(
            f"{FAILURE_MESSAGE}"
            "The owner of the fork repository does not have collaborator (write/admin) privileges."
        ),
    )
