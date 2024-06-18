#!/usr/bin/env python3
# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Flask Charm entrypoint."""

import logging
import typing

import ops
import paas_app_charmer.flask

from .repo_policy_compliance import change_policy

logger = logging.getLogger(__name__)


class FlaskCharm(paas_app_charmer.flask.Charm):
    """Flask Charm service."""

    def __init__(self, *args: typing.Any) -> None:
        """Initialize the instance.

        Args:
            args: passthrough to CharmBase.
        """
        super().__init__(*args)
        self.framework.observe(self.on.config_changed, self._on_config_changed)

    def _on_config_changed(self, _: ops.ConfigChangedEvent):
        """Handle event fired when config has changed."""
        change_policy()


if __name__ == "__main__":
    ops.main.main(FlaskCharm)
