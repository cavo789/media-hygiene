"""A guest's pairing ends the same evening (0709): a relative's TV keeps no access.

A guest paired today sees the guests' albums until the next local midnight (the
process zone: `[general] timezone`, `-e TZ=…` or the Windows host's, `config/zone`).
Then its cookie opens nothing: the pairing page again, with the guests' code. Both
kinds of guest end: a guest kept in `phones.json` (its `paired` date) and one paired
for this run only (its run token is drawn for the day, `lan_guest.guest_token`).
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import TYPE_CHECKING, Final

from media_hygiene.review.lan_phone_model import GUEST

if TYPE_CHECKING:
    from media_hygiene.review.lan_phone_model import Phone

GUEST_ENDS_AT: Final = time(0)  # local midnight: the end of the day it was paired


def local_day(at: datetime) -> date:
    """The local date of an instant.

    Args:
        at: An aware instant.

    Returns:
        Its date in the process zone.
    """
    return at.astimezone().date()


def guest_ends(paired: datetime) -> datetime:
    """When a guest paired at this instant stops seeing anything.

    Args:
        paired: When it was paired (aware).

    Returns:
        The next local midnight after it, aware.
    """
    following = local_day(paired) + timedelta(days=1)
    return datetime.combine(following, GUEST_ENDS_AT).astimezone()


def guest_over(phone: Phone, now: datetime) -> bool:
    """Tell whether a device kept in the file is a guest whose day is over.

    Args:
        phone: As on disk.
        now: The instant (a test's clock).

    Returns:
        True for a guest paired before today's local midnight; False for family.
    """
    return phone.role == GUEST and now >= guest_ends(phone.paired)
