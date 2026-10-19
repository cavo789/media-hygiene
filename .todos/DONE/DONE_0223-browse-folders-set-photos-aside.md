# 0223 — `browse`: walk through the folders as in Explorer, look at the photos, set some aside (remembered)

- **Priority**: High — the maintainer: "this use (deleting in Explorer) should no longer exist; I should do it from MH"
- **Batch**: tags
- **Depends**: 0215
- **Files**: `src/media_hygiene/cli/cmd_browse.py` (new), `src/media_hygiene/cli/app.py`, `src/media_hygiene/cli/safety.py`, `src/media_hygiene/cli/menu_catalog.py`, `src/media_hygiene/search/app.py`, `src/media_hygiene/search/folders.py` (new), `src/media_hygiene/search/statements.py`, `src/media_hygiene/search/views.py`, `src/media_hygiene/search/chosen.py`, `src/media_hygiene/search/templates/search.html.j2`, `src/media_hygiene/search/templates/browse.html.j2` (new), `src/media_hygiene/search/templates/browse.js.j2` (new), `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/integration/test_browse_page.py` (new), `tests/support/docs/scenario.py`, `tests/support/docs/pages.py`, `.config/mkdocs/mkdocs.yml`, `documentation/en/commands/browse.md` (new), `documentation/fr/commands/browse.md` (new), `documentation/en/reference-commands.md`, `documentation/fr/reference-commands.md`, `documentation/en/find/quick-guide.md`, `documentation/fr/find/quick-guide.md`

## Context

Asked by the maintainer on 2026-10-17: "can I easily walk through the library to delete photos?
Like Windows Explorer: I open a folder, I see photos and I delete some. This use should no longer
exist: you should know what was deleted, to propose deleting it again when someone puts it back
on the PC. If I do it from Windows Explorer, that is a problem. I should do it from MH."

Today the tool can find photos (`search`: words, a person, years, a part of the path) and, with
0215, set aside the photos a search found. There is no view of the folders themselves: the user
goes back to Explorer, and a file deleted there is unknown to the tool, so 0216 cannot recognise it
when it comes back.

## What to do

- `media-hygiene browse`: a page command (`PAGE_COMMANDS`, `READ_ONLY_COMMANDS`: photos `:ro`),
  the search page's own server opened on a **folder view** (one app, one selection, one way to save:
  0215's):
  - left, the tree of the library's folders from the index (each with its number of photos and
    videos and its size; collapsed below the mounted folders);
  - right, the photos and videos of the folder chosen, as thumbnails (the preview cache, a video by
    its still), sorted by name or by date; `Enter` or a double click shows one large, `←`/`→` the
    previous and next ones, as the Photos app;
  - select with a click, `Ctrl`/`Shift`, `Space`, `Ctrl+A` (the folder); `Delete` or *Set aside*
    saves the selection under 0215's `chosen` key of `decisions.json`, read back and shown with its
    count and size: "37 set aside — `mh clean --decisions` moves them to the quarantine".
  - when the page was opened from the home page (0209, 0210), an *Apply now* button ends it so that
    `mh` runs `clean --decisions` with its question, then opens the page again.
- `search` gets a link to the folder view and back.
- The words of the tool: nothing is deleted from the page; "set aside" moves to the quarantine,
  journaled and undoable, and remembered (0216: a photo set aside that comes back is proposed again);
  `purge` frees the space.
- A new verb (CLAUDE.md): its page in both languages, its name in `COMMANDS_TOO`, the mkdocs nav, a
  step in the "Find in short" guide and the `mh` menu ("Walk through your folders, set photos
  aside"); a capture of the page (synthetic pictures only).
- Size caps: `search/app.py` (176/200) only routes: the folder view's answers live in
  `search/folders.py`.

## Explicit non-goals

- Renaming, moving or editing photos from the page (`sort` moves; editors edit).
- Deleting for good from the page.
- Files deleted in Explorer: the tool does not see them. A later option could: the audit noticing
  the files gone since the last audit (the index keeps, for every file, its size and a digest of
  its first and last 64 KB), for the user to confirm in a page which ones were deleted on purpose.

## Acceptance

- Integration (HTTP): the tree's counts match the index; a folder's files listed in both orders; a
  selection saved and read back under `chosen`, the other keys kept; `clean --decisions` then sets
  aside exactly those files; another `Host` refused.
- Docs both languages; say in the report that `docs_screenshots` should run.

## Gain (estimated)

Removing photos no longer needs Explorer: every removal goes through the journal, can be undone,
and is remembered when the same file comes back — which a deletion in Explorer never is.

## Status — PARTIAL (2026-10-17)

### Done
- `media-hygiene browse` (page command, read-only, `PHOTO_READERS`, `PAGE_COMMANDS`): the search's
  own server; `/` serves the page the command opens, `/search` and `/browse` both pages, linked to
  each other.
- Tree from the index (`search/folder_tree.py`, `search/folders.py`: photos, videos, size with
  subfolders, files directly in it; mounted folders open, the rest closed); a folder's files by
  name or date; thumbnails (preview cache), a video by its first frames (`/video/`, `media-src`).
- Explorer picking (click, Ctrl, Shift, Space, Ctrl+A), Enter/double click large, ←/→; Delete or
  the button saves under 0215's `chosen` key, read back with count and size; on Ctrl+C, the
  next step proposed is `clean --decisions`.
- Menu step, `COMMANDS_TOO`, mkdocs nav, pages `commands/browse.md` (en, fr), reference,
  "Find in short" step 5 (steps 5-6 renumbered 6-7), French catalog.
- Tests: `tests/integration/tags/test_browse_page.py` (in `tags/` for its audited-tree fixture),
  `tests/unit/test_folder_tree.py`, `browse` added to `test_read_only_commands.py`.

### Not done
- The *Apply now* button when the page is opened from the home page.
  **Reason:** the home page (0209, 0210) does not exist yet.
- A capture of the page (`images/browse.webp`).
  **Reason:** `docs_screenshots` was not run (heavy, needs asking); add a `browse` mode to
  `tests/support/docs/browser.py` / `served.py` / `browsing.py`, run it, and reference the image
  in both `commands/browse.md` (the unused-image test fails until it is referenced).
- "Remembered when it comes back" is not claimed anywhere: it needs 0216.

## Inbox (2026-10-19)

- *Apply now* from the home page, and "remembered when it comes back" in the docs → refiled as 0243.
- The capture `browse.webp` → refiled as 0244.
