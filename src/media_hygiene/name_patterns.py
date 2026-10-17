"""The names cameras and apps give to files and folders: never someone's choice.

`plan` (the keep rules), `classify` and `tags` read them; `config.toml` may replace
them (`[keep] generated_names`, `generic_folders`).
"""

from __future__ import annotations

from typing import Final

from media_hygiene.date_names import DATE_FOLDERS

# Names cameras and apps generate, matched whole (no extension/copy mark, any case).
GENERATED_NAMES: Final = (
    r"_?(IMG|VID|MVI|MOV|SAM|DSC[NF]?|_DSC|PICT|CIMG)[_-]?\d+",
    r"(IMG|VID)[_-]\d{8}[_-]\d{6}([_-]\d+)?",
    r"(IMG|VID|AUD)-\d{8}-WA\d+",
    r"_?MG_\d+",
    r"P\d{7}",
    r"PXL_\d{8}_\d+.*",
    r"\d{8}_\d{6}(_\d+)?",
    r"\d{4}-\d{2}-\d{2} \d{2}\.\d{2}\.\d{2}(-\d+)?",
    r"(GOPR|G[HX]\d{2})\d{4}",
    r"DJI_\d+",
    r"(FB_IMG|received|Snapchat)[_-]\d+",
    r"(Screenshot|Screen Shot|Capture d.écran)([ _-].*)?",
    r"image\d*",
    r"[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}",
    r"[0-9a-f]{16,}",
    r"\d{1,6}",  # a bare number (`162.mp4`): an export or a renaming counter
)
# Folder names created by devices and apps, or saying only a date: not someone's choice.
GENERIC_FOLDERS: Final = (
    r"DCIM",
    r"\d{3}[A-Z0-9_]{5}",
    r"Camera( Roll| Uploads)?",
    r"WhatsApp (Images|Video)",
    r"Sent",
    r"Downloads?|Téléchargements",
    r"Screenshots|Captures d.écran",
    r"(New folder|Nouveau dossier)( \(\d+\))?",
    r"Import(s|ed)?|Temp|tmp",
    r"Photos from \d{4}",  # the year folders of a Google Photos Takeout (0217)
    *DATE_FOLDERS,
)
