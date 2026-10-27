# 0427 — A paired phone may download originals, behind a setting (never set photos aside)

- **Priority**: Medium
- **Batch**: home
- **Depends**: —
- **Files**: `src/media_hygiene/review/lan_paths.py`, `src/media_hygiene/config/`, `src/media_hygiene/config/templates/`, `src/media_hygiene/search/`, `documentation/en/commands/home.md`, `documentation/fr/commands/home.md`, `documentation/en/reference-config.md`, `documentation/fr/reference-config.md`

## Why

Decided by the maintainer (2026-10-27, during the `/todo:iterate` lot of 0361): in this family a
paired phone should be able to download a photo's or a video's original (`/original/`): a
relative takes a family film home. Today `lan_paths.py` refuses it (preview size only).

Narrowed the same day: **anywhere but the PC, everything is read-only** (security: a flaw in
pairing or in a page must never destroy anything; cleaning on a 6-inch screen invites
mistakes). Downloading an original reads, it changes nothing on the PC: allowed. *Set aside*
writes (quarantine): **dropped from this TODO, never allowed from a phone, no setting for it**.

## What

1. A `config.toml` setting under `[review]`, e.g. `lan_phone_originals = false`, **off by
   default**: a phone of an unknown home network gets nothing more than today. Its comment in
   the default `config.toml` says plainly what it allows (a paired phone downloads the
   originals of photos and videos, GPS included) and that it is off by default.
2. On: `/original/` joins the phone's explicit list (`phone_may`). Off: 403 as today. No write
   route ever joins the list, whatever the setting (the guard test of 0429).
3. A paired phone may **not** start the read-only audit: an audit follows a change made on the
   PC, it has no use on a phone. Remove it from the phone's allowed routes
   (`review/lan_paths.py`), with a test that the phone gets the 403 "on the PC" answer.
4. Tests for both values (setting off: 403; on: the original served); docs en + fr
   (`commands/home.md`: one 🔒 line "the phone is read-only, every change is made on the PC";
   the config reference).

## Acceptance

- Setting off: nothing changes; on: a paired phone downloads an original photo and video.
- *Set aside* from a phone answers 403 with the setting on or off.

## Decided (2026-10-27)

By the maintainer: download yes, *set aside* no; read-only everywhere but the PC is a product
rule. The setting was first named `lan_phone_writes` when it also covered *set aside*: renamed,
since it now allows a read only.
