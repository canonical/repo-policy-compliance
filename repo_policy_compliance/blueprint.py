# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Provides API blueprint for flask to run the policy checks."""


from flask import Blueprint

repo_policy_compliance = Blueprint("repo_policy_compliance", __name__)


@repo_policy_compliance.route("/one-time-token")
def one_time_token():
    return "test"
