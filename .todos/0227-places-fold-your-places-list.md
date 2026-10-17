# 0227 — `places`: fold the "Your places" list so the unnamed clusters stay in reach

- **Priority**: Low
- **Batch**: places
- **Depends**: —
- **Files**: `src/media_hygiene/places/templates/places.html.j2`, `documentation/en/commands/places.md`, `documentation/fr/commands/places.md`

## Wish

Maintainer, 2026-10-17: the *Your places* list ("Vos lieux") keeps growing (10 places today).
To reach *The largest clusters without a name* below it, they have to scroll. They want to
fold and unfold the list.

## Today

`places.html.j2`: two `<h2>` headings, each followed by a `<ul>`, `#places` then `#clusters`,
in the left column, with no way to fold either one.

## To do

1. Put each list in a `<details>` element with the count in its `<summary>`: "Your places (10)",
   "The largest clusters without a name (N)". Clusters open; places open while there are few of
   them (proposal: folded from 8 places on). Remember the reader's choice in `localStorage`,
   wrapped in try/catch, as the review pages do for their order.
2. When a place is saved or edited, the list it belongs to opens and the line flashes: the save
   is proven where the eye looks.
3. Same look as the review pages' *More keys* (`#moreKeys`): a muted summary with a pointer
   cursor.
4. Documentation EN + FR if a capture shows the column; then run `docs_screenshots`.
