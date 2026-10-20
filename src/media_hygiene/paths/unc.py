r"""Network folders (`\\NAS\Photos`): where the container sees them, and back (0245).

A share of a NAS is mounted by `mh` in a Docker volume (SMB3), on
`/data/unc/<host>/<share>`: the host path `\\NAS\Photos\2019` is
`/data/unc/NAS/Photos/2019` in the container, and back.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Final, NamedTuple

if TYPE_CHECKING:
    from pathlib import Path

# The folder below `/data` holding the network shares.
UNC_FOLDER: Final = "unc"
_UNC: Final = re.compile(
    r"^(?:\\\\|//)(?P<host>[^\\/]+)[\\/]+(?P<share>[^\\/]+)(?P<rest>(?:[\\/].*)?)$"
)
_SEPARATORS: Final = re.compile(r"[\\/]+")


class Share(NamedTuple):
    r"""A network folder: its host, its share, the folders below it."""

    host: str
    share: str
    rest: tuple[str, ...] = ()

    @property
    def unc(self) -> str:
        r"""The share as Windows writes it, without the folders below it.

        Returns:
            E.g. `\\NAS\Photos`.
        """
        return f"\\\\{self.host}\\{self.share}"


def share_of(host_path: str) -> Share | None:
    r"""Read a network path.

    Args:
        host_path: `\\NAS\Photos\2019` or `//NAS/Photos/2019`.

    Returns:
        Its host, share and folders; None for any other path.
    """
    match = _UNC.match(host_path)
    if match is None:
        return None
    rest = tuple(part for part in _SEPARATORS.split(match["rest"]) if part)
    return Share(match["host"], match["share"], rest)


def unc_point(data_dir: Path, host_path: str) -> Path | None:
    r"""Where a network path is in the container.

    Args:
        data_dir: The data mount point (`/data`).
        host_path: A network path.

    Returns:
        `/data/unc/<host>/<share>/...`, or None for another path.
    """
    share = share_of(host_path)
    if share is None:
        return None
    return data_dir.joinpath(UNC_FOLDER, share.host, share.share, *share.rest)


def unc_host(parts: tuple[str, ...]) -> str | None:
    r"""The network path of a container path below `/data/unc`.

    Args:
        parts: The parts of the path below `/data`.

    Returns:
        `\\host\share\...`, or None when the path is not below a share.
    """
    if len(parts) < 3 or parts[0] != UNC_FOLDER:  # noqa: PLR2004  # unc, host, share
        return None
    return "\\\\" + "\\".join(parts[1:])
