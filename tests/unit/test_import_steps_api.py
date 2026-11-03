"""The steps after an import, switched from the home page (0481)."""

from __future__ import annotations

import asyncio
import json
from http import HTTPStatus
from typing import TYPE_CHECKING

from media_hygiene.config.import_settings import ImportStep
from media_hygiene.review.http import Request
from media_hygiene.review.import_steps_api import (
    IMPORT_STEPS_PATH,
    StepsAsked,
    import_steps_route,
    saved_steps,
    steps_of,
)

if TYPE_CHECKING:
    from pathlib import Path

_HEADERS = {"host": "127.0.0.1:8080", "content-type": "application/json"}


def test_missing_file_reads_the_default_steps(tmp_path: Path) -> None:
    """No config.toml: every step, in the chain's order."""
    assert steps_of(tmp_path / "config.toml") == [step.value for step in ImportStep]


def test_a_step_switched_off_is_written_and_read_back(tmp_path: Path) -> None:
    """The file keeps its comments; the audit comes back while another step is on."""
    config = tmp_path / "config.toml"
    config.write_text(
        "# mine\n[imports]\nthen = ['audit', 'copies', 'tags']\n", "utf-8"
    )
    steps = saved_steps(config, StepsAsked(steps=(ImportStep.TAGS, ImportStep.BURSTS)))
    assert steps == ["audit", "bursts", "tags"]
    assert config.read_text("utf-8").startswith("# mine")
    assert steps_of(config) == steps


def test_none_ticked_writes_an_empty_chain(tmp_path: Path) -> None:
    """Nothing ticked: nothing runs after the copies."""
    config = tmp_path / "config.toml"
    assert saved_steps(config, StepsAsked()) == []


def test_the_route_reads_and_writes(tmp_path: Path) -> None:
    """GET then POST answer the file's steps; a bad body is refused."""
    config = tmp_path / "config.toml"

    def ask(method: str, body: bytes = b"") -> tuple[HTTPStatus, bytes]:
        request = Request(method, IMPORT_STEPS_PATH, _HEADERS, body)
        answer = asyncio.run(import_steps_route(config, request))
        return answer.status, answer.body

    status, body = ask("GET")
    assert status == HTTPStatus.OK
    assert len(json.loads(body)["steps"]) == len(ImportStep)
    status, body = ask("POST", b'{"steps": ["copies"]}')
    assert status == HTTPStatus.OK
    assert json.loads(body)["steps"] == ["audit", "copies"]
    assert ask("POST", b'{"steps": ["nope"]}')[0] == HTTPStatus.BAD_REQUEST
    assert ask("DELETE")[0] == HTTPStatus.METHOD_NOT_ALLOWED
