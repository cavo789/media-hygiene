r"""What `mh.ps1` says before reading photos that live in OneDrive's cloud only (0199).

Windows 11 puts Pictures in OneDrive during a setup with a Microsoft account; with
Files On-Demand a photo may be a placeholder whose data is in the cloud. Microsoft's
*File Attribute Constants*: `FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS` (0x00400000) means
reading the file fetches it from a remote store, `FILE_ATTRIBUTE_OFFLINE` (0x00001000)
that its data is not available immediately; listing a folder reads the attributes
only. Before a command that reads the photos' contents, `mh` counts such files in each
photo folder lying under a OneDrive root (or holding one), once per PowerShell
session, and asks before the run. The bash `mh` has no OneDrive: nothing there.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from media_hygiene.i18n import _
from media_hygiene.services.launcher_menu import shell_safe

# The commands reading the photos' contents; `status`, `history`, `config`, `reports`,
# `menu` and `inventory` read the tool's own folders only.
CLOUD_READERS: Final = frozenset(
    {"audit", "review", "clean", "crosscheck", "classify", "tags", "people", "search"}
)
# Where the OneDrive client says its folders are, one variable per account kind.
ONEDRIVE_ROOTS: Final = ("OneDrive", "OneDriveConsumer", "OneDriveCommercial")
# RECALL_ON_DATA_ACCESS, then OFFLINE: Windows PowerShell 5.1's `FileAttributes` enum
# lacks the first name, so both are numbers.
CLOUD_ATTRIBUTES: Final = ("0x00400000", "0x00001000")
_FIELDS: Final = ("count", "size", "folder", "free", "drive")


@dataclass(frozen=True, slots=True)
class CloudCheck:
    """What `mh.ps1` needs to find cloud-only photos, and to say so."""

    readers: tuple[str, ...]  # the commands of this CLI that read the photos
    roots: tuple[str, ...]  # `$env:OneDrive`…
    attributes: str  # `0x00400000 -bor 0x00001000`
    listing: str  # holds `${folder}`: said while the listing runs
    warning: str  # holds `${count}`, `${size}`, `${folder}`, `${free}`, `${drive}`
    question: str  # holds the yes letter
    yes: str  # the letter that goes on, besides `y`


def cloud_check(names: tuple[str, ...]) -> CloudCheck:
    """Gather the commands, the variables and the translated messages of the check.

    Args:
        names: The commands of the CLI.

    Returns:
        The check, its messages safe inside double quotes.
    """
    yes = shell_safe(_("y")).strip() or "y"
    warning = shell_safe(
        _(
            "{count} files ({size} GB) of {folder} are in OneDrive's cloud only: "
            "reading them downloads them onto this PC ({free} GB free on {drive}). "
            "To keep them here: right-click the folder, then Always keep on this "
            "device."
        )
    )
    for field in _FIELDS:
        warning = warning.replace(f"{{{field}}}", f"${{{field}}}")
    return CloudCheck(
        readers=tuple(name for name in names if name in CLOUD_READERS),
        roots=tuple(f"$env:{name}" for name in ONEDRIVE_ROOTS),
        attributes=" -bor ".join(CLOUD_ATTRIBUTES),
        listing=shell_safe(
            _("Looking for the files of {folder} in OneDrive's cloud only…")
        ).replace("{folder}", "${folder}"),
        warning=warning,
        question=shell_safe(_("Continue? ({yes}/N)")).replace("{yes}", yes),
        yes=yes,
    )
