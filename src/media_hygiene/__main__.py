"""Entry point: `media-hygiene` (the image ENTRYPOINT) and `python -m media_hygiene`."""

from __future__ import annotations

import signal
import sys
from typing import TYPE_CHECKING

from media_hygiene.constants import APP_NAME
from media_hygiene.teardown import quiet_teardown

if TYPE_CHECKING:
    from types import FrameType


def stop_like_ctrl_c(_signal: int, _frame: FrameType | None) -> None:
    """End on `docker stop` (SIGTERM) as on Ctrl+C: index committed, journal closed.

    The tool is PID 1 in the container: without a handler, SIGTERM is ignored and
    Docker kills it 10 seconds later, losing what the run had not committed.

    Raises:
        KeyboardInterrupt: Always, handled as Ctrl+C is.
    """
    raise KeyboardInterrupt


def main() -> None:
    """Install the interface language, then run the CLI."""
    # Imported here, not at the top: every worker of the image pool imports this module
    # again (as `__mp_main__`), and must not load the whole command line with it.
    # pylint: disable=import-outside-toplevel
    from media_hygiene.cli.app import build_app  # noqa: PLC0415
    from media_hygiene.cli.bare_options import with_default_decisions  # noqa: PLC0415
    from media_hygiene.i18n import install  # noqa: PLC0415
    from media_hygiene.i18n.bootstrap import resolve_locale  # noqa: PLC0415

    signal.signal(signal.SIGTERM, stop_like_ctrl_c)
    install(resolve_locale(sys.argv[1:]))
    app = build_app()
    # The command's last word said, a Ctrl+C while threads finish ends quietly (0275).
    with quiet_teardown():
        app(args=with_default_decisions(sys.argv[1:]), prog_name=APP_NAME)


if __name__ == "__main__":
    main()
