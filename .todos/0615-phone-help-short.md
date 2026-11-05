# 0615 — On the phone, the slideshow's help is three gestures, not the command page

- **Priority**: Medium
- **Batch**: phone
- **Depends**: —
- **Files**: `src/media_hygiene/cli/menu_catalog_share.py`, `src/media_hygiene/review/templates/home_draw.js.j2`, `src/media_hygiene/review/home_texts_family.py`, `documentation/en/commands/slideshow.md`, `documentation/fr/commands/slideshow.md`

## Why (maintainer, 2026-11-05, tested on the phone)

From the phone, the slideshow's help opens the whole `commands/slideshow` page: the tool's
pitch, `docker run` lines, settings, plan B. On the sofa, the reader wants how to drive the TV;
faced with Docker text they conclude "not what I'm looking for" and stop reading.

## What

- On a phone (the family/phone view, or a narrow LAN client), the help of the slideshow opens a
  short phone help: 3–5 lines (open the TV's address `http://<PC>:8089/`, pick an album, the
  remote's gestures: next, pause, stop), then one link "Everything about the slideshow (PC)".
- Either a short section at the top of the page with its anchor (`#on-the-phone` / `#sur-le-telephone`
  rewritten to be self-sufficient), or a small served page; pick the one the docs tests accept.
- Check the other help links reachable from the phone (albums, share) for the same problem; list
  them in the report, fix those that are cheap.

## Acceptance

From the phone view, the slideshow's help shows no `docker`/`mh` command and fits one phone
screen (estimated ≤ 120 words); the PC keeps the full page. Docs en + fr; a test on the link
the phone view gets.
