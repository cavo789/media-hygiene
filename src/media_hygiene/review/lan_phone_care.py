"""The paired phones' upkeep (0683): last seen, a name typed, expiry, *Forget all*.

Every write goes through `PhoneBook.save` (a draft renamed over the file, 0600) and is
rare: a phone's `last_seen` is written at most once an hour, or when its address
changes. The file is read on each question, so a phone forgotten while connected is
refused at its next request; a `/lan` restored from an older copy is simply what is
listed from then on (its phones without `last_seen` are dated at the next start, never
forgotten for lack of a date).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Final

from media_hygiene.review.lan_guest_day import guest_over

if TYPE_CHECKING:
    from media_hygiene.review.lan_phone_model import Phone
    from media_hygiene.review.lan_phones import PhoneBook

# A phone unseen this long is forgotten at the next start (estimated: a season away).
EXPIRY_DAYS: Final = 90
SEEN_EVERY: Final = timedelta(hours=1)
NAME_MAX: Final = 40  # what the PC's card keeps of a typed name


def now_utc() -> datetime:
    """The clock the upkeep reads; tests pass their own instant instead.

    Returns:
        Now, in UTC.
    """
    return datetime.now(UTC)


def _replaced(book: PhoneBook, phone: Phone) -> bool:
    """Write the list with this phone in place of its former self.

    Args:
        book: The file.
        phone: The phone, changed.

    Returns:
        True once written.
    """
    listed = tuple(phone if p.id == phone.id else p for p in book.listed())
    try:
        book.save(listed)
    except OSError:
        return False
    return True


def touch(book: PhoneBook, phone: Phone, seen: tuple[str, datetime]) -> None:
    """Note that a phone came, at most once an hour (or when its address changed).

    Args:
        book: The file.
        phone: The phone, as just read.
        seen: Its address (from the socket) and the instant.
    """
    address, at = seen
    fresh = phone.last_seen is not None and at - phone.last_seen < SEEN_EVERY
    if fresh and address == phone.address:
        return
    _replaced(book, phone.model_copy(update={"last_seen": at, "address": address}))


def booked(book: PhoneBook, token: str, peer: str) -> bool:
    """Tell whether the file lists this device now, and note that it came (0702).

    Read at every request, as the phones' file: a TV forgotten on the PC's card gets
    the pairing page at its next request, not at the next start of `mh`.

    Args:
        book: The file (`tvs.json` for a TV).
        token: The device's cookie, empty without one.
        peer: Its address, from the socket; empty keeps the one written.

    Returns:
        True for a device listed; False once forgotten on the PC.
    """
    device = book.holder(token)
    if device is None:
        return False
    touch(book, device, (peer or device.address, now_utc()))
    return True


def rename(book: PhoneBook, phone_id: str, name: str) -> bool:
    """Give a phone the name the user typed on the PC's card.

    Args:
        book: The file (phones or TVs).
        phone_id: Its `id`.
        name: What was typed.

    Returns:
        True when the file, read back, holds the new name; False for an empty name,
        an unknown phone or a file that cannot be written.
    """
    kept = " ".join(name.split())[:NAME_MAX]
    found = [p for p in book.listed() if p.id == phone_id]
    if not kept or not found:
        return False
    _replaced(book, found[0].model_copy(update={"name": kept}))
    return any(p.id == phone_id and p.name == kept for p in book.listed())


def forget_all(book: PhoneBook) -> bool:
    """Forget every phone and every TV: no cookie opens anything any more.

    Args:
        book: The phones' file (the TVs' beside it).

    Returns:
        True when both files, read back, are empty.
    """
    for each in (book, book.tvs()):
        try:
            each.save(())
        except OSError:
            return False
    return not book.listed() and not book.tvs().listed()


def expire(book: PhoneBook, now: datetime) -> tuple[str, ...]:
    """Forget the phones unseen for `EXPIRY_DAYS` and the guests of a past day (0709).

    Those never seen are dated.

    A phone paired before 0683 has no `last_seen`: it is dated now, and counts from
    here, rather than forgotten after an upgrade or a restore.

    Args:
        book: The phones' file (TVs, paired for good, are never expired).
        now: The instant (a test's clock).

    Returns:
        The names forgotten, said on the PC's card.
    """
    listed = book.listed()
    limit = now - timedelta(days=EXPIRY_DAYS)
    gone = tuple(
        p
        for p in listed
        if (p.last_seen is not None and p.last_seen < limit) or guest_over(p, now)
    )
    dated = tuple(
        p if p.last_seen else p.model_copy(update={"last_seen": now})
        for p in listed
        if p not in gone
    )
    if dated == listed:
        return ()
    try:
        book.save(dated)
    except OSError:
        return ()
    return tuple(p.name for p in gone)
