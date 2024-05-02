# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Shared types for testing."""

from dataclasses import dataclass
from typing import Literal, NamedTuple


@dataclass
class BranchWithProtection:
    """Class providing parameters for branch protection.

    Attributes:
        branch_protection_enabled: True if we need to enable branch protection enabled.
        bypass_pull_request_allowance_disabled: True if users/teams/apps are allowed to bypass
            pull requests.
    """

    branch_protection_enabled: bool = True
    bypass_pull_request_allowance_disabled: bool = True


class RequestedCollaborator(NamedTuple):
    """Information about the requested collaborators to be added.

    Attributes:
        permission: The permission the collaborators should have.
        role_name: The name of the role the collaborators should have
    """

    permission: Literal["admin", "pull"]
    role_name: str
