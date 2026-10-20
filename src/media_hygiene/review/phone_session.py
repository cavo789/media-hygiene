r"""The page freeing a phone, in progress: the files ticked, saved after every choice.

Opened with every file of the library and of the import ticked, the files set aside
before unticked (0248); the decisions file is written at once, then after each
choice, and read back. "Delete from the phone" ends the page only when the file read
back holds files ticked; `ticked_lines` then gives `mh` those files, as the plan
named them, from the file on the disk — never a file the page did not show.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.errors import DecisionsError
from media_hygiene.i18n import _
from media_hygiene.review.phone_file import (
    phone_decisions,
    read_ticked_back,
    write_phone_decisions,
)
from media_hygiene.review.phone_tiles import TileSource, preview_key
from media_hygiene.review.phone_views import PhoneReviewState, phone_groups
from media_hygiene.services.phone_plan import PhoneCase, Verdict

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from media_hygiene.review.phone_file import PhoneProof
    from media_hygiene.review.place import DecisionsPlace
    from media_hygiene.services.phone_proof import Ticked


@dataclass(frozen=True, slots=True)
class PhonePages:
    """What the page is about: the phone, its files, the file to write."""

    phone: str
    files: tuple[Ticked, ...]
    tiles: TileSource
    place: tuple[Path, DecisionsPlace]  # the decisions file: in the container, named


class PhoneSession:
    """The files of the phone under review and the ticks, in memory and on disk."""

    def __init__(self, source: PhonePages) -> None:
        """Tick the files of the library and of the import; never a set-aside.

        Args:
            source: The phone's files and the decisions file.
        """
        self._source = source
        self._ticked = [
            ticked.case is not PhoneCase.SET_ASIDE for ticked in source.files
        ]
        self._ranks = {
            (ticked.file.path.as_posix(), ticked.file.size): rank
            for rank, ticked in enumerate(source.files)
        }
        tiles = source.tiles
        self._previews = {
            preview_key(ticked): path
            for ticked in source.files
            if (path := tiles.preview(ticked)) is not None
        }
        self.freeing = False  # "Delete from the phone" pressed, the file proven

    @property
    def place(self) -> DecisionsPlace:
        """The decisions file, on the host.

        Returns:
            Its names.
        """
        return self._source.place[1]

    def counts(self) -> dict[str, int]:
        """How many files are ticked, and their bytes, as the page reads them.

        Returns:
            `ticked`, `bytes` and `total`.
        """
        pairs = zip(self._source.files, self._ticked, strict=True)
        sizes = [ticked.file.size for ticked, on in pairs if on]
        return {"ticked": len(sizes), "bytes": sum(sizes), "total": len(self._ticked)}

    def state(self) -> PhoneReviewState:
        """Describe every file and its tick, for the page.

        Returns:
            The state.
        """
        tiles = self._source.tiles
        return PhoneReviewState(
            phone=self._source.phone,
            decisions_place=self.place.host,
            tiles=tuple(
                tiles.tile(rank, ticked).model_copy(update={"ticked": on})
                for rank, (ticked, on) in enumerate(
                    zip(self._source.files, self._ticked, strict=True)
                )
            ),
            groups=phone_groups(self._source.files),
        )

    def preview_source(self, key: str) -> Path | None:
        """Find the PC file a tile shows.

        Args:
            key: The preview key, from the page.

        Returns:
            The file, in the container, or None for an unknown key.
        """
        return self._previews.get(key)

    def save(self) -> None:
        """Write the decisions file: every file of the page, ticked or not."""
        files = zip(self._source.files, self._ticked, strict=True)
        decisions = phone_decisions(self._source.phone, files)
        write_phone_decisions(self._source.place[0], decisions)

    def on_disk(self) -> PhoneProof:
        """Read the decisions file back from the disk.

        Returns:
            The files of the page it holds ticked.
        """
        return read_ticked_back(self._source.place[0], self._ranks)

    def decide(self, choices: Mapping[int, bool]) -> PhoneProof:
        """Tick or untick files, save them in one write, then read the file back.

        Args:
            choices: By file rank: True ticks it, False unticks it.

        Returns:
            The file as read back from the disk.

        Raises:
            DecisionsError: A file the page does not show, or a file that does not
                hold the choices once saved.
        """
        if any(not 0 <= rank < len(self._ticked) for rank in choices):
            raise DecisionsError(_("There is no such file on the page."))
        for rank, on in choices.items():
            self._ticked[rank] = on
        self.save()
        return self._proven()

    def free(self) -> PhoneProof:
        """Accept "Delete from the phone": the file read back must hold the ticks.

        Returns:
            The file as read back from the disk.

        Raises:
            DecisionsError: Nothing ticked, or a file that does not hold the ticks.
        """
        proof = self._proven()
        if not proof.ticked:
            raise DecisionsError(_("Nothing is ticked: nothing to delete."))
        self.freeing = True
        return proof

    def _proven(self) -> PhoneProof:
        """Read the file back and check it holds the ticks of the page.

        Returns:
            The file as read back.

        Raises:
            DecisionsError: It does not hold them.
        """
        proof = self.on_disk()
        wanted = tuple(rank for rank, on in enumerate(self._ticked) if on)
        if proof.ticked != wanted:
            raise DecisionsError(
                _("The decisions file does not hold your choice: try again.")
            )
        return proof

    def ticked_lines(self) -> tuple[str, ...]:
        """The files ticked in the file on the disk, as the plan named them.

        Returns:
            One plan line each, in the page's order.
        """
        files = self._source.files
        return tuple(
            Verdict(files[rank].file, files[rank].case, files[rank].reason).line()
            for rank in self.on_disk().ticked
        )
