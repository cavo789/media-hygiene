"""How a review ends in the terminal: where the choices are, and the `clean` to run."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.cli.next_steps import carried, suggest
from media_hygiene.i18n import _
from media_hygiene.review.place import decisions_flag
from media_hygiene.services.next_command import CHANGING, NextVerb

if TYPE_CHECKING:
    import typer

    from media_hygiene.review.place import DecisionsPlace
    from media_hygiene.services.runtime import Runtime


@dataclass(frozen=True, slots=True)
class CleanNext:
    """The `clean` that applies a review: its decisions file and what to say of it."""

    place: DecisionsPlace
    text: str  # translated, lower case, with `{option}` for `--decisions …`
    tier: str = ""  # e.g. `--tier near ` (with its trailing space)


def tell_choices_and_clean(
    ctx: typer.Context, runtime: Runtime, then: CleanNext
) -> None:
    """Say where the choices are saved, then the `clean` command that applies them.

    Args:
        ctx: Typer context of the review, whose options `clean` keeps.
        runtime: Settings, mount points and output.
        then: The decisions file and the step to suggest.
    """
    place = then.place
    runtime.output.info(_("Your choices are in {place}.").format(place=place.host))
    flag = decisions_flag(place.argument)
    command = carried(runtime, f"clean {then.tier}{flag}", ctx)
    suggest(runtime, then.text.format(option=flag), NextVerb(command, CHANGING))
