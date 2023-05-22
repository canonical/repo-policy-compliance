# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Provides API blueprint for flask to run the policy checks."""

import logging
import os
import secrets
from typing import cast

from flask import Blueprint, Response, request
from flask_httpauth import HTTPTokenAuth

from . import Result, all_

repo_policy_compliance = Blueprint("repo_policy_compliance", __name__)
auth = HTTPTokenAuth(scheme="Bearer")
runner_tokens: set[str] = set()

# Bandit thinks this is the token value when it is the name of the environment variable with the
# token value
CHARM_TOKEN_ENV_NAME = "CHARM_TOKEN"  # nosec
# Bandit thinks this is the token value when it is the name of the endpoint to get a one time token
ONE_TIME_TOKEN_ENDPOINT = "/one-time-token"  # nosec
CHECK_RUN_ENDPOINT = "/check-run"
CHARM_USER = "charm"
CHARM_ROLE = CHARM_USER
RUNNER_USER = "runner"
RUNNER_ROLE = RUNNER_USER

EXPECTED_KEYS = {
    "repository_name",
    "source_repository_name",
    "target_branch_name",
    "source_branch_name",
    "commit_sha",
}


@auth.verify_token
def verify_token(token: str) -> str | None:
    """Verify the authentication token.

    Args:
        token: The token to check.

    Returns:
        The identity associated with the token or None if no token matches.
    """
    charm_token = os.getenv(CHARM_TOKEN_ENV_NAME)

    if not charm_token:
        logging.error(
            (
                "%s environment variable is required for generating one time tokens, it is not "
                "defined or empty"
            ),
            CHARM_TOKEN_ENV_NAME,
        )
        return None

    if token == charm_token:
        return CHARM_USER

    if token in runner_tokens:
        runner_tokens.remove(token)
        return RUNNER_USER

    return None


@auth.get_user_roles
def get_user_roles(user: str) -> str | None:
    """Get the roles of a user.

    Args:
        user: The name of the user.

    Returns:
        The role of the user if they have one, else None.
    """
    if user == CHARM_USER:
        return CHARM_ROLE

    if user == RUNNER_USER:
        return RUNNER_ROLE

    # It shouldn't be possible to get here since each valid token should be associated with a user
    return None  # pragma: no cover


@repo_policy_compliance.route(ONE_TIME_TOKEN_ENDPOINT)
@auth.login_required(role=CHARM_ROLE)
def one_time_token() -> str:
    """Generate a one time token for a runner.

    Returns:
        The one time token.
    """
    token = secrets.token_hex(32)
    runner_tokens.add(token)
    return token


@repo_policy_compliance.route(CHECK_RUN_ENDPOINT, methods=["POST"])
@auth.login_required(role=RUNNER_ROLE)
def check_run() -> Response:
    """Check whether a run should proceed.

    Returns:
        Either to proceed with the run or an error not to proceed with a reason why.
    """
    data = cast(dict[str, str], request.json)
    missing_keys = EXPECTED_KEYS - data.keys()
    if missing_keys:
        return Response(response=f"missing data, {missing_keys=}, {EXPECTED_KEYS=}", status=400)

    if (report := all_(**data)).result == Result.FAIL:
        return Response(response=report.reason, status=403)

    return Response(status=204)
