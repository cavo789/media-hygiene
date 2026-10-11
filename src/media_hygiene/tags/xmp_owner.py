"""Which sidecars hold edits: those of other applications, not those of `xmp` alone.

The kept copy of a duplicate group prefers a file with a sidecar: someone edited it
(Lightroom, darktable). A sidecar `xmp` created, holding only our words, says no such
thing: it must not change which copy is kept.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.constants import APP_NAME
from media_hygiene.tags.xmp_doc import ABOUT, MH_NS, XmpError, parse, text_of
from media_hygiene.tags.xmp_merge import CAPTION, CREATOR, SUBJECT

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from media_hygiene.scan.sidecars import Sidecar
    from media_hygiene.tags.xmp_doc import XmpDoc

_XMP: Final = ".xmp"
_OURS: Final = frozenset({ABOUT, CREATOR, SUBJECT, CAPTION})
# A sidecar this large holds more than our few words: not read, not ours.
_LARGEST_OURS: Final = 256 * 1024


def is_ours(path: Path) -> bool:
    """Tell whether a sidecar was written by `xmp` alone.

    Args:
        path: The sidecar.

    Returns:
        True for an `.xmp` file this tool created and nobody edited since.
    """
    if path.suffix.casefold() != _XMP:
        return False
    try:
        if path.stat().st_size > _LARGEST_OURS:
            return False
        return written_by_us(parse(path.read_bytes()))
    except OSError, XmpError:
        return False


def with_edits(sidecars: Iterable[Sidecar]) -> list[Sidecar]:
    """Keep the sidecars that may hold edits: every one but ours.

    Args:
        sidecars: The sidecars a walk listed.

    Returns:
        Those not written by `xmp` alone.
    """
    return [sidecar for sidecar in sidecars if not is_ours(sidecar.file.path)]


def written_by_us(doc: XmpDoc) -> bool:
    """Tell whether a sidecar is ours alone: it holds no edit of another application.

    Args:
        doc: The sidecar.

    Returns:
        True when this tool created it and it holds only our properties.
    """
    descriptions = doc.descriptions()
    creators = [
        each.get(CREATOR) or text_of(each.find(CREATOR)) for each in descriptions
    ]
    if not any(creator.startswith(APP_NAME) for creator in creators if creator):
        return False
    return all(
        _is_ours(name)
        for each in descriptions
        for name in (*each.attrib, *(child.tag for child in each))
    )


def _is_ours(name: str) -> bool:
    """Tell whether a property is one this tool writes.

    Args:
        name: Its `{namespace}name`.

    Returns:
        True for ours.
    """
    return name in _OURS or name.startswith(f"{{{MH_NS}}}")
