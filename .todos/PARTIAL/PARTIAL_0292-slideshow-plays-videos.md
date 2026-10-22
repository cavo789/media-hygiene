# 0292 — `slideshow` plays videos too

- **Priority**: Low
- **Batch**: slideshow
- **Depends**: 0291
- **Files**: `src/media_hygiene/slideshow/`, `src/media_hygiene/review/videos.py`, `documentation/en/commands/slideshow.md`, `documentation/fr/commands/slideshow.md`

## Context

0291 shows photos only. Holiday folders hold videos from the phones too, often HEVC in `.mov`
or `.mp4`. Whether the maintainer's Samsung UE55ES6100 (2012) browser plays them: to check,
likely not for HEVC. A Chromecast with Google TV decodes HEVC in hardware on some models (to
check by model). 0291 now recommends the Chromecast's browser (measured faster than the TV,
2026-10-21): little or no transcoding may be needed there; the TV's own browser is the
fallback that may need it.

### First try (2026-10-21)

A phone `test3.mov` opened by its bare URL in the Chromecast's browser, served by `nginx`
(`video/quicktime`): the browser offered to **download** it instead of playing it, and the
downloaded file did not start. That says nothing yet about the codec: a bare `.mov` URL served
as `video/quicktime` is not played in the page by Chrome-based browsers (to check). To retry:
the same file copied as `test3.mp4` (served `video/mp4`), and its codec read with the image's
`ffprobe`. Note: `review/videos.py` serves `.mov` as `ContentType.QUICKTIME` today; the
slideshow may need `video/mp4` for a `.mov` holding H.264/HEVC in an MP4-compatible container.

### Second try (2026-10-21)

The same file copied as `test3.mp4` (served `video/mp4`) **plays in the Chromecast's
browser**. Its codec, read with the image's `ffprobe`: `h264`, 1280×720. So the container
was never the problem, only the `video/quicktime` type: serving phone `.mov` files as
`video/mp4` is enough for H.264. Still unknown: HEVC on the Chromecast, and how many HEVC
videos the collection holds (the `codec` column of `inventory.xlsx` counts them).

### The collection (measured 2026-10-21)

The maintainer's `inventory.xlsx`, **Codec** column: **1,187 `h264`** videos, **4 `hevc`**
(0.3 %). Transcoding is not worth it: it would serve 4 files.

## What to do

- Play the **original** on the Screen page in a `<video>` element, served as `video/mp4` for
  `.mov` and `.mp4` alike (not `ContentType.QUICKTIME`, which the Chromecast's browser offers
  to download).
- **No transcoding.** A video the screen cannot play (HEVC; `codec` from the index's
  `video_meta`) is skipped, and the remote says so on its thumbnail (one line, `_()`): the
  collection holds 4 of them.
- The TV's own browser (2012 fallback of 0291): photos only; the remote says videos need the
  Chromecast.
- The remote: a video's thumbnail marked ▶, play/pause, the slideshow timer waiting for the end
  of the video. The Screen page preloads the next photo while a video plays.

## Acceptance

- Tests: the content type of a `.mov` is `video/mp4` on the slideshow's route, an HEVC video is
  skipped and labelled, the timer waits for the video's end event.
- The maintainer plays a phone video of the holidays on the TV through the Chromecast, from
  the phone (part of 0291's evening test).

## Status — PARTIAL (2026-10-22)

### Done
- The slideshow shows the videos of the selection (images, RAW and videos from the index;
  codec and length from the audit's `ffprobe` metadata). `GET /film/<key>.<ext>` streams the
  original piece by piece (`Range`), `.mov`/`.mp4`/`.m4v` as `video/mp4`, `.webm` as
  `video/webm`; only the show's files. No transcoding.
- Played on the TV: codecs h264, vp8, vp9 (an unknown codec is tried: the TV's error moves on);
  HEVC or a container not served (avi, mkv…) is passed over by next/previous/timer, a jump to
  it refused, its thumbnail labelled on the phone ("Not on the TV: its format (hevc) does not
  play there.").
- Screen page (ES5): a third layer `<video>`; plays/pauses with the show; `GET /api/ended/<key>`
  on `ended` or `error` moves the show on; a play refused for sound is retried muted; the next
  photo is preloaded while a video plays. The timer waits for the end: a video stays its length
  plus max(15 s, half its length) (300 s when unknown) should the TV never say it ended.
- A browser without `img.decode` or saying it plays no H.264 (a 2012 TV's own) asks
  `/api/wait/<v>/photos`: once every paired TV is photos-only, the show passes over the videos
  and the remote says so.
- Remote: a video's first frame as thumbnail, marked ▶; status "the video plays to its end".
- Tests (`tests/unit/test_slideshow_films.py`, pick, app, screen), docs en+fr, translations,
  mh-measure step 31.

### Not done
- The evening test on the TV through the Chromecast (a phone `.mov` played from the phone,
  sound or muted, end -> next, pause/play, HEVC by its address, the TV's own browser skipping
  videos): `mh-measure.ps1 -Only 31 -Count 10`.
  **Reason:** needs the maintainer's TV and Chromecast.
