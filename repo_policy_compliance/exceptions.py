# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""All the exceptions that can be raised."""


class BaseError(Exception):
    """Base class for all exceptions."""


class InputError(BaseError):
    """Input is missing or unexpected."""


class ConfigurationError(BaseError):
    """There is a problem with configuration."""


class GithubClientError(BaseError):
    """Error occurred on Github API."""
