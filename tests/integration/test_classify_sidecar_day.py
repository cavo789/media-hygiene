"""0597: `classify` reads the day beside an undated photo, at each run."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.classify.dating_models import DateSource
from media_hygiene.classify.plan_file import ClassifyPlan
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from media_hygiene.tags.xmp_date import with_day
from tests.support.runtime import make_runtime
from tests.support.scenes import Shot, write_shot
from tests.support.sorting import classify

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations
    from media_hygiene.services.runtime import Runtime


def _row(runtime: Runtime) -> tuple[str | None, DateSource | None]:
    """The date of the only photo in a new plan, and where it comes from."""
    workbook = classify(runtime)
    plan = ClassifyPlan.model_validate_json(
        workbook.with_name("plan.json").read_text("utf-8")
    )
    (row,) = plan.rows
    return row.date, row.date_source


def test_written_then_undone_the_plan_follows_the_sidecar(
    locations: Locations,
) -> None:
    """Counts at the next classify; without the sidecar, the disk's date again."""
    photo = write_shot(locations.data_dir / "c" / "x" / "a.jpg", Shot(5, camera=False))
    runtime = make_runtime(locations)
    AuditService(runtime, NullProgress()).run()
    content = with_day(None, "2019-07-14", "media-hygiene 9.9")
    assert content is not None
    sidecar = photo.with_name("a.jpg.xmp")
    sidecar.write_bytes(content)
    assert _row(runtime) == ("2019-07-14T12:00:00", DateSource.SIDECAR)
    sidecar.unlink()
    assert _row(runtime)[1] is DateSource.MTIME
