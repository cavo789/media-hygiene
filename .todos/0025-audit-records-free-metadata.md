# 0025 — `audit` records the metadata it already has in hand (GPS, video date and place, EXIF extras)

- **Priority**: High — first building block of `classify` (0026); cheap, useful beyond sorting
- **Batch**: scan
- **Depends**: —
- **Files**: `src/media_dedup/scan/visual.py`, `src/media_dedup/scan/models.py`, `src/media_dedup/scan/video_check.py`, `src/media_dedup/scan/broken.py`, `src/media_dedup/scan/image_check.py`, `src/media_dedup/index/schema.py`, `src/media_dedup/index/repository.py`, `src/media_dedup/index/facts.py`, `src/media_dedup/report/summary.py`, `src/media_dedup/report/templates/`, `documentation/en/02-keep-the-cache.md`, `documentation/fr/02-keep-the-cache.md`

## Context

`audit` already decodes every image once (`image_check.inspect_image` → `visual.visual_facts`,
which holds the parsed EXIF) and runs `ffprobe` on every video (`video_check.video_problem`). A
lot of metadata is in hand at that moment and thrown away. Recording it makes the index a
reusable inventory for `classify` (0026) and for needs not identified yet, **as long as it stays
free**. Only facts that cost nothing extra during the audit are added.

Measured on a real 70,000-photo family collection (`media-dedup:latest`, one process):

| Step | Cost per image |
|---|---|
| Current audit decode (`inspect_image`) | 48.8 ms |
| Extra EXIF fields, read from the already-parsed EXIF | ≈ 0 (dict lookups) |
| Exposure stats on the gray 512 px thumbnail already computed | 0.35 ms (< 1 %) |
| Header-only re-read (`Image.open` + `getexif`, no decode), one-time backfill | 3.6 ms |

The same sample showed how uneven the metadata is:
- 90 % of images have an EXIF date, but several cameras had a wrong clock or a non-standard
  format (`07/03/2002 20:55:38`);
- 1.3 % have GPS: older Android phones did not record it, recent iPhones do.

## Proposal

- **Store facts, never judgments.** Labels such as "excellent / good / poor" are computed where
  they are needed, from raw measures and configurable thresholds. Sharpness alone misjudges a
  foggy landscape, so a stored label would bake in a bad guess.
- **Images**: from the EXIF already parsed in `visual_facts`, and all optional:
  - GPS latitude, longitude, altitude (IFD `0x8825`);
  - `OffsetTimeOriginal` (time zone);
  - lens model, focal length, exposure time, f-number, ISO, flash;
  - `Software`, `ImageDescription` / `UserComment` / `Artist` when present;
  - format (JPEG, HEIF, MPO, PNG…) and the JPEG quality estimated from the quantization tables
    (already loaded by Pillow);
  - from the gray thumbnail already made for the hashes: mean brightness and the share of
    clipped dark and bright pixels (exposure).
- **Videos**, in the **same** `ffprobe` call, by widening `-show_entries`:
  - `format=duration,bit_rate`;
  - video stream `codec_name,width,height,r_frame_rate` and rotation;
  - `format_tags=creation_time,location,com.apple.quicktime.location.ISO6709,com.apple.quicktime.creationdate,com.apple.quicktime.make,com.apple.quicktime.model`
    and the Android make/model tags.
  - Check that the demux-only ffprobe of the image (0010) still reports these tags (e2e).
- **Index schema v3**:
  - typed columns for what later steps query: `latitude`, `longitude`, and the media date for
    videos too;
  - one JSON column (a pydantic `MediaMetadata`, versioned) for the rest, so a future field
    does not need a schema change.
- `_is_complete` also requires the metadata version. **One-time backfill** after the upgrade:
  - images already in the index get a header-only EXIF re-read in the process pool, **not** a
    full decode;
  - videos get one `ffprobe` each.

  Estimate for 65,000 images: about 4 min on one process, well under that with the pool. Say
  it in the console the first time.
- **Inventory block** in the audit report and console summary: share of media with an EXIF
  date, with GPS, dated by video tags; images per format; videos total duration. It is computed
  from facts already collected, so it costs nothing.

## Acceptance

- [ ] Audit wall time on the docs sample unchanged within noise (measure before / after, note
      the numbers in the commit).
- [ ] GPS (JPEG, HEIC), video date and ISO 6709 location parsed; malformed values ignored, never
      fatal; unit tests with synthetic EXIF and ffprobe JSON.
- [ ] A v2 index upgrades in place; the backfill reads headers only (test with a counting fake).
- [ ] Inventory block in report + console; documentation en + fr; `.po` translated.
