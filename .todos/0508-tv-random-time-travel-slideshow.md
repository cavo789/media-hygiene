# 0508 — TV from the phone: a random slideshow that travels through time

- **Priority**: Medium
- **Batch**: phone
- **Depends**: 0507
- **Files**: `src/media_hygiene/services/slideshow_random.py` (new), `src/media_hygiene/services/slideshow_choices.py`, `src/media_hygiene/review/templates/home_run.js.j2`, `src/media_hygiene/review/home_texts_family.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_slideshow_random.py` (new), `tests/unit/test_tv_choices.py`, `documentation/en/commands/slideshow.md`, `documentation/fr/commands/slideshow.md`, `documentation/en/commands/home.md`, `documentation/fr/commands/home.md`

## Reported (maintainer, 2026-10-30)

A slideshow during a family meal is great, but a folder is a few dozen photos: the show loops
again and again. Wanted: a **random** show started from the phone, not a given folder, taking
X photos per event and lasting long — **without jumping between eras** at each photo (twenty
years ago, the girls today, fifteen years back, last year…).

Answers of the maintainer (2026-10-30):

- videos: **ignored**;
- not-a-photo (documents, receipts, screenshots…): **set aside** when it can be told;
- no "people only" filter: landscapes and sunsets are welcome too.

## Design: chapters walking through time

1. **Events** from the index alone (read-only, nothing moved): photos grouped by gaps between
   `media_date`s — reuse `classify/events.py`'s rule rather than a second definition.
   Undated photos are not used (they cannot be placed in time).
2. **A chapter** = a random period (about one year); 4–6 of its events, shown **oldest first**.
3. **Per event**, X photos (≈ 8–12, a named constant) spread over the event's duration (not
   its first ones); one shot per burst series (`similar.bursts`), one per near-duplicate
   group, the sharpest first (Laplacian sharpness of `VisualFacts`).
4. **Next chapter**: a *neighbouring* period (±1 to 3 years) by a random walk, with an
   occasional larger jump so the show does not stay stuck in one era; a period never shown
   twice before every other one was.
5. **A title card** at each event — the existing chapters of `slideshow_story` (0448:
   date + place from the user's places / GeoNames town), so a change of era reads as a new
   chapter, not as a jump.
6. **Filters**: images only (no video); not a screenshot nor a document
   (`classify.rules.matchers.is_screenshot`, the test `unwanted_reviewing` already uses);
   not tiny / almost black / almost white / blurred by the thresholds of
   `[review.unwanted]` (`unwanted_limits`) — the same verdicts, never a second copy of them.
   Excluded folders are never read (as everywhere).
7. **Length**: from the chosen duration and the seconds per slide, e.g. 1 h at 8 s ≈ 450
   photos (estimated), below `MAX_SLIDES = 3000` (`slideshow_pick.py`): no cap change.

The selection is a pure function of (index rows, seed, duration, era): testable, and the
seed makes a show reproducible in tests; a new tap = a new seed.

## Phone page

At the top of the TV choices (the single folder list of 0507): **"🎲 At random"**
("🎲 Au hasard"), with two optional choices:

- **duration**: 30 min / **1 h** (default) / 2 h;
- **era**: everything (default) / the last 5 years / a period (first and last year).

Started through the same path as a folder (`/choose`, `slideshow_selection.selected`: same
cap, a running show replaced). New body, validated by `Chosen`: e.g.
`{"random": {"minutes": 60, "first_year": …, "last_year": …}}`.

## Tests

- no era jump: consecutive events of a chapter are in date order; consecutive chapters are
  neighbours except for the rare planned jump (fixed seed);
- per-event count and spread; one shot per burst; videos, screenshots, documents and
  unwanted-by-threshold photos never chosen; undated photos never chosen;
- duration → number of slides; era bounds respected; an index with fewer photos than asked
  gives them all, no loop of the same photo before the others;
- a collection with a single event; an empty one (409 with the reason, as `_refused`).

## Settings?

The photos per event, the chapter size and the walk's step are named constants (memory "few
settings"); a `config.toml` setting only if the maintainer finds after use that
the family wants another rhythm — to ask in the feedback.

## Gain (estimated)

Today a meal-long show = one folder looping (a few dozen photos, every ~5 min at 8 s/slide).
After: ≈ 450 different photos for an hour, chosen across the whole collection, in a calm
chronological order, with no manual choice on the phone beyond one tap.

## Docs

`slideshow.md` and `home.md` (en + fr): the random show, how it chooses, its two choices;
`i18n_update` + French; `docs_screenshots` to run if a capture shows the phone's TV choices.
