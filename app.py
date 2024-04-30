# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Flask app making use of the blueprint."""
import logging

from flask import Flask

from repo_policy_compliance import blueprint, log

app = Flask(__name__)
app.register_blueprint(blueprint.repo_policy_compliance)

# the charm will run this file with gunicorn, so we need to set up logging
# we use the gunicorn logger to ensure that logs are captured and transmitted to loki
gunicorn_logger = logging.getLogger('gunicorn.error')
log.setup(gunicorn_logger.handlers)
