"""`POST /api/hand-tag`: a word typed on the photos picked, or taken off one (0555).

*🏷 Tag…* in the bar of the search page gives a word (typed, or one given before) to
the photos picked; the cross of a `hand` chip takes it off one photo. The word and its
photos are a decision: written to `/config/tags/<word>.toml` (`tags.hand_edit`), read
back from the disk, and the words of each photo shown come from what was read. The
search finds them at once (`HandIndex.give_hand`).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from media_hygiene.classify.hand_placed import Candidate, digest_of
from media_hygiene.config.hand_tags import LONGEST, HandTag
from media_hygiene.config.photo_ref import PhotoRef, content_id
from media_hygiene.i18n import _, ngettext
from media_hygiene.review.config_saving import save_refused
from media_hygiene.review.serving import json_response
from media_hygiene.tags.hand_edit import give_word, take_word
from media_hygiene.tags.hand_files import hand_words, read_hand_tags

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.review.http import Response
    from media_hygiene.search.fts import SearchIndex
    from media_hygiene.search.hand_index import HandIndex

HAND_TAG_PATH: Final = "/api/hand-tag"
_MOST: Final = 20_000  # photos picked at once, as *Move to an event…*
_DIGEST: Final = "SELECT full_digest FROM files WHERE rowid = ?"
_CONTROL: Final = re.compile(r"[\x00-\x1f\x7f]")


class TagAsked(BaseModel):
    """What the page asks: the words there are, a word given, or taken off."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    action: Literal["list", "add", "remove"] = "list"
    keys: tuple[int, ...] = Field(default=(), max_length=_MOST)
    word: str = Field(default="", max_length=LONGEST)


@dataclass(frozen=True, slots=True)
class TagDesk:
    """The words typed by hand: `config.toml` (None: not writable), the search."""

    index: HandIndex
    mapper: HostPathMapper
    config_file: Path | None

    def answer(self, body: bytes) -> Response:
        """List the words, give one to the photos picked, or take it off.

        Args:
            body: `TagAsked`, as JSON.

        Returns:
            Every word, each photo's words read back from the disk, and the line
            said; 400 for a body that cannot be read, 409 when `/config` cannot be
            written, 422 or 500 when the save fails.
        """
        try:
            asked = TagAsked.model_validate_json(body)
        except ValidationError as exc:
            said = exc.errors()[0]["msg"] if exc.errors() else str(exc)
            return json_response(HTTPStatus.BAD_REQUEST, {"error": said})
        word = " ".join(_CONTROL.sub(" ", asked.word).split())
        if asked.action != "list" and self.config_file is None:
            said = _("Words cannot be saved: /config is not mounted, or read-only.")
            return json_response(HTTPStatus.CONFLICT, {"error": said})
        if asked.action != "list" and not (word and asked.keys):
            return json_response(
                HTTPStatus.BAD_REQUEST, {"error": _("Type a word, pick a photo.")}
            )
        try:
            said = self._save(asked, word) if asked.action != "list" else ""
            return json_response(HTTPStatus.OK, self._read_back(asked.keys, said))
        except (ValueError, OSError) as exc:
            return save_refused(exc)

    def _save(self, asked: TagAsked, word: str) -> str:
        """Write the word given or taken off.

        Args:
            asked: The keys and the action.
            word: The word, cleaned.

        Returns:
            The line to say, before it is read back.
        """
        config = self.config_file
        if config is None:  # pragma: no cover - refused before
            return ""
        if asked.action == "remove":
            paths = {self._path(key) for key in asked.keys}
            ids = {
                photo.id
                for entry in read_hand_tags(config)
                for photo in entry.photos
                if self.mapper.to_container(photo.path) in paths
            }
            take_word(config, word, ids)
            return _("“{word}” taken off, read back from the disk.").format(word=word)
        refs = tuple(ref for key in asked.keys if (ref := self._ref(key)) is not None)
        give_word(config, HandTag(word=word, photos=refs))
        return ngettext(
            "“{word}” given to {n} photo, read back from the disk.",
            "“{word}” given to {n} photos, read back from the disk.",
            len(refs),
        ).format(word=word, n=len(refs))

    def _read_back(self, keys: tuple[int, ...], said: str) -> dict[str, object]:
        """Read the words from the disk, give them to the search, answer them.

        Args:
            keys: The photos the page shows changed.
            said: The line said.

        Returns:
            `words` (every word, sorted), `tags` (the words of each key), `saved`.
        """
        words = hand_words(self.config_file, self.mapper) if self.config_file else {}
        if said:
            self.index.give_hand(words)  # found at the next search
        every = sorted({w for found in words.values() for w in found}, key=str.casefold)
        paths = {key: self._path(key) for key in keys}
        tags = {str(k): list(words.get(p, ())) if p else [] for k, p in paths.items()}
        return {"words": every, "tags": tags, "saved": said}

    def _path(self, key: int) -> Path | None:
        """The container path of a key.

        Args:
            key: A key of the search.

        Returns:
            The path; None for an unknown key.
        """
        photo = self.index.source_of(key)
        return None if photo is None else photo.path

    def _ref(self, key: int) -> PhotoRef | None:
        """A photo as `{path, id}`: its digest the index's, else read once.

        Args:
            key: A key of the search.

        Returns:
            The reference, or None.
        """
        return ref_of(self.index, self.mapper, key)


def ref_of(index: SearchIndex, mapper: HostPathMapper, key: int) -> PhotoRef | None:
    """A photo as `{path, id}`: its digest the index's, else read once.

    Args:
        index: The open search.
        mapper: Writes its path as the user knows it.
        key: A key of the search.

    Returns:
        The reference; None for an unknown key, or a file that cannot be read.
    """
    photo = index.source_of(key)
    if photo is None:
        return None
    row = index.connection.execute(_DIGEST, (key,)).fetchone()
    sha = digest_of(Candidate(photo.path, photo.size, row[0] if row else None))
    if sha is None:
        return None
    return PhotoRef(path=mapper.to_host(photo.path), id=content_id(sha, photo.size))
