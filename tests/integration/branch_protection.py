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
    require_code_owner_reviews = branch_with_protection.require_code_owner_reviews

    if not branch_with_protection.bypass_pull_request_allowance_disabled:
        post_parameters = {
            "required_status_checks": None,
            "enforce_admins": None,
            "required_pull_request_reviews": {
                "dismiss_stale_reviews": branch_with_protection.dismiss_stale_reviews_enabled,
                "require_code_owner_reviews": require_code_owner_reviews,
                "bypass_pull_request_allowances": {
                    "users": ["gregory-schiano", "jdkanderson"],
                    "teams": ["is-charms"],
                    "apps": ["test"],
                },
            },
            "restrictions": None,
        }

        # This API endpoint is not supported by the library, we call it ourselves
        # pylint: disable=protected-access
        branch._requester.requestJsonAndCheck(  # type: ignore
            "PUT",
            branch.protection_url,
            headers={"Accept": Consts.mediaTypeRequireMultipleApprovingReviews},
            input=post_parameters,
        )
        # pylint: enable=protected-access

        return

    branch.edit_protection(
        require_code_owner_reviews=branch_with_protection.require_code_owner_reviews,
        dismiss_stale_reviews=branch_with_protection.dismiss_stale_reviews_enabled,
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
