"""The sentence and the words of `tags`, carried inside the copies to send (0381).

A photo sent alone leaves its `.xmp` sidecar behind, and many services read only what
is inside the file: the copy made by `share` gets an XMP packet (`dc:description`,
`dc:subject`, built like a sidecar) and the EXIF fields Windows Explorer shows under
Properties > Details (`XPKeywords`, `XPComment`, UCS-2). The original is never
rewritten.

- The words are read in the main process (the worker pool never opens the index),
  for the version of the file on the disk: tags of another size or mtime are stale.
- The sources are `[tags] xmp_sources`, never `person`: names do not travel.
- A description already in the EXIF (written by a person, a camera, Windows) wins:
  the model's sentence is then not written; `ImageDescription` is never touched (ASCII).
"""

from __future__ import annotations

import contextlib
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from PIL import Image

from media_hygiene.index.descriptions import PhotoVersion
from media_hygiene.index.read_only import connect_read_only
from media_hygiene.index.tag_rows import TagStore
from media_hygiene.report.thumbnails import unreadable_errors
from media_hygiene.tags.models import TagSource
from media_hygiene.tags.xmp_merge import XmpValues, new_document

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from pathlib import Path

_IMAGE_DESCRIPTION: Final = 0x010E
XP_COMMENT: Final = 0x9C9C
XP_KEYWORDS: Final = 0x9C9E
_UCS2: Final = "utf-16-le"
_UCS2_END: Final = b"\x00\x00"
_SEPARATOR: Final = ";"  # how Explorer separates the keywords
_SAID: Final = frozenset({TagSource.CAPTION, TagSource.VISION})  # what is asked about
_TOOL: Final = "media-hygiene share"


@dataclass(frozen=True, slots=True)
class SentWords:
    """What `tags` saw of one photo: its sentence and its words."""

    sentence: str = ""
    words: tuple[str, ...] = ()

    def __bool__(self) -> bool:
        """Anything to write.

        Returns:
            True with a sentence or a word.
        """
        return bool(self.sentence or self.words)


NO_WORDS: Final = SentWords()


def words_of(
    index_file: Path | None, photos: Sequence[Path], sources: Iterable[TagSource]
) -> dict[Path, SentWords]:
    """Read the sentence and the words of each photo, from the index, read-only.

    Args:
        index_file: The index; None (not mounted) or missing: no words.
        photos: The photos, in the container, as they are on the disk now.
        sources: The sources written (`[tags] xmp_sources`); `person` is ignored.

    Returns:
        The words of each photo that has a sentence or words of the vision model;
        empty when none has: nothing is then asked nor written.
    """
    if index_file is None or not index_file.is_file():
        return {}
    chosen = frozenset(sources) - {TagSource.PERSON, TagSource.CAPTION}
    found: dict[Path, SentWords] = {}
    with (
        contextlib.suppress(sqlite3.Error),
        closing(connect_read_only(index_file)) as connection,
    ):
        store = TagStore(connection)
        for photo in photos:
            stat = photo.stat()
            tags = store.of(PhotoVersion(photo, stat.st_size, stat.st_mtime_ns))
            if not any(tag.source in _SAID for tag in tags):
                continue
            sentences = [t.value for t in tags if t.source is TagSource.CAPTION]
            words = dict.fromkeys(t.value for t in tags if t.source in chosen)
            found[photo] = SentWords(sentences[0] if sentences else "", tuple(words))
    return found


def add_words(exif: Image.Exif, words: SentWords) -> bytes:
    """Put the words into the EXIF of a copy, and make its XMP packet.

    Args:
        exif: The EXIF of the copy, changed in place.
        words: The sentence and the words; empty writes nothing.

    Returns:
        The XMP packet (UTF-8), or empty bytes.
    """
    if not words:
        return b""
    sentence = "" if _described(exif) else words.sentence
    if words.words:
        exif[XP_KEYWORDS] = _ucs2(_SEPARATOR.join(words.words))
    if sentence:
        exif[XP_COMMENT] = _ucs2(sentence)
    return new_document(XmpValues(words.words, sentence), _TOOL).to_bytes()


def ucs2_text(value: object) -> str:
    """Read back an EXIF field of Windows (`XPKeywords`, `XPComment`).

    Args:
        value: The raw field.

    Returns:
        Its text; empty when it is not one.
    """
    if not isinstance(value, bytes):
        return ""
    return value.decode(_UCS2, errors="replace").rstrip("\x00")


def described_on_disk(folder: Path) -> int:
    """Count the copies of a folder that carry words, read back from the disk.

    Args:
        folder: The album's folder.

    Returns:
        The copies holding an XMP packet.
    """
    count = 0
    for path in folder.iterdir():
        with contextlib.suppress(*unreadable_errors()), Image.open(path) as image:
            count += bool(image.info.get("xmp"))
    return count


def _described(exif: Image.Exif) -> bool:
    """Tell whether the photo already has a description, written by someone else.

    Args:
        exif: The EXIF of the photo.

    Returns:
        True with an `ImageDescription` or an `XPComment` that is not empty.
    """
    human = exif.get(_IMAGE_DESCRIPTION)
    text = human.strip() if isinstance(human, str) else ""
    return bool(text or ucs2_text(exif.get(XP_COMMENT)).strip())


def _ucs2(text: str) -> bytes:
    """Encode a text the way Windows writes its EXIF fields.

    Args:
        text: The text.

    Returns:
        UCS-2 little endian, ended by a null character.
    """
    return text.encode(_UCS2) + _UCS2_END
