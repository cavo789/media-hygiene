"""An XMP sidecar as a tree: read safely, its few properties read and set, written back.

Sidecars come from other applications (Lightroom, darktable, digiKam): what lies
before and after the `x:xmpmeta` element (the `xpacket` instructions) is kept as is,
every namespace keeps its prefix, and only the properties this tool writes are
touched. A document type declaration is refused: XMP has none, and entities are a way
to attack an XML reader.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Final, cast

X_NS: Final = "adobe:ns:meta/"
RDF_NS: Final = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
DC_NS: Final = "http://purl.org/dc/elements/1.1/"
XMP_NS: Final = "http://ns.adobe.com/xap/1.0/"
# What this tool wrote last, to replace it next time and never add back a word the
# user removed in another application.
MH_NS: Final = "https://github.com/cavo789/media-hygiene/ns/xmp/1.0/"
PREFIXES: Final = {"x": X_NS, "rdf": RDF_NS, "dc": DC_NS, "xmp": XMP_NS, "mh": MH_NS}
LANG: Final = "{http://www.w3.org/XML/1998/namespace}lang"
DEFAULT_LANG: Final = "x-default"
ABOUT: Final = f"{{{RDF_NS}}}about"
DESCRIPTION: Final = f"{{{RDF_NS}}}Description"
LI: Final = f"{{{RDF_NS}}}li"
BAG: Final = f"{{{RDF_NS}}}Bag"
ALT: Final = f"{{{RDF_NS}}}Alt"
_RDF: Final = f"{{{RDF_NS}}}RDF"
_LISTS: Final = (BAG, f"{{{RDF_NS}}}Seq", ALT)
_FIRST_ELEMENT: Final = re.compile(r"<(?![?!])")
_LAST_END: Final = re.compile(r"</[^>]*>\s*(?:<\?[^>]*\?>\s*)*$")
_DOCTYPE: Final = b"<!DOCTYPE"
_BOM: Final = "﻿"


class XmpError(ValueError):
    """A sidecar that cannot be read as XMP: left alone, and listed."""


@dataclass(frozen=True, slots=True)
class XmpDoc:
    """A sidecar: the text around its root element, the root, its namespaces."""

    before: str
    root: ET.Element
    after: str
    namespaces: tuple[tuple[str, str], ...]

    def to_bytes(self) -> bytes:
        """Write the sidecar back, every namespace under its own prefix.

        Returns:
            The UTF-8 bytes.
        """
        for prefix, uri in (*self.namespaces, *PREFIXES.items()):
            if prefix and not re.fullmatch(r"ns\d+", prefix):
                ET.register_namespace(prefix, uri)
        body = ET.tostring(self.root, encoding="unicode")
        return f"{self.before}{body}{self.after}".encode()

    def rdf(self) -> ET.Element:
        """The `rdf:RDF` element, created when missing.

        Returns:
            It.
        """
        if self.root.tag == _RDF:
            return self.root
        found = self.root.find(_RDF)
        return found if found is not None else ET.SubElement(self.root, _RDF)

    def descriptions(self) -> list[ET.Element]:
        """Every `rdf:Description`, one created when there is none.

        Returns:
            Them, in document order.
        """
        rdf = self.rdf()
        found = rdf.findall(DESCRIPTION)
        return found or [ET.SubElement(rdf, DESCRIPTION, {ABOUT: ""})]

    def find(self, tag: str) -> ET.Element | None:
        """The property `tag` (`{namespace}name`), in any description.

        Args:
            tag: The property.

        Returns:
            Its element, or None.
        """
        return next(
            (
                found
                for each in self.descriptions()
                if (found := each.find(tag)) is not None
            ),
            None,
        )


def parse(data: bytes) -> XmpDoc:
    """Read a sidecar.

    Args:
        data: Its bytes.

    Returns:
        The document.

    Raises:
        XmpError: Not UTF-8, a document type declaration, or not well-formed XML.
    """
    if _DOCTYPE in data.upper():
        raise XmpError(_DOCTYPE.decode())
    try:
        text = data.decode().removeprefix(_BOM)
    except UnicodeDecodeError as exc:
        raise XmpError(str(exc)) from exc
    start, end = _FIRST_ELEMENT.search(text), _LAST_END.search(text)
    if start is None or end is None:
        raise XmpError(text[:40])
    closing = text.index(">", end.start()) + 1
    body = text[start.start() : closing]
    try:
        root = ET.fromstring(body)  # noqa: S314 - no DOCTYPE: no entity to expand
        reader: ET.XMLPullParser[tuple[str, str]] = ET.XMLPullParser(
            events=("start-ns",)
        )
        reader.feed(body)
        namespaces = tuple(
            cast("tuple[str, tuple[str, str]]", event)[1]
            for event in reader.read_events()
        )
    except ET.ParseError as exc:
        raise XmpError(str(exc)) from exc
    return XmpDoc(text[: start.start()], root, text[closing:], namespaces)


def items(element: ET.Element | None) -> list[str]:
    """The values of a list property (`rdf:Bag`, `rdf:Seq`, `rdf:Alt`).

    Args:
        element: The property, or None.

    Returns:
        Its values, in order; empty without any.
    """
    if element is None:
        return []
    return [
        (item.text or "").strip()
        for kind in _LISTS
        for holder in element.findall(kind)
        for item in holder.findall(LI)
    ]


def text_of(element: ET.Element | None) -> str:
    """The text of a simple property.

    Args:
        element: The property, or None.

    Returns:
        Its text, stripped; empty without any.
    """
    return "" if element is None else (element.text or "").strip()
