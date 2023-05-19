# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Module for modifying comments."""


def remove_quote_lines(body: str) -> str:
    """Remove any lines from a comment that start with >.

    Args:
        body: The content of the comment.

    Returns:
        The comment with any lines that start with > removed.
    """
    lines = body.splitlines()
    return "\n".join(line for line in lines if not line.strip().startswith(">"))
