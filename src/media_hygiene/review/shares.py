"""How sharp each shot of a series is next to the best one, for the review page."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.plan.burst_proposals import ShotLook


def shares(looks: Sequence[ShotLook | None]) -> tuple[float | None, ...]:
    """Give each shot's sharpness as a share of the sharpest's, None if not measured.

    A series ranked by its faces compares faces with faces; a shot without a face is
    compared with the frames of the others without one.

    Args:
        looks: The shots of the series, by rank.

    Returns:
        The shares, 0 to 1, in the same order; empty values when nothing is sharp.
    """
    known = [look for look in looks if look is not None]
    on_faces = max((look.faces or 0.0 for look in known if look.faced), default=0.0)
    frames = max((look.sharpness for look in known if look.faces is None), default=0.0)
    result: list[float | None] = []
    for look in looks:
        if look is None:
            result.append(None)
            continue
        value, top = (
            (look.faces, on_faces)
            if look.faces is not None
            else (look.sharpness, frames)
        )
        result.append(min(value / top, 1.0) if top else None)
    return tuple(result)


def compared(look: ShotLook) -> float:
    """Give the figure a shot is compared by: its faces' sharpness, else the frame's.

    Args:
        look: The shot.

    Returns:
        The sharpness the badge shows, the one `shares` divides.
    """
    return look.faces if look.faces is not None else look.sharpness
