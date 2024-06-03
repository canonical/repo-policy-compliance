# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Functions that help with branch protection."""


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
            # This seems to be required as of version 1.59 of PyGithub, without it the API returns
            # an error indicating that None is not a valid value for bypass pull request
            # allowances. Mypy also seems to be finding the wrong argument name
            # user_bypass_pull_request_allowances which is not a valid argument. Reported here:
            # https://github.com/PyGithub/PyGithub/issues/2578
            users_bypass_pull_request_allowances=[],  # type: ignore
        )
    else:
        branch.edit_protection(
            users_bypass_pull_request_allowances=[  # type: ignore
                "cbartz",
                "gregory-schiano",
                "jdkanderson",
            ],
            teams_bypass_pull_request_allowances=["is-charms"],  # type: ignore
            apps_bypass_pull_request_allowances=["test"],  # type: ignore
        )
