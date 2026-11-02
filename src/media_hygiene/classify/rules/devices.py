"""An event's cameras (0556): two events of the same days told apart by their devices.

A `date_range` rule written by *Move to an event…* keeps the cameras of the files moved.
A file of its days from another camera is another event's; one without a camera
(received, a scan, a screenshot) is never guessed: it is to be asked (TODO 0558).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from media_hygiene.classify.models import MediaInput
    from media_hygiene.classify.rules.matchers import Test


def devices_test(devices: tuple[str, ...], dated: Test) -> Test:
    """An event's dates, narrowed to its cameras (0556): two events may share days.

    Args:
        devices: The event's cameras, `Make Model`; none: any file of its days.
        dated: The test of its days.

    Returns:
        The test: a file of another camera is not the event's, nor one without a
        camera (received, a scan): that one is asked (`to_ask`), never guessed.
    """
    known = frozenset(device.casefold() for device in devices)

    def test(file: MediaInput) -> bool:
        """Tell whether one file is of the event's days and cameras.

        Args:
            file: The file.

        Returns:
            True when it is.
        """
        return dated(file) and (not known or _camera(file) in known)

    return test


def unrefused(refused: frozenset[str], test: Test) -> Test:
    """An event's test, without the files the user refused for it (0558).

    Args:
        refused: The content ids it never takes.
        test: Its test.

    Returns:
        The test: false for a refused file.
    """
    if not refused:
        return test
    return lambda file: file.digest not in refused and test(file)


def to_ask(devices: tuple[str, ...], dated: Test) -> Test:
    """The files of an event's days its cameras cannot tell: no camera in them.

    Args:
        devices: The event's cameras; none: nothing to ask, its days decide.
        dated: The test of its days.

    Returns:
        The test: true for a file of its days without a camera.
    """

    def test(file: MediaInput) -> bool:
        """Tell whether one file of the event's days must be asked.

        Args:
            file: The file.

        Returns:
            True when it has no camera and the event has some.
        """
        return bool(devices) and not _camera(file) and dated(file)

    return test


def _camera(file: MediaInput) -> str:
    """The camera of a file, as compared with an event's.

    Args:
        file: The file.

    Returns:
        Its make and model, lower case; empty without one.
    """
    return (file.camera or "").strip().casefold()
