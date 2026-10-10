"""Options only `review` has, translated once the locale is known."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, cast

import typer

from media_hygiene.cli.clean_options import decisions_option
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from typer.models import OptionInfo

# Uncommon, so rarely taken on the host, where it is published under the same number.
PAGE_PORT: Final = 8088


def decisions_file() -> OptionInfo:
    """`--decisions`: where the review saves its decisions, and resumes from.

    Returns:
        The option definition.
    """
    return decisions_option(
        _(
            "File the decisions are saved in, and resumed from. A relative path "
            "lies in the folder mounted on /reports. Default: decisions.json."
        )
    )


def port() -> OptionInfo:
    """`--port`: the port of the page, inside the container.

    Returns:
        The option definition.
    """
    return cast(
        "OptionInfo",
        typer.Option(
            "--port",
            min=1,
            help=_(
                "Port of the page. docker run publishes it under the same number "
                "on your computer: -p 127.0.0.1:9000:9000 for --port 9000. "
                "Default: {default}."
            ).format(default=PAGE_PORT),
            show_default=False,
        ),
    )
