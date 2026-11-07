"""Drop useless tags from the search page, merge a synonym, restore one (0546, 0622).

Reached through `POST /api/hand-tag`: `frequent` lists the most frequent tags to tick;
`drop_look` says how many photos carry some words and shows a few; `drop` removes them
and `merge` names a word as another tag (`services.tag_drop`), each answering what the
disk holds after it: the stop words and synonyms read back, the photos still carrying
the words counted again. `dropped` lists both, `restore` takes a word out of them: its
photos get it again at the next `tags`, from the answers kept, without asking the model.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _
from media_hygiene.index.tag_drop import keys_of
from media_hygiene.index.tag_merge import frequent
from media_hygiene.review.config_saving import save_refused
from media_hygiene.review.serving import json_response
from media_hygiene.search.tag_asked import cleaned
from media_hygiene.search.tag_drop_said import (
    dropped_line,
    listed,
    merged_line,
    sidecar_lines,
    stop_word_target,
)
from media_hygiene.search.views import JPEG, THUMB_PREFIX
from media_hygiene.services.tag_drop import Merge
from media_hygiene.tags.stop_edit import remove_stop_word, saved_stop_words
from media_hygiene.tags.synonym_edit import remove_synonym, saved_synonyms

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.review.http import Response
    from media_hygiene.search.fts import SearchIndex
    from media_hygiene.search.tag_asked import TagAsked
    from media_hygiene.services.tag_drop import Dropped

DROP_ACTIONS: Final = frozenset(
    {"drop_look", "drop", "dropped", "restore", "frequent", "merge"}
)
SHOWN: Final = 12  # the photos shown first: a look, the count says the rest
FREQUENT: Final = 30  # the tags offered to tick: the most frequent ones (0622)


@dataclass(frozen=True, slots=True)
class DropDesk:
    """Where the stop words are (None: not writable), the search, dropping, merging."""

    index: SearchIndex
    config_file: Path | None
    dropping: Callable[[Merge], Dropped]  # no target: dropped; else merged

    def answer(self, asked: TagAsked) -> Response:
        """Answer one of `DROP_ACTIONS`.

        Args:
            asked: What the page asks.

        Returns:
            The answer read back; 400 without a word or into a stop word, 409 when
            `/config` cannot be written, 422 or 500 when the save fails.
        """
        config = self.config_file
        words = tuple(
            dict.fromkeys(w for w in map(cleaned, (asked.word, *asked.words)) if w)
        )
        target = cleaned(asked.target)
        if (refused := _refused(asked, words, config)) is not None:
            return refused
        assert config is not None  # noqa: S101 - `_refused` said so
        try:
            if asked.action in {"drop_look", "frequent"}:
                return json_response(HTTPStatus.OK, self._look(words))
            if asked.action == "merge" and (no := stop_word_target(config, target)):
                return json_response(HTTPStatus.BAD_REQUEST, {"error": no})
            if asked.action in {"drop", "merge"}:
                merge = Merge(words[:1] if target else words, target)
                saved = self._drop(config, merge)
            else:
                saved = self._restore(config, words)
            return json_response(HTTPStatus.OK, {**listed(config), "saved": saved})
        except (ValueError, OSError) as exc:
            return save_refused(exc)
        except sqlite3.Error as exc:
            return save_refused(OSError(str(exc)))

    def _look(self, words: tuple[str, ...]) -> dict[str, object]:
        """How many photos carry the words, a few of them; the frequent tags.

        Args:
            words: The words; none: the frequent tags only.

        Returns:
            `words`, `count`, `thumbs`, `frequent`.
        """
        keys = keys_of(self.index.connection, words) if words else []
        thumbs = [f"{THUMB_PREFIX}{key}{JPEG}" for key in keys[:SHOWN]]
        tags = frequent(self.index.connection, FREQUENT) if not words else []
        return {
            "words": list(words),
            "count": len(keys),
            "thumbs": thumbs,
            "frequent": tags,
        }

    def _drop(self, config: Path, merge: Merge) -> str:
        """Drop or merge the words, then tell what the disk holds.

        Args:
            config: `config.toml`.
            merge: The words, and the tag they mean (none: dropped).

        Returns:
            The line to say.

        Raises:
            OSError: The change does not read back.
        """
        done = self.dropping(merge)
        self._stop_words(config)
        word = merge.words[0]
        if merge.target:
            written = {k.casefold(): v for k, v in saved_synonyms(config).items()}
            if written.get(word.casefold()) != merge.target:
                raise OSError(_("the word does not read back from config.toml"))
        elif any(each.casefold() not in self.index.stop_words for each in merge.words):
            raise OSError(_("the word does not read back from config.toml"))
        left = len(keys_of(self.index.connection, merge.words))
        first = (
            merged_line(word, merge.target, left)
            if merge.target
            else dropped_line(merge.words, left)
        )
        return " ".join([first, *sidecar_lines(done)])

    def _restore(self, config: Path, words: tuple[str, ...]) -> str:
        """Take the words out of the stop words and the synonyms.

        Args:
            config: `config.toml`.
            words: The words.

        Returns:
            The line to say.
        """
        for word in words:
            remove_stop_word(config, word)
            remove_synonym(config, word)
        self._stop_words(config)
        return _(
            "“{word}” restored, read back from the disk: "
            "its photos get it again at the next 'tags'."
        ).format(word="”, “".join(words))

    def _stop_words(self, config: Path) -> None:
        """Give the search the stop words read from the disk, the words searched anew.

        Args:
            config: `config.toml`.
        """
        self.index.stop_words = frozenset(
            word.casefold() for word in saved_stop_words(config)
        )
        self.index.built = None


def _refused(
    asked: TagAsked, words: tuple[str, ...], config: Path | None
) -> Response | None:
    """Say why a change cannot be done.

    Args:
        asked: What the page asks.
        words: The words, cleaned.
        config: `config.toml`, None when not writable.

    Returns:
        The refusal; None for what can be done.
    """
    if config is None:
        said = _("Words cannot be saved: /config is not mounted, or read-only.")
        return json_response(HTTPStatus.CONFLICT, {"error": said})
    if asked.action not in {"dropped", "frequent"} and not words:
        return json_response(HTTPStatus.BAD_REQUEST, {"error": _("Type a word.")})
    target = cleaned(asked.target).casefold()
    if asked.action == "merge" and (not target or target == words[0].casefold()):
        said = _("Type the tag it means.")
        return json_response(HTTPStatus.BAD_REQUEST, {"error": said})
    return None
