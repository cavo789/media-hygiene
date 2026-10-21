"""The home page opened to a phone on the home network, for one `mh --lan` run (0269).

`mh --lan` (PowerShell) publishes the home page's port on the PC's own address on the
home network too, never on every interface, and passes that address and a secret drawn
for the run (`MEDIA_HYGIENE_LAUNCHER_LAN_*`, never carried into another `mh` file). The
server derives from the secret a pairing code to type on the phone (or its QR code) and
the token the phone keeps in a cookie once paired: the same for the whole run, the home
page restarting after each step. Only a private IPv4 address is taken: never the
internet. Plain HTTP, as decided (2026-10-21): the session is short, at home.
"""

from __future__ import annotations

import hashlib
import hmac
import ipaddress
import os
import secrets
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.services.next_command import LAUNCHER_VARIABLE

if TYPE_CHECKING:
    from collections.abc import Mapping

    from media_hygiene.review.http import Request

LAN_ADDRESS_VARIABLE: Final = f"{LAUNCHER_VARIABLE}_LAN_ADDRESS"
LAN_SECRET_VARIABLE: Final = f"{LAUNCHER_VARIABLE}_LAN_SECRET"
PAIR_PREFIX: Final = "/pair/"
COOKIE_NAME: Final = "mh_lan"
CODE_DIGITS: Final = 8  # typed on a phone: digits only, 10^8 codes
_SECRET_BYTES: Final = 32
_CODE_LABEL: Final = b"media-hygiene pairing code"
_TOKEN_LABEL: Final = b"media-hygiene phone token"
_HALF: Final = CODE_DIGITS // 2


@dataclass(frozen=True, slots=True)
class LanAccess:
    """The PC's address on the home network, the port, and the run's secret."""

    address: str
    port: int
    secret: bytes

    @property
    def host(self) -> str:
        """The `Host` a phone sends: the address and the port.

        Returns:
            E.g. `192.168.1.20:8765`.
        """
        return f"{self.address}:{self.port}"

    @property
    def origin(self) -> str:
        """The page's origin on the phone, for the `Origin` of its requests.

        Returns:
            E.g. `http://192.168.1.20:8765`.
        """
        return f"http://{self.host}"

    @property
    def code(self) -> str:
        """The pairing code, derived from the secret: the same for the whole run.

        Returns:
            `CODE_DIGITS` digits.
        """
        digest = hmac.new(self.secret, _CODE_LABEL, hashlib.sha256).digest()
        return str(int.from_bytes(digest) % 10**CODE_DIGITS).zfill(CODE_DIGITS)

    @property
    def shown_code(self) -> str:
        """The code as shown to be typed: two groups of four digits.

        Returns:
            E.g. `0123 4567`.
        """
        return f"{self.code[:_HALF]} {self.code[_HALF:]}"

    @property
    def token(self) -> str:
        """The cookie of a paired phone, derived from the secret, never from the code.

        Returns:
            64 hexadecimal digits.
        """
        return hmac.new(self.secret, _TOKEN_LABEL, hashlib.sha256).hexdigest()

    @property
    def pair_url(self) -> str:
        """The address the QR code holds: the page, the code in its path.

        Returns:
            E.g. `http://192.168.1.20:8765/pair/01234567`.
        """
        return f"{self.origin}{PAIR_PREFIX}{self.code}"

    def names_me(self, request: Request) -> bool:
        """Tell whether a request names the PC's address on the home network.

        Args:
            request: The request.

        Returns:
            True when its `Host` is exactly the address and port: another name
            (DNS rebinding) is refused.
        """
        return request.headers.get("host", "") == self.host

    def code_matches(self, typed: str) -> bool:
        """Compare a typed code, spaces and dashes ignored, in constant time.

        Args:
            typed: What the phone sent.

        Returns:
            True when it is the run's code.
        """
        cleaned = typed.replace(" ", "").replace("-", "").replace("%20", "")
        return hmac.compare_digest(cleaned.encode(), self.code.encode())

    def is_paired(self, request: Request) -> bool:
        """Tell whether the request carries the token of a paired phone.

        Args:
            request: The request.

        Returns:
            True with the right cookie.
        """
        token = cookies(request.headers).get(COOKIE_NAME, "")
        return hmac.compare_digest(token.encode(), self.token.encode())


def cookies(headers: Mapping[str, str]) -> dict[str, str]:
    """Read the `Cookie` header.

    Args:
        headers: The request's headers.

    Returns:
        The cookies by name.
    """
    pairs = (
        part.strip().partition("=") for part in headers.get("cookie", "").split(";")
    )
    return {name: value for name, _equal, value in pairs if name}


def private_address(text: str) -> str | None:
    """Accept an address of a home network only: a private IPv4, never the internet.

    Args:
        text: The address `mh` found.

    Returns:
        It, or None for a public, loopback, link-local or malformed address.
    """
    try:
        address = ipaddress.IPv4Address(text.strip())
    except ValueError:
        return None
    if not address.is_private or address.is_loopback or address.is_link_local:
        return None
    return str(address)


def lan_access(port: int) -> LanAccess | None:
    """The access `mh --lan` asked for this run, from its environment.

    Args:
        port: The port the page listens on, published under the same number.

    Returns:
        The access; None without `mh --lan` or with an address refused. Without the
        secret (`media-hygiene home` run by hand), one is drawn for this server only.
    """
    address = private_address(os.environ.get(LAN_ADDRESS_VARIABLE, ""))
    if address is None:
        return None
    given = os.environ.get(LAN_SECRET_VARIABLE, "")
    secret = given.encode() if given else secrets.token_bytes(_SECRET_BYTES)
    return LanAccess(address, port, secret)


def lan_refused() -> str | None:
    """The address `mh --lan` gave when it is refused, to say so.

    Returns:
        The address given, or None when none was given or it was accepted.
    """
    given = os.environ.get(LAN_ADDRESS_VARIABLE, "").strip()
    if not given or private_address(given) is not None:
        return None
    return given
