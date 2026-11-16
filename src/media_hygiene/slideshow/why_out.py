"""Why each photo is out of the show (0831, 0832): the groups that set it out.

A group is a person ticked in *Avoid some people* (`person:✓ André`, `person:≈ André`)
or an event unticked (`event:<folder>`). A photo is out while one group holds it; a
photo set out by hand (*Do not show*) holds no group and stays out when its groups are
ticked back; one shown again by hand (*Show it again*) is never set out by a group
again in this show. Ticking a group back restores only what it had set out. In memory.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Set as AbstractSet

    from media_hygiene.slideshow.show import Show

HAND: Final = "hand"  # the reason of a photo set out by hand


@dataclass(frozen=True, slots=True)
class WhyOut:
    """The groups holding each photo out, the photos shown again by hand."""

    held: dict[int, set[str]] = field(default_factory=dict)
    kept_in: set[int] = field(default_factory=set)
    unticked: set[str] = field(default_factory=set)  # the events' folders

    def apply(self, show: Show, group: str, wanted: AbstractSet[int]) -> None:
        """Make a group hold exactly the photos wanted (none: ticked back).

        Args:
            show: The show.
            group: E.g. `event:2026/2026-04/Pâques`.
            wanted: The keys it sets out now.
        """
        for key in sorted(k for k, on in self.held.items() if group in on):
            if key in wanted:
                continue
            self.held[key].discard(group)
            if not self.held[key]:
                del self.held[key]
                show.set_out(key, out=False)
        for key in sorted(wanted - self.kept_in):
            groups = self.held.get(key)
            if key in show.skipped and groups is None:
                continue  # by hand: stays out, the group never takes it back
            self.held.setdefault(key, set()).add(group)
            if key not in show.skipped:
                show.set_out(key, out=True)

    def by_hand(self, key: int, *, out: bool) -> None:
        """Forget a photo's groups: *Do not show* or *Show it again* wins.

        Args:
            key: Its key.
            out: True when set out by hand, False when shown again.
        """
        self.held.pop(key, None)
        if out:
            self.kept_in.discard(key)
        else:
            self.kept_in.add(key)

    def view(self, show: Show) -> dict[str, list[str]]:
        """Why each photo out is out, for the remote.

        Args:
            show: The show.

        Returns:
            By key (as text), its groups sorted, or `["hand"]`.
        """
        return {
            str(key): sorted(self.held.get(key) or {HAND})
            for key in sorted(show.skipped)
        }
