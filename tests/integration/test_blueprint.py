# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Tests for the flask blueprint."""

import itertools
import secrets
from uuid import uuid4

import pytest
from flask import Flask
from flask.testing import FlaskClient
from github.Branch import Branch
from github.Repository import Repository

from repo_policy_compliance import blueprint

from .. import assert_


@pytest.fixture(name="app")
def fixture_app() -> Flask:
    """Provides a flask app with the blueprint."""
    app = Flask("test app for blueprint")
    app.register_blueprint(blueprint.repo_policy_compliance)
    app.config.update({"TESTING": True})

    return app


@pytest.fixture(name="client")
def fixture_client(app: Flask) -> FlaskClient:
    """Client to send requests to the flask app."""
    return app.test_client()


@pytest.fixture(name="charm_token")
def fixture_charm_token(monkeypatch: pytest.MonkeyPatch) -> str:
    """The token used by the charm to generate one time tokens."""
    token = secrets.token_hex(32)
    monkeypatch.setenv(blueprint.CHARM_TOKEN_ENV_NAME, token)
    return token


@pytest.fixture(name="runner_token")
def fixture_runner_token(client: FlaskClient, charm_token: str) -> str:
    """The token used by the runner to check whether runs are allowed."""
    token_response = client.get(
        blueprint.ONE_TIME_TOKEN_ENDPOINT, headers={"Authorization": f"Bearer {charm_token}"}
    )
    return token_response.data.decode("utf-8")


def test_one_time_token_no_auth(client: FlaskClient):
    """
    arrange: given flask application with the blueprint registered and the charm token environment
        variable set
    act: when a one time token is requested without an authorization header provided
    assert: then 401 is returned.
    """
    response = client.get(blueprint.ONE_TIME_TOKEN_ENDPOINT)

    assert response.status_code == 401, response.data


def test_one_time_token_wrong_auth(client: FlaskClient):
    """
    arrange: given flask application with the blueprint registered and the charm token environment
        variable set
    act: when a one time token is requested with the wrong token
    assert: then 401 is returned.
    """
    response = client.get(
        blueprint.ONE_TIME_TOKEN_ENDPOINT, headers={"Authorization": f"Bearer invalid"}
    )

    assert response.status_code == 401, response.data


def test_one_time_token_as_runner(client: FlaskClient, runner_token: str):
    """
    arrange: given flask application with the blueprint registered and the charm token environment
        variable set
    act: when a one time token is requested with a runner token
    assert: then 401 is returned.
    """
    # Try to generate another runner token using it
    runner_token_response = client.get(
        blueprint.ONE_TIME_TOKEN_ENDPOINT,
        headers={"Authorization": f"Bearer {runner_token}"},
    )

    assert runner_token_response.status_code == 403, runner_token_response.data


def test_one_time_token(client: FlaskClient, charm_token: str):
    """
    arrange: given flask application with the blueprint registered and the charm token environment
        variable set
    act: when a one time token is requested with the charm token
    assert: then it is returned.
    """
    response = client.get(
        blueprint.ONE_TIME_TOKEN_ENDPOINT, headers={"Authorization": f"Bearer {charm_token}"}
    )

    assert response.status_code == 200, response.data
    assert response.data


def test_check_run_twice_same_token(
    client: FlaskClient, runner_token: str, github_repository: Repository
):
    """
    arrange: given flask application with the blueprint registered and the charm token environment
        variable set
    act: when check run is requested with a runner token and a valid run multiple times
    assert: then 401 is returned for the second run.
    """
    main_branch = github_repository.get_branch(github_repository.default_branch)
    request_data = {
        "repository_name": github_repository.full_name,
        "source_repository_name": github_repository.full_name,
        "target_branch_name": github_repository.default_branch,
        "source_branch_name": github_repository.default_branch,
        "commit_sha": main_branch.commit.sha,
    }

    first_response = client.post(
        blueprint.CHECK_RUN_ENDPOINT,
        json=request_data,
        headers={"Authorization": f"Bearer {runner_token}"},
    )

    assert first_response.status_code == 204, first_response.data

    second_response = client.post(
        blueprint.CHECK_RUN_ENDPOINT,
        json=request_data,
        headers={"Authorization": f"Bearer {runner_token}"},
    )

    assert second_response.status_code == 401, second_response.data


def test_check_run_missing_data(client: FlaskClient, runner_token: str):
    """
    arrange: given flask application with the blueprint registered and the charm token environment
        variable set
    act: when check run is requested with a runner token and an not all required data
    assert: then 400 is returned.
    """
    response = client.post(
        blueprint.CHECK_RUN_ENDPOINT,
        json={},
        headers={"Authorization": f"Bearer {runner_token}"},
    )

    assert response.status_code == 400, response.data
    assert_.substrings_in_string(
        itertools.chain(("missing data"), blueprint.EXPECTED_KEYS), response.data.decode("utf-8")
    )


@pytest.mark.parametrize(
    "github_branch",
    [f"test-branch/blueprint/fail/{uuid4()}"],
    indirect=True,
)
def test_check_run_fail(
    client: FlaskClient, runner_token: str, github_repository: Repository, github_branch: Branch
):
    """
    arrange: given flask application with the blueprint registered and the charm token environment
        variable set
    act: when check run is requested with a runner token and an invalid run
    assert: then 403 is returned.
    """
    response = client.post(
        blueprint.CHECK_RUN_ENDPOINT,
        json={
            "repository_name": github_repository.full_name,
            "source_repository_name": github_repository.full_name,
            "target_branch_name": github_repository.default_branch,
            "source_branch_name": github_branch.name,
            "commit_sha": github_branch.commit.sha,
        },
        headers={"Authorization": f"Bearer {runner_token}"},
    )

    assert response.status_code == 403, response.data
    assert_.substrings_in_string(
        ("branch protection", "not enabled"), response.data.decode("utf-8")
    )


def test_check_run_pass(client: FlaskClient, runner_token: str, github_repository: Repository):
    """
    arrange: given flask application with the blueprint registered and the charm token environment
        variable set
    act: when check run is requested with a runner token and a valid run
    assert: then 204 is returned.
    """
    main_branch = github_repository.get_branch(github_repository.default_branch)

    response = client.post(
        blueprint.CHECK_RUN_ENDPOINT,
        json={
            "repository_name": github_repository.full_name,
            "source_repository_name": github_repository.full_name,
            "target_branch_name": github_repository.default_branch,
            "source_branch_name": github_repository.default_branch,
            "commit_sha": main_branch.commit.sha,
        },
        headers={"Authorization": f"Bearer {runner_token}"},
    )

    assert response.status_code == 204, response.data
