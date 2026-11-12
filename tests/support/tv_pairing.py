"""A TV paired by the code it shows, as a phone types it (0456, 0702)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.slideshow.screens import Screens

if TYPE_CHECKING:
    from media_hygiene.review.lan_phones import PhoneBook


def tv_paired(book: PhoneBook | None) -> tuple[Screens, str]:
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
