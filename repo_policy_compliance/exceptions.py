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


class GithubApiNotFoundError(GithubClientError):
    """Error occurred on Github API that the resource is not found."""

    def __init__(self, api_message: str | None = None):
        """Initialize the exception.

        Args:
            api_message: The message from the Github API. Should be something with "not found".
        """
        self.api_message = api_message


class RetryableGithubClientError(GithubClientError):
    """Error occurred on Github API that can be retried on user's end."""
