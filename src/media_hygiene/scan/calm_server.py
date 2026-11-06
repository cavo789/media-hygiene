"""Imported first by the fork server of the image pools: it ignores Ctrl+C at once.

Ctrl+C reaches every process of the terminal. The fork server imports Pillow and numpy
before it sets its own signal handlers; a Ctrl+C in that window killed it with a
traceback, and the pool broke (0627). Ignoring SIGINT before those imports closes the
window: the parent alone handles Ctrl+C, and closes the pool.
"""

from __future__ import annotations

import signal
import threading


def ignore_interrupts() -> None:
    """Ignore Ctrl+C in this process, when called from its main thread."""
    if threading.current_thread() is threading.main_thread():
        signal.signal(signal.SIGINT, signal.SIG_IGN)


ignore_interrupts()
