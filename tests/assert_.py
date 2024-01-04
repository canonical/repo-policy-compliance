# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Functions that help with asserting."""

import typing


def substrings_in_string(substrings: typing.Iterable[str], string: str) -> None:
    """Assert that a string contains substrings.

    Args:
        string: The string to check.
        substrings: The sub strings that must be contained in the string.
    """
    for substring in substrings:
        assert substring in string, f"{substring!r} not in {string!r}"  # nosec
