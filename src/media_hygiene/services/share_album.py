"""`share`: an album made ready to send, a folder and a zip (0296).

The album's files are followed if they moved (`share.album_follow`), as for
`slideshow --album`; those missing are counted. Only the photos are copied, each made
in the worker pool (`share.sent_photo`); the videos are left out and counted: one
video alone may pass a mail's limit. The photos are only read: the copies go to the
shares folder, which must be mounted and writable before anything is made.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING

from media_hygiene.constants import MediaKind
from media_hygiene.errors import MediaHygieneError, MountError
from media_hygiene.i18n import _
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.report.thumbnails import PREVIEWABLE
from media_hygiene.scan.filters import media_kind
from media_hygiene.services.slideshow_pick import album_paths
from media_hygiene.services.writable import ensure_writable
from media_hygiene.share.prepare import Delivery
from media_hygiene.share.sent_photo import SendJob, sent_jpeg

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime
    from media_hygiene.share.prepare import Sent


@dataclass(frozen=True, slots=True)
class SendRequest:
    """The album to prepare, and the GPS position kept for this run or not."""

    album: str
    keep_gps: bool = False  # `--keep-gps`; `[share] keep_gps` keeps it too


@dataclass(frozen=True, slots=True)
class Prepared:
    """The album ready to send, and what was left out of it."""

    sent: Sent
    keep_gps: bool
    videos: int  # left out on purpose
    missing: int  # files of the album found nowhere
    unreadable: int  # photos that could not be decoded


def prepare_album(runtime: Runtime, request: SendRequest) -> Prepared:
    """Copy the album's photos, resized, into its folder and its zip.

    Args:
        runtime: Settings, mount points and output.
        request: The album, and the GPS position kept or not.

    Returns:
        What was written, read back from the disk, and what was left out.

    Raises:
        MediaHygieneError: The album holds no photo found on the disk.
    """
    shares = _shares_ready(runtime)
    paths, missing = album_paths(runtime, request.album)
    sources = [runtime.mapper.to_container(path) for path in paths]
    photos = [source for source in sources if media_kind(source) in PREVIEWABLE]
    videos = sum(media_kind(source) is MediaKind.VIDEO for source in sources)
    if not photos:
        raise MediaHygieneError(
            _("No photo to prepare in the album {name}.").format(name=request.album),
            _("Add photos to it in search or browse; the videos are never copied."),
        )
    job = _job(runtime, request)
    delivery = Delivery(shares, request.album)
    unreadable = len(sources) - len(photos) - videos  # neither a photo nor a video
    try:
        for source, data in _made(runtime, job, photos):
            if data is None:
                unreadable += 1
            else:
                delivery.add(source.stem, data)
        sent = delivery.finish()
    finally:
        delivery.discard()  # Ctrl+C or a full disk: the earlier folder stays
    return Prepared(sent, job.keep_gps, videos, missing, unreadable)


def _job(runtime: Runtime, request: SendRequest) -> SendJob:
    """How each photo is made: `[share]`, the GPS kept by the option too.

    Args:
        runtime: Settings, mount points and output.
        request: The album, and `--keep-gps`.

    Returns:
        The job of the worker pool.
    """
    settings = runtime.settings.share
    keep_gps = request.keep_gps or settings.keep_gps
    return SendJob(settings.long_side_px, settings.quality, keep_gps)


def _made(
    runtime: Runtime, job: SendJob, photos: list[Path]
) -> Iterator[tuple[Path, bytes | None]]:
    """Make the copies in the worker pool, in the album's order.

    Args:
        runtime: Settings, mount points and output.
        job: How each photo is made.
        photos: The photos, in the container.

    Yields:
        Each photo, and its copy (None when it cannot be decoded).
    """
    with runtime.executor_factory() as executor:
        yield from zip(
            photos, executor.map(partial(sent_jpeg, job), photos), strict=True
        )


def _shares_ready(runtime: Runtime) -> Path:
    """The shares folder, checked mounted and writable before anything is made.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        It, in the container.

    Raises:
        MountError: It is not mounted, or not writable.
    """
    if not runtime.persistent(MountKind.SHARES):
        raise MountError(
            _("The copies to send are written to /shares, which is not mounted."),
            _(
                "mh mounts it for share; with docker run, add "
                '-v "$HOME\\media-hygiene\\Shares:/shares".'
            ),
        )
    ensure_writable(runtime, MountKind.SHARES)
    return runtime.locations.shares_dir
