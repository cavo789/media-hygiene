# 0311 — The home page's confirmation says when launching erases nothing yet

- **Priority**: Medium
- **Batch**: home
- **Depends**: —
- **Files**: `src/media_hygiene/cli/menu_entry.py`, `src/media_hygiene/cli/menu_catalog_import.py`, `src/media_hygiene/review/home_texts_run.py`, `src/media_hygiene/review/templates/home_run.js.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_menu_catalog.py`

## Why

The maintainer, 2026-10-23, about **Make room on the phone** (`phone --free`) on the home page:
the dialog shows the red **For good** badge and the title "Make room on the phone: for good?",
so they believed **Start** deletes at once. It does not: Start opens a page where the files the
PC already holds are ticked, the user unticks what they keep, and only that page's
**Delete … from the phone** button (with its own browser confirmation) erases, each file
copied again and compared with the PC's first (read in `mh_phone_free.ps1.j2`,
`phone_session.py`).

The dialog is generic (`openConfirm` in `home_run.js.j2`): every `Risk.FINAL` step gets the same
title `{title}: for good?` and the line "mh asks you again in {window} before touching
anything". Right for `purge`, misleading for a step whose deletion happens on a later page.

## What

- `Step` gets an optional confirmation text (title + one paragraph), used by `openConfirm`
  instead of the generic ones when set. Keep the **For good** badge: the end of the path is
  final.
- `phone-free`, approved by the maintainer on 2026-10-23:
  - title: "Make room on the phone: launching erases nothing"
  - text: "A page opens with the files the PC already holds, all ticked: untick those you
    keep. Nothing leaves the phone before that page's "Delete … from the phone" button, and
    each file is compared with the PC's copy once more just before."
  - French: « Faire de la place sur le téléphone : rien n'est effacé en lançant » / « Une page
    s'ouvre avec les fichiers que le PC détient déjà, tous cochés : décochez ceux que vous
    gardez. Rien ne quitte le téléphone avant le bouton « Supprimer … du téléphone » de cette
    page, et chaque fichier est encore comparé à la copie du PC juste avant. »
- Read the other `Risk.FINAL` steps of the catalog: any other one whose deletion happens on a
  later page (a review page, a question in the console) gets its own text too; list them in
  the commit.

## Tests

The rendered home state carries the step's own confirmation for `phone-free`, the generic one
for `purge`.

## Docs

The launcher page shows this dialog? To check (`grep -rn "for good" documentation/`); if a
capture holds it, `docs_screenshots` should run afterwards (not unasked).
