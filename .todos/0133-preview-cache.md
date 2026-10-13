# 0133 — A preview cache in /cache: decode each photo once per size

- **Priority**: High — every report decodes all its previews again, and so does every page of `review`, `review-sort`, `search` and `people`
- **Batch**: report
- **Depends**: —
- **Files**: `src/media_hygiene/report/thumbnails.py`, `src/media_hygiene/report/writer.py`, `src/media_hygiene/report/classify_writer.py`, `src/media_hygiene/review/files.py`, `src/media_hygiene/review/sort_app.py`, `src/media_hygiene/search/thumbs.py`, `src/media_hygiene/people/app.py`, `src/media_hygiene/review/respond.py`, `src/media_hygiene/review/serving.py`, `src/media_hygiene/paths/`, `documentation/en/start/02-keep-the-cache.md`, `documentation/fr/start/02-keep-the-cache.md`

## Context

Speed review of 2026-10-14. Previews are decoded from the original on every use:

- `report/writer.py` → `make_thumbnails(builder.thumbnail_jobs(record))`, 160 px
  (`Sizes.THUMBNAIL_EDGE`). Each report gets a new folder, so `audit`, `review`, `clean` and
  `crosscheck` all decode again every keeper, sample, near-duplicate picture and broken image they
  show. With near duplicates that can be thousands of photos. RAW files go through LibRaw.
- `classify_writer._previews`: up to 8 per event, for 70,000 photos spread over yearly pages.
- `review/files.py` and `people/app.py`: `review_preview`, 1600 px, decoded on each request. Going
  back to a photo decodes it again.
- `review/sort_app.py`: 400 px thumbnails and 1600 px previews. `search/thumbs.py`: 360 px grid.

A photo that does not change never needs a second decode for a given size.

## What to do

1. `paths`: a `previews/` folder under the cache mount point (`/cache`, never `/config`).
   Without a persistent `/cache`, keep today's behaviour.
2. `report/thumbnails.py`: `cached_preview(path, size, mtime_ns, edge)`. The cache key is a
   digest of (path, size, mtime_ns, edge, preview version), like `preview_name`. Write to a
   temporary name, then `os.replace`, so a crash never leaves a half-written JPEG.
3. Reports copy the cached file into their own `thumbs/`. `/reports` and `/cache` are different
   mounts, so a hard link is impossible. Copying 10 KB is far cheaper than decoding a 12 MP
   photo or a RAW file. The servers (`review`, `review-sort`, `search`, `people`) read the cache
   directly.
4. Bound it: cleaning `clean`/`purge` removes the previews of the files they delete (or a
   plain size cap, oldest first), so the cache does not grow forever. Say its size in `status`.
5. Browser cache across sessions: `review/respond.py` tags every cacheable answer with
   `RUN_TAG`, drawn anew at each run, so a browser re-downloads every preview when the next
   session starts. For previews, use the cache key as the ETag: it changes only when the file
   or the preview size changes, so a 304 answers what the browser already holds.
6. Docs en + fr: the cache also keeps previews, and deleting the volume rebuilds them.

## Acceptance

- A second `audit` with nothing changed decodes no picture for its report. A test with a counting
  fake checks this.
- `review` serves a photo already seen without decoding it.
- A file rewritten in place (new mtime) gets a new preview.
