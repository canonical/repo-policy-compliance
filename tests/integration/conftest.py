# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for integration tests."""

from typing import Generator

import pytest
from github import Consts
from github.Branch import Branch
from github.Repository import Repository

from repo_policy_compliance.github_client import inject as inject_github_client

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


@pytest.fixture(scope="session", name="github_repository")
def fixture_github_repository(github_repository_name: str):
    """Returns client to the Github repository."""
    github_client = inject_github_client(lambda client: client)()
    return github_client.get_repo(github_repository_name)


@pytest.fixture()
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
        edit_branch_protection(branch, branch_with_protection)

    branch_with_protection.github_branch = branch
    yield branch_with_protection

    if branch_with_protection.branch_protection_enabled:
        branch.remove_protection()

    branch_ref.delete()


def edit_branch_protection(branch: Branch, branch_with_protection: BranchWithProtection) -> None:
    """Enable or disable the branch protection parameters on the given branch.

    Args:
        branch: The branch to modify.
        branch_with_protection: The branch name and its protection parameters.
    """
    require_code_owner_reviews = branch_with_protection.require_code_owner_reviews

    if not branch_with_protection.bypass_pull_request_allowance_disabled:
        post_parameters = {
            "required_status_checks": None,
            "enforce_admins": None,
            "required_pull_request_reviews": {
                "dismiss_stale_reviews": branch_with_protection.dismiss_stale_reviews_enabled,
                "require_code_owner_reviews": require_code_owner_reviews,
                "bypass_pull_request_allowances": {
                    "users": ["gregory-schiano", "jdkanderson"],
                    "teams": ["is-charms"],
                    "apps": ["test"],
                },
            },
            "restrictions": None,
        }

        # This API endpoint is not supported by the library, we call it ourselves
        # pylint: disable=protected-access
        branch._requester.requestJsonAndCheck(  # type: ignore
            "PUT",
            branch.protection_url,
            headers={"Accept": Consts.mediaTypeRequireMultipleApprovingReviews},
            input=post_parameters,
        )
        # pylint: enable=protected-access

        return

    branch.edit_protection(
        require_code_owner_reviews=branch_with_protection.require_code_owner_reviews,
        dismiss_stale_reviews=branch_with_protection.dismiss_stale_reviews_enabled,
    )

    if branch_with_protection.required_signatures_enabled:
        # This API endpoint is not supported by the library, we call it ourselves
        # pylint: disable=protected-access
        branch._requester.requestJsonAndCheck(  # type: ignore
            "POST",
            url=f"{branch.protection_url}/required_signatures",
            headers={"Accept": Consts.signaturesProtectedBranchesPreview},
        )
        # pylint: enable=protected-access
