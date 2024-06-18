# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Module for interacting with repo-policy-compliance server."""

import logging

import requests
import tenacity

logger = logging.getLogger(__name__)


@tenacity.retry(
    retry=tenacity.retry_if_not_result(lambda value: value),
    wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
)
def _health_check():
    res = requests.get("http://localhost:8000")
    return res.ok


@tenacity.retry(
    retry=tenacity.retry_if_not_result(lambda value: value),
    wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
)
def change_policy():
    _health_check()
    res = requests.post("http://localhost:8000/policy/1")
    return res.ok
