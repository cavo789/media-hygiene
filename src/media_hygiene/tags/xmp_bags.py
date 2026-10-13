"""Bag properties of a sidecar, and how this tool shares one with other applications.

A tracked bag (`dc:subject` and its memory `mh:subjects`, `PersonInImage` and
`mh:people`) gets our values after those already there; the values we wrote last time
and no longer produce are taken back, and a value we wrote that is gone (removed in
another application) is not added again.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING

from media_hygiene.tags.xmp_doc import BAG, LI, items

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.tags.xmp_doc import XmpDoc


def merge_tracked(doc: XmpDoc, tags: tuple[str, str], wanted: Sequence[str]) -> None:
    """Merge our values into a bag, remembering which ones are ours.

    Args:
        doc: The sidecar, changed in place.
        tags: The bag (`dc:subject`), and where we remember ours (`mh:subjects`).
        wanted: Our values of today; none takes ours back.
    """
    shared, ours = tags
    present = items(doc.find(shared))
    written = items(doc.find(ours))
    added = [value for value in wanted if value not in written and value not in present]
    stale = {value for value in present if value in written and value not in wanted}
    set_list(doc, shared, [value for value in present if value not in stale] + added)
    set_list(doc, ours, [value for value in written if value in wanted] + added)


def tracked_snapshot(doc: XmpDoc, tags: tuple[str, str]) -> tuple[tuple[str, ...], ...]:
    """The values of a tracked bag and of its memory, to tell a change.

    Args:
        doc: The sidecar.
        tags: The bag and its memory.

    Returns:
        Both lists of values.
    """
    return tuple(tuple(items(doc.find(tag))) for tag in tags)


def set_list(doc: XmpDoc, tag: str, values: Sequence[str]) -> None:
    """Write a bag property where it is (in the first description when new).

    Args:
        doc: The sidecar.
        tag: The property.
        values: Its values; none removes it.
    """
    element = doc.find(tag)
    if not values:
        remove(doc, tag)
        return
    if element is None:
        element = ET.SubElement(doc.descriptions()[0], tag)
    for child in list(element):
        element.remove(child)
    bag = ET.SubElement(element, BAG)
    for value in values:
        ET.SubElement(bag, LI).text = value


def remove(doc: XmpDoc, tag: str) -> None:
    """Remove a property from every description.

    Args:
        doc: The sidecar.
        tag: The property.
    """
    for each in doc.descriptions():
        for child in each.findall(tag):
            each.remove(child)
