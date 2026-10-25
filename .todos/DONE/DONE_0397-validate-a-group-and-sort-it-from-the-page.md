# 0397 — See a group's photos, before → after, and "GO, sort them" from the page (event, rule, period)

- **Priority**: High
- **Batch**: review-sort
- **Depends**: 0390, 0396
- **Files**: `src/media_hygiene/cli/safety.py`, `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh.sh.j2`, `src/media_hygiene/services/sort_event.py`, `src/media_hygiene/services/sort_inputs.py`, `src/media_hygiene/review/sort_now.py`, `src/media_hygiene/review/sort_app.py`, `src/media_hygiene/review/templates/sort_review.html.j2`, `src/media_hygiene/review/templates/sort_review_choice.js.j2`, `src/media_hygiene/search/app.py`, `src/media_hygiene/search/templates/search.js.j2`, `src/media_hygiene/services/search_app.py`, `src/media_hygiene/review/templates/group_go.html.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/review-sort.md`, `documentation/fr/commands/review-sort.md`, `documentation/en/commands/browse.md`, `documentation/fr/commands/browse.md`, `documentation/en/sort/11-name-events-in-the-browser.md`, `documentation/fr/sort/11-name-events-in-the-browser.md`

## Why

Maintainer, 2026-10-25, before his first sort: "I want to see the photos of a group (an event,
a rule…) and say: OK, I validate this group, reorder its photos on the disk. For the wedding
of Hervé and Magda, if all is right, 14 photos: see them and say *I am sure, GO*. Little by
little, with a visual confirmation, surely at the start to reassure me and to bring out the
potential bugs of media-hygiene." Today the page cannot move anything through `mh`:
review-sort and browse mount the photos `:ro` (0390, left PARTIAL for that decision).

## What (decided by the maintainer, 2026-10-25)

- **Mounts**: `mh` mounts the photos **writable, with `/journal`**, for `review-sort`, `browse`,
  `search` and the home page that serves them (0356): out of `READ_ONLY_COMMANDS`
  (`cli/safety.py`, read by `mh.ps1.j2` and `mh.sh.j2`). Their 🔒 line becomes "nothing moves
  without your GO; every move is journaled, 'undo' puts it back" (in the ⌨ panel and the
  docs, both languages). This closes the item left open by 0390.
- **A group, shown before → after**: on review-sort (the event shown) and on search/browse (the
  period or the rule of 0396), a panel *Check, then sort* lists the group's files as tiles
  (the shared grid, skill `photo-picking-pages`), each with **where it is → where it goes**,
  grouped by destination folder ("14 → 2017\Fêtes\Mariages\Mariage d'Hervé et Magda");
  the files that do not move, and those left to another rule (a screenshot, 0394), apart and
  said. The destinations are those `sort` will use: the plan with the page's choices (0387)
  for an event; the dry run of 0396 for a rule or a period.
- **Leave some out**: picking files and *Leave these where they are* removes them from the
  group (a file choice "stay", as today's S).
- **GO**: *I checked: sort these N files* asks once (the count, the folders, the undo line),
  then sorts **exactly those files**: the choices are written as file decisions
  (`sort-decisions.json`, read back), and `sort` runs cut to those rows (0390's `only_event`
  generalised to a set of rows), in a thread; same guards, journal, manifest, `undo`. The
  answer is read back from the disk: "14 moved, 14 checked at their new place (run …): 'mh
  undo <run>' puts them back", and the tiles show their new place.
- **Nothing is moved without that GO**; the button stays disabled while the panel computes, or
  when a file of the group has no destination yet.

## Tests

The wedding case (14 files of the plan, the page's choices): the panel lists the 14 → their
folder, the screenshots apart; GO moves exactly those, journaled, `undo` puts them back; two
groups in a row (two runs, two undos); the mounts of `mh` (`writers` holds review-sort,
browse, search, home) in the launcher's tests; refused with the guard's sentence on a `:ro`
mount; say that `docs_screenshots` should run.
