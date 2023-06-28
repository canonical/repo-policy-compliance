# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Functions that help with branch protection."""


from github import Consts
from github.Branch import Branch

from .types_ import BranchWithProtection


def edit(branch: Branch, branch_with_protection: BranchWithProtection) -> None:
    """Enable or disable the branch protection parameters on the given branch.

    Args:
        branch: The branch to modify.
        branch_with_protection: The branch name and its protection parameters.
    """
    if branch_with_protection.bypass_pull_request_allowance_disabled:
        branch.edit_protection(
            require_code_owner_reviews=branch_with_protection.require_code_owner_reviews,
            dismiss_stale_reviews=branch_with_protection.dismiss_stale_reviews_enabled,
            # This seems to be required as of version 1.59 of PyGithub, without it the API returns
            # an error indicating that None is not a valid value for bypass pull request
            # allowances.
            users_bypass_pull_request_allowances=[],
        )
    else:
        branch.edit_protection(
            require_code_owner_reviews=branch_with_protection.require_code_owner_reviews,
            dismiss_stale_reviews=branch_with_protection.dismiss_stale_reviews_enabled,
            users_bypass_pull_request_allowances=["gregory-schiano", "jdkanderson"],
            teams_bypass_pull_request_allowances=["is-charms"],
            apps_bypass_pull_request_allowances=["test"],
        )

    if branch_with_protection.required_signatures_enabled:
        # This API endpoint is not supported by the library, we call it ourselves
        # pylint: disable=protected-access
        branch._requester.requestJsonAndCheck(  # type: ignore
            "POST",
            url=f"{branch.protection_url}/required_signatures",
            headers={"Accept": Consts.signaturesProtectedBranchesPreview},
        )
        # pylint: enable=protected-access
