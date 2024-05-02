# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Tests for the collaborators function."""

import itertools

import pytest

from repo_policy_compliance.check import Result, collaborators
from tests import assert_

from .types_ import RequestedCollaborator


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


def test_pass(github_repository_name: str, caplog: pytest.LogCaptureFixture):
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
    assert repr("collaborators") in caplog.text
    assert repr(report) in caplog.text
