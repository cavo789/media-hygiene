# 0585 — Intruder files page: no way back home, and a sidebar of shortcuts that looks clickable but is not

- **Priority**: High
- **Batch**: page-shell
- **Depends**: —
- **Files**: the intruders page templates (`review/templates/intruders*`), `review/templates/page_header.html.j2`, `review/templates/home_link.html.j2`, the shared sidebar of the page shell (0491, 0579)

## Reported (maintainer, 2026-11-03, Windows, `mh review --intruders` typed)

- The intruder files page has **no "Back to the home page" button** (a page missing the way
  back home is a bug: `.claude/rules/workflow.md`).
- The left band shows the shortcuts, but **none is clickable**: the user believes they can click
  them, nothing happens. Bad UX.

## To do

1. Reproduce on the demo tree: the page opened by the typed command and from the home page;
   which one lacks the link (0512 covers typed pages: check whether its part is done).
2. The shared header's home link on this page, in both cases.
3. The sidebar: links that work wherever the home server answers; when the page runs alone (no
   home server), either links to the pages it can reach or no sidebar at all — never inert
   items drawn as links.
4. A test over every page of the shell: a home link present, and every sidebar item is either an
   `<a href>` or not drawn.

## Acceptance

- [ ] The intruders page has *Back to the home page*, typed or opened from home
- [ ] No sidebar item looks clickable without being one, on any page (test)
