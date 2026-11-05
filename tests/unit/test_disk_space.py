"""The disk space page: limits read back, previews emptied, phone refused (0539)."""

from __future__ import annotations

import asyncio
import json
from http import HTTPStatus
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, Final

import pytest

from media_hygiene.review.doors import Door
from media_hygiene.review.http import Request
from media_hygiene.review.page_header import PAGE_STEPS
from media_hygiene.services.disk_here import DiskHere
from media_hygiene.services.disk_space import (
    Limits,
    limits_of,
    previews_bytes,
    save_limits,
)

if TYPE_CHECKING:
    from pathlib import Path

_JSON: Final = {"host": "127.0.0.1", "content-type": "application/json"}


def _here(tmp_path: Path) -> DiskHere:
    """The page on a temporary folder; the status stubbed: an empty quarantine."""
    locations = SimpleNamespace(config_file=tmp_path / "config.toml")
    runtime = SimpleNamespace(locations=locations, previews_dir=tmp_path / "previews")
    fresh: Any = SimpleNamespace(runtime=lambda: runtime)
    return DiskHere(fresh)


@pytest.fixture(autouse=True)
def _quarantine(monkeypatch: pytest.MonkeyPatch) -> None:
    """Nothing in the quarantine."""
    status = SimpleNamespace(quarantine=SimpleNamespace(runs=(), size=0))
    monkeypatch.setattr(
        "media_hygiene.services.disk_space.read_status", lambda _r: status
    )


def test_limits_keep_comments_and_are_read_back(tmp_path: Path) -> None:
    """Both written, the comment and other keys kept."""
    config = tmp_path / "config.toml"
    config.write_text("# mine\n[clean]\n# keep\nquarantine_headroom_gb = 1\n", "utf-8")
    saved = save_limits(config, Limits(previews_max_gb=2.5, purge_hint_days=9))
    assert saved == Limits(previews_max_gb=2.5, purge_hint_days=9)
    assert limits_of(config) == saved
    text = config.read_text("utf-8")
    assert "# mine" in text
    assert "# keep" in text


def test_the_post_empties_the_previews_and_says_what_is_on_disk(tmp_path: Path) -> None:
    """The answer is the state read again."""
    previews = tmp_path / "previews"
    previews.mkdir()
    (previews / "a.jpg").write_bytes(b"x" * 10)
    assert previews_bytes(previews) == 10
    post = Request("POST", "/disk-space/api/empty", _JSON, b"{}")
    reply = asyncio.run(_here(tmp_path).handle(post))
    assert reply.status is HTTPStatus.OK
    assert json.loads(reply.body)["previews_empty"] is True
    assert not list(previews.iterdir())


def test_a_bad_limit_is_refused_and_writes_nothing(tmp_path: Path) -> None:
    """A limit at zero: 400, no file."""
    body = json.dumps({"previews_max_gb": 0, "purge_hint_days": 1}).encode()
    post = Request("POST", "/disk-space/api/limits", _JSON, body)
    assert asyncio.run(_here(tmp_path).handle(post)).status is HTTPStatus.BAD_REQUEST
    assert not (tmp_path / "config.toml").exists()


def test_a_phone_never_reaches_it(tmp_path: Path) -> None:
    """Off the PC's door: refused."""
    get = Request("GET", "/disk-space/", _JSON, door=Door.LAN)
    assert asyncio.run(_here(tmp_path).handle(get)).status is HTTPStatus.FORBIDDEN


def test_the_page_renders(tmp_path: Path) -> None:
    """Its frame and its chapter."""
    assert "disk_space.html.j2" in PAGE_STEPS
    get = Request("GET", "/disk-space/", _JSON)
    assert b'id="previewsSize"' in asyncio.run(_here(tmp_path).handle(get)).body
