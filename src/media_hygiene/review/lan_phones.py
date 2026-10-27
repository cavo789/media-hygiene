"""The phones paired once with the home page, kept between runs (0431).

The first time, a phone types the run's code (or scans its QR code); the server then
draws a token for that phone alone, gives it in a long-lived cookie, and writes only its
SHA-256 in `/lan/phones.json` (0430's folder) with a name and a date. The next runs
recognise the cookie: no code. The PC's page lists the phones and forgets one on demand.
A missing or unreadable file means pairing again, never a failure.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, ValidationError

from media_hygiene.review.lan_tls import lan_folder

if TYPE_CHECKING:
    from pathlib import Path

PHONES_FILE: Final = "phones.json"
_TOKEN_BYTES: Final = 32
_ID_BYTES: Final = 6
# The device named after the browser's own words, else a plain "phone".
_DEVICES: Final = (("iPhone", "iPhone"), ("iPad", "iPad"), ("Android", "Android"))
DEFAULT_DEVICE: Final = "Phone"


class Phone(BaseModel):
    """A paired phone: never its token, only the token's hash."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    id: str
    name: str
    paired: datetime
    digest: str


class Phones(BaseModel):
    """The content of `phones.json`."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    phones: tuple[Phone, ...] = ()


def digest_of(token: str) -> str:
    """The hash kept for a token.

    Args:
        token: A phone's cookie.

    Returns:
        Its SHA-256, in hexadecimal.
    """
    return hashlib.sha256(token.encode()).hexdigest()


def device_name(user_agent: str) -> str:
    """Name a phone after its browser's `User-Agent`.

    Args:
        user_agent: The header.

    Returns:
        E.g. `Android`, `iPhone`; `DEFAULT_DEVICE` otherwise.
    """
    return next((name for word, name in _DEVICES if word in user_agent), DEFAULT_DEVICE)


class PhoneBook:
    """`phones.json` in the `/lan` folder: read on each question, saved atomically."""

    __slots__ = ("path",)

    def __init__(self, folder: Path) -> None:
        """Keep the file's place.

        Args:
            folder: The `/lan` folder.
        """
        self.path = folder / PHONES_FILE

    def listed(self) -> tuple[Phone, ...]:
        """The paired phones, as on disk.

        Returns:
            Them, oldest first; none when the file is missing or unreadable.
        """
        try:
            return Phones.model_validate_json(self.path.read_bytes()).phones
        except OSError, ValidationError:
            return ()

    def _save(self, phones: tuple[Phone, ...]) -> None:
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
        phone = Phone(
            id=secrets.token_hex(_ID_BYTES),
            name=name,
            paired=datetime.now(UTC),
            digest=digest_of(token),
        )
        try:
            self._save((*self.listed(), phone))
        except OSError:
            return None
        return token

    def knows(self, token: str) -> bool:
        """Tell whether a cookie is the token of a phone still paired.

        Args:
            token: The cookie's value.

        Returns:
            True for a phone listed (compared in constant time).
        """
        if not token:
            return False
        digest = digest_of(token).encode()
        found = [hmac.compare_digest(digest, p.digest.encode()) for p in self.listed()]
        return any(found)

    def forget(self, phone_id: str) -> bool:
        """Forget a phone: its cookie opens nothing any more.

        Args:
            phone_id: Its `id`.

        Returns:
            True when it is no longer in the file, read back.
        """
        kept = tuple(phone for phone in self.listed() if phone.id != phone_id)
        try:
            self._save(kept)
        except OSError:
            return False
        return all(phone.id != phone_id for phone in self.listed())


def phone_book(*, secure: bool) -> PhoneBook | None:
    """The paired-phones file, under HTTPS only: a cookie for good needs `Secure`.

    Args:
        secure: The home network's door is HTTPS (0430).

    Returns:
        The file in `/lan`; None in plain HTTP or without the folder.
    """
    folder = lan_folder() if secure else None
    return None if folder is None else PhoneBook(folder)
