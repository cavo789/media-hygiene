"""What to tell the user when the online place search fails."""

from __future__ import annotations

import urllib.error
from http import HTTPStatus
from typing import Final

from media_hygiene.errors import NominatimError
from media_hygiene.i18n import _

_REFUSED: Final = frozenset({HTTPStatus.FORBIDDEN, HTTPStatus.TOO_MANY_REQUESTS})


def failed(host: str, error: OSError) -> NominatimError:
    """Say why a request failed.

    Args:
        host: The service's host.
        error: What `urllib` raised: refused, another HTTP error, unreachable.

    Returns:
        The error to show.
    """
    if isinstance(error, urllib.error.HTTPError) and error.code in _REFUSED:
        message = _(
            "{host} refused the search (error {status}): its usage limits are "
            "reached. Try again later, or set another service in [places] "
            "nominatim_url."
        )
        return NominatimError(message.format(host=host, status=error.code))
    if isinstance(error, urllib.error.HTTPError):
        message = _("{host} answered with the error {status}.")
        return NominatimError(message.format(host=host, status=error.code))
    message = _(
        "Cannot reach {host}: is this computer offline? The offline town search "
        "still works."
    )
    return NominatimError(message.format(host=host))


def unexpected(host: str) -> NominatimError:
    """Say that the service answered something else than search results.

    Args:
        host: The service's host.

    Returns:
        The error to show.
    """
    message = _("{host} answered something that is not a search result.")
    return NominatimError(message.format(host=host))
