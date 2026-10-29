"""The TVs paired for good in `/lan/tvs.json`, and the code field on top (0456)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.review.lan_phones import TVS_FILE, PhoneBook
from media_hygiene.review.lan_phones_api import phones_list
from media_hygiene.slideshow.screens import Screens

if TYPE_CHECKING:
    from pathlib import Path


def _paired(book: PhoneBook | None) -> tuple[Screens, str]:
    """A TV arrived and paired by the code it shows.

    Args:
        book: The TVs' file, or None in memory.

    Returns:
        The TVs and the TV's token.
    """
    screens = Screens(book)
    token = screens.arrive("")
    assert token is not None
    code = screens.code_of(token)
    assert code is not None
    assert screens.confirm(code)
    return screens, token


def _waits(screens: Screens) -> bool:
    """Ask afresh whether a TV waits (no narrowing kept between two asks).

    Args:
        screens: The TVs.

    Returns:
        `Screens.waiting`.
    """
    return screens.waiting


def test_a_tv_waiting_is_said_then_no_more_once_paired() -> None:
    """The remote knows a TV shows its code until a phone typed it."""
    screens = Screens()
    assert not _waits(screens)
    token = screens.arrive("")
    assert token is not None
    assert _waits(screens)
    code = screens.code_of(token)
    assert code is not None
    assert screens.confirm(code)
    assert not _waits(screens)


def test_a_tv_stays_paired_after_a_restart(tmp_path: Path) -> None:
    """The server rebuilt from the same `/lan` folder knows the TV: no code."""
    _, token = _paired(PhoneBook(tmp_path).tvs())
    assert token not in (tmp_path / TVS_FILE).read_text("utf-8")  # only its hash
    again = Screens(PhoneBook(tmp_path).tvs())
    assert again.is_paired(token)
    assert again.arrive(token) is None
    assert again.paired == 1


def test_an_unknown_token_gets_a_code(tmp_path: Path) -> None:
    """A token the file does not hold is a stranger's."""
    _paired(PhoneBook(tmp_path).tvs())
    again = Screens(PhoneBook(tmp_path).tvs())
    assert not again.is_paired("f" * 64)
    assert again.arrive("f" * 64) is not None


def test_a_corrupt_file_means_codes_again(tmp_path: Path) -> None:
    """An unreadable `tvs.json` pairs the TVs again, nothing raised."""
    _, token = _paired(PhoneBook(tmp_path).tvs())
    (tmp_path / TVS_FILE).write_text("{not json", "utf-8")
    again = Screens(PhoneBook(tmp_path).tvs())
    assert not again.is_paired(token)
    assert again.arrive(token) is not None


def test_in_memory_the_tv_pairs_again_after_a_restart() -> None:
    """Plain HTTP without `/lan`: nothing written, a new run asks the code."""
    _, token = _paired(None)
    assert not Screens().is_paired(token)


def test_the_pcs_card_lists_and_forgets_the_tv(tmp_path: Path) -> None:
    """The TV is listed beside the phones and forgotten as a phone is."""
    phones = PhoneBook(tmp_path)
    _, token = _paired(phones.tvs())
    listed = phones_list(phones).body
    assert b'"TV"' in listed
    tv_id = phones.tvs().listed()[0].id
    assert phones.forget(tv_id)
    assert phones.tvs().forget(tv_id)
    assert not Screens(phones.tvs()).is_paired(token)
