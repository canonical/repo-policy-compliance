# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Tests for the policy module."""

import pytest

from repo_policy_compliance import policy

from .. import assert_


@pytest.mark.parametrize(
    "document, expected_result, expected_reason",
    [
        pytest.param({}, True, None, id="empty"),
        pytest.param(
            {"invalid": {**policy.ENABLED_RULE}}, False, ("invalid", "additional"), id="invalid"
        ),
        pytest.param(
            {prop: {**policy.ENABLED_RULE} for prop in policy.Property}, True, None, id="all"
        ),
    ]
    + [
        pytest.param(
            {prop: {}},
            False,
            ("invalid", "enabled", "required"),
            id=f"{prop} invalid",
        )
        for prop in policy.Property
    ]
    + [
        pytest.param(
            {prop: {**policy.ENABLED_RULE}},
            True,
            None,
            id=f"{prop} valid",
        )
        for prop in policy.Property
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
