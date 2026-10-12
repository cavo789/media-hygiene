"""The `Range` header of a video request: one range, from a start or from the end."""

from __future__ import annotations

from http import HTTPStatus

import pytest

from media_hygiene.review.videos import asked_part

SIZE = 1000
WHOLE = (HTTPStatus.OK, 0, SIZE)
PART = HTTPStatus.PARTIAL_CONTENT
BEYOND = (HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE, 0, 0)


@pytest.mark.parametrize(
    ("header", "expected"),
    [
        ("", WHOLE),
        ("bytes=0-", (PART, 0, SIZE)),
        ("bytes=10-19", (PART, 10, 10)),
        (" bytes=10-19 ", (PART, 10, 10)),
        ("bytes=990-5000", (PART, 990, 10)),
        ("bytes=-10", (PART, 990, 10)),
        ("bytes=-5000", (PART, 0, SIZE)),
        ("bytes=1000-", BEYOND),
        ("bytes=-0", BEYOND),
        ("bytes=20-10", WHOLE),
        ("bytes=0-1,5-6", WHOLE),
        ("bytes=a-b", WHOLE),
        ("bytes=-", WHOLE),
        ("bytes=5", WHOLE),
        ("items=0-10", WHOLE),
    ],
)
def test_asked_part(header: str, expected: tuple[HTTPStatus, int, int]) -> None:
    """Malformed or multiple ranges: the whole file, as HTTP allows."""
    assert asked_part(header, SIZE) == expected


def test_an_empty_file_has_no_part() -> None:
    """Nothing to send from an empty file but the whole of it."""
    assert asked_part("bytes=0-", 0) == BEYOND
    assert asked_part("", 0) == (HTTPStatus.OK, 0, 0)
