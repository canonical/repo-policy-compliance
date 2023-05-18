# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for integration tests."""

import os
from time import sleep
from typing import Iterator, cast

import pytest
from github.Branch import Branch
from github.Commit import Commit
from github.GithubException import GithubException
from github.PullRequest import PullRequest
from github.Repository import Repository

from repo_policy_compliance.github_client import inject as inject_github_client

from . import branch_protection
from .types_ import BranchWithProtection

REPOSITORY_ARGUMENT_NAME = "--repository"


def pytest_addoption(parser):
    """Parse additional pytest options.

    Args:
        parser: Options parser.
    """
    parser.addoption(REPOSITORY_ARGUMENT_NAME, action="store")


@pytest.fixture(scope="session", name="github_repository_name")
def fixture_github_repository_name(pytestconfig: pytest.Config) -> str:
    """The name of the repository to work with."""
    return pytestconfig.getoption(
        REPOSITORY_ARGUMENT_NAME, default="canonical/repo-policy-compliance"
    )


@pytest.fixture(scope="session")
def ci_github_token() -> str | None:
    """Get the GitHub token from the CI environment."""
    env_name = "CI_GITHUB_TOKEN"
    github_token = os.getenv(env_name)
    return github_token


@pytest.fixture(scope="session", name="github_repository")
def fixture_github_repository(github_repository_name: str):
    """Returns client to the Github repository."""
    github_client = inject_github_client(lambda client: client)()
    return github_client.get_repo(github_repository_name)


@pytest.fixture(name="forked_github_repository")
def fixture_forked_github_repository(
    github_repository: Repository,
) -> Iterator[Repository]:
    """Create a fork for a GitHub repository."""
    forked_repository = github_repository.create_fork()

    # Wait for repo to be ready
    for _ in range(10):
        try:
            sleep(10)
            forked_repository.get_branches()
            break
        except GithubException:
            pass
    else:
        assert False, "timed out whilst waiting for repository creation"

    yield forked_repository

    forked_repository.delete()


@pytest.fixture(name="github_branch")
def fixture_github_branch(
    github_repository: Repository, request: pytest.FixtureRequest
) -> Iterator[Branch]:
    """Create a new branch for testing."""
    branch_name: str = request.param

    main_branch = github_repository.get_branch(github_repository.default_branch)
    branch_ref = github_repository.create_git_ref(
        ref=f"refs/heads/{branch_name}", sha=main_branch.commit.sha
    )
    branch = github_repository.get_branch(branch_name)

    yield branch

    branch_ref.delete()


@pytest.fixture(name="forked_github_branch")
def fixture_forked_github_branch(
    forked_github_repository: Repository, request: pytest.FixtureRequest
) -> Iterator[Branch]:
    """Create a new forked branch for testing."""
    branch_name: str = request.param

    main_branch = forked_github_repository.get_branch(forked_github_repository.default_branch)
    branch_ref = forked_github_repository.create_git_ref(
        ref=f"refs/heads/{branch_name}", sha=main_branch.commit.sha
    )
    branch = forked_github_repository.get_branch(branch_name)

    yield branch

    branch_ref.delete()


@pytest.fixture(name="commit_on_forked_github_branch")
def fixture_commit_on_forked_github_branch(
    forked_github_branch: Branch, forked_github_repository: Repository
) -> Commit:
    """Create a new branch for testing."""
    # Create a commit on the branch
    commit = cast(
        Commit,
        forked_github_repository.create_file(
            "test.txt", "testing", "some content", branch=forked_github_branch.name
        )["commit"],
    )

    return commit


@pytest.fixture
def pr_from_forked_github_branch(
    forked_github_branch: Branch,
    forked_github_repository: Repository,
    github_repository: Repository,
    commit_on_forked_github_branch: Commit,
) -> Iterator[PullRequest]:
    """Create a new branch for testing."""
    # Create PR
    pull = github_repository.create_pull(
        title=forked_github_branch.name,
        body=f"PR for testing {commit_on_forked_github_branch.sha}",
        base=github_repository.default_branch,
        head=f"{forked_github_repository.owner.login}:{forked_github_branch.name}",
        draft=True,
    )

    yield pull

    pull.edit(state="closed")


@pytest.fixture
def protected_github_branch(
    github_branch: Branch, request: pytest.FixtureRequest
) -> Iterator[BranchWithProtection]:
    """Create a new branch for testing."""
    branch_with_protection: BranchWithProtection = request.param

    if branch_with_protection.branch_protection_enabled:
        branch_protection.edit(github_branch, branch_with_protection)

    yield branch_with_protection

    if branch_with_protection.branch_protection_enabled:
        github_branch.remove_protection()
