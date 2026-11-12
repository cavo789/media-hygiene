"""A guest's pairing ends the same evening (0709): refused, then the pairing page."""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime
from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest

from media_hygiene.review import lan_guest, lan_phones
from media_hygiene.review.doors import Door
from media_hygiene.review.http import Request
from media_hygiene.review.lan import COOKIE_NAME, LanAccess
from media_hygiene.review.lan_app import LanApp
from media_hygiene.review.lan_guest import guest_token, run_role
from media_hygiene.review.lan_guest_day import guest_ends, guest_over
from media_hygiene.review.lan_phone_care import expire
from media_hygiene.review.lan_phone_model import FAMILY, GUEST, Phone, digest_of
from media_hygiene.review.lan_phones import PhoneBook
from media_hygiene.review.lan_phones_api import phones_list

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from media_hygiene.review.lan_phone_model import Role

_ACCESS = LanAccess(address="192.168.1.20", port=8765, secret=b"k" * 32)
_HOST = "192.168.1.20:8765"
# Brussels in November: UTC+1. 22:30 local, then 00:30 local the next day.
_EVENING = datetime(2026, 11, 12, 21, 30, tzinfo=UTC)
_NIGHT = datetime(2026, 11, 12, 23, 30, tzinfo=UTC)


@pytest.fixture(autouse=True)
def _brussels(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """The process zone of a Belgian user."""
    monkeypatch.setenv("TZ", "Europe/Brussels")
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()


def _clock(monkeypatch: pytest.MonkeyPatch, at: datetime) -> None:
    monkeypatch.setattr(lan_phones, "now_utc", lambda: at)
    monkeypatch.setattr(lan_guest, "now_utc", lambda: at)


def _phone(token: str, role: Role) -> Phone:
    return Phone(
        id=role, name=role, paired=_EVENING, digest=digest_of(token), role=role
    )


def test_a_guest_ends_at_the_next_local_midnight() -> None:
    """Paired at 22:30 in Brussels: over at 00:00 Brussels, 23:00 UTC."""
    assert guest_ends(_EVENING) == datetime(2026, 11, 12, 23, 0, tzinfo=UTC)
    guest = _phone("g", GUEST)
    assert not guest_over(guest, datetime(2026, 11, 12, 22, 59, tzinfo=UTC))
    assert guest_over(guest, datetime(2026, 11, 12, 23, 0, tzinfo=UTC))
    assert not guest_over(_phone("f", FAMILY), _NIGHT)


def test_a_guest_kept_for_good_is_refused_after_midnight(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The family's phone still opens; the guest's cookie no longer does."""
    book = PhoneBook(tmp_path)
    book.save((_phone("g", GUEST), _phone("f", FAMILY)))
    _clock(monkeypatch, _EVENING)
    assert book.holder("g") is not None
    _clock(monkeypatch, _NIGHT)
    assert book.holder("g") is None
    assert book.holder("f") is not None


def test_an_ended_guest_gets_the_pairing_page(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """After midnight, `GET /` of the guest answers the pairing page (401)."""
    book = PhoneBook(tmp_path)
    book.save((_phone("g", GUEST),))
    _clock(monkeypatch, _NIGHT)
    app = LanApp(object(), _ACCESS, b"<p>phone</p>", phones=book)  # type: ignore[arg-type]
    headers = {"host": _HOST, "cookie": f"{COOKIE_NAME}=g"}
    reply = asyncio.run(app.handle(Request("GET", "/", headers, b"", Door.LAN)))
    assert reply.status == HTTPStatus.UNAUTHORIZED


def test_a_guest_of_this_run_ends_at_midnight_too(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The run token is drawn for the day: yesterday's opens nothing."""
    _clock(monkeypatch, _EVENING)
    yesterday = guest_token(_ACCESS)
    headers = {"host": _HOST, "cookie": f"{COOKIE_NAME}={yesterday}"}
    assert run_role(_ACCESS, Request("GET", "/", headers)) == GUEST
    _clock(monkeypatch, _NIGHT)
    assert guest_token(_ACCESS) != yesterday
    assert run_role(_ACCESS, Request("GET", "/", headers)) is None


def test_the_next_start_forgets_the_ended_guests(tmp_path: Path) -> None:
    """`expire` names them; the family's phone stays."""
    book = PhoneBook(tmp_path)
    guest = _phone("g", GUEST).model_copy(update={"last_seen": _EVENING})
    family = _phone("f", FAMILY).model_copy(update={"last_seen": _EVENING})
    book.save((guest, family))
    assert not expire(book, _EVENING)
    assert expire(book, _NIGHT) == (GUEST,)
    assert [p.role for p in book.listed()] == [FAMILY]


def test_the_card_says_until_when(tmp_path: Path) -> None:
    """The PC's list gives a guest's end; empty for the family."""
    book = PhoneBook(tmp_path)
    book.save((_phone("g", GUEST), _phone("f", FAMILY)))
    listed = phones_list(book).body.decode()
    assert '"until":"2026-11-13T00:00:00+01:00"' in listed.replace(" ", "")
    assert '"until":""' in listed.replace(" ", "")
