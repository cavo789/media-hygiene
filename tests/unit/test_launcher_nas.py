r"""A NAS backup in `mh.ps1` (0245): `\\NAS\Photos` mounted by a Docker volume, SMB3.

The share is never a `-v` of a host path (Docker Desktop mounts none), never looked
up as a folder; its password never written into the script. The bash `mh` refuses it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

import pytest

from media_hygiene.errors import MountError
from media_hygiene.paths.docker_run import Shell
from media_hygiene.paths.host_paths import HostPathMapper
from media_hygiene.services.launcher import launcher_script, render_script
from media_hygiene.services.launcher_backups import with_backups
from media_hygiene.services.launcher_folders import FolderChoice, with_folders
from media_hygiene.services.launcher_nas import SMB_OPTIONS, nas_share
from tests.unit.test_launcher_folders import _BACKUPS, _runtime

_NAS: Final = "\\\\192.168.0.27\\Photos"


def _script(shell: Shell, *backups: str) -> str:
    """The script of the photo folder on drive C with these backups, rendered."""
    runtime = _runtime()
    choice = FolderChoice(("C:\\Photos",), backups=backups)
    script = with_folders(runtime, launcher_script(runtime, shell, _BACKUPS), choice)
    return render_script(with_backups(runtime, script, choice.backups))


def test_a_share_is_seen_below_data_unc_and_back() -> None:
    r"""`\\NAS\Photos\2019` is `/data/unc/NAS/Photos/2019`, and back."""
    mapper = HostPathMapper(Path("/data"))
    inside = mapper.to_container(_NAS + "\\2019\\Été")
    assert inside == Path("/data/unc/192.168.0.27/Photos/2019/Été")
    assert mapper.to_host(inside) == _NAS + "\\2019\\Été"
    assert mapper.to_container("C:\\Photos") == Path("/data/c/Photos")


def test_a_share_is_kept_whole_with_its_password_file() -> None:
    """A folder of the share stands for the share; its password file is named once."""
    share = nas_share(Path("/data"), _NAS + "\\2019")
    assert share is not None
    assert share.unc == _NAS
    assert share.point == Path("/data/unc/192.168.0.27/Photos")
    assert share.credential == "nas-192.168.0.27-Photos.xml"
    assert nas_share(Path("/data"), "D:\\Backup") is None


def test_powershell_mounts_the_share_by_a_volume_never_a_host_path() -> None:
    """`-v` of the volume made for the run, `--backup` of the share; no password."""
    text = _script(Shell.POWERSHELL, _NAS, "D:\\Backup")
    assert "_mh_nas_mount $command" in text
    assert '"${volume}:/data/unc/192.168.0.27/Photos:ro"' in text
    assert SMB_OPTIONS in text
    assert "_mh_nas_release $nas.volumes" in text
    assert f'-v "{_NAS}' not in text
    assert '-v "D:\\Backup:/data/d/Backup:ro"' in text
    assert "password=$secret" in text  # the variable, read at run time only
    assert text.isascii()


def test_powershell_never_looks_the_share_up_as_a_folder() -> None:
    """The folders checked before a run are local ones: a share needs its password."""
    text = _script(Shell.POWERSHELL, _NAS)
    checked = text[text.index("    foreach ($folder in @(") :].splitlines()[0]
    assert "192.168.0.27" not in checked


def test_folders_keep_the_share_for_the_next_rewrite() -> None:
    """`mh folders add` writes mh again with every backup, the share included."""
    text = _script(Shell.POWERSHELL, _NAS)
    backups = next(
        line for line in text.splitlines() if "function global:_mh_backups" in line
    )
    assert "192.168.0.27" in backups


def test_bash_refuses_a_share_and_says_why() -> None:
    """From WSL or Linux, the user mounts the share: a NAS backup is for mh.ps1."""
    with pytest.raises(MountError, match="Windows PowerShell"):
        _script(Shell.BASH, _NAS)
