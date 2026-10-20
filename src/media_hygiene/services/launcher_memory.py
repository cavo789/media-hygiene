"""What the `mh` launcher remembers beside the folders: the language, the time zone.

The global `--locale fr` of the `launcher` run is an option of that run only: without
it in the script, `mh audit` would speak the language of `config.toml` (English by
default) while the guide in front of the reader quotes French. The time zone is kept
only when the run knew it (`-e TZ=…` or `[general] timezone`); otherwise `mh` reads the
computer's own zone at each run.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Final

from media_hygiene.config.zone import timezone_unknown
from media_hygiene.constants import ENV_PREFIX
from media_hygiene.i18n import _, ngettext
from media_hygiene.i18n.bootstrap import written_locale

if TYPE_CHECKING:
    from media_hygiene.services.launcher import LauncherScript
    from media_hygiene.services.runtime import Runtime

LOCALE_VARIABLE: Final = f"{ENV_PREFIX}GENERAL__LOCALE"
_TIMEZONE: Final = "TZ"
_UTC: Final = "UTC"


def locale_option(runtime: Runtime) -> tuple[str, ...]:
    """The `-e` option keeping a language given on the command line of this run.

    A language written in `config.toml` or in the environment is not repeated: the
    file is read again by every `mh` run, the environment is carried already.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        `-e "MEDIA_HYGIENE_GENERAL__LOCALE=fr"`, or nothing.
    """
    locale = runtime.settings.general.locale
    if locale is written_locale(runtime.locations):
        return ()
    return (f'-e "{LOCALE_VARIABLE}={locale.value}"',)


def remembered(runtime: Runtime, script: LauncherScript) -> str:
    """Say in one line what `mh` will reuse at every run.

    Args:
        runtime: Settings, mount points and output.
        script: The script just written.

    Returns:
        E.g. `mh remembers: 2 folders, 1 backup (read-only), language fr, time zone
        Europe/Brussels.`
    """
    count = len(script.data)
    folders = ngettext("{count} folder", "{count} folders", count).format(count=count)
    backups = len(script.backups) + len(script.nas)
    if backups:
        folders += ", " + ngettext(
            "{count} backup (read-only)",
            "{count} backups (read-only)",
            backups,
        ).format(count=backups)
    zone = (
        _("your computer's, read at each run")
        if timezone_unknown()
        else os.environ.get(_TIMEZONE, _UTC)
    )
    return _("mh remembers: {folders}, language {locale}, time zone {zone}.").format(
        folders=folders, locale=runtime.settings.general.locale.value, zone=zone
    )
