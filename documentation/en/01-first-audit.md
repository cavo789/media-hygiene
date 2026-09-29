# 1. Your first audit

[Documentation](README.md) › Step 1 of 13 · 🇫🇷 [Français](../fr/01-first-audit.md)

In this first step, you ask the tool to look at **one folder** of photos and to tell you what it
finds. Nothing is changed: an audit only reads.

## What you need

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.
- A folder of photos and videos, here `C:\Photos`.
- A PowerShell window (or a WSL terminal, see [step 3](03-several-folders.md#from-wsl)).

## Run the audit

Copy this command in PowerShell, with the path of your own folder instead of `C:\Photos`:

```powershell
docker run --rm -it -v "C:\Photos:/data/c/Photos:ro" cavo789/media-hygiene audit
```

The first run downloads the tool (a few hundred MB); the next ones start at once.

| Part | What it means |
|---|---|
| `docker run` | Starts the tool in a container, a small isolated box. |
| `--rm` | Deletes that box once the tool ends: nothing is left behind. |
| `-it` | Connects the box to your window: colours, progress bars, and questions you can answer. |
| `-v "C:\Photos:/data/c/Photos:ro"` | Lets the tool see your folder. The box only sees what you give it with `-v`: here `C:\Photos`, which it calls `/data/c/Photos`. |
| `:ro` | *Read-only*: Docker itself forbids any change to your folder. |
| `cavo789/media-hygiene` | The tool, as published on Docker Hub. |
| `audit` | What to do: look for duplicates and broken files. |

> 💡 The tool speaks English. Add `--locale fr` right after `cavo789/media-hygiene` for French:
> `cavo789/media-hygiene --locale fr audit`. [Step 7](07-configuration-file.md) makes it permanent.

## What you see while it runs

Each step shows one line of progress and, below it in grey, what it really does:

```text
⠴ Proving identity (full SHA-256) ━━━━━━━━━╸━━━━━━━━ 11,707/23,907 elapsed 0:00:47 · about 0:02:19 left
  Reads the remaining candidates in full: same SHA-256 means identical, byte for byte.
```

- **`11,707/23,907`**: files done in *this step*, out of the files it has to process.
- **`elapsed`**: time spent in this step. **`about … left`**: an estimate for this step only,
  based on its speed so far. It moves: a few large videos slow it down, small photos speed it up.
- **Ctrl+C** stops at any moment, without error messages. An audit never changes anything.

| On screen | What it really does |
|---|---|
| Listing media files | Walks through the folder and keeps the photos, RAW files and videos, recognised by their extension ([the list](06-file-types.md)). The total is not known yet: a running count replaces the bar. |
| Checking that files can be read | Finds broken files: empty ones (0 bytes), images and RAW files that cannot be decoded (each one is decoded in full), videos that cannot be opened. |
| Comparing files of equal size | Two files can only be identical if they have the same size. For those, reads their first and last 64 KB: quick, and it rules most of them out. |
| Proving identity (full SHA-256) | Reads the remaining candidates in full and computes their SHA-256 fingerprint: same fingerprint, same content, byte for byte. The longest step with large videos. |

On a large library, the first audit can take a long while: the [next step](02-keep-the-cache.md)
makes the following ones much faster.

## Read the result

Here is what an audit of `C:\Photos` prints (a demo library, whose pictures are drawn by a
program):

<!-- capture: audit-photos.txt -->
```text
──────────────────────────────────── Audit ─────────────────────────────────────
Audit summary
┌──────────────────────────────────────────────────────┬────────┐
│ Media files scanned                                  │     59 │
│ Groups of identical files                            │      8 │
│ Extra copies that can be deleted                     │     12 │
│ Space that can be freed                              │ 3.4 MB │
│ Broken files (empty or unreadable)                   │      0 │
│ Near duplicates (moved only with --tier near)        │      1 │
│ Burst series (moved only if set aside with 'review') │      3 │
│ Duration                                             │    1 s │
└──────────────────────────────────────────────────────┴────────┘

Inventory
┌───────────────────────────────────────┬──────────────────┐
│ Photos with a shooting date           │   57 of 58 (98%) │
│ Videos with a date in their tags      │      0 of 1 (0%) │
│ Photos and videos with a GPS position │     0 of 59 (0%) │
│ Photo formats                         │ JPEG 55 · HEIF 3 │
│ Total length of the videos            │              8 s │
└───────────────────────────────────────┴──────────────────┘

Folders sharing identical files
• 8 files are both in C:\Photos\2019\Seaside holidays (kept) and in
  C:\Photos\Old phone (deleted), 2.2 MB freed. C:\Photos\Old phone holds nothing
  else: it is entirely a copy of C:\Photos\2019\Seaside holidays.
• 3 files are both in C:\Photos\2019\Seaside holidays (kept) and in
  C:\Photos\2019\New folder (deleted), 864.7 KB freed. C:\Photos\2019\New folder
  holds nothing else: it is entirely a copy of C:\Photos\2019\Seaside holidays.
• 1 file is present several times in C:\Photos\2019\Seaside holidays: one copy
  is kept (287.5 KB freed).

💡 Add -v "<a folder of yours>:/reports" to get HTML reports.
💡 Run 'clean' (same -v options, without :ro) to free 3.4 MB.
💡 Second opinion: run Czkawka, an independent duplicate finder, on the same
folders, then 'media-hygiene crosscheck' (same -v options):
docker run --rm -v "C:\Photos:/data/c/Photos:ro" … -C /out/czkawka.json
💡 Choose which folders keep their copies: folders.preferred in config.toml, or
--prefer.
💡 Near duplicates and bursts are in the HTML report; 'clean --tier near' moves
near duplicates to the quarantine.
💡 Sort the burst series with the keyboard: 'media-hygiene review' (add -p
127.0.0.1::8080 to docker run).
💡 Add -v media-hygiene-cache:/cache: the next audits will be much faster.
```

The table first:

| Line | What it means |
|---|---|
| Media files scanned | Every photo, RAW file and video found. Sidecars (`.xmp`, …) are not counted. |
| Groups of identical files | How many distinct photos or videos exist in several identical copies. |
| Extra copies that can be deleted | The files a clean would delete. For every photo present several times, one copy is kept and the others are extra: a photo stored in 3 folders gives 2 extra copies. |
| Space that can be freed | The total size of those extra copies. |
| Broken files | Empty files (0 bytes) and files that cannot be opened (truncated JPEG, damaged video). |
| Orphan sidecars | Only when there are some: [sidecar files](reference-sidecars.md) left without their photo. |
| Near duplicates | The same photo saved again: resized, recompressed. Not identical files, left alone unless you ask ([step 11](11-near-duplicates.md)). |
| Burst series | Shots taken seconds apart. Never touched unless you choose ([step 10](10-review-bursts.md)). |
| Duration | How long the whole audit took. |

Then the *Inventory*: what your photos and videos say about themselves. How many photos have a
shooting date (written by the camera), how many videos carry a date in their tags, how many files
hold a GPS position, the formats of the photos and the total length of the videos. Nothing is
judged there: these are facts the files hold, counted for you.

Then *Folders sharing identical files*: each sentence is a pair of folders holding the same
files. The copies in the first folder are **kept**, those in the second one would be
**deleted**, and the space it frees comes last. The pairs freeing the most space come first.

- *"… holds nothing else: it is entirely a copy of …"*: the second folder only holds copies of
  files kept elsewhere. The most reassuring case: that folder is a plain copy.
- *"… is present several times in …: one copy is kept"*: the same file twice in one folder,
  such as `IMG_0101.jpg` and `IMG_0101 (1).jpg`.

Not the folder you want to keep? [Step 5](05-choose-the-kept-copy.md) shows how to choose.

Last come the 💡 tips. They suggest what to add next, and the next steps of this guide follow
them one by one.

> 🔒 Nothing has changed in `C:\Photos`: an audit never writes, and `:ro` made sure of it.

---

[Documentation](README.md) · Next: **[2. Keep the cache](02-keep-the-cache.md)** →
