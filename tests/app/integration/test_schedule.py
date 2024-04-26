# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Tests for the schedule function."""

# These tests are similar to workflow dispatch tests, in tests some duplication is ok to make the
# tests easier to understand
# pylint: disable=duplicate-code

import pytest

from repo_policy_compliance import ScheduleInput, policy, schedule
from repo_policy_compliance.check import Result

from .types_ import RequestedCollaborator


def test_invalid_policy():
    """
    arrange: given invalid policy
    act: when schedule is called with the policy
    assert: then a fail report is returned.
    """
    policy_document = {"invalid": "value"}

    report = schedule(
        input_=ScheduleInput(repository_name="repository 1"),
        policy_document=policy_document,
    )

    assert report.result == Result.FAIL, report.reason


@pytest.mark.parametrize(
    "collaborators_with_permission, policy_enabled, expected_result",
    [
        pytest.param(
            RequestedCollaborator("admin", "admin"),
            True,
            Result.FAIL,
            id="policy enabled",
        ),
        pytest.param(
            RequestedCollaborator("admin", "admin"),
            False,
            Result.PASS,
            id="policy disabled",
        ),
    ],
    indirect=["collaborators_with_permission"],
)
@pytest.mark.usefixtures("collaborators_with_permission")
def test_collaborators(github_repository_name: str, policy_enabled: bool, expected_result: Result):
    """
    arrange: given a branch that are compliant and outside collaborators with more than read
        permission and whether the policy is enabled
    act: when schedule is called with the policy
    assert: then the expected report is returned.
    """
    policy_document = {
        policy.JobType.SCHEDULE: {
            policy.ScheduleProperty.COLLABORATORS: {policy.ENABLED_KEY: policy_enabled}
        }
    }

    report = schedule(
        input_=ScheduleInput(repository_name=github_repository_name),
        policy_document=policy_document,
    )

    assert report.result == expected_result


def test_pass(github_repository_name: str, caplog: pytest.LogCaptureFixture):
    """
    arrange: given a branch and repository that is compliant
    act: when schedule is called
    assert: then a pass report is returned.
    """
    report = schedule(
        input_=ScheduleInput(repository_name=github_repository_name),
    )

    assert report.result == Result.PASS
    assert repr("schedule") in caplog.text
    assert repr(report) in caplog.text
