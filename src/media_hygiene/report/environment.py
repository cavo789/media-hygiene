"""The Jinja environment of the reports: autoescaped, translated, formatting filters."""

from __future__ import annotations

from datetime import UTC
from typing import TYPE_CHECKING, Final

from markupsafe import Markup

from media_hygiene.console.formatting import (
    human_duration,
    human_number,
    human_share,
    human_size,
)
from media_hygiene.i18n.templates import translated_environment
from media_hygiene.report.report_header import report_header

if TYPE_CHECKING:
    from datetime import datetime

    from jinja2 import Environment

_TEMPLATES_PACKAGE = "media_hygiene.report"
_SHOWN_FORMAT: Final = "%Y-%m-%d %H:%M"


def make_environment() -> Environment:
    """Create the environment; `_()` in templates uses the active language.

    Returns:
        The Jinja environment.
    """
    environment = translated_environment(_TEMPLATES_PACKAGE, escaped=("html", "j2"))
    environment.filters["size"] = human_size
    environment.filters["number"] = human_number
    environment.filters["share"] = human_share
    environment.filters["duration"] = human_duration
    environment.filters["when"] = when
    environment.globals["report_header"] = report_header
    return environment


def when(moment: datetime) -> Markup:
    """Render a moment in UTC; the page's script shows it in the reader's time zone.

    The container does not know the user's zone, the browser does: it rewrites every
    `<time datetime>` to local time. Without scripts, the UTC text stays.

    Args:
        moment: An aware datetime (a naive one is taken as UTC).

    Returns:
        A `<time>` element.
    """
    utc = moment.astimezone(UTC) if moment.tzinfo else moment.replace(tzinfo=UTC)
    return Markup('<time datetime="{iso}">{text} UTC</time>').format(
        iso=utc.isoformat(timespec="seconds"), text=utc.strftime(_SHOWN_FORMAT)
    )
