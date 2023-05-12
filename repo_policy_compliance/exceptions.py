# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""All the exceptions that can be raised."""


class BaseError(Exception):
    """Base class for all exceptions."""


class InputError(BaseError):
    """Input is missing or unexpected."""


class GithubClientError(BaseError):
    """Error occurred on Github API."""
