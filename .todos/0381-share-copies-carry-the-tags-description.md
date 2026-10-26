# 0381 — share: the copies carry what `tags` saw (sentence and words), asked with Yes by default

- **Priority**: Medium
- **Batch**: share
- **Depends**: —
- **Files**: `src/media_hygiene/share/sent_photo.py`, `src/media_hygiene/share/prepare.py`, `src/media_hygiene/services/share_album.py`, `src/media_hygiene/cli/cmd_share.py`, `src/media_hygiene/tags/xmp_doc.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/share.md`, `documentation/fr/commands/share.md`

## Context

Decided with the maintainer on 2026-10-25. The sentence and words of `tags` live in the
index (`descriptions`, `tags` tables). `mh xmp` carries them to a sidecar file next to each
original, but a photo sent alone (mail, WhatsApp, a social network, a cloud album) leaves its
sidecar behind, and many services read only what is inside the file. The originals are never
rewritten: that is a principle of the tool, and a rewrite would also change size and mtime
(full re-read, broken byte comparison of duplicates).

`share` already writes a **new JPEG copy** of each photo (`sent_photo.py`: upright, resized,
GPS removed, the original EXIF description kept, the original XMP packet never copied). The
copy is the right place: putting the words in it changes no original.

## Behaviour (maintainer's decision)

- `share` asks: "Add the description and the keywords found by `tags` to the copies?". The
  default is **Yes** (Enter accepts). Ask only when at least one photo of the album has
  `caption`/`vision` tags; otherwise say nothing.
- A flag for scripts and launches from a page: `--describe/--no-describe`. Without a terminal
  (`stdin` not a TTY) and without the flag: Yes, the maintainer's default. Note:
  `Output.confirm` defaults to No and answers No without a TTY, so this needs a default-Yes
  variant (`shrink_flow.py` uses `typer.confirm(..., default=True)` plus `--yes`; follow the
  pattern that fits).
- **Privacy, to say in one line** before the question or in the docs: the model's sentence
  sometimes describes intimate scenes (measured on 2026-10-25, a random sample of the real
  collection: "an adult in a bra in a lingerie shop"). This is why the user is asked. The
  `person` source (names) is **never** written by this feature. It follows
  `[tags] xmp_sources` minus `person`, or `vision` + `place`.

## What to write in each copy

- **An XMP packet** (UTF-8, Pillow ≥ 11 `save(..., xmp=...)`; the repo has 13.0.0, and
  `JpegImagePlugin` writes the APP1 marker, checked in the source): `dc:description` = the
  sentence, `dc:subject` = the words. Build it with the code of `tags/xmp_doc.py` /
  `xmp_bags.py` rather than a new writer.
- **For Windows Explorer** (the docs are Windows-first): the EXIF `XPKeywords` (0x9C9E,
  UCS-2, `;`-separated) and `XPComment` (0x9C9C) or `XPSubject`, so the words show up under
  Properties › Details. *To check* which fields Explorer shows on Windows 10/11.
- `ImageDescription` (0x010E) is ASCII per the EXIF spec: do not put accented French in it.
  **A description already there wins**: a description written by a person (camera, Windows) is
  never replaced by the model's.
- Tags of another version of the file (size/mtime changed since `tags`) are not used: same
  rule as `TagStore`.

## Steps

- [ ] `.claude/scripts/near_limit.sh` on the files above, and plan a new module (e.g.
  `share/sent_words.py`) before writing.
- [ ] `SendJob` / `SendRequest` carry `describe: bool` (parameter object, ≤ 3 args).
- [ ] Read the words in the main process, then pass them to the worker per photo. The pool
  must not open the index.
- [ ] Tests: read the packet back from a written copy (Pillow `info["xmp"]`, `getexif()`):
  accents kept, an existing human description kept, `person` never written, `--no-describe`
  writes nothing, a photo without tags gets nothing.
- [ ] `_say`: one line read back from the disk ("{n} copies carry their description").
- [ ] `i18n_update` + French; `share.md` in both languages (the question, the flag, what
  travels, the privacy line). Console output changes, so `docs_screenshots` should be run
  (do not run it unasked).

## Gain

**Estimated:** today, 0 % of the photos sent keep the words of `tags`. After this, every
photo of the album that `tags` described keeps them (in the 2026-10-25 run, 2,743 of the
photos the run had reached), whatever service receives it.
