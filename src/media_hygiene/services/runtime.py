"""Everything a command needs, resolved once per invocation."""

from __future__ import annotations

import multiprocessing
import threading
from concurrent.futures import Executor, ProcessPoolExecutor
from dataclasses import dataclass, field, replace
from multiprocessing import forkserver
from typing import TYPE_CHECKING, Final, override

from media_hygiene.config.layers import merge_layers
from media_hygiene.config.loader import LoadedSettings, load_settings
from media_hygiene.paths.host_paths import HostPathMapper
from media_hygiene.paths.mount_kind import MountKind

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path
    from types import TracebackType

    from media_hygiene.config.layers import Layer
    from media_hygiene.config.settings import Settings
    from media_hygiene.console.output import Output
    from media_hygiene.paths.locations import Locations
    from media_hygiene.paths.mounts import MountTable


# Imported once by the fork server, inherited by every worker it forks.
_WORKER_MODULES: Final = (
    "media_hygiene.scan.image_check",
    "media_hygiene.scan.raw_check",
    "pillow_heif",
)


class _ImagePool(ProcessPoolExecutor):
    """A process pool that stops at once when its block fails or Ctrl+C is pressed."""

    @override
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        """Wait for the workers after a normal end, terminate them otherwise.

        Workers only read files: stopping one in the middle of a decode loses nothing,
        while waiting for the decodes under way can take long on a slow disk.

        Args:
            exc_type: Type of the exception that ended the block, if any.
            exc_val: That exception.
            exc_tb: Its traceback.

        Returns:
            None: the exception, if any, goes on.
        """
        if exc_type is None:
            return super().__exit__(exc_type, exc_val, exc_tb)
        self.terminate_workers()
        return None


def process_pool() -> Executor:
    """Create the pool decoding images in parallel, one process per CPU.

    Returns:
        A process pool whose workers support HEIC and huge images.
    """
    # Pillow and LibRaw load with the first pool, never for `--version` or `--help`.
    from media_hygiene.scan.image_check import (  # noqa: PLC0415  # pylint: disable=import-outside-toplevel
        prepare_image_worker,
    )

    return _ImagePool(mp_context=_pool_context(), initializer=prepare_image_worker)


def warm_pool() -> None:
    """Start the fork server of the image pools now, in the background.

    It imports Pillow and numpy while the command lists the folders: the first pool
    then answers at once. Harmless when no pool follows.
    """
    _pool_context()  # its preload list, before the server starts
    threading.Thread(
        target=forkserver.ensure_running, name="warm-pool", daemon=True
    ).start()


def _pool_context() -> multiprocessing.context.ForkServerContext:
    """The start method of the image pools, its fork server importing what they need.

    The fork server imports only what workers need, never the CLI of `__main__`: each
    worker is a fork of a process that already holds Pillow, HEIC and numpy.

    Returns:
        The context.
    """
    context = multiprocessing.get_context("forkserver")
    context.set_forkserver_preload(list(_WORKER_MODULES))
    return context


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

    def warm_pool(self) -> None:
        """Start the fork server of the image pools now, when this run uses them."""
        if self.executor_factory is process_pool:
            warm_pool()

    @property
    def index_file(self) -> Path | None:
        """The index file, when the cache is mounted to keep it.

        Returns:
            Its path, or None for an index in memory.
        """
        if self.persistent(MountKind.CACHE):
            return self.locations.index_file
        return None

    @property
    def previews_dir(self) -> Path | None:
        """The folder previews are kept in, when the cache is mounted to keep them.

        Returns:
            Its path, or None: previews are then rendered each time.
        """
        if self.persistent(MountKind.CACHE):
            return self.locations.previews_dir
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
