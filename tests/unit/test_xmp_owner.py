"""A sidecar `xmp` wrote alone holds no edit: it never changes the copy kept."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.constants import MediaKind
from media_hygiene.plan.keeper import KeepPolicy
from media_hygiene.scan.models import DuplicateGroup, MediaFile
from media_hygiene.scan.sidecars import Sidecar, accompanied
from media_hygiene.tags.xmp_doc import parse
from media_hygiene.tags.xmp_merge import XmpValues, merge, new_document
from media_hygiene.tags.xmp_owner import is_ours, with_edits
from tests.support.sidecars import DARKTABLE

if TYPE_CHECKING:
    from pathlib import Path


def _photo(path: Path, mtime_ns: int) -> MediaFile:
    """A photo of the group, written on disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"same bytes")
    return MediaFile(path, 10, mtime_ns, MediaKind.IMAGE)


def _sidecar(photo: MediaFile, text: bytes) -> Sidecar:
    """Its sidecar `<name>.xmp`, written."""
    path = photo.path.with_name(photo.path.name + ".xmp")
    path.write_bytes(text)
    file = MediaFile(path, len(text), 0, MediaKind.SIDECAR)
    return Sidecar(file, frozenset({photo.path.name}))


def test_our_sidecar_does_not_change_the_copy_kept(tmp_path: Path) -> None:
    """Ours is ignored; darktable's, or ours edited since, keep their photo."""
    first = _photo(tmp_path / "a" / "IMG.jpg", 1)
    second = _photo(tmp_path / "b" / "IMG.jpg", 2)
    group = DuplicateGroup("digest", 10, (first, second))
    ours = new_document(XmpValues(("ours",)), "media-hygiene 9.9").to_bytes()
    sidecars = [_sidecar(second, ours)]
    policy = KeepPolicy(with_sidecar=accompanied(with_edits(sidecars)))
    assert policy.decide(group).keeper == first
    edited = parse(ours)
    merge(edited, XmpValues(("ours",)))
    edited.descriptions()[0].set("{http://darktable.sf.net/}xmp_version", "5")
    sidecars = [_sidecar(second, edited.to_bytes())]
    assert not is_ours(sidecars[0].file.path)
    assert accompanied(with_edits(sidecars)) == {second.path}
    sidecars = [_sidecar(second, DARKTABLE.encode())]
    policy = KeepPolicy(with_sidecar=accompanied(with_edits(sidecars)))
    assert policy.decide(group).keeper == second


def test_what_is_not_ours(tmp_path: Path) -> None:
    """Another extension, a missing or broken file, a huge one: not ours."""
    aae = tmp_path / "IMG.aae"
    aae.write_text("x")
    broken = tmp_path / "IMG.xmp"
    broken.write_text("<x")
    huge = tmp_path / "BIG.xmp"
    huge.write_bytes(b" " * 300_000)
    for path in (aae, broken, huge, tmp_path / "missing.xmp"):
        assert not is_ours(path)
