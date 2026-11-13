"""A folder renamed in Explorer, then any audit: the named face follows (TODO 0752).

`mh audit`, `import`'s audit and the home page's all run `AuditService.run`, which
ends on `relocate_after_audit`: one real audit proves the three.
"""

from __future__ import annotations

import hashlib
import tomllib
from typing import TYPE_CHECKING

from media_hygiene.config.photo_ref import content_id
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations
    from tests.support.media import MediaFactory


def test_a_renamed_folder_is_followed_by_the_audit(
    locations: Locations, media: MediaFactory
) -> None:
    """The face's path is rewritten to the photo's new folder, its id kept."""
    shot = media.image("c/Photos/2024/IMG_0096.jpg", seed=1)
    media.image("c/Photos/2024/other.jpg", seed=2)
    content = shot.read_bytes()
    photo_id = content_id(hashlib.sha256(content).hexdigest(), len(content))
    renamed = shot.parent.with_name("2024 Geer")
    shot.parent.rename(renamed)
    config = locations.config_file
    config.write_text('[[people.person]]\nname = "Chloé"\nfile = "people/Chloé.toml"\n')
    faces = config.parent / "people" / "Chloé.toml"
    faces.parent.mkdir(exist_ok=True)
    old = "C:\\Photos\\2024\\IMG_0096.jpg"
    faces.write_text(
        f"faces = [\n  {{path = '{old}', id = \"{photo_id}\", face = 1}},\n]\n"
    )
    AuditService(make_runtime(locations), NullProgress()).run()
    face = tomllib.loads(faces.read_text())["faces"][0]
    assert (face["path"], face["id"]) == (
        "C:\\Photos\\2024 Geer\\IMG_0096.jpg",
        photo_id,
    )
