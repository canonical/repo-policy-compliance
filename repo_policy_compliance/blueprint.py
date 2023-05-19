# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Provides API blueprint for flask to run the policy checks."""

import logging
import os
import secrets

from flask import Blueprint, Response, request
from flask_httpauth import HTTPTokenAuth

from . import Result, all_

repo_policy_compliance = Blueprint("repo_policy_compliance", __name__)
auth = HTTPTokenAuth(scheme="Bearer")

CHARM_TOKEN_ENV_NAME = "CHARM_TOKEN"
ONE_TIME_TOKEN_ENDPOINT = "/one-time-token"
CHECK_RUN_ENDPOINT = "/check-run"
CHARM_USER = "charm"
RUNNER_USER = "runner"

RUNNER_TOKENS = set()
EXPECTED_KEYS = {
    "repository_name",
    "source_repository_name",
    "target_branch_name",
    "source_branch_name",
    "commit_sha",
}


@auth.verify_token
def verify_token(token) -> str | None:
    """Verify the authentication token.

    Args:
        The token to check.

    Returns:
        The identity associated with the token or None if no token matches.
    """
    charm_token = os.getenv(CHARM_TOKEN_ENV_NAME)

    if not charm_token:
        logging.error(f"{CHARM_TOKEN_ENV_NAME} or empty, required for generating one time tokens")
        return None

    if token == charm_token:
        return CHARM_USER

    if token in RUNNER_TOKENS:
        RUNNER_TOKENS.remove(token)
        return RUNNER_USER

    return None


@auth.get_user_roles
def get_user_roles(user) -> str | None:
    """Get the roles of a user.

    Args:
        user: The name of the suer.

    Returns:
        The role of the user if they have one, else None.
    """
    if user == CHARM_USER:
        return CHARM_USER

    if user == RUNNER_USER:
        return RUNNER_USER

    return None


@repo_policy_compliance.route(ONE_TIME_TOKEN_ENDPOINT)
@auth.login_required(role=CHARM_USER)
def one_time_token():
    """Generate a one time token for a runner.

    Returns:
        The one time token.
    """
    token = secrets.token_hex(32)
    RUNNER_TOKENS.add(token)
    return token


@repo_policy_compliance.route(CHECK_RUN_ENDPOINT, methods=["POST"])
@auth.login_required(role=RUNNER_USER)
def check_run():
    """Check whether a run should proceed.

    Returns:
        Either to proceed with the run or an error not to proceed with a reason why.
    """
    data: dict[str, str] = request.json
    missing_keys = EXPECTED_KEYS - data.keys()
    if missing_keys:
        return Response(response=f"missing data, {missing_keys=}, {EXPECTED_KEYS=}", status=400)

    if (report := all_(**data)).result == Result.FAIL:
        return Response(response=report.reason, status=403)

    return Response(status=204)
