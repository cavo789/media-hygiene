"""The TV's side of the slideshow (0291): its page's script, its pictures.

The screen page's script must run in a 2012 TV browser: parsed here for any syntax
or global beyond ES5. The TV's picture is the photo upright, fitted to the screen,
baseline JPEG, kept in the cache folder.
"""

from __future__ import annotations

import io
import re
from typing import TYPE_CHECKING, Final

import pytest
from PIL import Image

from media_hygiene.i18n.templates import translated_environment
from media_hygiene.slideshow.screen_jpeg import ScreenJob, kept_screen_jpeg
from tests.support.es5 import post_es5

if TYPE_CHECKING:
    from pathlib import Path

_PATHS: Final = {
    "wait_prefix": "/api/wait/",
    "code_shown": "code",
    "ended_prefix": "/api/ended/",
    "photos_only": "/photos",
    "title_seconds": 3,
    "banner_seconds": 5,
}
_ORIENTATION: Final = 0x0112
_ROTATED: Final = 6  # EXIF: the camera was turned a quarter clockwise
_SCREEN_PX: Final = 640


def _screen_page(phone_url: str = "") -> str:
    return str(
        translated_environment("media_hygiene.slideshow", escaped=("html", "j2"))
        .get_template("screen.html.j2")
        .render(**_PATHS, phone_url=phone_url)
    )


def _screen_script() -> str:
    page = _screen_page()
    scripts = re.findall(r"<script>(.*?)</script>", page, re.DOTALL)
    assert len(scripts) == 1
    return str(scripts[0])


def test_the_screen_page_script_is_es5() -> None:
    """No arrow, let/const, template string, fetch nor Promise: a 2012 TV runs it."""
    script = _screen_script()
    assert "XMLHttpRequest" in script
    assert '"/api/ended/"' in script  # the end of a video is told (0292)
    assert not post_es5(script)


def test_the_tv_names_the_phones_address_never_its_code() -> None:
    """Under `mh --lan` the TV says where the phone opens the remote; else nothing."""
    url = "http://192.168.1.20:8088/"
    page = _screen_page(url)
    assert f"<code>{url}</code>" in page
    assert "/pair/" not in page  # the phone's own code is never on a page any TV sees
    assert url not in _screen_page()


def test_the_former_photo_is_hidden_and_the_code_fitted() -> None:
    """A Chromecast left parts of the former photo, and showed no code (2026-10-22)."""
    page = _screen_page()
    assert ".quiet { visibility: hidden; }" in page
    script = _screen_script()
    assert 'typeof ahead.decode === "function" ? "layer back quiet"' in script
    assert "fitCode();" in script
    assert "window.innerHeight" in script


@pytest.mark.parametrize(
    ("source", "finding"),
    [
        ("var f = (a) => a;", "punct =>"),
        ("let a = 1;", "name let"),
        ("const a = 1;", "name const"),
        ("var s = `x`;", "template string"),
        ("fetch('/');", "name fetch"),
        ("var b = a?.c;", "punct ?."),
        ("for (var x of y) {}", "name of"),
    ],
)
def test_the_check_finds_what_es5_lacks(source: str, finding: str) -> None:
    """Each post-ES5 form is found; strings and comments are not read."""
    assert finding in post_es5(source)
    assert not post_es5(f"var s = {source!r}; // {source}")


def _photo(target: Path, *, rotated: bool) -> Path:
    exif = Image.Exif()
    if rotated:
        exif[_ORIENTATION] = _ROTATED
    Image.new("RGB", (800, 600), (200, 30, 30)).save(target, "JPEG", exif=exif)
    return target


@pytest.mark.parametrize(
    ("rotated", "size"),
    [(False, (480, 360)), (True, (270, 360))],
)
def test_the_tv_picture_is_upright_and_fitted(
    tmp_path: Path, *, rotated: bool, size: tuple[int, int]
) -> None:
    """Fitted into screen_px x 9/16 of it, the EXIF orientation applied, baseline."""
    photo = _photo(tmp_path / "photo.jpg", rotated=rotated)
    picture = kept_screen_jpeg(ScreenJob(_SCREEN_PX, None), photo)
    assert picture is not None
    with Image.open(io.BytesIO(picture)) as image:
        assert image.size == size
        assert not image.info.get("progressive")


def test_the_tv_picture_is_kept_and_made_again_for_a_new_version(
    tmp_path: Path,
) -> None:
    """Kept in the cache folder once; a photo changed since gets a new one."""
    cache = tmp_path / "previews"
    photo = _photo(tmp_path / "photo.jpg", rotated=False)
    job = ScreenJob(_SCREEN_PX, cache)
    first = kept_screen_jpeg(job, photo)
    assert first is not None
    assert len(list(cache.iterdir())) == 1
    assert kept_screen_jpeg(job, photo) == first
    _photo(photo, rotated=True)  # rewritten: another size, another time
    assert kept_screen_jpeg(job, photo) != first
    assert len(list(cache.iterdir())) == 2
    assert kept_screen_jpeg(ScreenJob(_SCREEN_PX * 2, cache), photo) is not None
    assert len(list(cache.iterdir())) == 3


def test_a_photo_that_cannot_be_decoded_is_not_shown(tmp_path: Path) -> None:
    """None, kept as an empty file: that version is not decoded again."""
    broken = tmp_path / "broken.jpg"
    broken.write_bytes(b"not a jpeg")
    cache = tmp_path / "previews"
    job = ScreenJob(_SCREEN_PX, cache)
    assert kept_screen_jpeg(job, broken) is None
    assert [kept.stat().st_size for kept in cache.iterdir()] == [0]
    assert kept_screen_jpeg(job, broken) is None
    assert kept_screen_jpeg(job, tmp_path / "gone.jpg") is None
