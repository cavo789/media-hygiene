# 0523 — One-click shortcuts: album from an event or a search, TV from a card, end-of-task notice

- **Priority**: Medium
- **Batch**: share
- **Depends**: 0514
- **Files**: `src/media_hygiene/search/templates/search_events.js.j2`, `src/media_hygiene/search/events_desk.py`, `src/media_hygiene/share/album_api.py`, `src/media_hygiene/share/album_pickers.py`, `src/media_hygiene/share/templates/album.js.j2`, `src/media_hygiene/review/templates/home_run.js.j2`

## Asked (maintainer, 2026-10-30)

Fewer clicks for the things done all the time.

## What

1. **Album from an event**: a button on each event card (search, Events tab) creates an album
   named after the event with its files, and opens it. Today: pick every file, *Add to album*,
   type a name (estimated 4–5 actions → 1).
2. **Album from a search**: *Make an album of these results* (every file found, the files set
   aside excluded — 0518), named after the query.
3. **To the TV from a card**: event and album cards get the "Show on the TV" action the phone
   page has (paired TV, 0456); without a paired TV, the button is hidden.
4. **End of a long task**: a browser notification (Notification API, asked once, its answer
   remembered in `localStorage`) when a step followed in the page (0514) ends, so the user can
   leave the tab.

Each one is its own commit; 4 may be dropped if 0514 already says it.

## Done when

Each shortcut has a test of its API call and its result read back (album on disk), docs in both
languages.
