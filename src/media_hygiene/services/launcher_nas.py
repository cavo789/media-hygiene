r"""A NAS backup in `mh.ps1`: `mh folders add --backup \\NAS\Photos` (0245).

Docker Desktop cannot mount a network folder as a host path, nor see a drive mapped in
Windows: `mh` makes a Docker volume of the share (SMB3, read-only) before each command,
checked by a short `docker run`, and removes it after, so the password never stays in
Docker. The password is asked once and kept encrypted for this Windows user
(`Export-Clixml`, DPAPI), next to the tool's folders; never in `config.toml`, never in
a log. A NAS that does not answer is said in one line and left out of that command.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _
from media_hygiene.paths.unc import share_of, unc_point
from media_hygiene.services.launcher_menu import shell_safe, with_variable

if TYPE_CHECKING:
    from pathlib import Path

# SMB 3.1.1 with NTLMSSP: what a Synology set to SMB3 answered (measured 2026-10-20).
SMB_OPTIONS: Final = "ro,vers=3.1.1,sec=ntlmssp"
_UNSAFE_NAME: Final = re.compile(r"[^A-Za-z0-9._-]+")


@dataclass(frozen=True, slots=True)
class NasShare:
    r"""A share of a NAS given as a backup: where it is, where the container sees it."""

    unc: str  # `\\NAS\Photos`, as typed
    host: str
    share: str
    point: Path  # `/data/unc/NAS/Photos`
    credential: str  # the file name of its kept password, next to the tool's folders


@dataclass(frozen=True, slots=True)
class NasTexts:  # pylint: disable=too-many-instance-attributes
    """The lines `mh.ps1` says about a NAS; `${unc}` holds the share."""

    off: str
    user: str
    password: str
    keep: str
    kept: str
    wrong: str
    legacy: str
    unsafe: str
    answers: str
    powered_off: str


def nas_share(data_dir: Path, unc: str) -> NasShare | None:
    r"""Describe a network folder given as a backup.

    Args:
        data_dir: The data mount point (`/data`).
        unc: `\\NAS\Photos`, as typed.

    Returns:
        The share, or None for a path that is no network folder.
    """
    share = share_of(unc)
    if share is None:
        return None
    # The share as a whole: Docker mounts a share, never one of its folders.
    point = unc_point(data_dir, share.unc)
    if point is None:
        return None
    name = _UNSAFE_NAME.sub("-", f"{share.host}-{share.share}").strip("-")
    return NasShare(share.unc, share.host, share.share, point, f"nas-{name}.xml")


def nas_texts() -> NasTexts:
    """Translate the lines `mh.ps1` says about a NAS.

    Returns:
        The lines, `${unc}` in place of the share.
    """

    def said(text: str) -> str:
        """Make a line safe for the script, the share's variable in its field.

        Args:
            text: The translated line.

        Returns:
            The line for `mh.ps1`.
        """
        return with_variable(text, "{share}", "${unc}")

    return NasTexts(
        off=said(
            _(
                "{share} does not answer (the NAS is off?): this command runs "
                "without it. Power it on, then type the command again."
            )
        ),
        user=shell_safe(_("User name on the NAS")),
        password=said(_("Password of {share} (asked once, never shown)")),
        keep=shell_safe(
            _("Keep it, encrypted for your Windows account only, on this PC? (y/n)")
        ),
        kept=said(_("The password of {share} is kept: mh folders remove forgets it.")),
        wrong=said(
            _(
                "{share} refused this user name or password: type them again with "
                "mh folders add --backup."
            )
        ),
        legacy=said(
            _(
                "{share} could not be read by Docker: an older SMB? On a Synology: "
                "Control Panel, File Services, SMB, Advanced Settings, Maximum SMB "
                "protocol: SMB3."
            )
        ),
        unsafe=said(
            _(
                "The password of {share} holds a comma or a double quote, which Docker "
                "cannot pass: change it on the NAS."
            )
        ),
        answers=shell_safe(_("answers")),
        powered_off=shell_safe(_("does not answer (powered off?)")),
    )
