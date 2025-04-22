# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for integration tests."""
import enum
import logging
import os
import secrets
from collections import namedtuple
from enum import Enum
from typing import Iterator, cast
from uuid import uuid4

import pytest
import requests
from github import Github
from github.Auth import Token
from github.Branch import Branch
from github.Commit import Commit
from github.PullRequest import PullRequest
from github.Repository import Repository

import repo_policy_compliance
from repo_policy_compliance.github_client import (
    GITHUB_APP_ID_ENV_NAME,
    GITHUB_APP_INSTALLATION_ID_ENV_NAME,
    GITHUB_APP_PRIVATE_KEY_ENV_NAME,
    GITHUB_TOKEN_ENV_NAME,
    get_collaborators,
)

from ...conftest import REPOSITORY_ARGUMENT_NAME
from . import branch_protection
from .types_ import BranchWithProtection, RequestedCollaborator

logger = logging.getLogger(__name__)

TEST_GITHUB_APP_ID_ENV_NAME = f"AUTH_{GITHUB_APP_ID_ENV_NAME}"
TEST_GITHUB_APP_INSTALLATION_ID_ENV_NAME = f"AUTH_{GITHUB_APP_INSTALLATION_ID_ENV_NAME}"
TEST_GITHUB_APP_PRIVATE_KEY_ENV_NAME = f"AUTH_{GITHUB_APP_PRIVATE_KEY_ENV_NAME}"
TEST_GITHUB_TOKEN_ENV_NAME = f"AUTH_{GITHUB_TOKEN_ENV_NAME}"


class AuthenticationMethod(Enum):
    """The authentication method to use.

    Attributes:
        GITHUB_TOKEN: Use GitHub token authentication.
        GITHUB_APP: Use GitHub App authentication.
    """

    GITHUB_TOKEN = enum.auto()
    GITHUB_APP = enum.auto()


_AuthenticationMethodParams = namedtuple(
    "_AuthenticationMethodParams", ["app_id", "installation_id", "private_key", "github_token"]
)


@pytest.fixture(
    scope="function",
    name="github_auth",
    autouse=True,
    params=[
        pytest.param(
            _AuthenticationMethodParams(
                github_token=os.getenv(TEST_GITHUB_TOKEN_ENV_NAME),
                app_id=None,
                installation_id=None,
                private_key=None,
            ),
            id="Using GitHub Token authentication",
        ),
        pytest.param(
            _AuthenticationMethodParams(
                app_id=os.getenv(TEST_GITHUB_APP_ID_ENV_NAME),
                installation_id=os.getenv(TEST_GITHUB_APP_INSTALLATION_ID_ENV_NAME),
                private_key=os.getenv(TEST_GITHUB_APP_PRIVATE_KEY_ENV_NAME),
                github_token=None,
            ),
            marks=pytest.mark.skipif(
                not all(
                    [
                        os.getenv(TEST_GITHUB_APP_ID_ENV_NAME),
                        os.getenv(TEST_GITHUB_APP_INSTALLATION_ID_ENV_NAME),
                        os.getenv(TEST_GITHUB_APP_PRIVATE_KEY_ENV_NAME),
                    ]
                ),
                reason="GitHub App Auth environment variables are not set",
            ),
            id="Using GitHub App authentication",
        ),
    ],
)
def fixture_github_auth(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> AuthenticationMethod:
    """Setup the GitHub authentication method.

    We want to test with GitHub Token authentication and optionally GitHub App authentication,
    if the environment variables are set.
    This is achieved by monkeypatching the respective environment variables.

    Returns:
        The authentication method to use.
    """
    app_id = request.param.app_id
    app_install_id = request.param.installation_id
    app_private_key = request.param.private_key
    github_token = request.param.github_token

    auth_method = AuthenticationMethod.GITHUB_TOKEN

    if app_id:
        monkeypatch.setenv(GITHUB_APP_ID_ENV_NAME, app_id)
        auth_method = AuthenticationMethod.GITHUB_APP
    if app_install_id:
        monkeypatch.setenv(GITHUB_APP_INSTALLATION_ID_ENV_NAME, app_install_id)
    if app_private_key:
        monkeypatch.setenv(GITHUB_APP_PRIVATE_KEY_ENV_NAME, app_private_key)
    if github_token:
        monkeypatch.setenv(GITHUB_TOKEN_ENV_NAME, github_token)

    return auth_method


@pytest.fixture(scope="session", name="github_repository_name")
def fixture_github_repository_name(pytestconfig: pytest.Config) -> str:
    """The name of the repository to work with."""
    return pytestconfig.getoption(REPOSITORY_ARGUMENT_NAME)


@pytest.fixture(scope="session", name="github_token")
def fixture_github_token() -> str:
    """Get the GitHub token from the environment."""
    github_token = os.getenv(TEST_GITHUB_TOKEN_ENV_NAME)
    assert (
        github_token
    ), f"GitHub token must be set in the environment variable {TEST_GITHUB_TOKEN_ENV_NAME}"
    return github_token


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
    """Returns client to the Github repository using the CI GitHub token.

    This is useful for tests where we would like the user to be a bot
    (e.g. to test things like comments from a user that does not have write permission or above).
    This only works if the test repository is the same as the CI repository.
    """
    if not ci_github_token:
        return None

    github_client = Github(auth=Token(ci_github_token))
    return github_client.get_repo(github_repository_name)


@pytest.fixture(scope="session", name="github_repository")
def fixture_github_repository(github_repository_name: str, github_token: str) -> Repository:
    """Returns client to the Github repository."""
    github_client = Github(auth=Token(github_token))
    return github_client.get_repo(github_repository_name)


@pytest.fixture(name="forked_github_repository")
def fixture_forked_github_repository(
    github_repository: Repository,
) -> Iterator[Repository]:
    """Create a fork for a GitHub repository."""
    forked_repository = github_repository.create_fork()

    # Wait for repo to be ready. We assume its ready if we can get the default branch.
    forked_repository.get_branch(github_repository.default_branch)

    yield forked_repository


@pytest.fixture(name="github_branch")
def fixture_github_branch(
    github_repository: Repository, request: pytest.FixtureRequest
) -> Iterator[Branch]:
    """Create a new branch for testing."""
    branch_name: str = request.param
    branch_name += uuid4() # add uniqueness to avoid conflict on deletion

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
    branch_name += uuid4()  # add uniqueness to avoid conflict on deletion

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
    branch_name += uuid4()  # add uniqueness to avoid conflict on deletion

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


@pytest.fixture(name="ruleset_protected_github_branch")
def fixture_ruleset_protected_github_branch(
    github_token: str, github_branch: Branch, github_repository: Repository
) -> Iterator[Branch]:
    """Add ruleset protection for a branch."""
    # pygithub does not support the rulesets API yet:
    # https://github.com/PyGithub/PyGithub/issues/2718
    # We use the GitHub API with the requests module to create the ruleset
    url = f"https://api.github.com/repos/{github_repository.full_name}/rulesets"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {github_token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    data = {
        "name": f"{github_branch.name}-ruleset",
        "target": "branch",
        "enforcement": "active",
        "conditions": {
            "ref_name": {
                "include": [f"refs/heads/{github_branch.name}"],
                "exclude": [],
            }
        },
        "rules": [{"type": "deletion"}, {"type": "non_fast_forward"}],
    }

    response = requests.post(url, headers=headers, json=data, timeout=10)
    response.raise_for_status()

    yield github_branch

    # delete the ruleset
    ruleset_id = response.json()["id"]
    url = f"https://api.github.com/repos/{github_repository.full_name}/rulesets/{ruleset_id}"
    response = requests.delete(url, headers=headers, timeout=10)
    response.raise_for_status()


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
    # Change role name to the one requested.
    mixin_collabs_with_role_name = [
        {**collaborator, "role_name": requested_collaborator.role_name}
        for collaborator in mixin_collabs
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
def make_fork_from_non_collaborator(monkeypatch: pytest.MonkeyPatch):
    """Make sure that _check_fork_collaborator return False."""
    monkeypatch.setattr(
        repo_policy_compliance.check,
        "_check_fork_collaborator",
        lambda *_args, **_kwargs: False,
    )
