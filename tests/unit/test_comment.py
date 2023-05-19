# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Tests for the comment module."""

import pytest

from repo_policy_compliance import comment


@pytest.mark.parametrize(
    "body, expected_body",
    [
        pytest.param("", "", id="empty"),
        pytest.param("line 1", "line 1", id="single line no quote"),
        pytest.param(">line 1", "", id="single line single quote"),
        pytest.param(" >line 1", "", id="single line single quote single leading space"),
        pytest.param("  >line 1", "", id="single line single quote multiple leading spaces"),
        pytest.param("\t>line 1", "", id="single line single quote single leading tab"),
        pytest.param(">>line 1", "", id="single line multiple quotes"),
        pytest.param(
            """line 1
line 2""",
            """line 1
line 2""",
            id="multiple lines no quote",
        ),
        pytest.param(
            """>line 1
line 2""",
            "line 2",
            id="multiple lines first quote",
        ),
        pytest.param(
            """line 1
>line 2""",
            "line 1",
            id="multiple lines second quote",
        ),
        pytest.param(
            """>line 1
>line 2""",
            "",
            id="multiple lines all quotes",
        ),
    ],
)
def test_remove_quote_lines(body: str, expected_body: str):
    """
    arrange: given the body of a comment
    act: when remove_quote_lines is called with the body
    assert: then the expected body is returned.
    """
    returned_body = comment.remove_quote_lines(body=body)

    assert returned_body == expected_body
