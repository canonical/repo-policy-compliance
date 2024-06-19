# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Tests for the execute_job function."""

# The tests in this file have to rely on many fixtures, need access to private function to test it
# pylint: disable=too-many-arguments

from uuid import uuid4

import pytest
from github.Branch import Branch
from github.Commit import Commit
from github.PullRequest import PullRequest
from github.Repository import Repository

import repo_policy_compliance
from repo_policy_compliance.check import (
    AUTHORIZATION_STRING_PREFIX,
    JobMetadata,
    Result,
    execute_job,
)
from tests import assert_


def test_execute_job_not_fork():
    """
    arrange: given a repository that is not a fork.
    act: when execute_job is called.
    assert: a pass report is returned.
    """
    # The github_client is injected
    report = execute_job(  # pylint: disable=no-value-for-parameter
        job_metadata=JobMetadata(
            repository_name="test_repository",
            fork_or_branch_repository_name="test_repository",
            branch_name="test/branchname",
            commit_sha="test_commit_sha",
        )
    )

    assert report.result == Result.PASS


@pytest.mark.parametrize(
    "forked_github_branch",
    [f"test-branch/execute-job/no-pr/{uuid4()}"],
    indirect=True,
)
@pytest.mark.usefixtures("make_fork_from_collaborator")
def test_fail_forked_no_pr(
    forked_github_repository: Repository, forked_github_branch: Branch, github_repository_name: str
):
    """
    arrange: given a fork branch that doesn't have a PR
    act: when execute_job is called
    assert: then a fail report is returned.
    """
    # The github_client is injected
    report = execute_job(  # pylint: disable=no-value-for-parameter
        job_metadata=JobMetadata(
            repository_name=github_repository_name,
            fork_or_branch_repository_name=forked_github_repository.full_name,
            branch_name=forked_github_branch.name,
            commit_sha=forked_github_branch.commit.sha,
        )
    )

    assert report.result == Result.FAIL
    assert report.reason, "expected a reason along with the fail result"
    assert_.substrings_in_string(("no", "pull request"), report.reason)


@pytest.mark.parametrize(
    "forked_github_branch",
    [f"test-branch/execute-job/no-comment-on-pr/{uuid4()}"],
    indirect=True,
)
@pytest.mark.usefixtures("pr_from_forked_github_branch", "make_fork_from_collaborator")
def test_fail_forked_no_comment_on_pr(
    forked_github_repository: Repository, forked_github_branch: Branch, github_repository_name: str
):
    """
    arrange: given a fork branch that has a PR without any comments
    act: when execute_job is called
    assert: then a fail report is returned.
    """
    # The github_client is injected
    report = execute_job(  # pylint: disable=no-value-for-parameter
        job_metadata=JobMetadata(
            repository_name=github_repository_name,
            fork_or_branch_repository_name=forked_github_repository.full_name,
            branch_name=forked_github_branch.name,
            commit_sha=forked_github_branch.commit.sha,
        )
    )

    assert report.result == Result.FAIL
    assert report.reason, "expected a reason along with the fail result"
    assert_.substrings_in_string(("not", "authorized", "no comment"), report.reason)


@pytest.mark.parametrize(
    "forked_github_branch",
    [f"test-branch/execute-job/wrong-comment-on-pr/{uuid4()}"],
    indirect=True,
)
@pytest.mark.usefixtures("make_fork_from_collaborator")
def test_fail_forked_wrong_comment_on_pr(
    forked_github_repository: Repository,
    github_repository: Repository,
    forked_github_branch: Branch,
    github_repository_name: str,
    commit_on_forked_github_branch: Commit,
    pr_from_forked_github_branch: PullRequest,
):
    """
    arrange: given a fork branch that has a PR with the wrong comment on it
    act: when execute_job is called
    assert: then a fail report is returned.
    """
    pr_issue = github_repository.get_issue(pr_from_forked_github_branch.number)
    pr_issue.create_comment("comment 1")

    # The github_client is injected
    report = execute_job(  # pylint: disable=no-value-for-parameter
        job_metadata=JobMetadata(
            repository_name=github_repository_name,
            fork_or_branch_repository_name=forked_github_repository.full_name,
            branch_name=forked_github_branch.name,
            commit_sha=commit_on_forked_github_branch.sha,
        )
    )

    assert report.result == Result.FAIL
    assert report.reason, "expected a reason along with the fail result"
    assert_.substrings_in_string(("not", "authorized", "string"), report.reason)


@pytest.mark.parametrize(
    "forked_github_branch",
    [f"test-branch/execute-job/wrong-commit-sha-on-pr/{uuid4()}"],
    indirect=True,
)
@pytest.mark.usefixtures("make_fork_from_collaborator")
def test_fail_forked_wrong_commit_sha_on_pr(
    forked_github_repository: Repository,
    github_repository: Repository,
    forked_github_branch: Branch,
    github_repository_name: str,
    commit_on_forked_github_branch: Commit,
    pr_from_forked_github_branch: PullRequest,
):
    """
    arrange: given a fork branch that has a PR with the right comment but wrong commit SHA
    act: when execute_job is called
    assert: then a fail report is returned.
    """
    pr_issue = github_repository.get_issue(pr_from_forked_github_branch.number)
    main_branch = forked_github_repository.get_branch(forked_github_repository.default_branch)
    pr_issue.create_comment(f"{AUTHORIZATION_STRING_PREFIX} {main_branch.commit.sha}")

    # The github_client is injected
    report = execute_job(  # pylint: disable=no-value-for-parameter
        job_metadata=JobMetadata(
            repository_name=github_repository_name,
            fork_or_branch_repository_name=forked_github_repository.full_name,
            branch_name=forked_github_branch.name,
            commit_sha=commit_on_forked_github_branch.sha,
        )
    )

    assert report.result == Result.FAIL
    assert report.reason, "expected a reason along with the fail result"
    assert_.substrings_in_string(("not", "authorized", "write"), report.reason)


@pytest.mark.parametrize(
    "forked_github_branch",
    [f"test-branch/execute-job/quoted-authorization/{uuid4()}"],
    indirect=True,
)
@pytest.mark.usefixtures("make_fork_from_collaborator")
def test_fail_forked_quoted_authorizationr(
    forked_github_repository: Repository,
    github_repository: Repository,
    forked_github_branch: Branch,
    github_repository_name: str,
    commit_on_forked_github_branch: Commit,
    pr_from_forked_github_branch: PullRequest,
):
    """
    arrange: given a fork branch that has a PR with the right comment that is quoted
    act: when execute_job is called
    assert: then a fail report is returned.
    """
    pr_issue = github_repository.get_issue(pr_from_forked_github_branch.number)
    pr_issue.create_comment(f">{AUTHORIZATION_STRING_PREFIX} {commit_on_forked_github_branch.sha}")

    # The github_client is injected
    report = execute_job(  # pylint: disable=no-value-for-parameter
        job_metadata=JobMetadata(
            repository_name=github_repository_name,
            fork_or_branch_repository_name=forked_github_repository.full_name,
            branch_name=forked_github_branch.name,
            commit_sha=commit_on_forked_github_branch.sha,
        )
    )

    assert report.result == Result.FAIL
    assert report.reason, "expected a reason along with the fail result"
    assert_.substrings_in_string(("not", "authorized", "write"), report.reason)


@pytest.mark.parametrize(
    "forked_github_branch",
    [f"test-branch/execute-job/comment-from-wrong-user-on-pr/{uuid4()}"],
    indirect=True,
)
@pytest.mark.usefixtures("make_fork_from_collaborator")
def test_fail_forked_comment_from_wrong_user_on_pr(
    forked_github_repository: Repository,
    github_repository: Repository,
    forked_github_branch: Branch,
    github_repository_name: str,
    pr_from_forked_github_branch: PullRequest,
    commit_on_forked_github_branch: Commit,
    monkeypatch: pytest.MonkeyPatch,
    ci_github_repository: Repository | None,
):
    """
    arrange: given a fork branch that has a PR with the right comment from a user that does not
        have push access
    act: when execute_job is called
    assert: then a fail report is returned.
    """
    # Locally patch the get_collaborators call, in CI use bot to comment
    if ci_github_repository:
        ci_pr_issue = ci_github_repository.get_issue(pr_from_forked_github_branch.number)
        ci_pr_issue.create_comment(
            f"{AUTHORIZATION_STRING_PREFIX} {commit_on_forked_github_branch.sha}"
        )
    else:
        pr_issue = github_repository.get_issue(pr_from_forked_github_branch.number)
        pr_issue.create_comment(
            f"{AUTHORIZATION_STRING_PREFIX} {commit_on_forked_github_branch.sha}"
        )

        # Change the collaborators request to return no collaborators
        monkeypatch.setattr(
            repo_policy_compliance.check, "get_collaborators", lambda *_args, **_kwargs: []
        )

    # The github_client is injected
    report = execute_job(  # pylint: disable=no-value-for-parameter
        job_metadata=JobMetadata(
            repository_name=github_repository_name,
            fork_or_branch_repository_name=forked_github_repository.full_name,
            branch_name=forked_github_branch.name,
            commit_sha=commit_on_forked_github_branch.sha,
        )
    )

    assert report.result == Result.FAIL
    assert report.reason, "expected a reason along with the fail result"
    assert_.substrings_in_string(("not", "authorized"), report.reason)


@pytest.mark.parametrize(
    "github_branch",
    [f"test-branch/execute-job/repo-branch/{uuid4()}"],
    indirect=True,
)
def test_pass_main_repo(
    github_repository: Repository,
    github_branch: Branch,
    github_repository_name: str,
    caplog: pytest.LogCaptureFixture,
):
    """
    arrange: given a branch from the repository
    act: when execute_job is called
    assert: then a pass report is returned.
    """
    main_branch = github_repository.get_branch(github_repository.default_branch)

    # The github_client is injected
    report = execute_job(  # pylint: disable=no-value-for-parameter
        job_metadata=JobMetadata(
            repository_name=github_repository_name,
            fork_or_branch_repository_name=github_repository_name,
            branch_name=github_branch.name,
            commit_sha=main_branch.commit.sha,
        )
    )

    assert report.reason is None
    assert report.result == Result.PASS
    assert repr("execute_job") in caplog.text
    assert repr(report) in caplog.text


@pytest.mark.parametrize(
    "forked_github_branch",
    [f"test-branch/execute-job/fork-branch/{uuid4()}"],
    indirect=True,
)
@pytest.mark.usefixtures("make_fork_from_collaborator")
def test_pass_fork(
    forked_github_repository: Repository,
    github_repository: Repository,
    forked_github_branch: Branch,
    github_repository_name: str,
    pr_from_forked_github_branch: PullRequest,
    commit_on_forked_github_branch: Commit,
    ci_github_repository: Repository | None,
):
    """
    arrange: given a fork branch that has a PR with an authorization comment from a user with push
        or above permission
    act: when execute_job is called
    assert: then a pass report is returned.
    """
    pr_issue = github_repository.get_issue(pr_from_forked_github_branch.number)

    # In CI, add an authorization comment from the bot which checks that multiple authorization
    # comments are correctly handled where some are not from an authorized user
    if ci_github_repository:
        ci_pr_issue = ci_github_repository.get_issue(pr_from_forked_github_branch.number)
        ci_pr_issue.create_comment(
            f"{AUTHORIZATION_STRING_PREFIX} {commit_on_forked_github_branch.sha}"
        )

    # Add padding to ensure that the string just needs to be within the comment
    pr_issue.create_comment(
        f"padding {AUTHORIZATION_STRING_PREFIX} {commit_on_forked_github_branch.sha} padding"
    )

    # The github_client is injected
    report = execute_job(  # pylint: disable=no-value-for-parameter
        job_metadata=JobMetadata(
            repository_name=github_repository_name,
            fork_or_branch_repository_name=forked_github_repository.full_name,
            branch_name=forked_github_branch.name,
            commit_sha=commit_on_forked_github_branch.sha,
        )
    )

    assert report.reason is None
    assert report.result == Result.PASS


@pytest.mark.parametrize(
    "forked_github_branch",
    [f"test-branch/execute-job/push-fork-branch/{uuid4()}"],
    indirect=True,
)
def test_pass_fork_collaborator_no_comment(
    forked_github_repository: Repository,
    forked_github_branch: Branch,
    github_repository_name: str,
    commit_on_forked_github_branch: Commit,
):
    """
    arrange: given a fork branch from a push permission user that has a PR without an authorization
        comment from a push
    act: when execute_job is called
    assert: then a pass report is returned.
    """
    # The github_client is injected
    report = execute_job(  # pylint: disable=no-value-for-parameter
        job_metadata=JobMetadata(
            repository_name=github_repository_name,
            fork_or_branch_repository_name=forked_github_repository.full_name,
            branch_name=forked_github_branch.name,
            commit_sha=commit_on_forked_github_branch.sha,
        )
    )

    assert report.reason is None
    assert report.result == Result.PASS
