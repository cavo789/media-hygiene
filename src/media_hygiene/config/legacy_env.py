"""The environment variables of media-dedup 0.2, still read under their old prefix.

The project became media-hygiene in 0.3.0: `MEDIA_DEDUP_GENERAL__LOCALE` is now
`MEDIA_HYGIENE_GENERAL__LOCALE`. The scripts of a user keep working until
`LEGACY_PREFIX_REMOVED_IN`, with a warning; the new name wins when both are set. That
version deletes this module and its two callers (`__main__.py`, `cli/context.py`).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.constants import ENV_PREFIX

if TYPE_CHECKING:
    from collections.abc import Mapping, MutableMapping

LEGACY_ENV_PREFIX: Final = "MEDIA_DEDUP_"
LEGACY_PREFIX_REMOVED_IN: Final = "0.4.0"


def legacy_names(environ: Mapping[str, str]) -> tuple[str, ...]:
    """List the variables set under the old prefix.

    Args:
        environ: The process environment.

    Returns:
        Their names, sorted.
    """
    return tuple(name for name in sorted(environ) if name.startswith(LEGACY_ENV_PREFIX))


def adopt_legacy_variables(environ: MutableMapping[str, str]) -> None:
    """Give each old variable its new name, unless the new one is set already.

    Called first thing, before the language is resolved from the environment.

    Args:
        environ: The process environment, updated in place.
    """
    for name in legacy_names(environ):
        environ.setdefault(
            ENV_PREFIX + name.removeprefix(LEGACY_ENV_PREFIX), environ[name]
        )
