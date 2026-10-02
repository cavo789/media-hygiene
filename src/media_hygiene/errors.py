"""Domain exceptions: each carries a user-facing message and an optional tip."""

from __future__ import annotations


class MediaHygieneError(Exception):
    """Base class of every error the CLI reports to the user without a traceback."""

    def __init__(self, message: str, tip: str | None = None) -> None:
        """Store the translated message and an optional 💡 tip.

        Args:
            message: What went wrong, already translated.
            tip: How to fix it, already translated.
        """
        super().__init__(message)
        self.message = message
        self.tip = tip


class ConfigError(MediaHygieneError):
    """The configuration file or an override is invalid."""


class MountError(MediaHygieneError):
    """A mount point is missing, read-only when it must be writable, or empty."""


class JournalError(MediaHygieneError):
    """A journal cannot be found or read."""


class CrossCheckError(MediaHygieneError):
    """Czkawka results are missing, unreadable, or cover other folders."""


class DecisionsError(MediaHygieneError):
    """A decisions file is missing, invalid, or made for another audit."""


class WorkbookError(MediaHygieneError):
    """A classify workbook is missing, damaged, or made for another plan."""


class AiError(MediaHygieneError):
    """The local model cannot be reached, lacks a capability, or answered nonsense."""


class GeoDataError(MediaHygieneError):
    """The towns shipped for offline geocoding are missing or damaged."""


class NominatimError(MediaHygieneError):
    """The online place search cannot be reached, refused, or answered nonsense."""
