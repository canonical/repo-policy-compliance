# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for integration tests."""

from uuid import uuid4

import pytest
from github import Github, GitRef, Repository

from repo_policy_compliance.github_client import inject as inject_github_client

REPOSITORY_ARGUMENT_NAME = "--repository"


def pytest_addoption(parser):
    """Parse additional pytest options."""
    parser.addoption(REPOSITORY_ARGUMENT_NAME, action="store")


@pytest.fixture(scope="session", name="github_repository_name")
def fixture_github_repository_name(pytestconfig: pytest.Config) -> str:
    """The name of the repository to work with."""
    return pytestconfig.getoption(
        REPOSITORY_ARGUMENT_NAME, default="canonical/repo-policy-compliance"
    )


@pytest.fixture(scope="session", name="github_client")
def fixture_github_client(github_client: Github) -> Github:
    """Makes a Github client available."""
    return github_client


@pytest.fixture(scope="session", name="github_repository")
def fixture_github_repository(github_repository_name: str) -> Repository:
    """Returns client to the Github repository."""
    github_client = inject_github_client(lambda client: client)()
    return github_client.get_repo(github_repository_name)


@pytest.fixture(name="git_branch_name")
def fixture_git_branch_name() -> str:
    """Create a name of a branch for testing."""
    return f"testing/{uuid4()}"


@pytest.fixture()
def github_branch(github_repository: Repository, git_branch_name: str) -> GitRef:
    """Create a new branch for testing."""
    main_branch = github_repository.get_branch(github_repository.default_branch)
    branch_ref = github_repository.create_git_ref(
        ref=f"refs/heads/{git_branch_name}", sha=main_branch.commit.sha
    )
    branch = github_repository.get_branch(git_branch_name)

    yield branch

    branch.remove_protection()
    branch_ref.delete()
