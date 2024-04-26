#  Copyright 2024 Canonical Ltd.
#  See LICENSE file for licensing details.

"""Integration tests for the charmed flask application."""

import json
from typing import cast
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest
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


# http scheme is known to be used and therefore we can ignore the security warning in the test
async def test_app(app: Application, ops_test: OpsTest, charm_token: str):
    """
    arrange: given a running charm
    act: when a token is generated and a check request is made
    assert: then the requests succeeds.
    """
    unit_ips = await _get_unit_ips(ops_test=ops_test, application_name=app.name)
    assert len(unit_ips) >= 2

    request = Request(f"http://{unit_ips[0]}:{PORT}/one-time-token")
    request.add_header("Authorization", f"Bearer {charm_token}")
    with urlopen(request) as response:  # nosec: B310
        one_time_token = response.read().decode(encoding="utf-8")
    assert one_time_token

    request = Request(f"http://{unit_ips[0]}:{PORT}/health")
    with urlopen(request) as response:  # nosec: B310
        assert response.status == 204

    request = Request(f"http://{unit_ips[1]}:{PORT}/auth-health")
    request.add_header("Authorization", f"Bearer {one_time_token}")
    with urlopen(request) as response:  # nosec: B310
        assert response.status == 204
    with pytest.raises(HTTPError) as exc:
        with urlopen(request):  # nosec: B310
            pass
    assert exc.value.code == 401

    request = Request(f"http://{unit_ips[0]}:{PORT}/auth-health")
    request.add_header("Authorization", f"Bearer {one_time_token}")
    with pytest.raises(HTTPError) as exc:
        with urlopen(request):  # nosec: B310
            pass
    assert exc.value.code == 401
