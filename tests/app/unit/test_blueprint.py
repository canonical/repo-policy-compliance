# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Tests for the blueprint module."""

# internal functions are being accessed for testing.
# pylint: disable=protected-access

from unittest.mock import MagicMock

import pytest

import repo_policy_compliance.blueprint
from repo_policy_compliance import UsedPolicy


@pytest.mark.parametrize(
    "policy_content, env, expected_document",
    [
        pytest.param("", {}, UsedPolicy.ALLOW_FORKS, id="all defaults"),
        pytest.param("""{"test":"content"}""", {}, {"test": "content"}, id="policy document"),
        pytest.param(
            """{"test":"content"}""",
            {"DISALLOW_FORKS": "true"},
            {"test": "content"},
            id="policy document & env",
        ),
        pytest.param(
            """{"test":"content"}""",
            {"FLASK_DISALLOW_FORKS": "true"},
            {"test": "content"},
            id="policy document & flask env",
        ),
        pytest.param("", {"DISALLOW_FORKS": "true"}, UsedPolicy.ALL, id="env"),
        pytest.param("", {"FLASK_DISALLOW_FORKS": "true"}, UsedPolicy.ALL, id="flask env"),
        pytest.param("", {"DISALLOW_FORKS": "false"}, UsedPolicy.ALLOW_FORKS, id="env false"),
        pytest.param(
            "", {"FLASK_DISALLOW_FORKS": "false"}, UsedPolicy.ALLOW_FORKS, id="flask env false"
        ),
    ],
)
def test__get_policy_document(
    monkeypatch: pytest.MonkeyPatch,
    policy_content: str,
    env: dict,
    expected_document: dict | UsedPolicy,
):
    """
    arrange: given policy contents and disallow forks environment variables.
    act: when _get_policy_document is called.
    assert: expected policy is returned.
    """
    policy_document_mock = MagicMock()
    policy_document_mock.read_text = MagicMock(return_value=policy_content)
    monkeypatch.setattr(
        repo_policy_compliance.blueprint, "policy_document_path", policy_document_mock
    )
    for key, value in env.items():
        monkeypatch.setenv(key, value)

    assert repo_policy_compliance.blueprint._get_policy_document() == expected_document
