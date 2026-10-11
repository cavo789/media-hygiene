"""What the console says of `search "words"`: the files found, best first."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from rich.markup import escape
from rich.table import Table

from media_hygiene.console.formatting import human_number
from media_hygiene.i18n import _, ngettext
from media_hygiene.tags.models import TagSource

if TYPE_CHECKING:
    from media_hygiene.console.output import Output
    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.search.models import Found

_JOINED: Final = "; "


def show_found(output: Output, found: Found, mapper: HostPathMapper) -> None:
    """Print the files found as a table, or say that nothing matches.

    Args:
        output: Where to print.
        found: The total and the first files.
        mapper: Writes the paths as the user knows them.
    """
    if not found.total:
        output.warning(_("Nothing found."))
        output.tip(
            _(
                "Fewer words, or the start of a word with a star (anniv*), find "
                "more; place:durbuy looks among the places only."
            )
        )
        return
    table = Table(_("File"), _("Date"), _("Words"))
    for hit in found.hits:
        words = dict.fromkeys(
            word
            for source, values in hit.tags.items()
            if source is not TagSource.CAPTION
            for word in values
        )
        table.add_row(
            escape(mapper.to_host(hit.photo.path)),
            hit.date or "",
            escape(_JOINED.join(words)),
        )
    output.show(table)
    shown = len(found.hits)
    if shown < found.total:
        output.info(
            _("{total} files found; the first {shown} are listed (--limit).").format(
                total=human_number(found.total), shown=human_number(shown)
            )
        )
        return
    output.success(
        ngettext("{count} file found.", "{count} files found.", found.total).format(
            count=human_number(found.total)
        )
    )
