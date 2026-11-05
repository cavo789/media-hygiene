"""0531: a day written by the real writer: journaled, undone by `undo`."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.services.date_sidecars import DateWriter
from media_hygiene.tags.xmp_date import sidecar_day
from tests.support.cli import run
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations


def test_written_journaled_then_undone(cli: CliRunner, locations: Locations) -> None:
    """The sidecar is written, read back; `undo` removes it; the photo is unchanged."""
    photo = next((locations.data_dir / "c" / "Photos" / "DCIM").glob("*.jpg"))
    before = photo.read_bytes()
    writer = DateWriter(make_runtime(locations))
    done = writer.write(writer.jobs((photo,), "2019-07-15"))
    sidecar = photo.with_name(photo.name + ".xmp")
    assert done.run
    assert not done.failed
    assert sidecar_day(sidecar.read_bytes()) == "2019-07-15"
    assert done.run in done.undo_line()
    undone = run(cli, "undo", done.run)
    assert undone.exit_code == 0, undone.output
    assert not sidecar.exists()
    assert photo.read_bytes() == before
