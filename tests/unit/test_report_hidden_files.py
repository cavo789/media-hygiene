"""The reports folder's hidden `.mh-*` files are served to no device (0710)."""

from __future__ import annotations

import asyncio
from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest

from media_hygiene.review.report_files import report_file, report_response

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize(
    "path",
    [
        "/reports/.mh-step.json",
        "/reports/.mh-phone-page.json",
        "/reports/.mh-home.cid",
        "/reports/run/.mh-x/report.html",
        "/reports/%2Emh-step.json",
    ],
)
def test_the_tools_hidden_files_are_refused(tmp_path: Path, path: str) -> None:
    """Every `.mh-*` file or folder answers 404, as missing."""
    (tmp_path / ".mh-step.json").write_text("{}")
    (tmp_path / ".mh-phone-page.json").write_text("{}")
    (tmp_path / ".mh-home.cid").write_text("x")
    (tmp_path / "run" / ".mh-x").mkdir(parents=True)
    (tmp_path / "run" / ".mh-x" / "report.html").write_text("<p>")
    assert report_file(tmp_path, path) is None
    response = asyncio.run(report_response(tmp_path, path))
    assert response.status == HTTPStatus.NOT_FOUND


def test_a_report_is_still_served(tmp_path: Path) -> None:
    """A file whose name merely contains `.mh-` is still served."""
    (tmp_path / "a.mh-b.json").write_text("{}")
    response = asyncio.run(report_response(tmp_path, "/reports/a.mh-b.json"))
    assert response.status == HTTPStatus.OK
