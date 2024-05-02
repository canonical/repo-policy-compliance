# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for integration tests."""

import os
from time import sleep
from typing import Any, Callable, Iterator, cast

import pytest
from github import Github
from github.Auth import Token
from github.Branch import Branch
from github.Commit import Commit
from github.GithubException import GithubException
from github.PullRequest import PullRequest
from github.Repository import Repository

import repo_policy_compliance
from repo_policy_compliance.github_client import get_collaborators
from repo_policy_compliance.github_client import inject as inject_github_client

from . import branch_protection
from .types_ import BranchWithProtection, RequestedCollaborator

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


@pytest.fixture(scope="session", name="ci_github_token")
def fixture_ci_github_token() -> str | None:
    """Get the GitHub token from the CI environment."""
    env_name = "CI_GITHUB_TOKEN"
    github_token = os.getenv(env_name)
    return github_token


@pytest.fixture(scope="session", name="ci_github_repository")
def fixture_ci_github_repository(
    github_repository_name: str, ci_github_token: str | None
) -> None | Repository:
    """Returns client to the Github repository."""
    if not ci_github_token:
        return None

    github_client = Github(auth=Token(ci_github_token))
    return github_client.get_repo(github_repository_name)


@pytest.fixture(scope="session", name="github_repository")
def fixture_github_repository(github_repository_name: str) -> Repository:
    """Returns client to the Github repository."""
    github_client = inject_github_client(lambda client: client)()
    return github_client.get_repo(github_repository_name)


@pytest.fixture(name="forked_github_repository")
def fixture_forked_github_repository(
    github_repository: Repository,
) -> Iterator[Repository]:
    """Create a fork for a GitHub repository."""
    forked_repository = _simple_retry(github_repository.create_fork)

    # Wait for repo to be ready. We assume its ready if we can get the default branch.
    _simple_retry(forked_repository.get_branch, github_repository.default_branch)

    yield forked_repository

    _simple_retry(forked_repository.delete)


def _simple_retry(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Retry a function 10 times before failing.

    Args:
        func: The function to retry.
        args: The positional arguments to pass to the function.
        kwargs: The keyword arguments to pass to the function.

    Returns:
        The result of the function.
    """
    for _ in range(10):
        try:
            return func(*args, **kwargs)
        except GithubException:
            sleep(10)
    assert False, f"timed out while waiting for func {func.__name__} to complete"


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


@pytest.fixture(name="another_github_branch")
def fixture_another_github_branch(
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
    """Create a commit for testing."""
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
    """Create a new forked branch for testing."""
    # Create target for PR to avoid triggering recursive GitHub action runs
    main_branch = github_repository.get_branch(github_repository.default_branch)
    base_branch_name = f"test-branch/target-for-{forked_github_branch.name}"
    base_branch_ref = github_repository.create_git_ref(
        ref=f"refs/heads/{base_branch_name}",
        sha=main_branch.commit.sha,
    )
    base_branch = github_repository.get_branch(base_branch_name)
    github_repository.create_file(
        "another-test.txt", "testing", "some content", branch=base_branch.name
    )

    # Create PR
    pull = github_repository.create_pull(
        title=forked_github_branch.name,
        body=f"PR for testing {commit_on_forked_github_branch.sha}",
        base=base_branch.name,
        head=f"{forked_github_repository.owner.login}:{forked_github_branch.name}",
        draft=True,
    )

    yield pull

    pull.edit(state="closed")
    base_branch_ref.delete()


@pytest.fixture(name="protected_github_branch")
def fixture_protected_github_branch(
    github_branch: Branch, request: pytest.FixtureRequest
) -> Iterator[BranchWithProtection]:
    """Add protection to a branch."""
    branch_with_protection: BranchWithProtection = request.param

    if branch_with_protection.branch_protection_enabled:
        branch_protection.edit(github_branch, branch_with_protection)

    yield branch_with_protection

    if branch_with_protection.branch_protection_enabled:
        github_branch.remove_protection()


@pytest.fixture(name="pull_request_review_not_required")
def fixture_pull_request_review_not_required(
    github_branch: Branch,
) -> Iterator[Branch]:
    """Add protection to a branch."""
    github_branch.edit_protection(allow_force_pushes=False)

    yield github_branch

    github_branch.remove_protection()


@pytest.fixture
def protected_github_branch_with_commit_in_ci(
    github_branch: Branch, ci_github_repository: Repository | None
) -> Iterator[Branch]:
    """Add a signed commit if running in CI to a protected branch."""
    if ci_github_repository:
        ci_github_repository.create_file(
            "test.txt", "testing", "some content", branch=github_branch.name
        )

    # Can't use protected_github_branch since the commit needs to be done before the branch
    # protections are applied
    branch_with_protection = BranchWithProtection(bypass_pull_request_allowance_disabled=True)

    branch_protection.edit(branch=github_branch, branch_with_protection=branch_with_protection)

    yield github_branch

    github_branch.remove_protection()


@pytest.fixture(name="collaborators_with_permission")
def fixture_collaborators_with_permission(
    github_repository: Repository,
    request: pytest.FixtureRequest,
    monkeypatch: pytest.MonkeyPatch,
):
    """Add collaborators with certain permissions to the collaborators response."""
    requested_collaborator: RequestedCollaborator = request.param

    # Request non-outside collaborators with the requester permission to use for the response
    mixin_collabs = get_collaborators(
        affiliation="all",
        permission=requested_collaborator.permission,
        repository=github_repository,
    )
    mixin_collabs_with_role_name = [
        collaborator
        for collaborator in mixin_collabs
        if collaborator["role_name"] == requested_collaborator.role_name
    ]
    assert mixin_collabs_with_role_name

    # Change the collaborators request to return mixin collaborators
    monkeypatch.setattr(
        repo_policy_compliance.check,
        "get_collaborators",
        lambda *_args, **_kwargs: mixin_collabs_with_role_name,
    )

    return mixin_collabs_with_role_name


@pytest.fixture
def make_fork_branch_external(monkeypatch: pytest.MonkeyPatch):
    """Make sure that _branch_external_fork returns True."""
    monkeypatch.setattr(
        repo_policy_compliance.check,
        "_branch_external_fork",
        lambda *_args, **_kwargs: True,
    )
