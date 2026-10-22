"""The fixed mount points of the container, each overridable from the environment."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Final

from pydantic_settings import BaseSettings, SettingsConfigDict

from media_hygiene.constants import CONFIG_FILE_NAME, ENV_PREFIX, INDEX_FILE_NAME

if TYPE_CHECKING:
    from media_hygiene.paths.mount_kind import MountKind

# Below the cache: photo previews, each size kept once (`report.preview_cache`).
_PREVIEWS_DIR_NAME: Final = "previews"
# Mounted by `mh` for `share` only: the copies of an album to send (0296).
SHARES_POINT: Final = Path("/shares")


class Locations(BaseSettings):
    """Mount points of the container (`MEDIA_HYGIENE_<NAME>_DIR` overrides each one).

    `/config` holds the configuration file only, and the face lists of the people
    named (`people/<name>.toml`, linked from it: configuration the user wrote too);
    every other kind of data has its own mount point so the user can store it
    wherever they want on the host.
    """

    model_config = SettingsConfigDict(
        env_prefix=ENV_PREFIX, frozen=True, extra="ignore"
    )

    data_dir: Path = Path("/data")
    config_dir: Path = Path("/config")
    journal_dir: Path = Path("/journal")
    quarantine_dir: Path = Path("/quarantine")
    reports_dir: Path = Path("/reports")
    cache_dir: Path = Path("/cache")
    shares_dir: Path = SHARES_POINT

    @property
    def config_file(self) -> Path:
        """Path of the user-editable configuration file.

        Returns:
            `<config_dir>/config.toml`.
        """
        return self.config_dir / CONFIG_FILE_NAME

    @property
    def index_file(self) -> Path:
        """Path of the SQLite index that makes audits incremental.

        Returns:
            `<cache_dir>/index.sqlite`.
        """
        return self.cache_dir / INDEX_FILE_NAME

    @property
    def previews_dir(self) -> Path:
        """Folder of the previews kept between runs.

        Returns:
            `<cache_dir>/previews`.
        """
        return self.cache_dir / _PREVIEWS_DIR_NAME

    def path_of(self, kind: MountKind) -> Path:
        """Return the directory of a mount point.

        Args:
            kind: Which mount point.

        Returns:
            Its path inside the container.
        """
        return Path(getattr(self, f"{kind.value}_dir"))

    def is_explicit(self, kind: MountKind) -> bool:
        """Tell whether the path of `kind` was set through the environment.

        An explicit path is trusted as persistent even when it is not a Docker mount
        (devcontainer helpers and tests redirect everything to /tmp this way).

        Args:
            kind: Which mount point.

        Returns:
            True when `MEDIA_HYGIENE_<KIND>_DIR` was set.
        """
        return f"{kind.value}_dir" in self.model_fields_set
