# 0598 — `slideshow --folder` served by the home server, for a folder of the library

- **Priority**: Low
- **Batch**: one-interface
- **Depends**: 0594 (DONE)
- **Files**: `src/media_hygiene/services/slideshow_here.py`, `src/media_hygiene/review/album_show.py`, `src/media_hygiene/review/home_step.py`

## Why (study of 0594)

The step *Show your photos on the TV* takes any folder: outside the library it needs its own mount,
so the home server ends. A folder already mounted (in the library, or a backup) needs no restart.

## What

In `shown_here`: a folder that maps inside a mounted root answers `/slideshow/…`; any other keeps
today's path. `SlideshowHere` has the show's start already (`selected`, `Pick`).

## Done when

The step on a folder of the library changes page without ending the server (test).
