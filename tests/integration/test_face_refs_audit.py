"""Every audit finds the named faces' photos renamed outside (TODO 0570).

`mh audit`, `import`'s audit and the home page's audit all run `AuditService.run`,
which ends on the faces' relocation: one test of that service covers the three.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from typing import TYPE_CHECKING

from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from tests.support.demo import build_demo
from tests.support.runtime import make_runtime, output_of

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations


def test_an_explorer_rename_is_followed_by_the_audit(locations: Locations) -> None:
    """The face of a photo whose folder was renamed gets its new path, said."""
    build_demo(locations.data_dir)
    runtime = make_runtime(locations)
    AuditService(runtime, NullProgress()).run()
    photos = sorted(locations.data_dir.rglob("*.jpg"))
    digests = Counter(hashlib.sha256(p.read_bytes()).digest() for p in photos)
    photo = next(
        p for p in photos if digests[hashlib.sha256(p.read_bytes()).digest()] == 1
    )  # a copy elsewhere would win the tie (the same name, then the first path)
    config = locations.config_file
    config.write_text('[[people.person]]\nname = "Chloé"\nfile = "people/c.toml"\n')
    faces = config.parent / "people" / "c.toml"
    faces.parent.mkdir()
    faces.write_text(f'faces = [\n  "{photo}#0",\n]\n')
    AuditService(runtime, NullProgress()).run()  # the old form gets its id
    assert "id = " in faces.read_text()
    renamed = photo.with_name(f"renamed-{photo.name}")
    photo.rename(renamed)
    runtime = make_runtime(locations)
    AuditService(runtime, NullProgress()).run()
    assert runtime.mapper.to_host(renamed).replace("'", "") in faces.read_text()
    assert "renamed outside" in output_of(runtime)
