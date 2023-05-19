# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Tests for the collaborators function."""

import itertools
from typing import Literal, NamedTuple

import pytest
from github.Repository import Repository

import repo_policy_compliance
from repo_policy_compliance import Result, collaborators
from repo_policy_compliance.github_client import get as get_github_client
from repo_policy_compliance.github_client import get_collaborators

from .. import assert_


class RequestedCollaborator(NamedTuple):
    """Information about the requested collaborators to be added.

    Attrs:
        permission: The permission the collaborators should have.
        role_name: The name of the role the collaborators should have
    """

    permission: Literal["admin", "pull"]
    role_name: str


@pytest.fixture(name="collaborators_with_permission")
def fixture_collaborators_with_permission(
    github_repository: Repository,
    request: pytest.FixtureRequest,
    monkeypatch: pytest.MonkeyPatch,
):
    """Add collaborators with certain permissions to the collaborators response."""
    requested_collaborator: RequestedCollaborator = request.param

    github_client = get_github_client()
    monkeypatch.setattr(github_client, "get_repo", lambda *_args, **_kwargs: github_repository)
    monkeypatch.setattr(
        "repo_policy_compliance.github_client.Github", lambda *_args, **_kwargs: github_client
    )

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
        repo_policy_compliance,
        "get_collaborators",
        lambda *_args, **_kwargs: mixin_collabs_with_role_name,
    )

    return mixin_collabs_with_role_name


@pytest.mark.parametrize(
    "collaborators_with_permission", [RequestedCollaborator("admin", "admin")], indirect=True
)
def test_fail(github_repository_name: str, collaborators_with_permission: list[dict]):
    """
    arrange: given a repository with outside collaborators that have admin permission
    act: when collaborators is called with the name of the repository
    assert: then a fail report is returned.
    """
    # The github_client is injected
    report = collaborators(  # pylint: disable=no-value-for-parameter
        repository_name=github_repository_name
    )

    assert report.result == Result.FAIL
    assert report.reason, "expected a reason along with the fail result"
    assert_.substrings_in_string(
        itertools.chain(
            ("includes", "outside collaborators", "higher permission", "read"),
            (collaborator["login"] for collaborator in collaborators_with_permission),
        ),
        report.reason,
    )


@pytest.mark.parametrize(
    "collaborators_with_permission", [RequestedCollaborator("pull", "read")], indirect=True
)
@pytest.mark.usefixtures("collaborators_with_permission")
def test_pass_inject_collaborators(github_repository_name: str):
    """
    arrange: given a repository with outside collaborators that have read permission
    act: when collaborators is called with the name of the repository
    assert: then a pass report is returned.
    """
    # The github_client is injected
    report = collaborators(  # pylint: disable=no-value-for-parameter
        repository_name=github_repository_name
    )

    assert report.reason is None
    assert report.result == Result.PASS


def test_pass(github_repository_name: str):
    """
    arrange: given a repository with no outside collaborators
    act: when collaborators is called with the name of the repository
    assert: then a pass report is returned.
    """
    # The github_client is injected
    report = collaborators(  # pylint: disable=no-value-for-parameter
        repository_name=github_repository_name
    )

    assert report.reason is None
    assert report.result == Result.PASS
