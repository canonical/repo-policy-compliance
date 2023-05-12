# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Shared types for testing."""

from dataclasses import dataclass

from github.Branch import Branch


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
