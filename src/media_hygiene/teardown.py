"""Once a command has said its last word, Ctrl+C ends the process at once, quietly.

When the interpreter exits, it waits for the worker threads still busy: a page's
`GET /api/state` running in asyncio's default executor, an audit stopping between two
files. A Ctrl+C (or `docker stop`) during that wait used to break into
`threading._shutdown` and print a traceback (0275). After the command has returned,
nothing is left to save: such a signal ends the process with the command's own exit
code, its output flushed first.
"""

from __future__ import annotations

import contextlib
import os
import signal
import sys
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Iterator
    from types import FrameType

# What ends a command at teardown: Ctrl+C, and `docker stop`.
_SIGNALS: Final = (signal.SIGINT, signal.SIGTERM)
_FAILED: Final = 1  # the code of a command that ended on an unexpected error


def exit_code(code: object) -> int:
    """The process exit code of a `SystemExit` code, as the interpreter reads it.

    Args:
        code: `SystemExit.code`: None, a number, or a message.

    Returns:
        0 for None, the number itself, else 1 (a message is printed, then 1).
    """
    if code is None:
        return 0
    if isinstance(code, int):
        return code
    return _FAILED


class QuietEnd:
    """A signal handler ending the process with the code its command chose."""

    __slots__ = ("code",)

    def __init__(self, code: int) -> None:
        """Remember the code.

        Args:
            code: The exit code of the command that ended.
        """
        self.code = code

    def __call__(self, _signal: int, _frame: FrameType | None) -> None:
        """Flush what was printed, then end without waiting for the worker threads.

        Args:
            _signal: The signal received.
            _frame: The frame interrupted.
        """
        for stream in (sys.stdout, sys.stderr):
            with contextlib.suppress(OSError, ValueError, AttributeError):
                stream.flush()
        os._exit(self.code)  # the threads left only read: nothing to save


def arm(code: int) -> None:
    """From now on, Ctrl+C or `docker stop` end the process with this code.

    Args:
        code: The exit code of the command that ended.
    """
    handler = QuietEnd(code)
    for number in _SIGNALS:
        signal.signal(number, handler)


@contextlib.contextmanager
def quiet_teardown() -> Iterator[None]:
    """Run a command; once it ends, however it ends, arm the quiet end.

    Yields:
        Nothing: the command runs inside the block.

    Raises:
        BaseException: Whatever ended the command, `SystemExit` included, unchanged.
    """
    try:
        yield
    except SystemExit as ended:
        arm(exit_code(ended.code))
        raise
    except BaseException:
        arm(_FAILED)
        raise
    arm(0)
