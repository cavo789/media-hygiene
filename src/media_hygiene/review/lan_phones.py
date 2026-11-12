"""The phones paired once with the home page, kept between runs (0431).

The first time, a phone types the run's code (or scans its QR code); the server then
draws a token for that phone alone, gives it in a long-lived cookie, and writes only its
SHA-256 in `/lan/phones.json` (0430's folder) with a name and a date. The next runs
recognise the cookie: no code. The PC's page lists the phones and forgets one on demand.
A missing or unreadable file means pairing again, never a failure.
"""

from __future__ import annotations

import hmac
import secrets
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Final

from pydantic import ValidationError

from media_hygiene.review.lan_guest_day import guest_over
from media_hygiene.review.lan_phone_care import expire, now_utc
from media_hygiene.review.lan_phone_model import FAMILY, GUEST, Phone, Phones, digest_of
from media_hygiene.review.lan_tls import lan_folder

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.review.lan_activity import Activity
    from media_hygiene.review.lan_phone_model import Role

PHONES_FILE: Final = "phones.json"
TVS_FILE: Final = "tvs.json"  # the TVs of the slideshow paired for good (0456)
TV_NAME: Final = "TV"
_TOKEN_BYTES: Final = 32
_ID_BYTES: Final = 6


class PhoneBook:
    """`phones.json` in the `/lan` folder: read on each question, saved atomically."""

    __slots__ = ("activity", "expired", "path", "role")

    def __init__(self, folder: Path, file: str = PHONES_FILE) -> None:
        """Keep the file's place.

        Args:
            folder: The `/lan` folder.
            file: `phones.json`, or `tvs.json` for the slideshow's TVs.
        """
        self.path = folder / file
        self.expired: tuple[str, ...] = ()  # forgotten at this start, unseen (0683)
        self.activity: Activity | None = None  # what each phone did (0683)
        self.role: Role = FAMILY  # what `add` pairs (0684)

    def guests(self) -> PhoneBook:
        """The same file, pairing guests (0684).

        Returns:
            A book whose `add` writes `role = "guest"`.
        """
        book = PhoneBook(self.path.parent, self.path.name)
        book.activity, book.expired, book.role = self.activity, self.expired, GUEST
        return book

    def tvs(self) -> PhoneBook:
        """The TVs' file beside this one: the same rules, another cookie.

        Returns:
            `tvs.json` in the same folder.
        """
        return PhoneBook(self.path.parent, TVS_FILE)

    def listed(self) -> tuple[Phone, ...]:
        """The paired phones, as on disk.

        Returns:
            Them, oldest first; none when the file is missing or unreadable.
        """
        try:
            return Phones.model_validate_json(self.path.read_bytes()).phones
        except OSError, ValidationError:
            return ()

    def save(self, phones: tuple[Phone, ...]) -> None:
        """Write the list in full, through a draft renamed over the file.

        Args:
            phones: The whole list.
        """
        draft = self.path.with_suffix(".json.new")
        draft.write_text(Phones(phones=phones).model_dump_json(indent=2), "utf-8")
        draft.chmod(0o600)
        draft.replace(self.path)

    def add(self, name: str) -> str | None:
        """Pair a phone: draw its token, keep its hash.

        Args:
            name: What the PC's page calls it.

        Returns:
            The token for its cookie; None when the file cannot be written.
        """
        token = secrets.token_hex(_TOKEN_BYTES)
        return token if self.keep(token, name) else None

    def keep(self, token: str, name: str) -> bool:
        """Pair a device whose token is already drawn (a TV's cookie, 0456).

        Args:
            token: Its token; only its hash is written.
            name: What the PC's page calls it.

        Returns:
            True once written and read back.
        """
        phone = Phone(
            id=secrets.token_hex(_ID_BYTES),
            name=name,
            paired=datetime.now(UTC),
            digest=digest_of(token),
            role=self.role,
        )
        try:
            self.save((*self.listed(), phone))
        except OSError:
            return False
        return self.knows(token)

    def knows(self, token: str) -> bool:
        """Tell whether a cookie is the token of a phone still paired.

        Args:
            token: The cookie's value.

        Returns:
            True for a phone listed.
        """
        return self.holder(token) is not None

    def holder(self, token: str) -> Phone | None:
        """The paired phone holding this cookie, read from the file now.

        Args:
            token: The cookie's value.

        Returns:
            It (compared in constant time); None when unknown, forgotten, or a
            guest whose day is over (0709).
        """
        digest = digest_of(token).encode()
        found = [
            p for p in self.listed() if hmac.compare_digest(digest, p.digest.encode())
        ]
        if not token or not found or guest_over(found[0], now_utc()):
            return None
        return found[0]

    def forget(self, phone_id: str) -> bool:
        """Forget a phone: its cookie opens nothing any more.

        Args:
            phone_id: Its `id`.

        Returns:
            True when it is no longer in the file, read back.
        """
        kept = tuple(phone for phone in self.listed() if phone.id != phone_id)
        try:
            self.save(kept)
        except OSError:
            return False
        return all(phone.id != phone_id for phone in self.listed())


def phone_book(*, secure: bool) -> PhoneBook | None:
    """The paired-phones file, under HTTPS only: a cookie for good needs `Secure`.

    Args:
        secure: The home network's door is HTTPS (0430).

    Returns:
        The file in `/lan`, the phones unseen for long forgotten (0683); None in
        plain HTTP or without the folder.
    """
    folder = lan_folder() if secure else None
    if folder is None:
        return None
    book = PhoneBook(folder)
    book.expired = expire(book, now_utc())
    return book
