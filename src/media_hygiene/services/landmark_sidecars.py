"""Write the landmark of one photo into its sidecar (0649): journaled, undone by `undo`.

The large view's *📍 Landmark…* names it, or says a name is wrong. The sidecar is the
truth (`tags.xmp_landmark`); the answer reads it back from the disk.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import version
from typing import TYPE_CHECKING

from media_hygiene.actions.kinds import Phase
from media_hygiene.actions.xmp_write import XmpJob
from media_hygiene.constants import APP_NAME
from media_hygiene.paths.host_paths import is_within
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.acting import ensure_can_act
from media_hygiene.services.xmp import XmpService
from media_hygiene.services.xmp_plan import XmpPlan
from media_hygiene.services.xmp_sidecars import sidecar_of
from media_hygiene.tags.xmp_doc import XmpError, parse
from media_hygiene.tags.xmp_landmark import (
    SidecarLandmark,
    landmark_in,
    with_landmark,
    with_rejected,
)

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime


@dataclass(frozen=True, slots=True)
class LandmarkAsked:
    """A name given to a photo, or said to be wrong."""

    photo: Path
    name: str
    wrong: bool = False


def sidecar_landmark(photo: Path) -> SidecarLandmark:
    """What the sidecar of a photo says, read from the disk now.

    Args:
        photo: The photo.

    Returns:
        Its landmark; nothing for no sidecar, or one that cannot be read.
    """
    try:
        sidecar = sidecar_of(photo, {})
        return landmark_in(parse(sidecar.read_bytes()))
    except OSError, XmpError:
        return SidecarLandmark()


@dataclass(frozen=True, slots=True)
class LandmarkWriter:
    """Writes the sidecars, with the guards of every command that changes files."""

    runtime: Runtime

    def write(self, asked: LandmarkAsked) -> str:
        """Write the name (or its rejection) under a new run.

        Args:
            asked: The photo and the name.

        Returns:
            The run; empty when nothing changed (a protected folder, another
            application's name, the same name).
        """
        ensure_can_act(self.runtime, Phase.XMP.value)
        untouched = map(
            self.runtime.mapper.to_container, self.runtime.settings.folders.untouched
        )
        if any(is_within(asked.photo, folder) for folder in untouched):
            return ""
        job = _job(asked)
        if job is None or job.content == job.previous:
            return ""
        service = XmpService(self.runtime, NullProgress())
        return service.execute(XmpPlan(jobs=[job]), lambda: False).run_id


def _job(asked: LandmarkAsked) -> XmpJob | None:
    """The sidecar of the photo, holding the name or its rejection.

    Args:
        asked: The photo and the name.

    Returns:
        The job; None for another application's name, or a sidecar that cannot be read.
    """
    tool = f"{APP_NAME} {version(APP_NAME)}"
    try:
        sidecar = sidecar_of(asked.photo, {})
        previous = sidecar.read_bytes() if sidecar.is_file() else None
    except OSError:
        return None
    try:
        doc = None if previous is None else parse(previous)
    except XmpError:
        return None
    if asked.wrong:
        doc = with_rejected(doc, asked.name, tool)
    else:
        doc = with_landmark(doc, asked.name, tool)
    if doc is None:
        return None
    return XmpJob(asked.photo, sidecar, doc.to_bytes(), previous)
