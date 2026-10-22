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
