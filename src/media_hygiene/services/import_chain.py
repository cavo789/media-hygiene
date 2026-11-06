"""Where the chain after an import is (0604): `import-chain.json` of the cache folder.

The chain runs in `mh.ps1`, on the host (`mh_phone.ps1.j2`): it writes this file before
each step, and at its end. The home server only reads it, except after a copy from the
import page (0619), which writes it *waiting* for `mh import --chain`. The folder is the
one Explorer shows, the same words as `phone-end`: a folder renamed since is simply
said missing by the steps. A window closed writes nothing: a chain *running* whose file
has not changed for `STALE_HOURS` is said stopped, and offered again.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, ValidationError

from media_hygiene.config.import_settings import ImportStep
from media_hygiene.paths.docker_run import Shell
from media_hygiene.review.home_fields import write_whole
from media_hygiene.services.import_end import day_of
from media_hygiene.services.next_command import LAUNCHER_VARIABLE

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime

CHAIN_FILE: Final = "import-chain.json"
CHAIN_FLAG: Final = "--chain"  # `mh import --chain`: read by `mh.ps1`, never Docker
FROM_FLAG: Final = "--from-step"
ALL_FILES: Final = "all"  # `--since all`
STALE_HOURS: Final = 24  # longer than a night of `tags` between two steps (estimated)


class ChainState(StrEnum):
    """Where a chain is, the words `mh.ps1` writes."""

    WAITING = "waiting"
    RUNNING = "running"
    STOPPED = "stopped"
    DONE = "done"


class ImportChain(BaseModel):
    """The file: its steps, the one running or next, the import it follows."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    steps: tuple[ImportStep, ...]
    at: ImportStep
    state: ChainState
    folder: str  # as Explorer shows it
    since: str  # the import's period
    failed: tuple[ImportStep, ...] = ()
    updated: str = ""  # ISO, UTC


def chain_file(runtime: Runtime) -> Path:
    """The file of a run.

    Args:
        runtime: Mount points.

    Returns:
        In the cache folder.
    """
    return runtime.locations.cache_dir / CHAIN_FILE


def read_chain(file: Path, now: datetime | None = None) -> ImportChain | None:
    """Read the file; a chain left *running* too long is said stopped.

    Args:
        file: The chain's file.
        now: The time; None: now.

    Returns:
        The chain; None for a file missing or damaged.
    """
    try:
        # `-sig`: Windows PowerShell 5.1 writes a byte order mark.
        chain = ImportChain.model_validate_json(file.read_text("utf-8-sig"))
    except OSError, ValueError, ValidationError:
        return None
    if chain.state is not ChainState.RUNNING:
        return chain
    try:
        updated = datetime.fromisoformat(chain.updated)
    except ValueError:
        return chain
    if (now or datetime.now(UTC)) - updated < timedelta(hours=STALE_HOURS):
        return chain
    return chain.model_copy(update={"state": ChainState.STOPPED})


def waiting_chain(runtime: Runtime, copied: tuple[Path, ...]) -> ImportChain | None:
    """Write the chain a copy from the page leaves to `mh` (0619).

    Args:
        runtime: Settings and mount points.
        copied: The copies read back (container paths).

    Returns:
        The chain written; None without a copy, without a step, or out of `mh.ps1`.
    """
    steps = runtime.settings.imports.then
    if not copied or not steps:
        return None
    if os.environ.get(LAUNCHER_VARIABLE) != Shell.POWERSHELL.value:
        return None  # the chain lives in `mh.ps1`: the page then says to audit again
    folder = os.path.commonpath([path.parent for path in copied])
    days = [day for path in copied if (day := day_of(path)) is not None]
    chain = ImportChain(
        steps=steps,
        at=steps[0],
        state=ChainState.WAITING,
        folder=runtime.mapper.to_host(Path(folder)),
        since=min(days).isoformat() if len(days) == len(copied) else ALL_FILES,
        updated=datetime.now(UTC).isoformat(),
    )
    write_whole(chain_file(runtime), chain.model_dump_json(indent=0) + "\n")
    return chain
