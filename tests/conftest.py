# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for charm tests."""

from pytest import Parser

CHARM_FILE_PARAM = "--charm-file"
FLASK_APP_IMAGE_PARAM = "--repo-policy-compliance-image"

# this is not a hardcoded password, ignore bandit warning
GITHUB_TOKEN_PARAM = "--github-token"  # nosec


def pytest_addoption(parser: Parser) -> None:
    """Parse additional pytest options.

    Args:
        parser: Pytest parser.
    """
    parser.addoption(CHARM_FILE_PARAM, action="store", help="Charm file to be deployed")
    parser.addoption(FLASK_APP_IMAGE_PARAM, action="store", help="Flask app image to be deployed")
    parser.addoption(GITHUB_TOKEN_PARAM, action="store", help="GitHub token")
