"""`review-sort` at the edges: a file chosen twice, an unwritable folder, kept files."""

from __future__ import annotations

import asyncio
import json
from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest

from media_hygiene.errors import MountError, WorkbookError
from media_hygiene.services.sort_reviewing import open_sort_review
from tests.support.carrying import edit, final
from tests.support.runtime import make_runtime, output_of
from tests.support.sort_review import call, classified, first_event, reopened
from tests.support.sorting import PARTY, build_library, classify, sort

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations

READ_ONLY = 0o555
WRITABLE = 0o755


def test_a_file_edited_otherwise_in_both_places(locations: Locations) -> None:
    """Refused with the file's path and both folders; taken back, the workbook wins."""
    runtime, workbook = classified(locations)
    app = reopened(runtime)

    async def send() -> tuple[str, list[str]]:
        event, rows = await first_event(app)
        body = {"event": event, "rows": rows[:1], "category": "Best of"}
        await call(app, "POST /api/files", body)
        return event, rows

    event, rows = asyncio.run(send())
    edit(workbook, final("IMG_0000.jpg", "2016/Other"))
    with pytest.raises(WorkbookError) as refused:
        sort(runtime)
    assert "IMG_0000.jpg: page '2016/Best of', workbook '2016/Other'" in (
        refused.value.message
    )
    app = reopened(runtime)

    async def take_back() -> list[str]:
        answer = await call(app, "POST /api/forget", {"event": event, "rows": rows[:1]})
        return [photo["page"] for photo in json.loads(answer.body)["photos"]]

    assert asyncio.run(take_back())[0] == ""
    sort(runtime)
    assert (locations.data_dir / "c/2016/Other/IMG_0000.jpg").is_file()


def test_folders_it_cannot_write_and_a_workbook_open(locations: Locations) -> None:
    """Refused before serving; a save that fails says so; Excel's lock file warns."""
    runtime, workbook = classified(locations)
    (workbook.parent / "~$classify.xlsx").write_text("lock", encoding="utf-8")
    workbook.parent.chmod(READ_ONLY)
    try:
        with pytest.raises(MountError, match="cannot write"):
            open_sort_review(runtime, None)
        workbook.parent.chmod(WRITABLE)
        app = reopened(runtime)
        workbook.parent.chmod(READ_ONLY)

        async def choose() -> tuple[int, str]:
            event = (await first_event(app))[0]
            answer = await call(app, "POST /api/event", {"event": event, "name": "X"})
            return answer.status, json.loads(answer.body)["error"]

        status, error = asyncio.run(choose())
    finally:
        workbook.parent.chmod(WRITABLE)
    assert status == HTTPStatus.INTERNAL_SERVER_ERROR
    assert error.startswith("Cannot save the decisions file")
    assert "open in Excel or LibreOffice" in output_of(runtime)


def test_files_left_as_they_are_and_photos_gone(locations: Locations) -> None:
    """A protected photo takes no choice; a photo deleted since has no preview."""
    build_library(locations.data_dir)
    runtime = make_runtime(locations, {"folders": {"protected": ["C:\\Photos\\2016"]}})
    classify(runtime)
    app = reopened(runtime)
    (locations.data_dir / PARTY / "IMG_0005.jpg").unlink()

    async def try_it() -> tuple[int, str, int, bool]:
        event, rows = await first_event(app)
        body = {"event": event, "rows": rows[:1], "category": "X"}
        answer = await call(app, "POST /api/files", body)
        gone = await call(app, f"GET /preview/{rows[-1]}.jpg")
        view = json.loads((await call(app, f"GET /api/event/{event}")).body)
        movable = any(photo["movable"] for photo in view["photos"])
        return answer.status, json.loads(answer.body)["error"], gone.status, movable

    status, error, gone, movable = asyncio.run(try_it())
    assert (status, gone, movable) == (422, 404, False)
    assert "is left as it is" in error
