"""`/person/api/scan` and `/api/look`: one photo's faces found now, or looked at again.

The same analysis as `audit --people` (`faces.worker.find_faces`, in the worker pool),
for this photo only, kept in the index like the audit's: the next audit skips it, the
people page counts it; the page then reads the photo again (`PersonFinder.photo`).
A second look (`second_look`: turned, less strict) adds the faces the photo lacks to
the index the same way (`face_tops.add_found`): named like any other. A video is
never analysed (`video_said`): faces are looked for in photos only.
"""

from __future__ import annotations

import asyncio
import dataclasses
import sqlite3
from typing import TYPE_CHECKING

from media_hygiene.faces.detect import MIN_SCORE
from media_hygiene.faces.models import PhotoFaces
from media_hygiene.faces.worker import FaceJob, OnnxRecipe, find_faces
from media_hygiene.i18n import _
from media_hygiene.index.descriptions import PhotoVersion
from media_hygiene.index.face_rows import FaceStore
from media_hygiene.index.face_tops import add_found, boxes_of, mark_topped
from media_hygiene.index.repository import FactsRepository
from media_hygiene.person.second_look import LookJob, second_look
from media_hygiene.report.thumbnails import PREVIEWABLE
from media_hygiene.scan.filters import media_kind

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.faces.worker import FinderRecipe
    from media_hygiene.person.app import PersonApp


def video_said(path: Path) -> str | None:
    """The sentence for a file whose faces are never looked for: not a photo.

    Args:
        path: The file, in the container.

    Returns:
        The sentence; None for a photo.
    """
    if media_kind(path) in PREVIEWABLE:
        return None
    return _(
        "This is a video: faces are looked for in photos only. "
        "Give the path of a photo of this person."
    )


async def scanned_now(app: PersonApp, typed: str) -> dict[str, object]:
    """Find the faces of a photo now, keep them in the index, answer as `photo`.

    Args:
        app: The page.
        typed: The photo's path.

    Returns:
        The photo's faces as `PersonFinder.photo` gives them; a sentence (`said`)
        when the models or the index are missing, or the photo cannot be read.
    """
    finder = app.finder
    path = finder.place.resolve(typed)
    if path is None or video_said(path) is not None:
        return finder.photo(typed)  # it says why
    recipe = app.recipe()
    index = finder.faces.file
    if recipe is None or index is None:
        said = _("The face models are not in the cache yet: run 'audit --people' once.")
        return {"faces": [], "said": said}
    try:
        with FactsRepository.open(index) as repository:
            unread = await _kept(app, (path, recipe), repository.connection)
    except sqlite3.Error:
        return {"faces": [], "said": _("The index cannot be written: try again.")}
    if unread is not None:
        return {"faces": [], "said": unread}
    finder.faces.refresh()
    return finder.photo(typed)


async def _kept(
    app: PersonApp, asked: tuple[Path, FinderRecipe], connection: sqlite3.Connection
) -> str | None:
    """Find a photo's faces and keep them: all of them, or those an older scan lacks.

    Args:
        app: The page.
        asked: The photo, in the container, and the recipe of the finder.
        connection: The index, writable.

    Returns:
        None once kept; a sentence for a photo that cannot be read.
    """
    path, recipe = asked
    model = app.finder.faces.model
    stat = path.stat()
    version = (str(path), stat.st_size, stat.st_mtime_ns)
    store = FaceStore(connection, model)
    photo = PhotoVersion(path, stat.st_size, stat.st_mtime_ns)
    beside = boxes_of(connection, model, version) if store.scanned(photo) else None
    strict = (  # the page's recipe is the second look's, looser
        dataclasses.replace(recipe, least=MIN_SCORE)
        if isinstance(recipe, OnnxRecipe)
        else recipe
    )
    job = FaceJob(path, stat.st_size, stat.st_mtime_ns, strict, beside=beside)
    found = await asyncio.get_running_loop().run_in_executor(
        app.executor, find_faces, job
    )
    if found is None:
        return _("This photo cannot be read.")
    if beside is None:
        store.put(found)
        mark_topped(connection, model, found)
    else:  # scanned before 0841: only the faces it lacks, after its own
        add_found(connection, model, found)
    return None


async def looked_again(app: PersonApp, typed: str) -> dict[str, object]:
    """Look again at a photo, turned and less strict; keep the new faces (0841).

    Args:
        app: The page.
        typed: Its path.

    Returns:
        The photo's faces as `PersonFinder.photo` gives them, the new ones among
        them; a sentence (`said`) when none is new, or nothing could be done.
    """
    finder = app.finder
    path = finder.place.resolve(typed)
    if path is None or video_said(path) is not None:
        return finder.photo(typed)  # it says why
    recipe = app.recipe()
    index = finder.faces.file
    if recipe is None or index is None:
        said = _("The face models are not in the cache yet: run 'audit --people' once.")
        return {"faces": [], "said": said}
    try:
        with FactsRepository.open(index) as repository:
            added = await _looked(app, (path, recipe), repository.connection)
    except sqlite3.Error:
        return {"faces": [], "said": _("The index cannot be written: try again.")}
    if isinstance(added, str):
        return {"faces": [], "said": added}
    finder.faces.refresh()
    answer = finder.photo(typed)
    if not added:
        answer["said"] = _("No new face found, even turned: draw the one missed.")
    return answer


async def _looked(
    app: PersonApp, asked: tuple[Path, FinderRecipe], connection: sqlite3.Connection
) -> int | str:
    """Look at a photo turned, keep the faces it did not have.

    Args:
        app: The page.
        asked: The photo, in the container, and the loose recipe.
        connection: The index, writable.

    A photo not analysed down to `MIN_SCORE` is analysed first, as the audit would.

    Returns:
        How many faces were added; a sentence for a photo that cannot be read.
    """
    path, recipe = asked
    if not app.finder.faces.scanned(path):
        unread = await _kept(app, asked, connection)
        if unread is not None:
            return unread
    model = app.finder.faces.model
    stat = path.stat()
    version = (str(path), stat.st_size, stat.st_mtime_ns)
    job = LookJob(path, recipe, boxes_of(connection, model, version))
    found = await asyncio.get_running_loop().run_in_executor(
        app.executor, second_look, job
    )
    if found:
        add_found(connection, model, PhotoFaces(path, *version[1:], found, 0.0))
    return len(found)
