#  Copyright 2024 Canonical Ltd.
#  See LICENSE file for licensing details.

"""Fixtures for the github-runner-webhook-router charm."""

import os
import secrets
from time import sleep

import pytest
import pytest_asyncio
from juju.application import Application
from juju.model import Model
from pytest_operator.plugin import OpsTest

from tests.conftest import CHARM_FILE_PARAM, FLASK_APP_IMAGE_PARAM


@pytest.fixture(scope="session", name="github_token")
def fixture_github_token() -> str:
    """Get the GitHub token from the environment."""
    github_token = os.getenv("GITHUB_TOKEN")
    assert github_token
    return github_token


@pytest.fixture(scope="session", name="charm_token")
def fixture_charm_token() -> str | None:
    """Get the charm token."""
    return secrets.token_hex(16)


@pytest.fixture(name="charm_file", scope="module")
def charm_file_fixture(pytestconfig: pytest.Config) -> str:
    """Return the path to the built charm file."""
    charm = pytestconfig.getoption(CHARM_FILE_PARAM)
    assert charm, f"Please specify the {CHARM_FILE_PARAM} command line option"
    return charm


@pytest.fixture(name="flask_app_image", scope="module")
def flask_app_image_fixture(pytestconfig: pytest.Config) -> str:
    """Return the path to the flask app image"""
    flask_app_image = pytestconfig.getoption(FLASK_APP_IMAGE_PARAM)
    assert flask_app_image, f"{FLASK_APP_IMAGE_PARAM} must be set"
    return flask_app_image


@pytest.fixture(name="model", scope="module")
def model_fixture(ops_test: OpsTest) -> Model:
    """Juju model used in the test."""
    assert ops_test.model is not None
    return ops_test.model


@pytest.fixture(name="app_name", scope="module")
def app_name_fixture() -> str:
    """Application name."""
    return "repo-policy-compliance"


@pytest_asyncio.fixture(name="app", scope="module")
async def app_fixture(
    model: Model,
    charm_file: str,
    flask_app_image: str,
    app_name: str,
    github_token: str,
    charm_token: str,
) -> Application:
    """Deploy the application."""
    resources = {"flask-app-image": flask_app_image}
    config = {
        "GITHUB_TOKEN": github_token,
        "CHARM_TOKEN": charm_token,
    }
    application = await model.deploy(
        charm_file,
        resources=resources,
        application_name=app_name,
        config=config,
    )
    await model.wait_for_idle(apps=[app_name], status="active")
    return application
