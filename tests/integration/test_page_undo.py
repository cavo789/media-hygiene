"""The ↶ Undo of a page's toast runs `mh undo <run>` itself (0601), proven on disk."""

from __future__ import annotations

import asyncio
import json
from http import HTTPStatus
from typing import TYPE_CHECKING

from media_hygiene.review.write_routes import CHANGES
from media_hygiene.search.undo_api import UNDO_PATH, latest_answer, undo_answer
from media_hygiene.services.page_undo import PageUndo
from tests.integration.test_clean_undo import clean, manifest
from tests.support.demo import build_demo
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations


def test_the_page_undoes_its_run_and_reads_the_files_back(
    locations: Locations,
) -> None:
    """The latest run undone: each file found again where it was, the disk as before."""
    build_demo(locations.data_dir)
    before = manifest(locations.data_dir)
    runtime = make_runtime(locations)
    run_id = clean(runtime)
    assert manifest(locations.data_dir) != before
    undo = PageUndo(runtime)
    assert json.loads(latest_answer(undo).body) == {"run_id": run_id}
    body = json.dumps({"run": run_id}).encode()
    answer = asyncio.run(undo_answer(undo, body))
    said = json.loads(answer.body)
    assert answer.status == HTTPStatus.OK
    assert said["meant"] > 0
    assert said["back"] == said["meant"]
    assert said["intact"] is True
    assert manifest(locations.data_dir) == before


def test_only_the_latest_run_is_undone_from_a_page(locations: Locations) -> None:
    """An older or unknown run: 409, the terminal command offered; nothing touched."""
    build_demo(locations.data_dir)
    undo = PageUndo(make_runtime(locations))
    assert json.loads(latest_answer(undo).body) == {"run_id": None}
    answer = asyncio.run(undo_answer(undo, b'{"run": "20990101-000000"}'))
    assert answer.status == HTTPStatus.CONFLICT
    assert "media-hygiene undo 20990101-000000" in json.loads(answer.body)["error"]
    assert asyncio.run(undo_answer(undo, b"{}")).status == HTTPStatus.BAD_REQUEST


def test_the_undo_route_is_a_pc_only_change() -> None:
    """Never reachable from the phone: it moves files."""
    assert UNDO_PATH in CHANGES
