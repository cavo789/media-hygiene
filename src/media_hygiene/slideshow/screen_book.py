"""The TVs of a run: kept for good beside the phones (0456), else in memory."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.slideshow.screens import Screens

if TYPE_CHECKING:
    from media_hygiene.review.lan_phones import PhoneBook


def screens_of(phones: PhoneBook | None) -> Screens:
    """The TVs of a run: kept beside the phones paired for good (0456), else in memory.

    Args:
        phones: `phones.json` under HTTPS; None otherwise.

    Returns:
        The TVs, none paired in memory yet.
    """
    return Screens(None if phones is None else phones.tvs())
