# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Tests for the collaborators function."""

# Need to override private methods for mocking
# pylint: disable=protected-access

import itertools
from typing import NamedTuple
from urllib import parse

import pytest
from github.Repository import Repository

from repo_policy_compliance import Result, collaborators
from repo_policy_compliance.github_client import get as get_github_client

from .. import assert_


class RequestedCollaborator(NamedTuple):
    """Information about the requested collaborators to be added.

    Attrs:
        permission: The permission the collaborators should have.
        role_name: The name of the role the collaborators should have
    """

    permission: str
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
    collaborators_url = github_repository.collaborators_url.removesuffix("{/collaborator}")
    query = {"permission": requested_collaborator.permission}
    # mypy thinks the attribute doesn't exist when it actually does exist
    (headers, mixin_collabs) = github_repository._requester.requestJsonAndCheck(  # type: ignore
        "GET", f"{collaborators_url}?{parse.urlencode(query)}"
    )
    mixin_collabs_with_role_name = [
        collaborator
        for collaborator in mixin_collabs
        if collaborator["role_name"] == requested_collaborator.role_name
    ]
    assert mixin_collabs_with_role_name

    # mypy thinks the attribute doesn't exist when it actually does exist
    monkeypatch.setattr(
        github_repository._requester,  # type: ignore
        "requestJsonAndCheck",
        lambda *_args, **_kwargs: (headers, mixin_collabs_with_role_name),
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

    assert report.reason
    assert_.substrings_in_string(
        itertools.chain(
            ("includes", "outside collaborators", "higher permission", "read"),
            (collaborator["login"] for collaborator in collaborators_with_permission),
        ),
        report.reason,
    )
    assert report.result == Result.FAIL


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
