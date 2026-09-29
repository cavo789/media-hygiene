"""Everything a command needs, resolved once per invocation."""

from __future__ import annotations

from concurrent.futures import Executor, ProcessPoolExecutor
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING

from media_hygiene.config.layers import merge_layers
from media_hygiene.config.loader import LoadedSettings, load_settings
from media_hygiene.paths.host_paths import HostPathMapper
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.scan.image_check import prepare_image_worker

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.config.layers import Layer
    from media_hygiene.config.settings import Settings
    from media_hygiene.console.output import Output
    from media_hygiene.paths.locations import Locations
    from media_hygiene.paths.mounts import MountTable


def process_pool() -> Executor:
    """Create the pool decoding images in parallel, one process per CPU.

    Returns:
        A process pool whose workers support HEIC and huge images.
    """
    return ProcessPoolExecutor(initializer=prepare_image_worker)


@dataclass(frozen=True, slots=True)
class Runtime:
    """Settings, mount points and output of one command invocation."""

    loaded: LoadedSettings
    locations: Locations
    mounts: MountTable
    output: Output
    cli_layer: Layer = field(default_factory=dict[str, dict[str, object]])
    executor_factory: Callable[[], Executor] = process_pool

    @property
    def settings(self) -> Settings:
        """The effective settings.

        Returns:
            The validated settings.
        """
        return self.loaded.settings

    @property
    def mapper(self) -> HostPathMapper:
        """Translator between container and host paths.

        Returns:
            The mapper rooted at the data directory, aware of the Windows folders
            Docker Desktop mounted.
        """
        return HostPathMapper(self.locations.data_dir, self.mounts.host_sources)

    def persistent(self, kind: MountKind) -> bool:
        """Tell whether data written to a mount point survives the container.

        Args:
            kind: Which mount point.

        Returns:
            True for a Docker mount or an explicit path.
        """
        return self.mounts.is_persistent(self.locations, kind)

    @property
    def index_file(self) -> Path | None:
        """The index file, when the cache is mounted to keep it.

        Returns:
            Its path, or None for an index in memory.
        """
        if self.persistent(MountKind.CACHE):
            return self.locations.index_file
        return None

    def with_overrides(self, layer: Layer) -> Runtime:
        """Reload the settings with extra command-line overrides.

        Args:
            layer: Overrides given to a command, e.g. `--protect`.

        Returns:
            A runtime using the merged overrides.
        """
        cli = merge_layers(self.cli_layer, layer)
        return replace(self, loaded=load_settings(self.locations, cli), cli_layer=cli)
