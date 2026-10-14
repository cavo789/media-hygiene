# 0141 — Faster video frames: an `ffmpeg` built for speed, one run per video

- **Priority**: Low — since 0132 caches the colours, it only shortens the first audit of a collection with videos (measured 2026-10-14: colours 0.0 s on a warm audit); was Medium
- **Batch**: docker
- **Depends**: 0131, 0132
- **Files**: `Dockerfile`, `src/media_hygiene/scan/keyframes.py`, `src/media_hygiene/scan/colour.py`, `src/media_hygiene/scan/video_models.py`, `src/media_hygiene/scan/video_prints.py`, `tests/integration/`

## Context

Speed review of 2026-10-14 (second pass).

**1. The decoding `ffmpeg` is built for size, not speed.** The `ffmpeg` stage of the
`Dockerfile` passes `--enable-small` ("optimize for size instead of speed": `-Os` instead of
`-O3`, some tables computed at run time instead of built in). For `ffprobe`, which only reads
container headers, that costs nothing. For `ffmpeg`, which decodes H.264/HEVC from the
previous keyframe up to each position (accurate seek), it slows the work that dominates the
video part of a first audit. The binary is 6 MB today, so a few MB more is acceptable.

**2. One process and one container parse per frame.** `keyframes.fingerprint` runs `ffmpeg`
once per position in `FRAME_POSITIONS` (5), and `colour.video_colour` runs it 3 more times for
each near-duplicate candidate (`_VIDEO_POSITIONS`, until 0132 stores the colour). Each run
starts a process, opens and parses the container again (the `moov` atom of a long MP4 can be
megabytes), and seeks.

## What to do

1. Measure first, in the devcontainer, on a few real phone videos (H.264 and HEVC, 1080p and
   4K, 10 s and 5 min). Build two `ffmpeg` binaries with and without `--enable-small` (one
   build at a time: the PC crashes under heavy load, use the gentle helpers). Time
   `keyframes.fingerprint` on each video. Drop `--enable-small` from the `ffmpeg` stage only
   if it is faster; keep it for `ffprobe`.
2. Also measure `-threads 2` against today's `-threads 1` on 4K HEVC. Several videos already
   run at once, but a single long 4K video can end up running alone at the end of the pass.
3. One run per video: give `ffmpeg` one input per position (`-ss t1 -i f -ss t2 -i f …`) and
   one `-filter_complex` that scales each one, then joins them (`concat=n=5:v=1`) into one
   rawvideo output of 5 × 4,096 bytes. Splitting the bytes gives the same 5 frames as today,
   so `VIDEO_PRINT_VERSION` stays 1. An integration test checks that the hashes are identical
   to the per-frame runs on the test videos. If a frame cannot be decoded, fall back to
   today's per-frame runs for that video. Today the whole video gets no fingerprint then, so
   keep that outcome.
4. With 0132 in place, the colour frames of a video can come from the same run: a `split`
   filter outputs the 64 px grey square for the hash and the RGB square for the colour. Do it
   only if 0131 shows that the colours of videos are worth it.

## Acceptance

- Same fingerprints as before on the test videos (no re-fingerprinting of existing indexes).
- Measured on the maintainer's real videos (0104): fingerprint time per video before and
  after, written in the commit message.
- `dive_ci` still passes.

## Status — UNNEEDED (2026-10-14)

Measured, nothing changed. FFmpeg 9.0.2 built twice with the `Dockerfile` options (one container
on 4 CPUs: 28 s and 40 s), plus `concat,split,trim` to try one run per video. The commands are
those of `keyframes.py`, on real videos of `C:\Photos` (read-only), the page cache warm, best
of 3 runs. The collection holds no HEVC and no 4K video (2003–2023: H.264 up to 1080p, and
MJPEG), so the HEVC/4K cases of item 1 could not be measured.

CPU time (user + system) for the 5 frames of one video:

| Video | `--enable-small` (today) | without it | `-threads 2` | one run (concat) |
|---|---|---|---|---|
| H.264 1080p, 9 s, 45 Mb/s | 1.76 s | 1.73 s | 1.82 s | 2.79 s |
| H.264 1080p, 44 s | 0.92 s | 0.90 s | 0.96 s | 1.65 s |
| H.264 1080p, 137 s | 0.52 s | 0.51 s | 0.56 s | 0.94 s |

Wall time of the same runs: 1.69 / 1.63 / 1.00 / 1.11 s for the first video; a small
H.264 (219 s) and an MJPEG (237 s) take 0.05–0.22 s whatever the variant.

- **`--enable-small`**: 2 % of CPU, against a binary of 10.5 MB instead of 5.7 MB. Kept.
  Frames are byte for byte identical with both builds.
- **`-threads 2`**: shorter wall time for a single video, but more CPU. An audit already runs
  one video per processor (`VideoPrinter._slots`); it would only help the last video of the
  pass. Not done.
- **One run per video** (5 inputs, `trim=end_frame=1`, `concat`): 60–80 % more CPU. Its
  shorter wall time comes from ffmpeg 9's threads (one per input), which an audit already gets
  by running several videos at once. Worse, the frames differ on 2 videos out of 5, and an
  MJPEG video gives 3 frames instead of 5: it would mean `VIDEO_PRINT_VERSION` + 1 and a
  fallback path, for a loss. Rejected.
- **Colour frames from the same run** (item 4): since 0132 the colours are stored, so a warm
  audit spends 0.0 s on them. Not done.

What a first audit pays: 0.5–1.8 s of CPU per 1080p video, spread over every processor (about
2–4 minutes for 2,000 videos on 16 CPUs). Revive only if the maintainer's collection gains
4K HEVC videos and the `fingerprints` step of `Time per step` shows it on a first audit.
