"""After a copy from the import page (0619): the chain handed to `mh`, as the console's.

Under the home server, `mh` runs `import --chain` in its window at once, each step
keeping its own question there, and the home page follows it; a page typed in a console
(`mh import --pick <folder>`) has no such `mh` beside it: `mh.ps1` finds the chain
waiting when the page ends.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from media_hygiene.review.step_watch import keep_step, keeps_server
from media_hygiene.services.import_chain import CHAIN_FLAG, waiting_chain

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.import_chain import ImportChain
    from media_hygiene.services.runtime import Runtime


def start_chain(runtime: Runtime, copied: tuple[Path, ...]) -> ImportChain | None:
    """Leave the chain waiting, and hand it to the `mh` beside the server, if any.

    Args:
        runtime: Settings and mount points.
        copied: The copies read back.

    Returns:
        The chain; None when no chain follows this copy.
    """
    chain = waiting_chain(runtime, copied)
    if chain is not None and keeps_server():
        # Refused (another step runs): it stays waiting, the home page offers it.
        asyncio.run(
            keep_step(
                runtime.locations.reports_dir,
                ("import", CHAIN_FLAG),
                f"mh import {CHAIN_FLAG}",
            )
        )
    return chain
