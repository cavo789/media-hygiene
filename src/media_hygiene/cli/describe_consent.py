"""Before the local model describes photos: few enough, `--yes`, or the user agrees.

Shared by `classify` (its `subject` rules) and `tags`. Above `confirm_above` photos,
the user is asked first; a refusal (or no terminal) keeps the cache only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from media_hygiene.console.formatting import human_duration, human_number
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from media_hygiene.index.descriptions import PhotoVersion
    from media_hygiene.services.runtime import Runtime


class PendingDescriptions(Protocol):
    """Work that holds photos not described yet, and how long describing them takes."""

    @property
    def missing(self) -> tuple[PhotoVersion, ...]:
        """The photos the cache has no description of."""

    @property
    def estimate(self) -> float:
        """How long describing them should take, in seconds."""


def may_describe(
    runtime: Runtime,
    work: PendingDescriptions,
    yes: bool,  # noqa: FBT001
) -> bool:
    """Tell whether the missing photos may be described now.

    Args:
        runtime: Settings and output.
        work: The photos to describe and the estimate.
        yes: `--yes` was given.

    Returns:
        True when there is something to describe, few enough or accepted.
    """
    count = len(work.missing)
    if not count:
        return False
    if yes or count <= runtime.settings.classify.ai.confirm_above:
        return True
    question = _("Describe {count} photos now, about {duration}?").format(
        count=human_number(count), duration=human_duration(work.estimate)
    )
    if runtime.output.confirm(question):
        return True
    runtime.output.tip(
        _(
            "Nothing described: the cache only. Measure first with --sample 50, "
            "or describe without being asked with --yes."
        )
    )
    return False
