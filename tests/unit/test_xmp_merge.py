"""Our words in a sidecar: created, merged, idempotent, never somebody else's taken."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from media_hygiene.tags.xmp_doc import LI, XmpError, items, parse
from media_hygiene.tags.xmp_merge import (
    CAPTION,
    PERSON_IN_IMAGE,
    SUBJECT,
    XmpValues,
    merge,
    new_document,
)
from media_hygiene.tags.xmp_owner import written_by_us
from tests.support.sidecars import DARKTABLE, LIGHTROOM

_TOOL = "media-hygiene 9.9"


def _round_trip(text: str, values: XmpValues) -> bytes:
    """Merge values into a sidecar, write it, read it back once more."""
    doc = parse(text.encode())
    assert merge(doc, values)
    return doc.to_bytes()


def test_a_new_sidecar_is_ours_and_reads_back() -> None:
    """Words in `dc:subject`, the sentence in `dc:description`, our creator."""
    data = new_document(XmpValues(("ours", "Durbuy"), "Un ours."), _TOOL).to_bytes()
    assert data.startswith(b"<?xpacket begin=")
    doc = parse(data)
    assert items(doc.find(SUBJECT)) == ["ours", "Durbuy"]
    assert items(doc.find(CAPTION)) == ["Un ours."]
    assert written_by_us(doc)
    assert not merge(doc, XmpValues(("ours", "Durbuy"), "Un ours."))


def test_merged_into_lightroom_keeps_everything_else() -> None:
    """Its word stays first, its settings and prefixes stay; not ours afterwards."""
    data = _round_trip(LIGHTROOM, XmpValues(("ours",), "Un ours."))
    text = data.decode()
    assert 'crs:Exposure2012="+0.35"' in text
    assert 'xmp:CreatorTool="Adobe Photoshop Lightroom Classic"' in text
    assert text.startswith('<?xpacket begin="﻿"')
    assert text.rstrip().endswith('<?xpacket end="w"?>')
    doc = parse(data)
    assert items(doc.find(SUBJECT)) == ["famille", "ours"]
    assert not written_by_us(doc)
    assert not merge(doc, XmpValues(("ours",), "Un ours."))  # idempotent


def test_darktable_keeps_its_sentence_and_history() -> None:
    """Somebody else's sentence is never replaced."""
    doc = parse(_round_trip(DARKTABLE, XmpValues(("neige",), "De la neige.")))
    assert items(doc.find(CAPTION)) == ["Mon texte"]
    assert items(doc.find(SUBJECT)) == ["neige"]
    assert b'darktable:operation="exposure"' in doc.to_bytes()


def test_removed_words_stay_removed_and_old_ones_are_taken_back() -> None:
    """A word the user removed is not added again; one we no longer give goes."""
    doc = new_document(XmpValues(("ours", "forêt"), "Un ours."), _TOOL)
    bag = doc.find(SUBJECT)
    assert bag is not None
    bag[0].remove(bag[0][0])  # removed in another application
    assert items(doc.find(SUBJECT)) == ["forêt"]
    assert merge(doc, XmpValues(("ours", "neige"), "Un ours dans la neige."))
    assert items(doc.find(SUBJECT)) == ["neige"]  # "ours" not back, "forêt" ours: gone
    assert items(doc.find(CAPTION)) == ["Un ours dans la neige."]
    assert merge(doc, XmpValues((), ""))
    assert doc.find(SUBJECT) is None
    assert doc.find(CAPTION) is None


@pytest.mark.parametrize(
    "data",
    [
        b'<!DOCTYPE x [<!ENTITY a "b">]><x:xmpmeta xmlns:x="adobe:ns:meta/"/>',
        b"<x:xmpmeta xmlns:x='adobe:ns:meta/'><unclosed></x:xmpmeta>",
        b"\xff\xfe not utf-8",
        b"no xml at all",
    ],
)
def test_what_is_not_xmp_is_refused(data: bytes) -> None:
    """A DOCTYPE, broken XML, another encoding: refused, never rewritten."""
    with pytest.raises(XmpError):
        parse(data)


def test_people_are_written_shared_and_taken_back() -> None:
    """`PersonInImage`: ours added, another tool's kept, ours gone with the source."""
    doc = new_document(XmpValues(("ours",), people=("Léa",)), _TOOL)
    assert items(doc.find(PERSON_IN_IMAGE)) == ["Léa"]
    bag = doc.find(PERSON_IN_IMAGE)
    assert bag is not None
    ET.SubElement(bag[0], LI).text = "Paul"  # named in digiKam
    assert merge(doc, XmpValues(("ours",), people=("Léa", "Zoé")))
    assert items(doc.find(PERSON_IN_IMAGE)) == ["Léa", "Paul", "Zoé"]
    assert merge(doc, XmpValues(("ours",)))  # the `person` source removed
    assert items(doc.find(PERSON_IN_IMAGE)) == ["Paul"]
    assert new_document(XmpValues(("ours",)), _TOOL).find(PERSON_IN_IMAGE) is None
