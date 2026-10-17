"""Project-wide constants and enumerations: the single home of every fixed value."""

from __future__ import annotations

from enum import IntEnum, StrEnum
from typing import Final

APP_NAME: Final = "media-hygiene"
HOME_PAGE: Final = "https://github.com/cavo789/media-hygiene"
DOC_PAGES: Final = "https://cavo789.github.io/media-hygiene"  # + _("fr/…/"), docs.yml
ENV_PREFIX: Final = "MEDIA_HYGIENE_"
GETTEXT_DOMAIN: Final = "media_hygiene"
CONFIG_FILE_NAME: Final = "config.toml"
INDEX_FILE_NAME: Final = "index.sqlite"
JOURNAL_SUFFIX: Final = ".jsonl"
REPORT_FILE_NAME: Final = "report.html"
# Near duplicates and re-encoded videos alone, next to the report.
NEAR_FILE_NAME: Final = "near.html"
REPORT_INDEX_FILE_NAME: Final = "index.html"
SUMMARY_FILE_NAME: Final = "summary.json"
PLAN_CSV_FILE_NAME: Final = "plan.csv"
CLASSIFY_PLAN_FILE_NAME: Final = "plan.json"
CLASSIFY_WORKBOOK_FILE_NAME: Final = "classify.xlsx"
CLASSIFY_FOLDER_SUFFIX: Final = "classify"
INVENTORY_FOLDER_SUFFIX: Final = "inventory"
INVENTORY_FILE_STEM: Final = "inventory"
CZKAWKA_IMAGE: Final = "jlesage/czkawka:v26.09.2"  # to run Czkawka yourself
CZKAWKA_FILE_NAME: Final = "czkawka.json"
CZKAWKA_OUTPUT_DIR: Final = "/out"
THUMBNAILS_DIR_NAME: Final = "thumbs"
PAIRS_DIR_NAME: Final = "pairs"
MOUNTINFO_PATH: Final = "/proc/self/mountinfo"
FFPROBE_BINARY: Final = "ffprobe"
FFMPEG_BINARY: Final = "ffmpeg"
# A folder holding this file is an album of `album`: hard links that every scan skips.
ALBUM_MARKER: Final = ".media-hygiene-album"


class Locale(StrEnum):
    """Languages the interface is translated into."""

    EN = "en"
    FR = "fr"


class Verbosity(StrEnum):
    """Log levels, from the quietest to the most detailed."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    VERBOSE = "verbose"  # info, plus every tip a command has (not only the best two)
    DEBUG = "debug"


class ColorMode(StrEnum):
    """When to emit ANSI colours."""

    AUTO = "auto"
    ALWAYS = "always"
    NEVER = "never"


class MediaKind(StrEnum):
    """Families of files: media, other files asked for with `--ext`, sidecars."""

    IMAGE = "image"
    RAW = "raw"
    VIDEO = "video"
    OTHER = "other"
    SIDECAR = "sidecar"


class KeepReason(StrEnum):
    """What made the kept copy win: the policy's criteria in order, then a review."""

    PROTECTED = "protected"
    PREFERRED = "preferred"
    HAS_SIDECAR = "has-sidecar"
    NOT_A_COPY = "not-a-copy"
    MEANINGFUL_NAME = "meaningful-name"
    MEANINGFUL_FOLDER = "meaningful-folder"
    OLDEST = "oldest"
    SHORTEST_PATH = "shortest-path"
    ALPHABETICAL = "alphabetical"
    REVIEWED = "reviewed"


class NearReason(StrEnum):
    """What made the kept version of near duplicates win."""

    RESOLUTION = "resolution"  # the highest resolution
    SIZE = "size"  # the same resolution, a larger file by 1 % or more
    RULES = "rules"  # the same resolution and about the same size: the usual rules
    CHOSEN = "chosen"  # a person kept another version (`review --near`)


class BrokenReason(StrEnum):
    """Why a media file is considered broken."""

    EMPTY = "empty"
    UNREADABLE_IMAGE = "unreadable-image"
    UNREADABLE_RAW = "unreadable-raw"
    UNREADABLE_VIDEO = "unreadable-video"


class InventoryFormat(StrEnum):
    """File format of `inventory`: an Excel workbook, or a CSV file."""

    XLSX = "xlsx"
    CSV = "csv"


class CleanTier(StrEnum):
    """How far `clean` goes: exact duplicates, the sure near duplicates, or them all."""

    EXACT = "exact"
    NEAR = "near"
    NEAR_ALL = "near-all"


class RunKind(StrEnum):
    """Which command produced a report."""

    AUDIT = "audit"
    CLEAN = "clean"


class ExitCode(IntEnum):
    """Process exit codes."""

    OK = 0
    FAILURE = 1
    USAGE = 2
    INTERRUPTED = 130  # 128 + SIGINT, as shells report Ctrl+C


class Sizes(IntEnum):
    """Byte counts and limits used by the scanner and the reports."""

    HASH_CHUNK = 1024 * 1024
    PARTIAL_HASH = 64 * 1024
    THUMBNAIL_EDGE = 160
    MAX_GROUPS_IN_REPORT = 500
    PAIR_SAMPLES = 4
    MAX_SAMPLED_PAIRS = 50
    RANDOM_SAMPLE = 30
    MAX_BURSTS_IN_REPORT = 200
    MAX_ORPHANS_IN_REPORT = 500
    IO_CONCURRENCY = 16


IMAGE_EXTENSIONS: Final = frozenset(
    {".avif", ".bmp", ".gif", ".heic", ".heif", ".jpe", ".jpeg", ".jpg"}
    | {".png", ".tif", ".tiff", ".webp"},
)
RAW_EXTENSIONS: Final = frozenset(
    {".arw", ".cr2", ".cr3", ".dng", ".nef", ".orf", ".pef", ".raf", ".rw2", ".srw"},
)
VIDEO_EXTENSIONS: Final = frozenset(
    {".3g2", ".3gp", ".avi", ".flv", ".m2ts", ".m4v", ".mkv", ".mov", ".mp4"}
    | {".mpeg", ".mpg", ".mts", ".ts", ".webm", ".wmv"},
)
MEDIA_EXTENSIONS: Final = IMAGE_EXTENSIONS | RAW_EXTENSIONS | VIDEO_EXTENSIONS
# Sidecars hold the metadata or edits of their photo: it is kept; moved once orphan.
SIDECAR_EXTENSIONS: Final = frozenset({".aae", ".thm", ".xmp"})
