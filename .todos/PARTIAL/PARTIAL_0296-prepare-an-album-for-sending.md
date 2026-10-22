# 0296 — Prepare an album for sending: resized copies without GPS, a folder and a zip

- **Priority**: Medium — covers e-mail, social networks and a USB stick at once, with no account and no password
- **Batch**: share
- **Depends**: 0295
- **Files**: `src/media_hygiene/share/prepare.py` (new), `src/media_hygiene/cli/cmd_share.py` (new), `src/media_hygiene/cli/menu_catalog_share.py`, `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh.sh.j2`, `src/media_hygiene/config/settings.py`, `src/media_hygiene/config/templates/config.toml.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/share.md` (new), `documentation/fr/commands/share.md` (new), `tests/support/docs/scenario.py`, `.config/mkdocs/mkdocs.yml`

## Context

Designed in chat with the maintainer (2026-10-22). A browser cannot attach files to an e-mail
(`mailto:` carries text only); sending from the container would need the user's mail
password (SMTP): ruled out. Facebook no longer lets an application publish to a personal
profile (the `publish_actions` permission was removed in 2018 — **to check** in Meta's
documentation before writing it in the docs); only business pages, with an app reviewed by
Meta: out of proportion. Agreed: `mh` prepares the photos; the user attaches the zip to a mail,
or creates the Facebook album and adds the folder by hand — fast, since the photos are ready.

## Decided (2026-10-22, the maintainer, in chat)

- One feature for e-mail and social networks: **Prepare for sending** an album (0295).
- **GPS removed by default** (a photo sent must not say where the house is); an option keeps
  it.
- A fixed destination rather than a folder typed each time (e.g. `C:\Temp`): no arbitrary
  folder mounted for writing.

## What to do

1. Each photo of the album: EXIF orientation applied, fitted into a long side (proposed
   2048 px), JPEG quality 85 (proposed), GPS tags removed unless asked; the date, camera and
   description kept. Videos: copied as they are or left out (to decide; say it in the report).
2. Written under one folder per album, e.g. `<user>\media-hygiene\Shares\Crete 2023\`, plus
   `Crete 2023.zip`; the mount added by `mh` for this command only; an album prepared again
   replaces its folder (said in one line).
3. At the end: the count, the total size, the size of the zip, read back from the disk; a
   warning above 25 MB (an attachment limit of the big webmails — **to check**: Gmail's and
   Outlook.com's current limits); `mh` opens Explorer on the folder.
4. Reached from the *Share* area (0294) and from the album's page.
5. `[share] long_side_px`, `quality`, `keep_gps` (false) as settings? Proposed; say so in the
   report.
6. Docs en + fr (a new verb: its page, `COMMANDS_TOO`, the menu catalog, mkdocs nav),
   translations, `docs_screenshots` afterwards.

## Acceptance

- An album of photos from several folders gives one folder and one zip; no original touched
  (a test compares the originals before and after).
- A photo with GPS gives a copy without it by default, with it when asked (a test reads the
  EXIF back).
- Size per photo: measured on synthetic pictures here, and on real ones by the maintainer
  (estimated beforehand 0.3–1 MB each from 0291's 0.28 MB at 1920 px, measured 2026-10-22).

## Decided (2026-10-22, by the maintainer, `/todo:iterate`)

Item 1: videos are **left out and counted** ("3 videos not included"): only the resized photos
are copied (one video alone can pass a mail's limit).

## Status — PARTIAL (2026-10-22)

### Done
- `share --album "<name>"`: each photo upright, long side 2048, JPEG 85, GPS removed unless
  `--keep-gps` / `[share] keep_gps`; date, camera, description kept; maker notes and XMP dropped.
  Videos left out and counted; missing and unreadable photos counted.
- One folder and one zip per album in `/shares` (`$HOME\media-hygiene\Shares`, mounted by `mh`
  for `share` only; `mh.ps1` opens it in the Explorer); an album prepared again replaces its
  folder (said); counts and sizes read back from the disk; warning above 25 MB (worded as "some
  webmails", the limits still to check).
- `[share] long_side_px`, `quality`, `keep_gps` settings; Share area step and the album bar's
  📨 *Prepare for sending* button; docs en+fr, COMMANDS_TOO, mkdocs nav, translations.
- Tests: originals compared before/after, GPS read back removed/kept, launcher mounts, read-only run.
- Size measured on synthetic 12 MP pictures: 0.27–0.83 MB per copy.

### Not done
- Sizes on real photos and the Explorer opening on Windows: `.\mh-measure.ps1 -Only 32 -Count 60`.
  **Reason:** only the maintainer's PC has the real photos and Windows.
- `docs_screenshots` (new help, Share area, album bar; reference capture hand-edited).
  **Reason:** heavy (image build + browser), never run unasked.
