"""Paired devices' upkeep (0683): last seen, rename, expiry, *Forget all*, activity.

Clocks are injected; `/lan` restored from an older copy, moved, and a device forgotten
while connected are covered (workflow rule for data stored by path).
"""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from typing import TYPE_CHECKING, Final
from unittest.mock import MagicMock

from media_hygiene.review.doors import Door
from media_hygiene.review.http import Request, Response
from media_hygiene.review.lan import COOKIE_NAME, LanAccess
from media_hygiene.review.lan_activity import ACTIVITY_FILE, Activity
from media_hygiene.review.lan_app import LanApp
from media_hygiene.review.lan_phone_care import EXPIRY_DAYS, expire, touch
from media_hygiene.review.lan_phones import PHONES_FILE, TVS_FILE, PhoneBook
from media_hygiene.review.lan_phones_api import (
    FORGET_ALL_PATH,
    PHONES_PATH,
    RENAME_PATH,
)
from media_hygiene.review.local_app import PAGE_PATH
from media_hygiene.search.views import PREVIEW_PREFIX, THUMB_PREFIX
from media_hygiene.services import home_lan
from tests.support.tv_pairing import tv_paired

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    import pytest

_ADDRESS: Final = "192.168.1.20"
_PEER: Final = "192.168.1.42"
_PORT: Final = 8088
_LOCAL: Final = f"127.0.0.1:{_PORT}"
_T0: Final = datetime(2026, 11, 10, 9, 0, tzinfo=UTC)
_OLD_FILE: Final = (
    '{"phones": [{"id": "a1", "name": "Android", '
    '"paired": "2025-01-02T10:00:00Z", "digest": "00"}]}'
)


class _Home:
    """Stands for the home page: answers 200."""

    async def handle(self, _request: Request) -> Response:
        """Answer 200.

        Returns:
            An empty page.
        """
        return Response(HTTPStatus.OK, b"home")


class _Clock:
    """A clock the test moves by hand."""

    def __init__(self) -> None:
        self.now = _T0

    def __call__(self) -> datetime:
        return self.now


def _app(tmp_path: Path, clock: _Clock) -> LanApp:
    book = PhoneBook(tmp_path)
    lan = LanAccess(_ADDRESS, _PORT, b"a" * 32, secure=True)
    book.activity = Activity(book, clock)
    return LanApp(_Home(), lan, b"<p>phone</p>", phones=book)


def _phone(path: str, token: str) -> Request:
    headers = {"host": f"{_ADDRESS}:{_PORT}", "cookie": f"{COOKIE_NAME}={token}"}
    return Request("GET", path, headers, b"", Door.LAN, peer=_PEER)


def _pc(path: str, body: dict[str, str] | None = None) -> Request:
    if body is None:
        return Request("GET", path, {"host": _LOCAL}, b"", Door.PC)
    headers = {
        "host": _LOCAL,
        "content-type": "application/json",
        "origin": f"http://{_LOCAL}",
    }
    return Request("POST", path, headers, json.dumps(body).encode(), Door.PC)


def _ask(app: LanApp, request: Request) -> Response:
    return asyncio.run(app.handle(request))


def test_an_older_file_loads_and_is_dated_not_forgotten(tmp_path: Path) -> None:
    """A `phones.json` from before 0683 (or a restored copy) loads; dated at start."""
    (tmp_path / PHONES_FILE).write_text(_OLD_FILE, encoding="utf-8")
    book = PhoneBook(tmp_path)
    (phone,) = book.listed()
    assert (phone.last_seen, phone.address) == (None, "")
    assert not expire(book, _T0)
    assert book.listed()[0].last_seen == _T0  # counts from now, read back


def test_a_phone_unseen_for_long_is_forgotten(tmp_path: Path) -> None:
    """Past `EXPIRY_DAYS` the phone goes, said by name; a recent one and TVs stay."""
    book = PhoneBook(tmp_path)
    old, recent = book.add("Old"), book.add("Recent")
    assert old is not None
    assert recent is not None
    assert book.tvs().add("TV") is not None
    first, second = book.listed()
    touch(book, first, (_PEER, _T0 - timedelta(days=EXPIRY_DAYS + 1)))
    touch(book, book.listed()[1], (_PEER, _T0 - timedelta(days=EXPIRY_DAYS - 1)))
    assert expire(book, _T0) == ("Old",)
    assert [p.id for p in PhoneBook(tmp_path).listed()] == [second.id]
    assert not book.knows(old)
    assert book.knows(recent)
    assert len(book.tvs().listed()) == 1  # paired for good (0456)
    assert not expire(book, _T0)  # nothing more to write


def test_last_seen_is_written_at_most_once_an_hour(tmp_path: Path) -> None:
    """Seen again within the hour: no write, unless the address changed."""
    book = PhoneBook(tmp_path)
    assert book.add("Android") is not None
    touch(book, book.listed()[0], (_PEER, _T0))
    written = (tmp_path / PHONES_FILE).stat().st_mtime_ns
    touch(book, book.listed()[0], (_PEER, _T0 + timedelta(minutes=30)))
    assert (tmp_path / PHONES_FILE).stat().st_mtime_ns == written
    assert book.listed()[0].last_seen == _T0
    touch(book, book.listed()[0], ("192.168.1.43", _T0 + timedelta(minutes=31)))
    assert book.listed()[0].address == "192.168.1.43"
    assert (tmp_path / PHONES_FILE).stat().st_mode & 0o777 == 0o600


def test_the_card_lists_renames_and_forgets_all(tmp_path: Path) -> None:
    """Name, paired, last seen, address; rename and *Forget all* read back."""
    clock = _Clock()
    app = _app(tmp_path, clock)
    assert app.phones is not None
    token = app.phones.add("Android")
    assert token is not None
    assert app.phones.tvs().add("TV") is not None
    assert _ask(app, _phone(PAGE_PATH, token)).status is HTTPStatus.OK
    listed = json.loads(_ask(app, _pc(PHONES_PATH)).body)["phones"]
    assert listed[0]["seen"] == _T0.isoformat()
    assert listed[0]["address"] == _PEER
    assert [p["tv"] for p in listed] == [False, True]
    phone_id = listed[0]["id"]
    named = _ask(app, _pc(RENAME_PATH, {"id": phone_id, "name": "  Léa's  phone "}))
    assert json.loads(named.body)["phones"][0]["name"] == "Léa's phone"
    assert PhoneBook(tmp_path).listed()[0].name == "Léa's phone"
    bad = _ask(app, _pc(RENAME_PATH, {"id": phone_id}))
    assert bad.status is HTTPStatus.BAD_REQUEST
    gone = _ask(app, _pc(FORGET_ALL_PATH, {}))
    assert json.loads(gone.body)["phones"] == []
    assert json.loads((tmp_path / TVS_FILE).read_text(encoding="utf-8")) == {
        "phones": []
    }
    # forgotten while connected: its very next request gets the pairing page
    after = _ask(app, _phone(PAGE_PATH, token))
    assert after.status is HTTPStatus.UNAUTHORIZED


def test_activity_counts_pages_and_pictures_written_rarely(tmp_path: Path) -> None:
    """Counts per day in memory; written after `FLUSH_EVERY`, merged with the file."""
    clock = _Clock()
    app = _app(tmp_path, clock)
    assert app.phones is not None
    token = app.phones.add("Android")
    assert token is not None
    phone_id = app.phones.listed()[0].id
    for path in (PAGE_PATH, f"{PREVIEW_PREFIX}x", f"{PREVIEW_PREFIX}y", THUMB_PREFIX):
        _ask(app, _phone(path, token))
    assert not (tmp_path / ACTIVITY_FILE).exists()  # never one write per picture
    listed = json.loads(_ask(app, _pc(PHONES_PATH)).body)["phones"]
    assert listed[0]["days"] == [{"day": "2026-11-10", "pages": 1, "pictures": 2}]
    clock.now += timedelta(minutes=6)
    _ask(app, _phone(PAGE_PATH, token))
    text = (tmp_path / ACTIVITY_FILE).read_text(encoding="utf-8")
    assert '"pages":2' in text
    assert "preview" not in text  # counts only, never which photo
    assert (tmp_path / ACTIVITY_FILE).stat().st_mode & 0o777 == 0o600
    assert phone_id in text


def test_activity_restored_merges_prunes_old_days_and_forgotten(
    tmp_path: Path,
) -> None:
    """A restored older `activity.json` adds its days; old days and phones go."""
    book = PhoneBook(tmp_path)
    assert book.add("Android") is not None
    phone_id = book.listed()[0].id
    restored = {
        "devices": {
            phone_id: {"2026-11-09": {"pages": 3}, "2026-09-01": {"pages": 9}},
            "gone": {"2026-11-09": {"pages": 1}},
        }
    }
    (tmp_path / ACTIVITY_FILE).write_text(json.dumps(restored), encoding="utf-8")
    activity = Activity(book, _Clock())
    activity.flush()
    on_disk = json.loads((tmp_path / ACTIVITY_FILE).read_text(encoding="utf-8"))
    assert on_disk == {"devices": {phone_id: {"2026-11-09": {"pages": 3}}}}
    (tmp_path / ACTIVITY_FILE).write_text("{broken", encoding="utf-8")
    assert activity.of(phone_id) == []  # an unreadable file: counting starts again


def test_a_moved_lan_folder_means_pairing_again(tmp_path: Path) -> None:
    """`mh --lan` mounting another (empty) folder: nobody is known, nothing fails."""
    book = PhoneBook(tmp_path / "old")
    (tmp_path / "old").mkdir()
    token = book.add("Android")
    assert token is not None
    (tmp_path / "new").mkdir()
    moved = PhoneBook(tmp_path / "new")
    assert not moved.knows(token)
    assert Activity(moved, _Clock()).of(book.listed()[0].id) == []


def test_a_tv_forgotten_while_connected_is_refused_at_once(tmp_path: Path) -> None:
    """0702: forgotten on the PC, the same run's TV gets the pairing page next."""
    book = PhoneBook(tmp_path)
    screens, token = tv_paired(book.tvs())
    assert screens.is_paired(token, _PEER)
    assert screens.paired == 1
    assert book.tvs().forget(book.tvs().listed()[0].id)
    assert not screens.is_paired(token, _PEER)
    assert screens.paired == 0
    assert screens.arrive(token) is not None  # a new token: its code shown again
    assert not screens.is_paired("", _PEER)


def test_a_tv_unwritten_stays_paired_in_memory(tmp_path: Path) -> None:
    """`tvs.json` unwritable at pairing: the TV keeps the show for this run."""
    book = PhoneBook(tmp_path / "gone")
    screens, token = tv_paired(book.tvs())
    assert screens.is_paired(token, _PEER)
    assert not screens.is_paired("0" * 64, _PEER)


def test_a_tv_s_last_seen_is_written_at_most_once_an_hour(tmp_path: Path) -> None:
    """Its first request dates it; later ones within the hour write nothing."""
    book = PhoneBook(tmp_path)
    screens, token = tv_paired(book.tvs())
    assert screens.is_paired(token, _PEER)
    tv = book.tvs().listed()[0]
    assert tv.last_seen is not None
    assert tv.address == _PEER
    written = (tmp_path / TVS_FILE).stat().st_mtime_ns
    assert screens.is_paired(token, _PEER)
    assert screens.is_paired(token)  # no address: the one written is kept
    assert (tmp_path / TVS_FILE).stat().st_mtime_ns == written
    assert book.tvs().listed()[0].address == _PEER


def test_activity_is_written_as_mh_ends(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The counts since the last write are kept at the end of `mh`, not lost (0772)."""
    book = PhoneBook(tmp_path)
    assert book.add("Android") is not None
    ending: list[Callable[[], None]] = []
    monkeypatch.setattr(home_lan, "phone_book", lambda **_kw: book)
    monkeypatch.setattr("atexit.register", ending.append)
    monkeypatch.setattr(home_lan, "LanApp", lambda *_a, **_kw: None)
    access = LanAccess(_ADDRESS, _PORT, b"a" * 32, secure=True)
    home_lan.lan_door(MagicMock(), MagicMock(), (access, MagicMock()))
    assert book.activity is not None
    book.activity.saw(book.listed()[0], _phone(PAGE_PATH, "x"))
    assert not (tmp_path / ACTIVITY_FILE).exists()
    for flush in ending:
        flush()
    assert '"pages":1' in (tmp_path / ACTIVITY_FILE).read_text(encoding="utf-8")
