"""The guests' code of `mh --lan` (0684): a device paired by it sees chosen albums only.

The PC's card shows two codes: the family's (`LanAccess.code`: the whole library and
the reports, as a phone always had) and the guests'. Both derive from the run's
secret with their own label; the role is the code typed, never a choice the device
makes. A guest paired this run holds its own run token; under HTTPS, its token for
good is kept in `phones.json` with `role = "guest"`.
"""

from __future__ import annotations

import hashlib
import hmac
from typing import TYPE_CHECKING, Final

from media_hygiene.review.lan import CODE_DIGITS, COOKIE_NAME, PAIR_PREFIX, cookies
from media_hygiene.review.lan_phone_model import FAMILY, GUEST

if TYPE_CHECKING:
    from media_hygiene.review.http import Request
    from media_hygiene.review.lan import LanAccess
    from media_hygiene.review.lan_phone_model import Role

_CODE_LABEL: Final = b"media-hygiene guest code"
_TOKEN_LABEL: Final = b"media-hygiene guest token"
_HALF: Final = CODE_DIGITS // 2


def guest_code(lan: LanAccess) -> str:
    """The guests' code, new at each *Open pairing again* as the family's.

    Args:
        lan: The run's access, at the generation the card shows.

    Returns:
        `CODE_DIGITS` digits.
    """
    label = _CODE_LABEL + f" {lan.generation}".encode()
    digest = hmac.new(lan.secret, label, hashlib.sha256).digest()
    return str(int.from_bytes(digest) % 10**CODE_DIGITS).zfill(CODE_DIGITS)


def guest_shown(lan: LanAccess) -> str:
    """The guests' code as typed: two groups of four digits.

    Args:
        lan: The run's access.

    Returns:
        E.g. `0123 4567`.
    """
    code = guest_code(lan)
    return f"{code[:_HALF]} {code[_HALF:]}"


def guest_pair_url(lan: LanAccess) -> str:
    """The address the guests' QR code holds.

    Args:
        lan: The run's access.

    Returns:
        E.g. `https://192.168.1.20:8765/pair/01234567`.
    """
    return f"{lan.origin}{PAIR_PREFIX}{guest_code(lan)}"


def guest_token(lan: LanAccess) -> str:
    """The cookie of a guest paired this run: never the family's.

    Args:
        lan: The run's access.

    Returns:
        64 hexadecimal digits.
    """
    return hmac.new(lan.secret, _TOKEN_LABEL, hashlib.sha256).hexdigest()


def code_role(lan: LanAccess, typed: str) -> Role | None:
    """The role a typed code pairs, compared in constant time.

    Args:
        lan: The run's access, at the generation the card shows.
        typed: What the device sent, spaces and dashes ignored.

    Returns:
        `family`, `guest`, or None for a wrong code.
    """
    cleaned = typed.replace(" ", "").replace("-", "").replace("%20", "").encode()
    guest = hmac.compare_digest(cleaned, guest_code(lan).encode())
    if lan.code_matches(typed):
        return FAMILY
    return GUEST if guest else None


def run_role(lan: LanAccess, request: Request) -> Role | None:
    """The role of a device holding this run's cookie.

    Args:
        lan: The run's access.
        request: The request.

    Returns:
        `family`, `guest`, or None without a run cookie.
    """
    if lan.is_paired(request):
        return FAMILY
    token = cookies(request.headers).get(COOKIE_NAME, "")
    return (
        GUEST
        if hmac.compare_digest(token.encode(), guest_token(lan).encode())
        else None
    )
