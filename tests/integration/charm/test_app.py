#  Copyright 2024 Canonical Ltd.
#  See LICENSE file for licensing details.

"""Integration tests for the charmed flask application."""

import json
from typing import cast
from urllib.request import Request, urlopen

from juju.application import Application
from pytest_operator.plugin import OpsTest

PORT = 8000


async def _get_unit_ips(ops_test: OpsTest, application_name: str) -> tuple[str, ...]:
    """Retrieve unit ip addresses of a certain application.

    Args:
        ops_test: ops_test plugin.
        application_name: application name.

    Returns:
        a tuple containing unit ip addresses.
    """
    _, status, _ = await ops_test.juju("status", "--format", "json")
    status = json.loads(status)
    units = status["applications"][application_name]["units"]
    return tuple(
        cast(str, unit_status["address"])
        for _, unit_status in sorted(units.items(), key=lambda kv: int(kv[0].split("/")[-1]))
    )


async def test_app(app: Application, ops_test: OpsTest, charm_token: str):
    """
    arrange: given a running charm
    act: when a token is generated and a check request is made
    assert: then the requests succeeds.
    """
    address = (await _get_unit_ips(ops_test=ops_test, application_name=app.name))[0]

    request = Request(f"http://{address}:{PORT}/one-time-token")
    request.add_header("Authorization", f"Bearer {charm_token}")
    assert urlopen(request).read().decode(encoding="utf-8")

    request = Request(f"http://{address}:{PORT}/health")
    assert urlopen(request).status == 204
