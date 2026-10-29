# `shrink`: lighten heavy videos

[Documentation](../README.md) › [Commands](../reference-commands.md) › `shrink` · 🇫🇷 [Français](../../fr/commands/shrink.md)

## In short

**Win back the space of the old camera clips: about four times lighter, the picture kept.**

Old cameras stored every frame of a video as a separate JPEG (MJPEG): a minute takes about a
hundred megabytes. `shrink` lists those videos, from what the last [`audit`](audit.md) learnt,
with the space each one would free. With `--apply`, it re-encodes them in H.264, the format
every computer, phone and TV plays, checks each result, and moves the original to the
[quarantine](../reference-glossary.md#quarantine).

**Lighter, same visible quality, never "lossless"**: a re-encoding always drops details the eye
does not see. That is why the original goes to the quarantine, not to the bin: watch a few,
then [`purge`](purge.md) frees the space, or [`undo`](undo.md) brings everything back.

**When**: after a [`clean`](clean.md), when the disk is still full. **⚖ Heaviest files** in
[the folders of `search`](search.md#walk-through-your-folders) shows where the space goes.

**Try it** (only lists, changes nothing):

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  cavo789/media-hygiene shrink
```

## At a glance

| | |
|---|---|
| Your photos | ✋ Acts with `--apply` only: each video chosen is replaced by a lighter `.mp4`, its original moved to the quarantine. |
| Needs | `/cache` (the audit's facts); with `--apply`, your folders **without** `:ro`, `/journal` and `/quarantine`. |
| Writes | The lighter videos, the journal; the originals in the quarantine. |
| Undo | [`undo <run>`](undo.md) removes each lighter video (while it is unchanged) and brings its original back. |
| With `mh` | `mh shrink`, then `mh shrink --try` (the home page's action) or `mh shrink --apply`. |

## Run it

First the list (the folders may stay `:ro`), then add `--apply`:

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene shrink --apply
```

The list says what each video is and what it would weigh after, an **estimate**: only the
encoding tells.

```text
3 videos worth lightening: 1.9 GB today, about 240 MB after (estimated: only the encoding tells).
   C:\Photos\2009\Zoo\MVI_0042.AVI — mjpeg, 640×480, 4 min: 812 MB → ~95 MB
```

## Try first: before and after in the browser

`--try` encodes the first `try_count` videos of the list (10 by default, the largest gains
first; or those below `--folder`) as **drafts**, one at a time in the background, with the
same settings as `--apply`, and opens a page that shows each one as soon as it is ready:

- **B, the draft**, plays in the page, with its size, its gain in % and its encoding time;
- **A, the original**: the MJPEG and PCM of old cameras play in no browser, so the page shows
  frames of the original and of the draft taken at the same instants (10, 50 and 90 % of the
  film), at 100 %; the `B` key swaps A and B. `←` / `→` move between the videos.
- **Lighten this one** (`L`) or **Choose every draft shown** (`A`): each choice is saved in
  `shrink-decisions.json` and shown as read back from the disk. **Lighten the chosen now**
  (`Enter`) hands over to the terminal, which asks the usual question, then lightens them as
  `--apply` does (originals in the quarantine, journaled, undoable), **reusing each draft**:
  nothing is encoded twice. A video moved, renamed or changed since the page is skipped, with a
  line.

```powershell
docker run --rm -it -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene shrink --try
```

**The drafts are always removed**: they are written only in `/cache/shrink-try/` (the cache
volume, never next to your photos), and removed when the page closes, on Ctrl+C or when the
container is stopped. If the computer was switched off in the middle, the next `shrink` removes
them and says so in one line. Without a `/cache` mount, `--try` refuses (with the line to add);
one `--try` at a time. Before each draft, `/cache` must have twice its estimated size free, or
the drafts stop there: a draft weighs about 29 % of its original (measured on a Panasonic
clip), so the 10 heaviest clips of a large collection may take 1 to 2 GB for a while.

Estimated time: about 8 s of encoding per minute of film on a 32-processor PC, so about 30 s
for a 3-minute clip, and 5 minutes for 10 of them: the first draft shows long before the last.

## Which videos

- **The codecs of old cameras and of the 2000s**: MJPEG, DV, MPEG-4 part 2 (DivX, Xvid),
  Windows Media, MPEG-1 and 2 (`codecs` in the `[shrink]` section of `config.toml`).
- **Any video that spends far too many bits for its picture**: more than `bits_per_pixel` (0.5)
  bits per pixel and per frame. A phone's H.264 spends about 0.1 to 0.3: it is **left alone**,
  since a second lossy generation shows and gains little.
- Never one in a protected, excluded or backup folder, nor one shorter than a second.
- **Never one it lightened itself**: each lighter video carries a mark inside the file (the tag
  `media_hygiene`, `media-hygiene shrink crf=23`; the camera's comment stays). Renamed, moved
  by `sort` or in the Explorer, copied elsewhere, even with the journals gone: it is never
  offered again.
- **Not worth it**: a result that is not at least `min_gain_percent` (30) % lighter is thrown
  away, the original stays, and the video is not tried again while it is unchanged.

## Two levels

| | What it does | For |
|---|---|---|
| *(default)* | Same size and frame rate, x264 at CRF 23: visually the same. | Everything worth keeping as it is. |
| `--lighter` | At most 720 lines on the short side: lighter still for a larger picture (a 720-line clip stays as by default). | The clips whose quality matters less (the children's first videos). Choose them with `--folder`. |

Measured on two MJPEG clips of a Panasonic camera (1280×720, 43 s and 3 min 35 s): CRF 23 kept
26 and 29 % of their size, CRF 18 66 and 69 %, with no visible difference between them nor with
the original; both played in Windows and on a phone, with their date. Hence CRF 23 by default
(`same_crf` in `config.toml`: 18 for the finest picture). Encoding took 8 to 11 seconds
per minute of film on a 32-processor PC (16 used). Another camera, another subject: other
figures; the list says its estimate, and the real gain is said after each video.

## What is kept, and checked

- **Kept**: the date the video was shot (`creation_time`, and the local date of an iPhone), its
  place, every sound track (in AAC), the picture turned upright, the file's date (the
  modification time): `classify` and `sort` find the same date.
- **Checked before the original goes**: the lighter video lasts as long (to half a second), has
  as many sound tracks, says the same date and place, and its frames decode. Otherwise it is
  thrown away and the original is not touched.
- **The name**: `clip.avi` becomes `clip.mp4`; a sidecar `clip.avi.xmp` follows as `clip.mp4.xmp`.
  A file already named `clip.mp4` next to it is never replaced: that video is skipped.
- **Never imported again**: the original is remembered like any file you set aside. If a phone
  or a backup still holds it, `mh import --phone` does not import it again, and the next `clean` sets a
  copy that came back aside.

## Options

| Option | What it does |
|---|---|
| `--folder PATH` | Only the videos below this folder (host path); repeat it for several. |
| `--lighter` | At most 720 lines, a stronger compression. |
| `--try` | Drafts of the first `try_count` ones, compared in the browser; lighten from the page. |
| `--apply` | Lighten them; without it, only list them. |
| `--yes`, `-y` | Do not ask first. |

## Good to know

- **Slow**: a re-encoding takes about as long as the film, or longer on a small computer; one
  video at a time, on half of the processors (`threads`), so that the computer stays usable.
  Ctrl+C stops after the video being encoded; type the command again for the rest.
- **Started from the home page**: the re-encoding runs in the window of `mh` (the home server
  never writes your photos); the page stays open and shows how far it is (videos done, the one
  being encoded), then its new state.
- **The space comes back with `purge`**: until then, the originals are in the quarantine.
- **A video renamed (`.avi` → `.mp4`) keeps its links**: `albums.json`, `decisions.json` and the
  videos chosen with `--try` name the new `.mp4`, read back from the disk; `undo` gives them the
  original's name again.
- **Settings**: the `[shrink]` section of `config.toml` (`codecs`, `bits_per_pixel`,
  `min_gain_percent`, `same_crf`, `lighter_crf`, `lighter_lines`, `preset`, `threads`,
  `try_count`: the drafts of `--try`, 10 by default).
- **A container change alone (`.mov` → `.mp4` without re-encoding) frees nothing**: it is not
  offered.

## Go further

- [Clean in short](../clean/quick-guide.md)
- [Undo, history and purge](../clean/09-undo-history-purge.md)

## The built-in help

<details>
<summary><code>shrink --help</code></summary>

<!-- capture: help-shrink.txt -->
```text
 Usage: media-hygiene shrink [OPTIONS]

 List the heavy videos worth lightening (old cameras, MJPEG); with --apply,
 re-encode them in H.264, each one checked, the original in the quarantine
 (journaled, undoable).

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --folder           <str>  Only the videos below this folder (host path, as   │
│                           you mounted it); repeat it for several. Default:   │
│                           every mounted folder.                              │
│ --lighter                 Lighter still for a large picture: at most 720     │
│                           lines (lighter_lines in config.toml). For clips    │
│                           whose quality matters less.                        │
│ --apply                   Lighten them; without it, only list them with the  │
│                           gain expected.                                     │
│ --try                     Encode the first ones (try_count in config.toml)   │
│                           as drafts, in /cache only, and compare before and  │
│                           after in the browser; lighten from the page. The   │
│                           drafts are removed when the page closes.           │
│ --yes      -y             Lighten without asking first.                      │
│ --help     -h             Show this message and exit.                        │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [All commands](../reference-commands.md) · [Documentation](../README.md)
