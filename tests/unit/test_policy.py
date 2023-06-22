# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Tests for the policy module."""

from itertools import chain, repeat

import pytest

from repo_policy_compliance import policy

from .. import assert_


@pytest.mark.parametrize(
    "document, expected_result, expected_reason",
    [
        pytest.param({}, True, None, id="empty"),
        pytest.param(
            {"invalid": "value"},
            False,
            ("invalid", "additional"),
            id="invalid top level",
        ),
        pytest.param(
            {
                policy.JobType.PULL_REQUEST: {
                    name: {**policy.ENABLED_RULE} for name in policy.PullRequestProperty
                },
                policy.JobType.WORKFLOW_DISPATCH: {
                    name: {**policy.ENABLED_RULE} for name in policy.WorkflowDispatchProperty
                },
            },
            True,
            None,
            id="all",
        ),
    ]
    + [
        pytest.param(
            {job_type: {"invalid": {**policy.ENABLED_RULE}}},
            False,
            ("invalid", "additional"),
            id=f"invalid {job_type} level",
        )
        for job_type in policy.JobType
    ]
    + [
        pytest.param(
            {job_type: {name: {}}},
            False,
            ("invalid", policy.ENABLED_KEY, "required"),
            id=f"{job_type} {name} invalid",
        )
        for job_type, name in chain(
            zip(repeat(policy.JobType.PULL_REQUEST), policy.PullRequestProperty),
            zip(repeat(policy.JobType.WORKFLOW_DISPATCH), policy.WorkflowDispatchProperty),
        )
    ]
    + [
        pytest.param(
            {job_type: {name: {**policy.ENABLED_RULE}}},
            True,
            None,
            id=f"{job_type} {name} valid",
        )
        for job_type, name in chain(
            zip(repeat(policy.JobType.PULL_REQUEST), policy.PullRequestProperty),
            zip(repeat(policy.JobType.WORKFLOW_DISPATCH), policy.WorkflowDispatchProperty),
        )
    ],
)
def test_check(document: dict, expected_result: bool, expected_reason: tuple[str, ...] | None):
    """
    arrange: given a policy document
    act: when check is called with the document
    assert: then the expected result and reason is returned
    """
    returned_report = policy.check(document=document)

    assert returned_report.result == expected_result
    if expected_reason is not None:
        assert returned_report.reason is not None
        assert_.substrings_in_string(expected_reason, returned_report.reason.lower())
