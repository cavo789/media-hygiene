# 0333 — One page frame for every page of the tool: the pages that still differ, converted

- **Priority**: Critical
- **Batch**: review-ui
- **Depends**: 0304
- **Files**: `src/media_hygiene/review/templates/page_frame.html.j2` (new), `src/media_hygiene/review/templates/pick_grid.css.j2`, `src/media_hygiene/review/templates/review_side.css.j2`, `src/media_hygiene/review/templates/review.html.j2`, `src/media_hygiene/review/templates/near_review.html.j2`, `src/media_hygiene/review/templates/gone_review.html.j2`, `src/media_hygiene/review/templates/unwanted_review.html.j2`, `src/media_hygiene/review/templates/pairs_review.html.j2`, `src/media_hygiene/review/templates/sort_review.html.j2`, `src/media_hygiene/people/templates/people.html.j2`, `src/media_hygiene/places/templates/places.html.j2`, `src/media_hygiene/slideshow/templates/slideshow.html.j2`, `src/media_hygiene/share/templates/album.html.j2`, `tests/unit/test_page_frame.py` (new), `tests/unit/test_page_headers.py`, `tests/integration/test_home_page.py`, `.claude/skills/photo-picking-pages/SKILL.md`

## Why

The maintainer, 2026-10-23, after finding the phone page without *Back to the home page* (0332):
"identify the web pages whose layout differs from our standard, so that we settle it once and
for all". Their rule: every page has the same layout and the same features, at the same place,
where possible and where they apply (memory *Same features on every page*).

## The standard (from `browse`, `search` and the phone page, 2026-10-23)

1. `page_header.html.j2` on top (the page's name, the theme, *Back to the home page* when opened
   from the home page) and `home_link.html.j2` (the way back, the `/api/alive` pings — 0262).
2. Two columns (`.layout`, `review_side.css.j2`): on the left `#side` — what leads to the content
   (tabs, a list, a form) then, at the bottom, the ⌨ **Keyboard** panel (`#keys`, *More keys*, the
   🔒 line); on the right `#content` — **one** sticky bar (`#bar`: where you are, or what to do with
   what is picked; the saved line read back from the disk; *Apply now* when opened from the home
   page), then the content (`main`).
3. Nothing else above the content: no second `<header>`, no `<footer>` bar; hints go in the keys
   panel or a `<details>`. The bar keeps its height (the content never jumps).
4. `<title>{page} — media-hygiene</title>`, the favicon, `theme.css.j2`.

## Survey (measured 2026-10-23: `grep` of each served page and the scripts it includes)

| Page | Header + way home | Left column `#side` | ⌨ panel | One bar, no footer | Apply now | Divergence |
|---|---|---|---|---|---|---|
| `browse`, `search` | ✓ | ✓ | ✓ | ✓ | ✓ | the reference |
| phone (`phone_review`) | header ✓, way home ✗ (0332) | ✓ | ✓ | ✓ | — (0315) | 0332 |
| bursts (`review`) | ✓ | ✓ | ✓ | own `<header>` + `<footer>` | ✓ | bar and footer |
| `--near` (`near_review`) | ✓ | ✓ | ✓ | own `<header>` + `<footer>` | ✓ | bar and footer |
| `--gone`, `--junk`, `--pairs` | ✓ | own `<aside>` (not `#side`, its own CSS) | own copy | own `<header>` + `<footer>` | ✗ | column, panel, bar, footer, Apply now |
| `review-sort` (`sort_review`) | ✓ | ✗ (one column) | ✗ (keys in hint lines) | own `<header>` + `<footer>` | ✗ | everything but the header |
| `people` | ✓ | ✗ (one column) | ✗ (keys in the comment, not on the page) | own `<header>` | ✓ | column, panel, bar |
| `places` (map) | ✓ | own `<aside>` | ✗ (4 `keydown` handlers, no panel) | a `<header>` inside `main` | ✗ | panel, bar |
| `slideshow` (PC remote) | ✓ | ✗ | — (no keys) | own `<header>` | — | bar |
| `album` (albums, PC and paired phone) | ✗ (served in front of the home page) | ✗ | — | own `<header>` | — | to decide (see 4) |

Exempt, the reason to keep (to write in the test, item 3): the home page itself and the
documentation (`doc.html.j2`: the home page's shell, its own standard); `lan_pair` (a phone not
paired yet: nothing to go back to); `screen` (the TV: a 2012 browser, black screen, no UI);
`report/base.html.j2` (a static report opened from disk, no server).

## What

1. **A shared frame** `page_frame.html.j2` (a Jinja layout the page `extends`, or includes in
   parts as the `pick_*` templates do — choose by what keeps each page's own script readable):
   header, `.layout`, `#side` with a `side` block and the keys panel (`pick_keys.html.j2`'s
   markup, its rows given by the page), `#content` with the bar (`bar` block, the saved line,
   *Apply now*) and `main`; `home_link.html.j2` at the end. `browse`, `search` and the phone
   page move onto it first, with no visible change (their tests and `test_pick_pages.py` green).
2. **Convert each page of the survey**, one commit each, its tests green, in this order: the
   bursts and `--near` reviews (drop the `<footer>`: its buttons go in the bar), `--gone`,
   `--junk`, `--pairs` (their `<aside>` becomes `#side`; *Apply now*), `review-sort`, `places`,
   `slideshow`; `people` last, **after the people TODOs 0323–0329** (another session is
   reshaping that page: rebase on them, do not race them). A page whose keys are only in hint
   lines or a comment gets its ⌨ panel.
3. **A test that holds the rule**, `tests/unit/test_page_frame.py`: every template with a
   `<!DOCTYPE` under `src/media_hygiene/*/templates/` renders the frame's parts once
   (`page_header`, `home_link`, `id="side"`, `id="keys"` when it has a `keydown`, `id="bar"`, no
   `<footer>`), except an explicit list where each exemption carries its reason (above). The
   exclusion sets of `test_page_headers.py` and `test_home_page.py` move into it. Two
   exemptions are temporary, named so: the phone page's way home ("until 0332") and `people`
   ("until 0323–0329 are done"); whichever TODO runs last removes its line.
4. **`album`**: check how it is reached on the PC (from the home page's *Your albums*?). If a PC
   user can open it, it gets the way back home; its phone layout (a tap, a swipe) stays as it is.
5. The skill `photo-picking-pages` points to the frame for the layout part; the pages of tiles
   keep their `pick_*` parts on top of it.

## Overlaps (do not do twice)

- 0304 (the keys panel's style on every page with shortcuts): done first; here, its place.
- 0319, 0320 (bursts and `--junk` pick as `browse`), 0321 (the large view on group reviews):
  they build on this frame — run them after it.
- 0332 (the phone page's way home) and 0315 (its *Apply now*): the phone page's own items.

## Tests

`test_page_frame.py` as above; each converted page's existing tests green; for each page
converted, a headless Chromium check of its keys (skill `photo-picking-pages`, checklist item
2) — no `pageerror`, the content's top the same before and after a choice.

## Docs

The pages' captures change: say that `docs_screenshots` should run (not unasked). The command
pages describing a footer or a header line of a converted page, both languages.

## Explicit NON-goals

- The pickings of the review pages (0319, 0320) and their large view (0321).
- The home page and the documentation's shell.
- The HTML reports written to disk (`report/`).
