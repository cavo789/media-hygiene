# 0145 — `kind = "screenshot"`: a PNG with a camera's dated name is an edited photo, not a screenshot

- **Priority**: Low — measured: 52 of 52,056 files go to "Documents and screenshots", about 5–8 of them wrongly; `classify` only proposes, the workbook shows them before any `sort`
- **Batch**: classify
- **Depends**: —
- **Files**: `src/media_hygiene/classify/rules/matchers.py`, `tests/unit/test_classify_rules.py`, `documentation/en/sort/06-write-down-what-you-know.md`, `documentation/fr/sort/06-write-down-what-you-know.md`

## Context

Check 0035 of TODO 0056 (Part 4), run on 2026-10-14 by Claude on the real collection. The run
was read-only: `classify` with the default `config.toml` (no vision model), on a copy of the
maintainer's index, reports in a throwaway volume.

`matchers.is_screenshot` says yes to a screenshot name, and to a PNG or tiny image without a
camera trace. With the default rules, `existing_folder` comes first, so only loose files in
generic folders (year, `YYYY-MM`) reach the screenshot rule. Of the 52 files it takes:

- about 44 are right: 38 Android `Screenshot_YYYYMMDD-HHMMSS.png`, plus messaging pictures
  (`received_*.png/.jpeg`) and GIFs;
- 5 are PNGs named like a phone camera, `IMG_YYYYMMDD_HHMMSS.png`. An Android camera never
  writes PNG: these are photos edited, then exported;
- 3 or so are PNGs with a plain name in a year folder (e.g. `2011/<word>.png`, 4.3 MB), most
  likely exported photos as well. Their name says nothing about them.

The index also shows where the rule would err if `existing_folder` did not come first. Of 135
PNGs without a camera trace, the clear photos are a few exported baby photos in a named 2004
folder and phone-camera-named PNGs. iPad screenshots, `IMG_NNNN.PNG` with 4 digits, are true
screenshots, as are Screenpresso captures.

Videos named with a resolution (`720p`, `1080p`) are fine: one file only, and it is a recorded
online class, i.e. a true download.

## Change (proposal: the maintainer confirms or drops it)

In `is_screenshot`, before the PNG test: a name of a phone camera with date and time is not a
screenshot. Patterns: `IMG_YYYYMMDD_HHMMSS`, `YYYYMMDD_HHMMSS`, `PXL_YYYYMMDD_…`. They must not
match the 4-digit `IMG_NNNN` of iPad screenshots. The name rule (`Screenshot_…`) still wins
first.

Plain-named PNGs stay screenshots: nothing in their name tells them apart from a downloaded
image or a design, and the workbook shows them before `sort`.

## Tests

`test_classify_rules.py`: `IMG_20170923_124027.png` and `20220827_165332.png` without a camera
trace → not a screenshot; `IMG_1807.PNG` and `Screenshot_20170923-111739.png` → screenshot.

## Docs (en + fr)

The `kind` rule explains what a screenshot is (`sort/06-write-down-what-you-know.md`, the `screenshot` bullet): add "a PNG named like a
camera (`IMG_20190123_202218.png`) is taken for an edited photo".

## Acceptance

- The targeted tests pass; the 5 camera-named PNGs above leave the "Documents and screenshots"
  category on the next `classify` run (to be checked by the maintainer).
