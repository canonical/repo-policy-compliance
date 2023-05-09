# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Tests for the target_branch_protection function."""

import typing
from dataclasses import dataclass
from uuid import uuid4

import pytest
from github.Branch import Branch

from repo_policy_compliance import Result, target_branch_protection
from repo_policy_compliance.exceptions import GithubClientError, InputError
from repo_policy_compliance.github_client import GITHUB_TOKEN_ENV_NAME


def assert_substrings_in_string(substrings: typing.Iterable[str], string: str) -> None:
    """Assert that a string contains substrings.

    Args:
        string: The string to check.
        substrings: The sub strings that must be contained in the string.
    """
    for substring in substrings:
        assert substring in string, f"{substring!r} not in {string!r}"  # nosec


@dataclass
class BranchWithProtection:
    """Class providing parameters for branch protection.

    Attributes:
        name: The name of the Github branch.
        github_branch: The Github branch object.
        branch_protection_enabled: True if we need to enable branch protection enabled.
        require_code_owner_reviews: True if branch requires review from code owner.
        dismiss_stale_reviews_enabled: True if branch dismisses stale reviews.
        bypass_pull_request_allowance_disabled: True if users/teams/apps are allowed to bypass
            pull requests.
        required_signatures_enabled: True if branch requires signatures.
    """

    name: str
    github_branch: Branch | None = None
    branch_protection_enabled: bool = True
    require_code_owner_reviews: bool = True
    dismiss_stale_reviews_enabled: bool = True
    bypass_pull_request_allowance_disabled: bool = True
    required_signatures_enabled: bool = True


@pytest.mark.parametrize(
    "github_branch, reason_string_array",
    [
        pytest.param(
            BranchWithProtection(name=f"not-protected/{uuid4()}", branch_protection_enabled=False),
            ("not enabled"),
            id="branch_protection disabled",
        ),
        pytest.param(
            BranchWithProtection(
                name=f"no-code-owner-review/{uuid4()}", require_code_owner_reviews=False
            ),
            ("codeowner", "pull request", "review", "not required"),
            id="code-owner missing",
        ),
        pytest.param(
            BranchWithProtection(
                name=f"stale-review-not-dismissed/{uuid4()}",
                dismiss_stale_reviews_enabled=False,
            ),
            ("stale", "reviews", "not dismissed"),
            id="stale-review not-dismissed",
        ),
        pytest.param(
            BranchWithProtection(
                name=f"pull-request-allowance-not-empty/{uuid4()}",
                bypass_pull_request_allowance_disabled=False,
            ),
            ("pull request", "reviews", "can be bypassed"),
            id="pull-request-allowance not empty",
        ),
        pytest.param(
            BranchWithProtection(
                name=f"requires-signature/{uuid4()}", required_signatures_enabled=False
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
    act: when target_branch_protection is called with the name of the branch.
    assert: then a fail report is returned.
    """
    # The github_client is injected
    report = target_branch_protection(  # pylint: disable=no-value-for-parameter
        repository_name=github_repository_name, branch_name=github_branch.name
    )

    assert_substrings_in_string(reason_string_array, str(report.reason))
    assert github_branch.name in str(report.reason)
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
    act: when target_branch_protection is called with the name of the branch.
    assert: then a pass report is returned.
    """
    # The github_client is injected
    report = target_branch_protection(  # pylint: disable=no-value-for-parameter
        repository_name=github_repository_name, branch_name=github_branch.name
    )

    assert report.reason is None
    assert report.result == Result.PASS


@pytest.mark.parametrize(
    "github_token_value,exception_context,exception_message",
    [
        pytest.param("", pytest.raises(InputError), "was not provided", id="github_token empty"),
        pytest.param(
            None, pytest.raises(GithubClientError), "Bad Credential error", id="github_token none"
        ),
        pytest.param(
            "abcd",
            pytest.raises(GithubClientError),
            "Bad Credential error",
            id="github_token wrong",
        ),
    ],
)
def test_github_token(
    github_token_value: str | None,
    exception_context: typing.ContextManager,
    exception_message: str,
    github_repository_name: str,
    monkeypatch: pytest.MonkeyPatch,
):
    """
    arrange: A github repository name and a missing github token.
    act: when the github client is injected to target_branch_protection.
    assert: An expected error is raised with a specific error message.
    """
    monkeypatch.delenv(GITHUB_TOKEN_ENV_NAME)
    monkeypatch.setenv(GITHUB_TOKEN_ENV_NAME, str(github_token_value))
    with exception_context as error:
        # The github_client is injected
        target_branch_protection(  # pylint: disable=no-value-for-parameter
            repository_name=github_repository_name, branch_name="arbitrary"
        )
    assert_substrings_in_string([GITHUB_TOKEN_ENV_NAME, exception_message], str(error.value))
