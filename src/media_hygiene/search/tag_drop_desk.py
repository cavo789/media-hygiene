"""Drop a useless word from the search page, see the dropped ones, restore one (0546).

Reached through `POST /api/hand-tag`: `drop_look` says how many photos carry a word and
shows a few; `drop` removes it (`services.tag_drop`) and answers what the disk holds
after it: the stop words read back, the photos still carrying it counted again.
`dropped` lists them, `restore` takes one out of the stop words: its photos get it
again at the next `tags`, from the answers kept, without asking the model.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _, ngettext
from media_hygiene.index.tag_drop import keys_of
from media_hygiene.review.config_saving import save_refused
from media_hygiene.review.serving import json_response
from media_hygiene.search.views import JPEG, THUMB_PREFIX
from media_hygiene.tags.stop_edit import (
    dropped_words,
    remove_stop_word,
    saved_stop_words,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.review.http import Response
    from media_hygiene.search.fts import SearchIndex
    from media_hygiene.services.tag_drop import Dropped

DROP_ACTIONS: Final = frozenset({"drop_look", "drop", "dropped", "restore"})
SHOWN: Final = 12  # the photos shown first: a look, the count says the rest


@dataclass(frozen=True, slots=True)
class DropDesk:
    """Where the stop words are (None: not writable), the search, the dropping."""

    index: SearchIndex
    config_file: Path | None
    dropping: Callable[[str], Dropped]

    def answer(self, action: str, word: str) -> Response:
        """Answer one of `DROP_ACTIONS`.

        Args:
            action: What the page asks.
            word: The word, cleaned; empty to list.

        Returns:
            The answer read back; 400 without a word, 409 when `/config` cannot be
            written, 422 or 500 when the save fails.
        """
        config = self.config_file
        if config is None:
            said = _("Words cannot be saved: /config is not mounted, or read-only.")
            return json_response(HTTPStatus.CONFLICT, {"error": said})
        if action != "dropped" and not word:
            return json_response(HTTPStatus.BAD_REQUEST, {"error": _("Type a word.")})
        try:
            if action == "drop_look":
                return json_response(HTTPStatus.OK, self._look(word))
            saving = {"drop": self._drop, "restore": self._restore}.get(action)
            saved = saving(config, word) if saving else ""
            return json_response(
                HTTPStatus.OK, {"dropped": list(dropped_words(config)), "saved": saved}
            )
        except (ValueError, OSError) as exc:
            return save_refused(exc)
        except sqlite3.Error as exc:
            return save_refused(OSError(str(exc)))

    def _look(self, word: str) -> dict[str, object]:
        """How many photos carry the word, and a few of them.

        Args:
            word: The word.

        Returns:
            `word`, `count`, `thumbs`.
        """
        keys = keys_of(self.index.connection, word)
        thumbs = [f"{THUMB_PREFIX}{key}{JPEG}" for key in keys[:SHOWN]]
        return {"word": word, "count": len(keys), "thumbs": thumbs}

    def _drop(self, config: Path, word: str) -> str:
        """Drop the word, then tell what the disk holds.

        Args:
            config: `config.toml`.
            word: The word.

        Returns:
            The line to say.

        Raises:
            OSError: The stop word does not read back.
        """
        done = self.dropping(word)
        self._stop_words(config)
        if word.casefold() not in self.index.stop_words:
            raise OSError(_("the word does not read back from config.toml"))
        left = len(keys_of(self.index.connection, word))
        lines = [
            _(
                "“{word}” dropped, read back from the disk: "
                "in the stop words, still on {left} photos."
            ).format(word=word, left=left)
        ]
        if done.sidecars:
            lines.append(
                ngettext(
                    "Taken out of {n} sidecar: 'mh undo {run}' puts it back.",
                    "Taken out of {n} sidecars: 'mh undo {run}' puts them back.",
                    done.sidecars,
                ).format(n=done.sidecars, run=done.run_id)
            )
        if done.failed:
            lines.append(
                ngettext(
                    "{n} sidecar left as it was.",
                    "{n} sidecars left as they were.",
                    done.failed,
                ).format(n=done.failed)
            )
        if done.waiting:
            lines.append(
                _(
                    "Sidecars not written from here: "
                    "the next 'xmp --apply' takes it out."
                )
            )
        return " ".join(lines)

    def _restore(self, config: Path, word: str) -> str:
        """Take the word out of the stop words.

        Args:
            config: `config.toml`.
            word: The word.

        Returns:
            The line to say.
        """
        remove_stop_word(config, word)
        self._stop_words(config)
        return _(
            "“{word}” restored, read back from the disk: "
            "its photos get it again at the next 'tags'."
        ).format(word=word)

    def _stop_words(self, config: Path) -> None:
        """Give the search the stop words read from the disk, the words searched anew.

        Args:
            config: `config.toml`.
        """
        self.index.stop_words = frozenset(
            word.casefold() for word in saved_stop_words(config)
        )
        self.index.built = None
