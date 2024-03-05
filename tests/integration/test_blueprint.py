# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Tests for the flask blueprint."""

import http
import itertools
import secrets
from collections.abc import Iterable, Iterator
from uuid import uuid4

import pytest
from flask import Flask
from flask.testing import FlaskClient
from github.Branch import Branch
from github.Repository import Repository

from repo_policy_compliance import blueprint, github_client, policy

from .. import assert_
from .types_ import RequestedCollaborator

EXPECTED_PULL_REQUEST_KEYS = (
    "repository_name",
    "source_repository_name",
    "target_branch_name",
    "source_branch_name",
    "commit_sha",
)

EXPECTED_WORKFLOW_DISPATCH_KEYS = ("repository_name",)
EXPECTED_PUSH_KEYS = ("repository_name",)
EXPECTED_SCHEDULE_KEYS = ("repository_name",)
EXPECTED_DEFAULT_KEYS = ("repository_name",)


@pytest.fixture(name="app")
def fixture_app() -> Iterator[Flask]:
    """Provides a flask app with the blueprint."""
    app = Flask("test app for blueprint")
    app.register_blueprint(blueprint.repo_policy_compliance)
    app.config.update({"TESTING": True})

    yield app

    # Clean up policy
    blueprint.policy_document_path.write_text("", encoding="utf-8")


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


def get_runner_token(client: FlaskClient, charm_token: str) -> str:
    """Get a one-time token for a runner.

    Args:
        client: Client to the flask application.
        charm_token: Token with the charm role.

    Returns:
        A one-time token for a runner.
    """
    token_response = client.get(
        blueprint.ONE_TIME_TOKEN_ENDPOINT, headers={"Authorization": f"Bearer {charm_token}"}
    )
    return token_response.data.decode("utf-8")


@pytest.fixture(name="runner_token")
def fixture_runner_token(client: FlaskClient, charm_token: str) -> str:
    """The token used by the runner to check whether runs are allowed."""
    return get_runner_token(client=client, charm_token=charm_token)


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

    assert (
        runner_token_response.status_code == http.HTTPStatus.FORBIDDEN
    ), runner_token_response.data


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

    assert response.status_code == http.HTTPStatus.OK, response.data
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

    assert first_response.status_code == http.HTTPStatus.NO_CONTENT, first_response.data

    second_response = client.post(
        blueprint.CHECK_RUN_ENDPOINT,
        json=request_data,
        headers={"Authorization": f"Bearer {runner_token}"},
    )

    assert second_response.status_code == http.HTTPStatus.UNAUTHORIZED, second_response.data


@pytest.mark.parametrize(
    "endpoint",
    [
        pytest.param(
            blueprint.PULL_REQUEST_CHECK_RUN_ENDPOINT, id=blueprint.PULL_REQUEST_CHECK_RUN_ENDPOINT
        ),
        pytest.param(
            blueprint.WORKFLOW_DISPATCH_CHECK_RUN_ENDPOINT,
            id=blueprint.WORKFLOW_DISPATCH_CHECK_RUN_ENDPOINT,
        ),
        pytest.param(blueprint.PUSH_CHECK_RUN_ENDPOINT, id=blueprint.PUSH_CHECK_RUN_ENDPOINT),
        pytest.param(
            blueprint.SCHEDULE_CHECK_RUN_ENDPOINT, id=blueprint.SCHEDULE_CHECK_RUN_ENDPOINT
        ),
        pytest.param(
            blueprint.DEFAULT_CHECK_RUN_ENDPOINT, id=blueprint.DEFAULT_CHECK_RUN_ENDPOINT
        ),
    ],
)
def test_check_run_not_json(endpoint: str, client: FlaskClient, runner_token: str):
    """
    arrange: given flask application with the blueprint registered and the charm token environment
        variable set and an endpoint
    act: when check run endpoint is requested with a runner token and an data that isn't JSON
    assert: then 415 is returned.
    """
    response = client.post(endpoint, data="", headers={"Authorization": f"Bearer {runner_token}"})

    assert response.status_code == 415, response.data
    assert_.substrings_in_string(("Content-Type", "JSON"), response.data.decode("utf-8"))


@pytest.mark.parametrize(
    "endpoint, expected_keys",
    [
        pytest.param(
            blueprint.PULL_REQUEST_CHECK_RUN_ENDPOINT,
            EXPECTED_PULL_REQUEST_KEYS,
            id=blueprint.PULL_REQUEST_CHECK_RUN_ENDPOINT,
        ),
        pytest.param(
            blueprint.WORKFLOW_DISPATCH_CHECK_RUN_ENDPOINT,
            EXPECTED_WORKFLOW_DISPATCH_KEYS,
            id=blueprint.WORKFLOW_DISPATCH_CHECK_RUN_ENDPOINT,
        ),
        pytest.param(
            blueprint.PUSH_CHECK_RUN_ENDPOINT,
            EXPECTED_PUSH_KEYS,
            id=blueprint.PUSH_CHECK_RUN_ENDPOINT,
        ),
        pytest.param(
            blueprint.SCHEDULE_CHECK_RUN_ENDPOINT,
            EXPECTED_SCHEDULE_KEYS,
            id=blueprint.SCHEDULE_CHECK_RUN_ENDPOINT,
        ),
        pytest.param(
            blueprint.DEFAULT_CHECK_RUN_ENDPOINT,
            EXPECTED_DEFAULT_KEYS,
            id=blueprint.DEFAULT_CHECK_RUN_ENDPOINT,
        ),
    ],
)
def test_check_run_missing_data(
    endpoint: str, expected_keys: Iterable[str], client: FlaskClient, runner_token: str
):
    """
    arrange: given flask application with the blueprint registered and the charm token environment
        variable set and an endpoint
    act: when check run endpoint is requested with a runner token and an not all required data
    assert: then 400 is returned.
    """
    response = client.post(endpoint, json={}, headers={"Authorization": f"Bearer {runner_token}"})

    assert response.status_code == 400, response.data
    assert_.substrings_in_string(
        itertools.chain(("missing",), expected_keys), response.data.decode("utf-8")
    )


@pytest.mark.parametrize(
    "github_branch, collaborators_with_permission",
    [
        (
            f"test-branch/blueprint/pull-request/fail/{uuid4()}",
            RequestedCollaborator("admin", "admin"),
        )
    ],
    indirect=["github_branch", "collaborators_with_permission"],
)
@pytest.mark.usefixtures("collaborators_with_permission")
def test_pull_request_check_run_fail(
    client: FlaskClient, runner_token: str, github_repository: Repository, github_branch: Branch
):
    """
    arrange: given flask application with the blueprint registered and the charm token environment
        variable set
    act: when pull request check run is requested with a runner token and an invalid run
    assert: then 403 is returned.
    """
    response = client.post(
        blueprint.PULL_REQUEST_CHECK_RUN_ENDPOINT,
        json={
            "repository_name": github_repository.full_name,
            "source_repository_name": github_repository.full_name,
            "target_branch_name": github_repository.default_branch,
            "source_branch_name": github_branch.name,
            "commit_sha": github_branch.commit.sha,
        },
        headers={"Authorization": f"Bearer {runner_token}"},
    )

    assert response.status_code == http.HTTPStatus.FORBIDDEN, response.data
    assert_.substrings_in_string(("outside collaborators",), response.data.decode("utf-8"))


@pytest.mark.parametrize(
    "github_branch, collaborators_with_permission, endpoint",
    [
        pytest.param(
            f"test-branch/blueprint/workflow-dispatch/fail/{uuid4()}",
            RequestedCollaborator("admin", "admin"),
            blueprint.WORKFLOW_DISPATCH_CHECK_RUN_ENDPOINT,
            id="workflow dispatch",
        ),
        pytest.param(
            f"test-branch/blueprint/workflow-dispatch/fail/{uuid4()}",
            RequestedCollaborator("admin", "admin"),
            blueprint.PUSH_CHECK_RUN_ENDPOINT,
            id="push",
        ),
        pytest.param(
            f"test-branch/blueprint/workflow-dispatch/fail/{uuid4()}",
            RequestedCollaborator("admin", "admin"),
            blueprint.SCHEDULE_CHECK_RUN_ENDPOINT,
            id="schedule",
        ),
        pytest.param(
            f"test-branch/blueprint/workflow-dispatch/fail/{uuid4()}",
            RequestedCollaborator("admin", "admin"),
            blueprint.DEFAULT_CHECK_RUN_ENDPOINT,
            id="default",
        ),
    ],
    indirect=["github_branch", "collaborators_with_permission"],
)
@pytest.mark.usefixtures("collaborators_with_permission")
def test_branch_check_run_fail(
    client: FlaskClient,
    runner_token: str,
    github_repository: Repository,
    github_branch: Branch,
    endpoint: str,
):
    """
    arrange: given flask application with the blueprint registered and the charm token environment
        variable set
    act: when check run is requested with a runner token and an invalid run
    assert: then 403 is returned.
    """
    response = client.post(
        endpoint,
        json={
            "repository_name": github_repository.full_name,
            "branch_name": github_branch.name,
            "commit_sha": github_branch.commit.sha,
        },
        headers={"Authorization": f"Bearer {runner_token}"},
    )

    assert response.status_code == http.HTTPStatus.FORBIDDEN, response.data
    assert_.substrings_in_string(("outside collaborators",), response.data.decode("utf-8"))


@pytest.mark.parametrize(
    "endpoint, props",
    [
        pytest.param(
            blueprint.PULL_REQUEST_CHECK_RUN_ENDPOINT,
            EXPECTED_PULL_REQUEST_KEYS,
            id=blueprint.PULL_REQUEST_CHECK_RUN_ENDPOINT,
        ),
        pytest.param(
            blueprint.WORKFLOW_DISPATCH_CHECK_RUN_ENDPOINT,
            EXPECTED_WORKFLOW_DISPATCH_KEYS,
            id=blueprint.WORKFLOW_DISPATCH_CHECK_RUN_ENDPOINT,
        ),
        pytest.param(
            blueprint.PUSH_CHECK_RUN_ENDPOINT,
            EXPECTED_PUSH_KEYS,
            id=blueprint.PUSH_CHECK_RUN_ENDPOINT,
        ),
        pytest.param(
            blueprint.SCHEDULE_CHECK_RUN_ENDPOINT,
            EXPECTED_SCHEDULE_KEYS,
            id=blueprint.SCHEDULE_CHECK_RUN_ENDPOINT,
        ),
        pytest.param(
            blueprint.DEFAULT_CHECK_RUN_ENDPOINT,
            EXPECTED_DEFAULT_KEYS,
            id=blueprint.DEFAULT_CHECK_RUN_ENDPOINT,
        ),
    ],
)
def test_check_run_empty_values(
    endpoint: str, props: Iterable[str], client: FlaskClient, runner_token: str
):
    """
    arrange: given flask application with the blueprint registered and the charm token environment
        variable set and an endpoint
    act: when check run endpoint is requested with a runner token and a run with empty values
    assert: then 400 is returned.
    """
    response = client.post(
        endpoint,
        json={prop: "" for prop in props},
        headers={"Authorization": f"Bearer {runner_token}"},
    )

    assert response.status_code == 400, response.data


@pytest.mark.parametrize(
    "endpoint",
    [
        pytest.param(blueprint.CHECK_RUN_ENDPOINT, id="check run"),
        pytest.param(blueprint.PULL_REQUEST_CHECK_RUN_ENDPOINT, id="pull request"),
    ],
)
def test_pull_request_check_run_pass(
    endpoint: str, client: FlaskClient, runner_token: str, github_repository: Repository
):
    """
    arrange: given flask application with the blueprint registered and the charm token environment
        variable set
    act: when pull request check run is requested with a runner token and a valid run
    assert: then 204 is returned.
    """
    main_branch = github_repository.get_branch(github_repository.default_branch)

    response = client.post(
        endpoint,
        json={
            "repository_name": github_repository.full_name,
            "source_repository_name": github_repository.full_name,
            "target_branch_name": github_repository.default_branch,
            "source_branch_name": github_repository.default_branch,
            "commit_sha": main_branch.commit.sha,
        },
        headers={"Authorization": f"Bearer {runner_token}"},
    )

    assert response.status_code == http.HTTPStatus.NO_CONTENT, response.data


@pytest.mark.parametrize(
    "endpoint",
    [
        pytest.param(blueprint.WORKFLOW_DISPATCH_CHECK_RUN_ENDPOINT, id="workflow dispatch"),
        pytest.param(blueprint.PUSH_CHECK_RUN_ENDPOINT, id="push"),
        pytest.param(blueprint.SCHEDULE_CHECK_RUN_ENDPOINT, id="schedule"),
        pytest.param(blueprint.DEFAULT_CHECK_RUN_ENDPOINT, id="default"),
    ],
)
def test_branch_check_run_pass(
    client: FlaskClient, runner_token: str, github_repository: Repository, endpoint: str
):
    """
    arrange: given flask application with the blueprint registered and the charm token environment
        variable set
    act: when branch check run is requested with a runner token and a valid run
    assert: then 204 is returned.
    """
    main_branch = github_repository.get_branch(github_repository.default_branch)

    response = client.post(
        endpoint,
        json={
            "repository_name": github_repository.full_name,
            "branch_name": github_repository.default_branch,
            "commit_sha": main_branch.commit.sha,
        },
        headers={"Authorization": f"Bearer {runner_token}"},
    )

    assert response.status_code == http.HTTPStatus.NO_CONTENT, response.data


@pytest.mark.parametrize(
    "endpoint, method",
    [
        pytest.param(
            blueprint.ONE_TIME_TOKEN_ENDPOINT, "get", id=blueprint.ONE_TIME_TOKEN_ENDPOINT
        ),
        pytest.param(blueprint.POLICY_ENDPOINT, "post", id=blueprint.POLICY_ENDPOINT),
        pytest.param(blueprint.CHECK_RUN_ENDPOINT, "post", id=blueprint.CHECK_RUN_ENDPOINT),
        pytest.param(
            blueprint.PULL_REQUEST_CHECK_RUN_ENDPOINT,
            "post",
            id=blueprint.PULL_REQUEST_CHECK_RUN_ENDPOINT,
        ),
        pytest.param(
            blueprint.WORKFLOW_DISPATCH_CHECK_RUN_ENDPOINT,
            "post",
            id=blueprint.WORKFLOW_DISPATCH_CHECK_RUN_ENDPOINT,
        ),
        pytest.param(
            blueprint.PUSH_CHECK_RUN_ENDPOINT, "post", id=blueprint.PUSH_CHECK_RUN_ENDPOINT
        ),
        pytest.param(
            blueprint.SCHEDULE_CHECK_RUN_ENDPOINT, "post", id=blueprint.SCHEDULE_CHECK_RUN_ENDPOINT
        ),
        pytest.param(
            blueprint.DEFAULT_CHECK_RUN_ENDPOINT, "post", id=blueprint.DEFAULT_CHECK_RUN_ENDPOINT
        ),
        pytest.param(
            blueprint.ALWAYS_FAIL_CHECK_RUN_ENDPOINT,
            "post",
            id=blueprint.ALWAYS_FAIL_CHECK_RUN_ENDPOINT,
        ),
    ],
)
def test_endpoint_method_unauth(endpoint: str, method: str, client: FlaskClient):
    """
    arrange: given endpoint
    act: when a request without the Authorization header or an invalid token is sent
    assert: then 401 is returned.
    """
    response = getattr(client, method)(endpoint, headers={})

    assert response.status_code == http.HTTPStatus.UNAUTHORIZED, response.data

    response = getattr(client, method)(endpoint, headers={"Authorization": "Bearer invalid"})

    assert response.status_code == http.HTTPStatus.UNAUTHORIZED, response.data


def test_policy_invalid(client: FlaskClient, charm_token: str):
    """
    arrange: given flask application with the blueprint registered and the charm token environment
        variable set
    act: when an invalid policy is sent to the policy endpoint
    assert: then 400 is returned.
    """
    response = client.post(
        blueprint.POLICY_ENDPOINT,
        json={"invalid": "value"},
        headers={"Authorization": f"Bearer {charm_token}"},
    )

    assert response.status_code == 400, response.data


@pytest.mark.parametrize(
    "github_branch, collaborators_with_permission",
    [
        (
            f"test-branch/blueprint/pull-request/fail-policy/{uuid4()}",
            RequestedCollaborator("admin", "admin"),
        )
    ],
    indirect=["github_branch", "collaborators_with_permission"],
)
@pytest.mark.usefixtures("collaborators_with_permission")
def test_pull_request_check_run_fail_policy_disabled(
    client: FlaskClient,
    runner_token: str,
    charm_token: str,
    github_repository: Repository,
    github_branch: Branch,
):
    """
    arrange: given flask application with the blueprint registered and the charm token environment
        variable set
    act: when pull request check run is requested with a runner token and an invalid run and with
        the policy enabled and then disabled
    assert: then 403 and 204 is returned, respectively.
    """
    fail_response = client.post(
        blueprint.PULL_REQUEST_CHECK_RUN_ENDPOINT,
        json={
            "repository_name": github_repository.full_name,
            "source_repository_name": github_repository.full_name,
            "target_branch_name": github_repository.default_branch,
            "source_branch_name": github_branch.name,
            "commit_sha": github_branch.commit.sha,
        },
        headers={"Authorization": f"Bearer {runner_token}"},
    )

    assert fail_response.status_code == http.HTTPStatus.FORBIDDEN, fail_response.data

    # Disable branch protection policy
    policy_response = client.post(
        blueprint.POLICY_ENDPOINT,
        json={
            policy.JobType.PULL_REQUEST: {
                prop: {policy.ENABLED_KEY: False} for prop in policy.PullRequestProperty
            }
        },
        headers={"Authorization": f"Bearer {charm_token}"},
    )

    assert policy_response.status_code == http.HTTPStatus.NO_CONTENT, policy_response.data

    disabled_response = client.post(
        blueprint.PULL_REQUEST_CHECK_RUN_ENDPOINT,
        json={
            "repository_name": github_repository.full_name,
            "source_repository_name": github_repository.full_name,
            "target_branch_name": github_repository.default_branch,
            "source_branch_name": github_branch.name,
            "commit_sha": github_branch.commit.sha,
        },
        headers={
            "Authorization": f"Bearer {get_runner_token(client=client, charm_token=charm_token)}"
        },
    )

    assert disabled_response.status_code == http.HTTPStatus.NO_CONTENT, disabled_response.data


@pytest.mark.parametrize(
    "github_branch, collaborators_with_permission",
    [
        (
            f"test-branch/blueprint/workflow-dispatch/fail-policy/{uuid4()}",
            RequestedCollaborator("admin", "admin"),
        )
    ],
    indirect=["github_branch", "collaborators_with_permission"],
)
@pytest.mark.usefixtures("collaborators_with_permission")
def test_workflow_dispatch_check_run_fail_policy_disabled(
    client: FlaskClient,
    runner_token: str,
    charm_token: str,
    github_repository: Repository,
    github_branch: Branch,
):
    """
    arrange: given flask application with the blueprint registered and the charm token environment
        variable set
    act: when workflow dispatch check run is requested with a runner token and an invalid run and
        with the policy enabled and then disabled
    assert: then 403 and 204 is returned, respectively.
    """
    fail_response = client.post(
        blueprint.WORKFLOW_DISPATCH_CHECK_RUN_ENDPOINT,
        json={
            "repository_name": github_repository.full_name,
            "branch_name": github_branch.name,
            "commit_sha": github_branch.commit.sha,
        },
        headers={"Authorization": f"Bearer {runner_token}"},
    )

    assert fail_response.status_code == http.HTTPStatus.FORBIDDEN, fail_response.data

    # Disable branch protection policy
    policy_response = client.post(
        blueprint.POLICY_ENDPOINT,
        json={
            policy.JobType.WORKFLOW_DISPATCH: {
                prop: {policy.ENABLED_KEY: False} for prop in policy.WorkflowDispatchProperty
            }
        },
        headers={"Authorization": f"Bearer {charm_token}"},
    )

    assert policy_response.status_code == http.HTTPStatus.NO_CONTENT, policy_response.data

    disabled_response = client.post(
        blueprint.WORKFLOW_DISPATCH_CHECK_RUN_ENDPOINT,
        json={
            "repository_name": github_repository.full_name,
            "branch_name": github_branch.name,
            "commit_sha": github_branch.commit.sha,
        },
        headers={
            "Authorization": f"Bearer {get_runner_token(client=client, charm_token=charm_token)}"
        },
    )

    assert disabled_response.status_code == http.HTTPStatus.NO_CONTENT, disabled_response.data


@pytest.mark.parametrize(
    "github_branch, collaborators_with_permission",
    [
        (
            f"test-branch/blueprint/push/fail-policy/{uuid4()}",
            RequestedCollaborator("admin", "admin"),
        )
    ],
    indirect=["github_branch", "collaborators_with_permission"],
)
@pytest.mark.usefixtures("collaborators_with_permission")
def test_push_check_run_policy_disabled(
    client: FlaskClient,
    runner_token: str,
    charm_token: str,
    github_repository: Repository,
    github_branch: Branch,
):
    """
    arrange: given flask application with the blueprint registered and the charm token environment
        variable set
    act: when push check run is requested with a runner token, an invalid run and
        with the policy enabled and then disabled
    assert: then 403 and 204 is returned, respectively.
    """
    fail_response = client.post(
        blueprint.PUSH_CHECK_RUN_ENDPOINT,
        json={
            "repository_name": github_repository.full_name,
            "branch_name": github_branch.name,
            "commit_sha": github_branch.commit.sha,
        },
        headers={"Authorization": f"Bearer {runner_token}"},
    )

    assert fail_response.status_code == http.HTTPStatus.FORBIDDEN, fail_response.data

    # Disable branch protection policy
    policy_response = client.post(
        blueprint.POLICY_ENDPOINT,
        json={
            policy.JobType.PUSH: {
                prop: {policy.ENABLED_KEY: False} for prop in policy.PushProperty
            }
        },
        headers={"Authorization": f"Bearer {charm_token}"},
    )

    assert policy_response.status_code == http.HTTPStatus.NO_CONTENT, policy_response.data

    disabled_response = client.post(
        blueprint.PUSH_CHECK_RUN_ENDPOINT,
        json={
            "repository_name": github_repository.full_name,
            "branch_name": github_branch.name,
            "commit_sha": github_branch.commit.sha,
        },
        headers={
            "Authorization": f"Bearer {get_runner_token(client=client, charm_token=charm_token)}"
        },
    )

    assert disabled_response.status_code == http.HTTPStatus.NO_CONTENT, disabled_response.data


@pytest.mark.parametrize(
    "github_branch, collaborators_with_permission",
    [
        (
            f"test-branch/blueprint/schedule/fail-policy/{uuid4()}",
            RequestedCollaborator("admin", "admin"),
        )
    ],
    indirect=["github_branch", "collaborators_with_permission"],
)
@pytest.mark.usefixtures("collaborators_with_permission")
def test_schedule_check_run_policy_disabled(
    client: FlaskClient,
    runner_token: str,
    charm_token: str,
    github_repository: Repository,
    github_branch: Branch,
):
    """
    arrange: given flask application with the blueprint registered and the charm token environment
        variable set
    act: when schedule check run is requested with a runner token, an invalid run and
        with the policy enabled and then disabled
    assert: then 403 and 204 is returned, respectively.
    """
    fail_response = client.post(
        blueprint.SCHEDULE_CHECK_RUN_ENDPOINT,
        json={
            "repository_name": github_repository.full_name,
            "branch_name": github_branch.name,
            "commit_sha": github_branch.commit.sha,
        },
        headers={"Authorization": f"Bearer {runner_token}"},
    )

    assert fail_response.status_code == http.HTTPStatus.FORBIDDEN, fail_response.data

    # Disable branch protection policy
    policy_response = client.post(
        blueprint.POLICY_ENDPOINT,
        json={
            policy.JobType.SCHEDULE: {
                prop: {policy.ENABLED_KEY: False} for prop in policy.ScheduleProperty
            }
        },
        headers={"Authorization": f"Bearer {charm_token}"},
    )

    assert policy_response.status_code == http.HTTPStatus.NO_CONTENT, policy_response.data

    disabled_response = client.post(
        blueprint.SCHEDULE_CHECK_RUN_ENDPOINT,
        json={
            "repository_name": github_repository.full_name,
            "branch_name": github_branch.name,
            "commit_sha": github_branch.commit.sha,
        },
        headers={
            "Authorization": f"Bearer {get_runner_token(client=client, charm_token=charm_token)}"
        },
    )

    assert disabled_response.status_code == http.HTTPStatus.NO_CONTENT, disabled_response.data


def test_always_fail(client: FlaskClient, runner_token: str):
    """
    arrange: given flask application with the blueprint registered and the charm token environment
        variable set
    act: when always fail is requested with a runner token
    assert: then 403 is returned.
    """
    response = client.post(
        blueprint.ALWAYS_FAIL_CHECK_RUN_ENDPOINT,
        headers={"Authorization": f"Bearer {runner_token}"},
    )

    assert response.status_code == http.HTTPStatus.FORBIDDEN, response.data


@pytest.mark.parametrize(
    "invalid_token", [pytest.param("", id="empty"), pytest.param("invalid", id="invalid")]
)
def test_health_fail(client: FlaskClient, invalid_token: str, monkeypatch: pytest.MonkeyPatch):
    """
    arrange: given flask application with the blueprint registered and invalid token set in
        GITHUB_TOKEN environment variable
    act: when the health check endpoint is requested
    assert: then 500 is returned.
    """
    monkeypatch.setenv(github_client.GITHUB_TOKEN_ENV_NAME, invalid_token)

    response = client.get(blueprint.HEALTH_ENDPOINT)

    assert response.status_code == 500, response.data


def test_health(client: FlaskClient):
    """
    arrange: given flask application with the blueprint registered
    act: when the health check endpoint is requested
    assert: then 204 is returned.
    """
    response = client.get(blueprint.HEALTH_ENDPOINT)

    assert response.status_code == http.HTTPStatus.NO_CONTENT, response.data


@pytest.mark.parametrize(
    "endpoint",
    [
        pytest.param(blueprint.CHECK_RUN_ENDPOINT, id="check run endpoint"),
        pytest.param(blueprint.PULL_REQUEST_CHECK_RUN_ENDPOINT, id="PR check run endpoint"),
        pytest.param(
            blueprint.WORKFLOW_DISPATCH_CHECK_RUN_ENDPOINT,
            id="workflow dispatch check run endpoint",
        ),
        pytest.param(blueprint.DEFAULT_CHECK_RUN_ENDPOINT, id="default check run endpoint"),
        pytest.param(blueprint.PUSH_CHECK_RUN_ENDPOINT, id="push check run endpoint"),
        pytest.param(blueprint.SCHEDULE_CHECK_RUN_ENDPOINT, id="schedule check run endpoint"),
    ],
)
def test_internal_server_error(
    client: FlaskClient,
    endpoint: str,
    github_repository: Repository,
    runner_token: str,
    monkeypatch: pytest.MonkeyPatch,
):
    """
    arrange: given a monkeypatched github client get function that raises ConfigurationError.
    act: when blueprint routes are called.
    assert: 500 error is returned with reason.
    """
    monkeypatch.setenv(github_client.GITHUB_TOKEN_ENV_NAME, "")
    main_branch = github_repository.get_branch(github_repository.default_branch)
    request_data = {
        "repository_name": github_repository.full_name,
        "source_repository_name": github_repository.full_name,
        "target_branch_name": github_repository.default_branch,
        "source_branch_name": github_repository.default_branch,
        "commit_sha": main_branch.commit.sha,
    }

    response = client.post(
        endpoint, json=request_data, headers={"Authorization": f"Bearer {runner_token}"}
    )

    assert response.status_code == http.HTTPStatus.INTERNAL_SERVER_ERROR, response.data
    assert (
        "Something went wrong while configuring repository compliance policy check. "
        "Please contact the operator" in str(response.data, encoding="utf-8")
    )
