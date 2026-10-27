"""The certificates of the home network's door: a local authority, then HTTPS (0430).

A phone installs an app (0432) only from a secure page. `mh --lan` mounts a folder of
the user's home as `/lan` (`Locations.lan_dir`, never `/config`, never `/cache`: a cache
restored would force installing the authority again on every phone). The first time,
an authority is created there (`ca.key` never leaves it, `ca.crt` is what a phone
installs, once); a server certificate signed by it names the PC's address. When the
address changes, only the server certificate is issued again: the phones keep trusting
the authority. `openssl`, already in the image, makes them (+0 bytes, measured
2026-10-27; `cryptography` would add 16 MB). Without the folder or `openssl`, the door
stays plain HTTP, as before.
"""

from __future__ import annotations

import contextlib
import os
import shutil
import ssl
import subprocess  # openssl only, its arguments built here
from typing import TYPE_CHECKING, Final

from media_hygiene.paths.locations import Locations

if TYPE_CHECKING:
    from pathlib import Path

CA_CERT: Final = "ca.crt"  # what a phone installs
CA_KEY: Final = "ca.key"  # never served
SERVER_CERT: Final = "server.crt"
SERVER_KEY: Final = "server.key"
SERVER_FOR: Final = "server.address"  # the address the server certificate names
CA_NAME: Final = "Media Hygiene (this PC)"
CA_DAYS: Final = 7300  # twenty years: installed once on each phone
SERVER_DAYS: Final = 825  # the longest iOS accepts for a server certificate
_TIMEOUT: Final = 60
_KEY: Final = ("-newkey", "ec", "-pkeyopt", "ec_paramgen_curve:prime256v1", "-noenc")


def _openssl(folder: Path, *arguments: str) -> None:
    """Run `openssl req -x509` in the folder.

    Args:
        folder: Where the files are written.
        *arguments: The rest of the command.

    Raises:
        OSError: `openssl` is missing.
    """
    tool = shutil.which("openssl")
    if tool is None:
        missing = "openssl"
        raise FileNotFoundError(missing)
    command = (tool, "req", "-x509", *_KEY, *arguments)
    subprocess.run(  # noqa: S603  # a fixed tool, arguments built here
        command, cwd=folder, check=True, capture_output=True, timeout=_TIMEOUT
    )


def _issue_ca(folder: Path) -> None:
    """Create the authority, its key readable by the owner only.

    Args:
        folder: The `/lan` folder.
    """
    _openssl(
        folder,
        *("-keyout", f"{CA_KEY}.new", "-out", f"{CA_CERT}.new"),
        *("-days", str(CA_DAYS), "-subj", f"/CN={CA_NAME}"),
        *("-addext", "basicConstraints=critical,CA:TRUE"),
        *("-addext", "keyUsage=critical,keyCertSign,cRLSign"),
    )
    (folder / f"{CA_KEY}.new").chmod(0o600)
    (folder / f"{CA_KEY}.new").replace(folder / CA_KEY)
    (folder / f"{CA_CERT}.new").replace(folder / CA_CERT)


def _issue_server(folder: Path, address: str) -> None:
    """Sign a server certificate for the address with the authority.

    Args:
        folder: The `/lan` folder, the authority in it.
        address: The PC's address on the home network.
    """
    _openssl(
        folder,
        *("-keyout", f"{SERVER_KEY}.new", "-out", f"{SERVER_CERT}.new"),
        *("-days", str(SERVER_DAYS), "-subj", f"/CN={address}"),
        *("-CA", CA_CERT, "-CAkey", CA_KEY),
        *("-addext", f"subjectAltName=IP:{address}"),
        *("-addext", "extendedKeyUsage=serverAuth"),
        *("-addext", "basicConstraints=critical,CA:FALSE"),
        *("-addext", "keyUsage=critical,digitalSignature"),
    )
    (folder / f"{SERVER_KEY}.new").chmod(0o600)
    (folder / f"{SERVER_KEY}.new").replace(folder / SERVER_KEY)
    (folder / f"{SERVER_CERT}.new").replace(folder / SERVER_CERT)
    (folder / SERVER_FOR).write_text(address, encoding="utf-8")


def _names(folder: Path) -> str:
    """The address the server certificate was issued for.

    Args:
        folder: The `/lan` folder.

    Returns:
        It, or "" when there is none yet.
    """
    if not (folder / SERVER_CERT).is_file() or not (folder / SERVER_KEY).is_file():
        return ""
    with contextlib.suppress(OSError):
        return (folder / SERVER_FOR).read_text(encoding="utf-8").strip()
    return ""


def certificates(folder: Path, address: str) -> bool:
    """Make sure the folder holds the authority and a certificate for the address.

    Args:
        folder: The `/lan` folder.
        address: The PC's address on the home network.

    Returns:
        True when both are there; False without the folder, or when `openssl` failed.
    """
    try:
        if not ((folder / CA_CERT).is_file() and (folder / CA_KEY).is_file()):
            _issue_ca(folder)
        if _names(folder) != address:
            _issue_server(folder, address)
    except OSError, subprocess.SubprocessError:
        return False
    return True


def server_context(folder: Path) -> ssl.SSLContext:
    """The TLS settings of the home network's door.

    Args:
        folder: The `/lan` folder, its certificates made.

    Returns:
        A server context with the server certificate.
    """
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(folder / SERVER_CERT, folder / SERVER_KEY)
    return context


def lan_folder() -> Path | None:
    """The `/lan` folder, when `mh --lan` mounted it.

    Returns:
        It, or None when it is not a folder this process may write to.
    """
    folder = Locations().lan_dir
    return folder if folder.is_dir() and os.access(folder, os.W_OK) else None


def secure_door(address: str) -> ssl.SSLContext | None:
    """The TLS settings for the address, the certificates made when needed.

    Args:
        address: The PC's address on the home network.

    Returns:
        The context; None when the door stays plain HTTP.
    """
    folder = lan_folder()
    if folder is None or not certificates(folder, address):
        return None
    try:
        return server_context(folder)
    except OSError, ssl.SSLError:
        return None
