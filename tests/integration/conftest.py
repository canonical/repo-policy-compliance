# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for integration tests."""

import os
from typing import Generator

import pytest
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


@pytest.fixture
def github_branch(
    github_repository: Repository,
    request: pytest.FixtureRequest,
) -> Generator[BranchWithProtection, None, None]:
    """Create a new branch for testing."""
    branch_with_protection: BranchWithProtection = request.param

    main_branch = github_repository.get_branch(github_repository.default_branch)
    branch_ref = github_repository.create_git_ref(
        ref=f"refs/heads/{branch_with_protection.name}", sha=main_branch.commit.sha
    )
    branch = github_repository.get_branch(branch_with_protection.name)

    if branch_with_protection.branch_protection_enabled:
        branch_protection.edit(branch, branch_with_protection)

    branch_with_protection.github_branch = branch
    yield branch_with_protection

    if branch_with_protection.branch_protection_enabled:
        branch.remove_protection()

    branch_ref.delete()
