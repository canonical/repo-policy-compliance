# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Tests for the execute_job function."""

from uuid import uuid4

import pytest
from github.Branch import Branch
from github.Repository import Repository

from repo_policy_compliance import Result, execute_job

from .. import assert_


@pytest.mark.parametrize(
    "forked_github_branch",
    [f"execute-job/no-pr/{uuid4()}"],
    indirect=True,
)
def test_fail_forked_no_pr(
    forked_github_repository: Repository, forked_github_branch: Branch, github_repository_name: str
):
    """
    arrange: given a fork branch that doesn't have a PR
    act: when execute_job is called with the name of the branch
    assert: then a fail report is returned.
    """
    # The github_client is injected
    report = execute_job(  # pylint: disable=no-value-for-parameter
        repository_name=github_repository_name,
        source_repository_name=forked_github_repository.full_name,
        branch_name=forked_github_branch.name,
        commit_sha=forked_github_branch.commit.sha,
    )

    assert report.reason
    assert_.substrings_in_string(("no", "pull request"), report.reason)
    assert report.result == Result.FAIL


@pytest.mark.parametrize(
    "forked_github_branch",
    [f"execute-job/no-comment-on-pr/{uuid4()}"],
    indirect=True,
)
@pytest.mark.usefixtures("pr_from_forked_github_branch")
def test_fail_forked_no_comment_on_pr(
    forked_github_repository: Repository, forked_github_branch: Branch, github_repository_name: str
):
    """
    arrange: given a fork branch that doesn't have a PR
    act: when execute_job is called with the name of the branch
    assert: then a fail report is returned.
    """
    # The github_client is injected
    report = execute_job(  # pylint: disable=no-value-for-parameter
        repository_name=github_repository_name,
        source_repository_name=forked_github_repository.full_name,
        branch_name=forked_github_branch.name,
        commit_sha=forked_github_branch.commit.sha,
    )

    assert report.reason
    assert_.substrings_in_string(("not", "authorized"), report.reason)
    assert report.result == Result.FAIL


@pytest.mark.parametrize(
    "github_branch",
    [f"execute-job/repo-branch/{uuid4()}"],
    indirect=True,
)
def test_pass_main_repo(
    github_repository: Repository, github_branch: Branch, github_repository_name: str
):
    """
    arrange: given a branch from the repository
    act: when execute_job is called with the name of the branch
    assert: then a pass report is returned.
    """
    main_branch = github_repository.get_branch(github_repository.default_branch)

    # The github_client is injected
    report = execute_job(  # pylint: disable=no-value-for-parameter
        repository_name=github_repository_name,
        source_repository_name=github_repository_name,
        branch_name=github_branch.name,
        commit_sha=main_branch.commit.sha,
    )

    assert report.reason is None
    assert report.result == Result.PASS
