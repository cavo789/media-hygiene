"""The guess of the turn a sideways photo needs (0711), with a fake face finder."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PIL import Image

from media_hygiene.faces.straighten import (
    ORIENTATION_OF,
    Candidate,
    Turn,
    guess_turn,
    proposed_turn,
    turned,
    worth_guessing,
)

if TYPE_CHECKING:
    from collections.abc import Callable

_MARK = (255, 0, 0)


def _picture(mark: tuple[int, int]) -> Image.Image:
    """A 40 x 20 black picture with one red pixel."""
    picture = Image.new("RGB", (40, 20))
    picture.putpixel(mark, _MARK)
    return picture


def _finder(faces: int) -> Callable[[Image.Image], int]:
    """A fake finder: `faces` faces when the red pixel is at the top left."""

    def count(picture: Image.Image) -> int:
        """Count the fake faces."""
        return faces if picture.getpixel((0, 0)) == _MARK else 0

    return count


def test_only_untagged_camera_photos_are_guessed() -> None:
    """Screenshots, console captures, collages and tagged photos are left out."""
    assert worth_guessing(Candidate("Panasonic DMC-FX37", None, screenshot=False))
    assert worth_guessing(Candidate("SAMSUNG WB700", 1, screenshot=False))
    assert worth_guessing(Candidate("Canon", 0, screenshot=False))
    assert not worth_guessing(Candidate("Canon", 6, screenshot=False))
    assert not worth_guessing(Candidate("Canon", None, screenshot=True))
    assert not worth_guessing(Candidate("Nintendo 3DS", None, screenshot=False))
    assert not worth_guessing(Candidate(None, None, screenshot=False))  # a collage
    assert not worth_guessing(Candidate("  ", None, screenshot=False))


def test_a_face_as_stored_leaves_the_photo() -> None:
    """A person lying down whose face is found as stored is not turned."""
    assert proposed_turn({Turn.NONE: 1, Turn.QUARTER: 2}) is None
    assert proposed_turn({Turn.NONE: 0}) is None


def test_half_turn_needs_two_faces() -> None:
    """Upside down only when two faces or more agree."""
    assert proposed_turn({Turn.HALF: 1}) is None
    assert proposed_turn({Turn.HALF: 2}) is Turn.HALF
    assert proposed_turn({Turn.QUARTER: 1}) is Turn.QUARTER
    assert (
        proposed_turn({Turn.QUARTER: 1, Turn.THREE_QUARTERS: 3}) is Turn.THREE_QUARTERS
    )


def test_guess_finds_the_turn_that_stands_the_mark_upright() -> None:
    """Each stored position of the mark gives the turn that brings it top left."""
    count = _finder(1)
    assert guess_turn(_picture((0, 19)), count) is Turn.QUARTER
    assert guess_turn(_picture((39, 0)), count) is Turn.THREE_QUARTERS
    assert guess_turn(_picture((0, 0)), count) is None
    assert guess_turn(_picture((39, 19)), count) is None
    assert guess_turn(_picture((39, 19)), _finder(2)) is Turn.HALF


def test_turned_size_and_orientation_codes() -> None:
    """A quarter turn swaps the sides; each turn has its EXIF code."""
    assert turned(_picture((0, 0)), Turn.QUARTER).size == (20, 40)
    assert turned(_picture((0, 0)), Turn.NONE).size == (40, 20)
    assert ORIENTATION_OF == {Turn.QUARTER: 6, Turn.HALF: 3, Turn.THREE_QUARTERS: 8}
