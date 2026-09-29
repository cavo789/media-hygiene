"""Entry point: `media-hygiene` (the image ENTRYPOINT) and `python -m media_hygiene`."""

from __future__ import annotations

import os
import sys

from media_hygiene.cli.app import build_app
from media_hygiene.config.legacy_env import adopt_legacy_variables
from media_hygiene.constants import APP_NAME
from media_hygiene.i18n import install
from media_hygiene.i18n.bootstrap import resolve_locale


def main() -> None:
    """Install the interface language, then run the CLI."""
    adopt_legacy_variables(os.environ)
    install(resolve_locale(sys.argv[1:]))
    build_app()(prog_name=APP_NAME)


if __name__ == "__main__":
    main()
