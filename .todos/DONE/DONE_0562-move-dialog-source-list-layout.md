# 0562 — Move to an event dialog: checkbox and folder on one line, no horizontal scrollbar

- **Priority**: Low
- **Batch**: search-move
- **Depends**: —
- **Files**: `src/media_hygiene/search/templates/move_dialog.html.j2`, `src/media_hygiene/search/templates/move_dialog.js.j2`

## Reported (maintainer, 2026-11-01)

In the search page's *Move to an event* dialog, the list of source folders
(`#moveSources`, "13 files — C:\Photos\Développement Jan-17", one checkbox each) looks broken:

- each checkbox sits alone, centred, on its own line, and its text on the next line: the
  reader cannot tell which box belongs to which folder;
- the list shows a horizontal scrollbar (browser default look) although the lines are short.

## Likely cause (to check in the browser's inspector)

`move_dialog.html.j2` already tries `.sources label { display: block !important; }` ("one
line: box, then text"), but a broader rule probably still applies to the checkbox — a shared
form style giving every `input` `width: 100%` / `display: block` (the name field's style), so
the box takes the whole width (hence centred) and pushes the text down, and its width plus
padding overflows the `overflow: auto` list (hence the horizontal bar).

## Wanted

- Each row: checkbox at the left, then "N files — folder" on the same line, the long folder
  wrapping under the text (not under the box): `label { display: flex; gap; align-items:
  baseline }`, `input[type=checkbox] { width: auto; flex: none; margin: 0 }`.
- Whole row clickable, a light hover / zebra so the rows read as a list; the count in bold or
  muted so the folder stands out.
- `overflow-x: hidden` (or simply no overflowing child) on `.sources`: only a vertical scroll
  when the list is long, styled like the rest of the page (thin scrollbar).
- Check the same in dark theme and at phone width.

## Done when

- A screenshot of the dialog with three long folders shows one line per folder (box + text),
  no horizontal scrollbar; a unit test of the rendered template asserts the checkbox rule
  (`width: auto`) is present so a shared style cannot take it back silently.
- Documentation captures showing this dialog: `docs_screenshots` should run (not run here).
