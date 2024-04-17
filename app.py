# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Flask app making use of the blueprint."""

from flask import Flask

from repo_policy_compliance import blueprint

app = Flask("production app")
app.register_blueprint(blueprint.repo_policy_compliance)
