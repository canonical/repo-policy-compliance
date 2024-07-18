#  Copyright 2024 Canonical Ltd.
#  See LICENSE file for licensing details.

"""Fixtures for the repo-policy-compliance charm."""

import secrets

import pytest
import pytest_asyncio
from juju.application import Application
from juju.model import Model
from pytest_operator.plugin import OpsTest

from tests.conftest import CHARM_FILE_PARAM, FLASK_APP_IMAGE_PARAM, GITHUB_TOKEN_PARAM


@pytest.fixture(scope="session", name="github_token")
def fixture_github_token(pytestconfig: pytest.Config) -> str:
    """Get the GitHub token."""
    token = pytestconfig.getoption(GITHUB_TOKEN_PARAM)
    assert token, "Please provide a GitHub token"
    return token


@pytest.fixture(scope="session", name="charm_token")
def fixture_charm_token() -> str | None:
    """Get the charm token."""
    return secrets.token_hex(16)


@pytest.fixture(scope="session", name="tokens")
def fixture_tokens(github_token: str, charm_token: str) -> dict[str, str]:
    """Return the GitHub and charm tokens."""
    return {"github_token": github_token, "charm_token": charm_token}


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


@pytest_asyncio.fixture(name="app", scope="function")
async def app_fixture(
    model: Model,
    charm_file: str,
    flask_app_image: str,
    app_name: str,
    tokens: dict[str, str],
) -> Application:
    """Deploy the application."""
    resources = {"flask-app-image": flask_app_image}
    config = tokens
    application = await model.deploy(
        charm_file, resources=resources, application_name=app_name, config=config, num_units=2
    )

    database_name = "postgresql-k8s"
    await model.deploy(
        database_name,
        channel="14/edge",
        series="jammy",
        trust=True,
        config={
            "profile": "testing",
            "plugin_hstore_enable": "true",
            "plugin_pg_trgm_enable": "true",
        },
        revision=239
    )
    await model.integrate(app_name, f"{database_name}:database")
    await model.wait_for_idle(apps=[app_name, database_name], status="active")

    return application
