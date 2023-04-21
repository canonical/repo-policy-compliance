# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for integration tests."""

import pytest
from github import Consts, Github, GitRef, Repository

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


@pytest.fixture()
def github_branch(github_repository: Repository, request: pytest.FixtureRequest) -> GitRef:
    """Create a new branch for testing."""
    main_branch = github_repository.get_branch(github_repository.default_branch)
    branch_ref = github_repository.create_git_ref(
        ref=f"refs/heads/{request.param}", sha=main_branch.commit.sha
    )
    branch = github_repository.get_branch(request.param)

    yield branch

    branch_ref.delete()
