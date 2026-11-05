"""The day a photo was taken, in its sidecar (0531): `photoshop:DateCreated`.

The field digiKam, Lightroom and darktable read. A date there from another application
is never replaced; ours (tracked in `mh:`, as the places are) can be corrected. The same
reader serves every date field a sidecar may hold.
"""

from __future__ import annotations

import re
from typing import Final

from media_hygiene.tags.xmp_doc import EXIF_NS, MH_NS, PHOTOSHOP_NS, XMP_NS, parse
from media_hygiene.tags.xmp_doc import text_of as _text_of
from media_hygiene.tags.xmp_merge import XmpValues, new_document
from media_hygiene.tags.xmp_places import set_tracked, simple_value

DATE_CREATED: Final = f"{{{PHOTOSHOP_NS}}}DateCreated"
_TRACKED: Final = f"{{{MH_NS}}}date"
_READ: Final = (
    DATE_CREATED,
    f"{{{EXIF_NS}}}DateTimeOriginal",
    f"{{{XMP_NS}}}CreateDate",
)
_DAY: Final = re.compile(r"\d{4}-\d{2}-\d{2}")


def sidecar_day(data: bytes) -> str | None:
    """The day a sidecar says its photo was taken.

    Args:
        data: The sidecar's bytes.

    Returns:
        `YYYY-MM-DD`; None without a full day.

    Raises:
        XmpError: The sidecar cannot be read.
    """
    doc = parse(data)
    for name in _READ:
        if found := _DAY.match(simple_value(doc, name)):
            return found.group()
    return None


def with_day(previous: bytes | None, day: str, tool: str) -> bytes | None:
    """A sidecar holding this day.

    Args:
        previous: The sidecar there; None: a new one.
        day: `YYYY-MM-DD`.
        tool: `media-hygiene <version>`, the creator of a new sidecar.

    Returns:
        Its bytes; None when another application's date is there: left as it is.

    Raises:
        XmpError: The sidecar there cannot be read.
    """
    doc = new_document(XmpValues(()), tool) if previous is None else parse(previous)
    current = simple_value(doc, DATE_CREATED)
    if current and current != _text_of(doc.find(_TRACKED)):
        return None
    set_tracked(doc, (DATE_CREATED, _TRACKED), day)
    return doc.to_bytes()
