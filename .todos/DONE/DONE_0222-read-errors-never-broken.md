# 0222 — A file the disk or the cloud could not read is reported and tried again, never kept as "broken" nor set aside

- **Priority**: High — a read that fails once is stored as "broken" until the file changes, and `clean` sets broken files aside
- **Batch**: scan
- **Depends**: —
- **Files**: `src/media_hygiene/scan/image_check.py`, `src/media_hygiene/scan/raw_check.py`, `src/media_hygiene/scan/video_check.py`, `src/media_hygiene/scan/file_check.py`, `src/media_hygiene/scan/broken.py`, `src/media_hygiene/scan/read_errors.py` (new), `src/media_hygiene/index/schema.py`, `src/media_hygiene/plan/unread.py` (new), `src/media_hygiene/services/audit.py`, `src/media_hygiene/report/templates/report.html.j2`, `src/media_hygiene/console/unread_view.py` (new), `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_read_errors.py` (new), `tests/integration/test_unread_files.py` (new), `documentation/en/reference-safety.md`, `documentation/fr/reference-safety.md`, `documentation/en/reference-troubleshooting.md`, `documentation/fr/reference-troubleshooting.md`

## Context

Found on 2026-10-17 while designing the OneDrive guard (0199). The image check treats every
`OSError` as a decoding failure (`scan/image_check.py`, `_DECODE_ERRORS`: "a corrupt file can make
a decoder raise almost anything: all mean unreadable"), so does the RAW check (`raw_check.py`), and
a video is broken when `ffprobe` fails, whatever its last line says (`video_check.py`). The verdict
is stored in the index at once (`scan/broken.py`: `repository.put`), keyed by path, size and mtime:
it stays until the file changes. `clean` then sets broken files aside.

So a read that fails for a reason outside the file — a disk with a bad moment, a USB disk
unplugged during the audit, a network drive, a OneDrive placeholder whose download fails (the PC
offline; Microsoft's documentation: reading such a file fetches it from the cloud) — leaves a
healthy photo marked "broken" for good, and the next `clean` proposes to set it aside. On the
maintainer's index (2026-10-17) no file is broken: nothing to repair there.

## Design (proposed 2026-10-17)

- A **read error** is an `OSError` that carries an `errno` (`EIO`, `ETIMEDOUT`, `EAGAIN`, `ENXIO`,
  `EACCES`, `ENOENT`…), raised while opening or reading the file; a **decoding failure** is
  everything else: Pillow's own `OSError` without `errno` ("image file is truncated"),
  `SyntaxError`, LibRaw's errors, and so on. For a video, `ffprobe`'s last line holding the system
  message of such an errno (`Input/output error`…) is a read error.
- A read error: the file is **not** broken; its facts are **not** stored (the next audit tries
  again); it is counted "could not be read this time" — a console line and a report section listing
  the files, as the folders the walker could not read — and it is never in `clean`'s plan.
- A stored verdict whose detail is a system read error (from an older version) is checked again
  once.
- Size caps: `scan/broken.py` (187/200) and `scan/file_check.py` (185/200) are nearly full: the
  classification of an error lives in the new `scan/read_errors.py`, the checks only call it.
- What it changes: a photo on a failing disk is listed instead of being set aside by `clean`
  (setting it aside would read it again anyway when the quarantine is on another drive).

## Explicit non-goals

- Retrying within the same audit (a failing disk would only be slower).
- Telling a OneDrive placeholder apart from the container (its attributes are not visible through
  Docker's file sharing): 0199 warns before the read, on Windows.

## Acceptance

- Unit (`test_read_errors.py`): an `OSError(errno.EIO, …)` while decoding → not broken, not stored;
  Pillow's truncated-file `OSError` (no errno) → broken as today; an `ffprobe` failure whose last
  line is `Input/output error` → not read; another `ffprobe` failure → broken as today.
- Integration (`test_unread_files.py`): a file made unreadable for one audit (a decoder raising
  `EIO`), then readable: the first audit lists it "could not be read this time", `clean` leaves it,
  the second audit checks it and finds it healthy.
- Docs both languages: the safety page (a file the disk or the cloud could not read is never moved),
  the troubleshooting page.

## Gain (estimated)

A healthy photo misread once (unplugged disk, network or cloud hiccup) is no longer marked broken
for good, nor proposed to the quarantine; on the maintainer's collection nothing changes today (no
broken file, measured 2026-10-17).

## Decided (2026-10-17)

The maintainer accepted the change of behaviour: a file the disk or the cloud could not read is
reported "could not be read this time", never stored as broken nor set aside, and read again at the
next audit; a photo on a failing disk is listed instead of being set aside.
