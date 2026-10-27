"""`share` (0296): an album of several folders gives one folder and one zip.

The originals are compared byte for byte, and by date, before and after; the copies
and the zip are read back from the disk; the videos are left out and counted.
"""

from __future__ import annotations

import asyncio
import zipfile
from concurrent.futures import ThreadPoolExecutor
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING, Final

import pytest
from PIL import ExifTags, Image

from media_hygiene.errors import MountError
from media_hygiene.index.descriptions import PhotoVersion
from media_hygiene.index.repository import FactsRepository
from media_hygiene.index.tag_rows import TagStore
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.review.http import Request, Response
from media_hygiene.review.presence import PRESENCE_PATH
from media_hygiene.services.album_pages import album_page, album_pages
from media_hygiene.services.albums import album_store
from media_hygiene.services.share_album import SendRequest, prepare_album
from media_hygiene.share.album_store import AlbumChange
from media_hygiene.share.prepare import folder_name
from media_hygiene.tags.models import FileTags, Tag, TagSource
from tests.support.cli import point_mounts, run
from tests.support.runtime import make_locations, make_runtime
from tests.unit.test_share_sent_photo import gps_photo

if TYPE_CHECKING:
    from collections.abc import Callable

    from typer.testing import CliRunner

    from media_hygiene.services.runtime import Runtime

_ALBUM: Final = "Crete 2023"


def _manifest(folder: Path) -> dict[str, tuple[bytes, int]]:
    """Every file below a folder: its bytes and its modification time."""
    return {
        str(path): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in sorted(folder.rglob("*"))
        if path.is_file()
    }


def _album(runtime: Runtime) -> None:
    """Two photos of the same name in two folders, and a video, in one album."""
    data = runtime.locations.data_dir
    files = (
        gps_photo(data / "c" / "Photos" / "Crete" / "IMG_1.jpg"),
        gps_photo(data / "c" / "Phone" / "DCIM" / "img_1.jpg"),
        data / "c" / "Phone" / "DCIM" / "VID_1.mp4",
    )
    files[2].write_bytes(b"\x00\x00\x00\x18ftypmp42 a video")
    album_store(runtime).add(AlbumChange(_ALBUM, files))


def _gps(path: Path) -> dict[int, object]:
    """The GPS tags of a copy, read back."""
    with Image.open(path) as image:
        return dict(image.getexif().get_ifd(ExifTags.IFD.GPSInfo))


def test_an_album_gives_one_folder_one_zip_and_no_original_touched(
    tmp_path: Path,
) -> None:
    """Two folders in, one folder and one zip out; GPS removed; the video counted."""
    runtime = make_runtime(make_locations(tmp_path))
    _album(runtime)
    before = _manifest(runtime.locations.data_dir)
    prepared = prepare_album(runtime, SendRequest(_ALBUM))
    assert _manifest(runtime.locations.data_dir) == before
    sent = prepared.sent
    assert sent.folder == runtime.locations.shares_dir / _ALBUM
    # In the order of their paths (Phone before Photos); the same name in Windows,
    # whatever the case: numbered.
    assert sorted(path.name for path in sent.folder.iterdir()) == [
        "IMG_1_1.jpg",
        "img_1.jpg",
    ]
    assert (sent.photos, sent.zipped, prepared.videos, prepared.missing) == (2, 2, 1, 0)
    assert sent.size == sum(path.stat().st_size for path in sent.folder.iterdir())
    assert sent.archive == runtime.locations.shares_dir / "Crete 2023.zip"
    assert sent.zip_size == sent.archive.stat().st_size
    with zipfile.ZipFile(sent.archive) as archive:
        assert sorted(archive.namelist()) == [
            "Crete 2023/IMG_1_1.jpg",
            "Crete 2023/img_1.jpg",
        ]
    assert not any(_gps(path) for path in sent.folder.iterdir())
    assert not sent.replaced
    assert not list(runtime.locations.shares_dir.glob(".*"))  # no draft left


def test_prepared_again_the_album_replaces_its_folder_and_keeps_gps_when_asked(
    tmp_path: Path,
) -> None:
    """A second run replaces the folder (said); `keep_gps` keeps the position."""
    runtime = make_runtime(make_locations(tmp_path))
    _album(runtime)
    prepare_album(runtime, SendRequest(_ALBUM))
    stale = runtime.locations.shares_dir / _ALBUM / "old.jpg"
    stale.write_bytes(b"from an earlier album")
    prepared = prepare_album(runtime, SendRequest(_ALBUM, keep_gps=True))
    assert prepared.sent.replaced
    assert prepared.keep_gps
    assert not stale.exists()
    assert all(_gps(path) for path in prepared.sent.folder.iterdir())


def test_without_the_shares_folder_nothing_is_made(tmp_path: Path) -> None:
    """Not mounted: refused before any copy, the tip says how to mount it."""
    runtime = make_runtime(make_locations(tmp_path, MountKind.SHARES))
    with pytest.raises(MountError) as refused:
        prepare_album(runtime, SendRequest(_ALBUM))
    assert "/shares" in str(refused.value)


def test_a_name_windows_refuses_becomes_a_folder_name() -> None:
    """What Windows refuses in a name is replaced; never `..` nor empty."""
    assert folder_name("Crete: 2023/07") == "Crete_ 2023_07"
    assert folder_name(" .. ") == "album"


def test_the_command_says_what_was_read_back(
    cli: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The counts, the zip, the GPS line, the video left out; the next step."""
    locations = make_locations(tmp_path)
    point_mounts(locations, monkeypatch)
    _album(make_runtime(locations))
    result = run(cli, "share", "--album", _ALBUM)
    assert result.exit_code == 0, result.output
    text = " ".join(result.output.split())
    assert "2 photos ready to send" in text
    assert "read back from" in text
    assert "The GPS positions were removed" in text
    assert "1 video not included" in text
    assert "What next: attach" in text
    again = " ".join(run(cli, "share", "--album", _ALBUM).output.split())
    assert "The earlier copies of this album were replaced." in again
    unknown = run(cli, "share", "--album", "Nowhere")
    assert unknown.exit_code != 0
    assert "No album named Nowhere" in " ".join(unknown.output.split())


class _Home:
    """The home page behind the albums: records what reaches it."""

    def __init__(self) -> None:
        """Nothing asked yet."""
        self.paths: list[str] = []

    async def handle(self, request: Request) -> Response:
        """Record the path; answer 200."""
        self.paths.append(request.path)
        return Response(HTTPStatus.OK)


def test_the_albums_page_keeps_the_home_server_alive(tmp_path: Path) -> None:
    """0341: the page pings `/api/alive`, which reaches the home page's presence."""
    page = album_page().decode()
    assert PRESENCE_PATH in page
    assert 'id="mhStopped"' in page
    assert "Media Hygiene has stopped" in page
    runtime = make_runtime(make_locations(tmp_path))
    home = _Home()
    headers = {"host": "127.0.0.1:8088", "content-type": "application/json"}
    alive = Request("POST", PRESENCE_PATH, headers, b"{}")
    with ThreadPoolExecutor(1) as executor:
        pages = album_pages(runtime, home, executor)
        reply = asyncio.run(pages.handle(alive))
    assert (reply.status, home.paths) == (HTTPStatus.OK, [PRESENCE_PATH])


def test_every_framed_page_says_when_media_hygiene_stopped() -> None:
    """0341: the shared presence, overlay included, is on the pages' home link."""
    link = (
        Path(__file__).resolve().parents[2]
        / "src/media_hygiene/review/templates/home_link.html.j2"
    ).read_text("utf-8")
    assert '{% include "presence.html.j2" %}' in link
    assert "window.mhEnded()" in link


def _tagged(runtime: Runtime, tags: tuple[Tag, ...]) -> list[Path]:
    """The album's photos, the first given tags in the index (current version)."""
    _album(runtime)
    data = runtime.locations.data_dir
    photos = [data / "c" / "Photos" / "Crete" / "IMG_1.jpg"]
    photos.append(data / "c" / "Phone" / "DCIM" / "img_1.jpg")
    files = [
        FileTags(PhotoVersion(path, path.stat().st_size, path.stat().st_mtime_ns), tags)
        for path in photos[:1]
    ]
    with FactsRepository.open(runtime.locations.index_file) as repository:
        TagStore(repository.connection).replace(list(TagSource), files)
    return photos


_SEEN: Final = (
    Tag(TagSource.CAPTION, "Une plage à Réthymnon.", "vision"),
    Tag(TagSource.VISION, "plage", "vision"),
    Tag(TagSource.PERSON, "Anna"),
    Tag(TagSource.FOLDER, "Crete"),
)


def _recorder(asked: list[int]) -> Callable[[int], bool]:
    """An answer of Yes that records each count asked."""

    def answer(count: int) -> bool:
        asked.append(count)
        return True

    return answer


def _packets(folder: Path) -> dict[str, str]:
    """The XMP packet of each copy, as text (empty without one)."""
    found: dict[str, str] = {}
    for path in sorted(folder.iterdir()):
        with Image.open(path) as image:
            packet = image.info.get("xmp", b"")
            found[path.name] = packet.decode() if isinstance(packet, bytes) else ""
    return found


def test_the_words_of_tags_travel_asked_once_names_never(tmp_path: Path) -> None:
    """0381: asked with the count; vision words only (no name, no folder word)."""
    runtime = make_runtime(make_locations(tmp_path))
    _tagged(runtime, _SEEN)
    asked: list[int] = []
    prepared = prepare_album(runtime, SendRequest(_ALBUM, describe=_recorder(asked)))
    assert asked == [1]
    assert prepared.described == 1
    packets = _packets(prepared.sent.folder)
    assert not packets["img_1.jpg"]  # the photo without tags gets nothing
    assert "<rdf:li>plage</rdf:li>" in packets["IMG_1_1.jpg"]
    assert "Anna" not in packets["IMG_1_1.jpg"]
    assert "Crete" not in packets["IMG_1_1.jpg"]


def test_declined_or_stale_the_copies_carry_nothing(tmp_path: Path) -> None:
    """`--no-describe` writes nothing; a photo changed since `tags` is not asked."""
    runtime = make_runtime(make_locations(tmp_path))
    photos = _tagged(runtime, _SEEN)
    declined = prepare_album(runtime, SendRequest(_ALBUM, describe=lambda _n: False))
    assert declined.described == 0
    assert not any(_packets(declined.sent.folder).values())
    photos[0].write_bytes(photos[0].read_bytes() + b"\x00")  # another version
    asked: list[int] = []
    prepare_album(runtime, SendRequest(_ALBUM, describe=_recorder(asked)))
    assert not asked


def test_the_command_says_how_many_copies_carry_words(
    cli: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without a terminal nor the option: Yes, said; `--no-describe`: not said."""
    locations = make_locations(tmp_path)
    point_mounts(locations, monkeypatch)
    _tagged(make_runtime(locations), _SEEN)
    said = " ".join(run(cli, "share", "--album", _ALBUM).output.split())
    assert "1 copy carries its description and keywords" in said
    quiet = " ".join(
        run(cli, "share", "--album", _ALBUM, "--no-describe").output.split()
    )
    assert "carries its description" not in quiet
