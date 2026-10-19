# 1. Your first audit

[Documentation](../README.md) › Start, step 1 of 3 · 🇫🇷 [Français](../../fr/start/01-first-audit.md)

In this first step, you write `mh`, a short command that remembers your folder, then you ask it
to look at that folder of photos and to tell you what it finds. Nothing is changed: an audit
only reads, and `mh` gives it your folder read-only (`:ro`): the system itself forbids any
change ([how your photos stay safe](../reference-safety.md)).

## What you need

- Docker installed and running: [step 0](00-install-docker.md) shows how, on Windows or Linux.
- A folder of photos and videos, here `C:\Photos`.
- A PowerShell window (Start menu, type *PowerShell*). WSL or Linux? See the box at the end of
  this section.

## Write `mh`, once

**First**, let PowerShell run the scripts written on your computer, `mh` included: Windows
forbids it by default (*running scripts is disabled on this system*). For your account only; the
scripts downloaded from the internet must still be signed:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned -Force
```

**Then** write `mh`, with your folder instead of `C:\Photos`, as Explorer shows it:

```powershell
New-Item -ItemType Directory -Force "$HOME\media-hygiene", (Split-Path $PROFILE) | Out-Null
docker run --rm cavo789/media-hygiene launcher --photos "C:\Photos" > "$HOME\media-hygiene\mh.ps1"
Add-Content $PROFILE '. "$HOME\media-hygiene\mh.ps1"'
. "$HOME\media-hygiene\mh.ps1"
```

The first run downloads the tool (a few hundred MB); the next ones start at once.

| Line | What it does |
|---|---|
| `New-Item …` | Creates `$HOME\media-hygiene` (the tool's own folders go there) and the folder of your PowerShell profile. |
| `docker run … launcher --photos "C:\Photos"` | Asks the tool to write `mh` for that folder, into `mh.ps1`. No `-it`: what it prints goes into the file. |
| `Add-Content $PROFILE …` | Every new PowerShell window knows `mh`, tomorrow too. |
| `. "…\mh.ps1"` | Loads `mh` in this window. |

This is the only long command of the guide. Several folders, a USB disk? [Step
3](03-several-folders.md) adds them with `mh folders add`. **Rather click than type?**
`mh shortcut` puts a *Media Hygiene* icon on your Desktop: a double-click opens the home page.

## Run the audit

```powershell
mh audit
```

`mh` alone opens the [home page](../commands/home.md) in your browser: it proposes the next step,
and its button runs it in the PowerShell window (`mh menu`: the same steps in the terminal).
`mh audit` runs it directly. Behind it, `mh`
types the `docker run` for you: your folder read-only, the cache, the folders of the reports, the
configuration, the journal and the quarantine in `$HOME\media-hygiene` (created when missing),
and your time zone, asked from Windows at each run.

> 💡 Photos in OneDrive (often *Pictures* on Windows 11)? `mh` says first how many are in the cloud
> only, since reading them downloads them, and asks before going on
> ([OneDrive "Files On-Demand"](../reference-troubleshooting.md#onedrive-files-on-demand)).

> 💡 The tool speaks English. For French, write `mh` with `--locale fr` right after
> `cavo789/media-hygiene` in the `launcher` line: `cavo789/media-hygiene --locale fr launcher …`.

??? note "Without `mh`: one `docker run` (WSL, Linux, or just to try)"

    The same audit as a single Docker command, nothing to install but Docker:

    ```powershell
    docker run --rm -it -v "C:\Photos:/data/c/Photos:ro" cavo789/media-hygiene audit
    ```

    | Part | What it means |
    |---|---|
    | `docker run` | Starts the tool in a container, a small isolated box. |
    | `--rm` | Deletes that box once the tool ends: nothing is left behind. |
    | `-it` | Connects the box to your window: colours, progress bars, and questions you can answer. |
    | `-v "C:\Photos:/data/c/Photos:ro"` | Lets the tool see your folder. The box only sees what you give it with `-v`: here `C:\Photos`, which it calls `/data/c/Photos`. |
    | `:ro` | *Read-only*: Docker itself forbids any change to your folder. |
    | `cavo789/media-hygiene` | The tool, as published on Docker Hub. |
    | `audit` | What to do: look for duplicates and broken files. |

    In a WSL terminal, the same folder is `/mnt/c/Photos`; on Linux, see [step 0](00-install-docker.md#your-first-command-on-linux).
    `mh` exists for bash too: `launcher --shell bash --photos /mnt/c/Photos > ~/media-hygiene/mh.sh`,
    then `source ~/media-hygiene/mh.sh` ([`launcher`](../commands/launcher.md)). Without `mh`,
    each command of the guides needs its own mounts: the [next step](02-keep-the-cache.md) and
    [step 3](03-several-folders.md) show them.

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
| Listing media files | Walks through the folder and keeps the photos, RAW files and videos, recognised by their extension ([the list](../clean/06-file-types.md)). The total is not known yet: a running count replaces the bar. |
| Checking that files can be read | Finds broken files: empty ones (0 bytes), images and RAW files that cannot be decoded (each one is decoded in full), videos that cannot be opened. |
| Fingerprinting videos | Once per video, kept in the cache: decodes a few frames and fingerprints them, to find [re-encoded copies](../clean/11-near-duplicates.md#videos-too-re-encoded-copies). |
| Comparing files of equal size | Two files can only be identical if they have the same size. For those, reads their first and last 64 KB: quick, and it rules most of them out. |
| Proving identity (full SHA-256) | Reads the remaining candidates in full and computes their SHA-256 fingerprint: same fingerprint, same content, byte for byte. The longest step with large videos. |

### How long the first audit takes

The first audit decodes every photo once: on a large library, and through Docker on Windows,
that takes minutes, sometimes hours. When more than 500 files are to be checked, the tool times
its first 20 seconds, then says once how long the rest will take, rounded up:

```text
⏳ 23,412 photos and 318 videos to check for the first time: about 45 min. You can stop at any
time (Ctrl+C): what is checked is kept, and the next audit takes seconds.
```

`mh` keeps the cache: the [next step](02-keep-the-cache.md) shows what it saves.

## Read the result

Here is what `mh audit` prints the first time on `C:\Photos` (a demo library, whose pictures
are drawn by a program):

<!-- capture: audit-mh.txt|re:^🔒| -->
```text
🔒 Read-only: your photos and videos are not touched.
──────────────────────────────────── Audit ─────────────────────────────────────
Audit summary
┌──────────────────────────────────────────────────────┬────────┐
│ Media files scanned                                  │     65 │
│ Groups of identical files                            │      8 │
│ Extra copies that can be set aside                   │     12 │
│ Space that can be freed                              │ 3.4 MB │
│ Broken files (empty or unreadable)                   │      0 │
│ Near duplicates (moved only with --tier near)        │      2 │
│ Re-encoded videos (moved only with --tier near)      │      1 │
│ Burst series (moved only if set aside with 'review') │      3 │
│ Duration                                             │    2 s │
└──────────────────────────────────────────────────────┴────────┘

Folders sharing identical files
• 8 files are both in C:\Photos\2019\Seaside holidays (kept) and in
  C:\Photos\Old phone (copies 'clean' moves to the quarantine), 2.3 MB to free
  with 'purge'. C:\Photos\Old phone holds nothing else: it is entirely a copy of
  C:\Photos\2019\Seaside holidays.
• 3 files are both in C:\Photos\2019\Seaside holidays (kept) and in
  C:\Photos\2019\New folder (copies 'clean' moves to the quarantine), 872.9 KB
  to free with 'purge'. C:\Photos\2019\New folder holds nothing else: it is
  entirely a copy of C:\Photos\2019\Seaside holidays.
• 1 file is present several times in C:\Photos\2019\Seaside holidays: one copy
  is kept (292.0 KB to free).

What you can do
✅ 12 identical copies, 3.4 MB: no risk, one command.
👀 3 groups of near duplicates: 1 sure, 2 to look at (~1 min in 'review
--near'); 'clean --tier near' moves the sure ones.
🎞️ 3 burst series: optional, ~2 min in 'review'; the series not reviewed are
kept whole.

✅ HTML report:
C:\Users\you\media-hygiene\reports\20261019-153448-audit\report.html
👉 What next: run 'clean' to set 3.4 MB of copies aside.
mh clean
💡 Type mh open: your browser shows every report.
💡 Choose which folders keep their copies: folders.preferred in config.toml, or
--prefer.
(3 more tips: add --verbosity verbose to see them.)
```

The table first (a word you do not know? [the words of this guide](../reference-glossary.md)):

| Line | What it means |
|---|---|
| Media files scanned | Every photo, RAW file and video found. Sidecars (`.xmp`, …) are not counted. |
| Groups of identical files | How many distinct photos or videos exist in several identical copies. |
| Extra copies that can be set aside | The files a clean would move to the quarantine (nothing is erased). For every photo present several times, one copy is kept and the others are extra: a photo stored in 3 folders gives 2 extra copies. |
| Space that can be freed | The total size of those extra copies. |
| Broken files | Empty files (0 bytes) and files that cannot be opened (truncated JPEG, damaged video). |
| Orphan sidecars | Only when there are some: [sidecar files](../reference-sidecars.md) left without their photo. |
| Near duplicates | The same photo saved again: resized, recompressed. Not identical files, left alone unless you ask ([cleaning, step 11](../clean/11-near-duplicates.md)). |
| Burst series | Shots taken seconds apart. Never touched unless you choose ([cleaning, step 10](../clean/10-review-bursts.md)). |
| Duration | How long the whole audit took. With `--verbosity verbose`, a line below the table splits it by step (*Time per step: listing 1.2 s · checks 3.4 s · …*), then the report says how long it took to write. |

With `--verbosity verbose` (a global option, before `audit`), the *Inventory* follows: what your
photos and videos say about themselves. How many photos have a shooting date (written by the
camera), how many videos carry a date in their tags, how many files hold a GPS position, the
formats of the photos and the total length of the videos. Nothing is judged there: these are
facts the files hold, counted for you. The [`inventory`](../reference-inventory.md) command
lists them file by file.

Then *Folders sharing identical files*: each sentence is a pair of folders holding the same
files. The copies in the first folder are **kept**; those in the second one are the copies
`clean` will move to the quarantine, and the space they take comes last. It is a forecast: the
audit has moved nothing. The pairs freeing the most space come first.

- *"… holds nothing else: it is entirely a copy of …"*: the second folder only holds copies of
  files kept elsewhere. The most reassuring case: that folder is a plain copy.
- *"… is present several times in …: one copy is kept"*: the same file twice in one folder,
  such as `IMG_0101.jpg` and `IMG_0101 (1).jpg`.

Not the folder you want to keep? [Cleaning, step 5](../clean/05-choose-the-kept-copy.md) shows how to choose.

Then *What you can do*: at most three lines, each with what it gains and what it costs you.

| Line | What it means |
|---|---|
| ✅ identical copies | No risk, one command: `clean` sets them aside, `undo` brings them back. |
| 👀 near duplicates | Groups to look at before moving them, with an estimate of the time it takes ([cleaning, step 11](../clean/11-near-duplicates.md)). |
| 🎞️ burst series | Optional: a series you do not review is kept whole ([cleaning, step 10](../clean/10-review-bursts.md)). |

The 👉 line gives the step that logically comes next, as the `mh` command to type: `mh clean`.
`mh` picks its mounts by itself: your folder without `:ro` for a command that changes it, the
journal and the quarantine. Run without `mh`, the same line gives the **full `docker run`**,
ready to paste, with those mounts written out.

Then at most two 💡 tips, the most useful first (`mh open` shows the HTML report of this audit
in your browser). Without `mh`, the options worth setting once (the cache, your time zone, a
reports folder) share a single ⚙️ line: `mh` sets them all for you. A last line says how many
tips were left out: add `--verbosity verbose` to see them all.

> 🔒 Nothing has changed in `C:\Photos`: an audit never writes, and the `:ro` `mh` gives it made
> sure of it.

---

← [0. Install Docker](00-install-docker.md) · [Documentation](../README.md) · Next: **[2. Keep the cache](02-keep-the-cache.md)** →
