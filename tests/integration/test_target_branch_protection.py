# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""Tests for the target_branch_protection function."""


import pytest
from github import GitRef


def test_success(git_branch: GitRef):
    """
    arrange: given a branch with the required protection settings
    act: when target_branch_protection is called with the name of the branch
    assert: then the returned report has a success result
    """
    pytest.set_trace()
