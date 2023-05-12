# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Tests for the source_branch_protection function."""

import itertools
from uuid import uuid4

import pytest

from repo_policy_compliance import Result, source_branch_protection

from .. import assert_
from .types_ import BranchWithProtection


@pytest.mark.parametrize(
    "github_branch, reason_string_array",
    [
        pytest.param(
            BranchWithProtection(
                name=f"source-branch/not-protected/{uuid4()}", branch_protection_enabled=False
            ),
            ("not enabled"),
            id="branch_protection disabled",
        ),
        pytest.param(
            BranchWithProtection(
                name=f"source-branch/requires-signature/{uuid4()}",
                required_signatures_enabled=False,
            ),
            ("signed", "commits", "not required"),
            id="required-signature disabled",
        ),
    ],
    indirect=["github_branch"],
)
def test_fail(
    github_branch: BranchWithProtection,
    reason_string_array: tuple[str],
    github_repository_name: str,
):
    """
    arrange: given a branch that is not compliant.
    act: when source_branch_protection is called with the name of the branch.
    assert: then a fail report is returned.
    """
    # The github_client is injected
    report = source_branch_protection(  # pylint: disable=no-value-for-parameter
        repository_name=github_repository_name, branch_name=github_branch.name
    )

    assert_.substrings_in_string(
        itertools.chain(reason_string_array, github_branch.name), str(report.reason)
    )
    assert report.result == Result.FAIL


@pytest.mark.parametrize(
    "github_branch", [BranchWithProtection(name=f"protected/{uuid4()}")], indirect=True
)
def test_pass(
    github_branch: BranchWithProtection,
    github_repository_name: str,
):
    """
    arrange: given a branch that is compliant.
    act: when source_branch_protection is called with the name of the branch.
    assert: then a pass report is returned.
    """
    # The github_client is injected
    report = source_branch_protection(  # pylint: disable=no-value-for-parameter
        repository_name=github_repository_name, branch_name=github_branch.name
    )

    assert report.reason is None
    assert report.result == Result.PASS
