# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Provides persistence for runner tokens."""

# Using local variables means that this blueprint can only be used with a single worker. This is
# done to reduce deployment complexity as a database would otherwise be required.
_runner_tokens: set[str] = set()


def add_token(token: str) -> None:
    """Add a new token.

    Args:
        token: The token to add.
    """
    _runner_tokens.add(token)


def check_token(token: str) -> bool:
    """Check whether a token is valid.

    Args:
        token: The token to check.

    Returns:
        Whether the token is valid.
    """
    if token in _runner_tokens:
        _runner_tokens.remove(token)
        return True
    return False
