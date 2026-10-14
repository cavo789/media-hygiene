# Clean in short: the whole path

[Documentation](../README.md) › Clean in short · 🇫🇷 [Français](../../fr/clean/quick-guide.md)

Everything the tool can do to clean, in order, one step at a time, ready to paste into
**PowerShell**. Each step takes a few lines and links to its detailed page, should you want to
understand. At the bottom, you have seen it all: [the last section](#you-have-seen-it-all) lists
each command and the step that shows it. Replace `C:\Photos` with your folder (or add more:
[several folders and disks](../start/03-several-folders.md)).

No hurry: you can stop after any step, skip the ones marked *optional*, and everything `clean`
does can be undone until `purge`. Back after a few days? `mh status` says where you are and what
comes next. No command of this path needs an AI: Docker is enough.

## 0. Once: write the `mh` command

```powershell
mkdir -Force "$HOME\media-hygiene"
docker run --rm `
  -e TZ=Europe/Brussels `
  -v "C:\Photos:/data/c/Photos" `
  cavo789/media-hygiene launcher > "$HOME\media-hygiene\mh.ps1"
. "$HOME\media-hygiene\mh.ps1"
```

This is the only long command: it writes `mh`, a short command that remembers your folders and
mounts, for each step, exactly what it needs (in your local time, thanks to `-e TZ=…`: put your
own zone if it is not `Europe/Brussels`). Its folders, in `$HOME\media-hygiene`, are created
by `mh` itself the first time:

| Folder | What it receives |
|---|---|
| `reports` | The HTML reports, to open in your browser. |
| `config` | `config.toml`, your settings. |
| `journal` | The journal of each clean: what makes `undo` possible. |
| `quarantine` | The files set aside, until you erase them. |

In a new terminal, load `mh` again with the last line above. To have `mh` in every terminal,
write that line into your PowerShell profile, once:

```powershell
New-Item -ItemType Directory -Force (Split-Path $PROFILE) | Out-Null
Add-Content $PROFILE '. "$HOME\media-hygiene\mh.ps1"'
```

PowerShell refuses to load it? See [write your folders once](../start/03-several-folders.md#write-your-folders-once-mh).
One more folder later? Run the command above again with one more `-v`.

## 1. Audit

```powershell
mh audit
```

Nothing is modified: `mh` mounts your folders read-only (`:ro`) for every command that does not
change them. The first audit reads everything; thanks to the cache, the next ones take seconds.
The console sums up what it found: duplicate copies, the space they take, broken files. Details:
[your first audit](../start/01-first-audit.md), [keep the cache](../start/02-keep-the-cache.md).

## 2. Read the report

At the end of the audit, Ctrl+click the path of `report.html` (or open `index.html` in
`$HOME\media-hygiene\reports`: it lists every report). Read it in this order:

1. **The folder pairs**: for each one, which folder keeps its copies. This is the quickest
   check.
2. **The groups of identical files**: each copy, and why that one stays.
3. **Broken files and orphan sidecars**: an unreadable photo, an `.xmp` or `.aae` whose photo is
   gone ([sidecar files](../reference-sidecars.md)); `clean` sets them aside too.
4. **Near duplicates and burst series**: nothing is done with them yet, they come at steps 9 and
   10.

Each file, with what will happen to it, is also in `plan.csv`, next to the report, to open in
Excel. Details: [the HTML report](04-html-report.md).

## 3. Choose which copy stays

The tool chooses the kept copy of each group by itself (a folder you named rather than a `DCIM`,
the original rather than `IMG_0001 (1).jpg`, the oldest…). You disagree for **a whole folder**?
Say so after `audit`, then read the report again:

```powershell
mh audit --prefer "C:\Photos\Family"
```

| Option | The folder… |
|---|---|
| `--prefer "C:\Photos\Family"` | keeps its copies first. |
| `--protect "C:\Photos\Family"` | is **never** modified and always keeps the copy: identical copies elsewhere go. |
| `--exclude "D:\Backup"` | is not analysed at all: a real backup is not a duplicate. |
| `--exclude-name "Thumbnails,*.lrdata"` | is ignored by its name, on every disk (thumbnails, catalogues). |

Each option can be repeated. Give the same ones to `mh clean` (step 7), or write them down once
and for all (step 5). Details: [choose which copy stays](05-choose-the-kept-copy.md).

You disagree with **a single pair**? In the report, the *Your decision* list of that pair offers
*Swap the folders* or *Leave alone*. Then click **Download decisions.json** and save the file in
`$HOME\media-hygiene\reports`, next to `index.html`: `mh clean --decisions` applies it at step 7.
Details: [decide pair by pair](12-decide-pair-by-pair.md).

## 4. Only some file types (optional)

By default, the audit looks at photos, RAW images and videos. `--ext` narrows the analysis to a
few types, or widens it to other files:

```powershell
mh audit --ext heic,video
```

`--ext video` looks at the videos only; `--ext pdf` also looks for duplicate PDFs. Your own lists
of types are named in `[scan.categories]` of `config.toml`. Details: [only some file
types](06-file-types.md).

## 5. Write your choices down once (optional)

Rather than repeating `--prefer`, `--protect`, `--exclude` with every command, write them in
`config.toml`. The first time, `config` creates a commented file:

```powershell
mh config
notepad "$HOME\media-hygiene\config\config.toml"
```

The settings most people change, Windows paths between **single quotes**:

```toml
[folders]
preferred = ['C:\Photos\Family']
protected = []
excluded = ['D:\Backup']
```

Each setting is explained in the file itself. Run `mh config` again: it shows each setting, where
it comes from (the file, an environment variable, the command line, which one wins) and the state
of each mounted folder. Details: [the configuration file](07-configuration-file.md).

## 6. A second opinion, before cleaning (optional)

Before setting family photos aside, you want independent proof? Czkawka, another open-source
duplicate finder, can check the same folders:

```powershell
mh crosscheck
```

Czkawka ships in the image: `crosscheck` runs it on your folders (a few minutes on a large
collection the first time), then compares both results group by group and says where they
differ. Details: [a second opinion](13-second-opinion.md).

## 7. Set the exact duplicates aside

```powershell
mh clean
```

For `clean`, `mh` mounts your folders writable (`clean` moves files) and adds the journal and the
quarantine. `clean` audits again, says what it will do and asks for confirmation: answer `y`. The
extra copies, the unreadable files and the orphan sidecars go to the quarantine, never over
another file; each copy is first compared byte by byte with the one that stays. A clean report
says what happened to each file.

- You downloaded `decisions.json` at step 3? `mh clean --decisions`.
- Need the space at once? `mh clean --delete` deletes the copies instead of moving them; `undo`
  can still rebuild them from the kept copy. Keep it for when you trust the tool.

Details: [clean](08-clean.md), [how your photos stay safe](../reference-safety.md).

## 8. Check, see what was done, undo

```powershell
explorer "$HOME\media-hygiene\quarantine"
mh history
```

The quarantine mirrors your folders, under one folder per clean. `history` lists each run: its
command, the files set aside or deleted, the space freed, what was restored. You change your
mind?

```powershell
mh undo
```

Everything goes back to its place. `mh undo <run>` undoes an older run, by the name `history`
gives it. Details: [undo, history, purge](09-undo-history-purge.md).

## 9. Near duplicates (optional)

Shrunk or recompressed copies (WhatsApp, e-mail…) and re-encoded videos are not identical to the
original: look at them first in the report of step 2, sections *Near duplicates* and *Re-encoded
videos*. Then:

```powershell
mh clean --tier near
```

`--tier near` moves the **sure** groups only (same picture and sound, identical fingerprints, a
smaller copy in a messaging folder) and says how many groups to check stay in place: decide them
one at a time in your browser with `mh review --near`, then `mh clean --tier near --decisions`;
or `--tier near-all` moves them all. The highest resolution stays, everything goes to the
quarantine: `undo` if a group does not suit you. Details: [near duplicates](11-near-duplicates.md).

## 10. Bursts (optional)

Series of photos taken seconds apart: you choose which ones to keep, in your browser.

```powershell
mh review
```

Open the address it prints, `http://127.0.0.1:8088/`, in your browser (Ctrl+click) and sort
with the keyboard; the obvious series are all accepted in one click. Each choice is saved at once
in `decisions.json`, in your reports folder; **Ctrl+C** stops, the next `review` resumes where
you were. Then `--decisions` moves the discarded photos to the quarantine:

```powershell
mh clean --decisions
```

The same `decisions.json` also keeps your folder pairs (step 3) and your near duplicates
(step 9): a single `mh clean --tier near --decisions` applies all three. Details: [sort burst
series in your browser](10-review-bursts.md).

## 11. Free the space, for good

So far, nothing is erased: the quarantine still takes the space. Once you have checked:

```powershell
mh purge
```

It asks for confirmation. `mh purge <run>` empties the quarantine of that run only. After
`purge`, `undo` can no longer bring these files back.

## 12. Check the result, and come back later

`mh audit` again: it should say *Nothing to clean*. Its remaining near duplicates and bursts are
the ones you chose to keep.

In the weeks that follow:

- **Where am I?** `mh status` says, in a second and without analysing anything, the last audit,
  what is in the quarantine and since when, what `undo` can still restore, the decisions not yet
  applied, then the next step as a full command.
- **New photos?** Start again at step 1: thanks to the cache, only the new ones are read.
- **Too many reports?** `mh reports --prune 10` keeps the ten most recent and rebuilds
  `index.html`.

Details: [where am I?](09-undo-history-purge.md#where-am-i-status), [list and tidy the
reports](04-html-report.md#list-and-tidy-the-reports).

## You have seen it all

Each command of the clean, and the step of this page that shows it:

| Command | Step | What it does |
|---|---|---|
| [`launcher`](../commands/launcher.md) | 0 | Writes `mh`, which remembers your folders. |
| [`audit`](../commands/audit.md) | 1 to 4 | Finds duplicates and broken files, without modifying anything; `--prefer`, `--protect`, `--exclude`, `--exclude-name`, `--ext`. |
| [`config`](../commands/config.md) | 5 | Creates `config.toml`, then shows each setting and where it comes from. |
| [`crosscheck`](../commands/crosscheck.md) | 6 | Compares the audit with Czkawka. |
| [`clean`](../commands/clean.md) | 7, 9, 10 | Sets aside copies, broken files, orphan sidecars; `--decisions`, `--tier near`, `--delete`. |
| [`history`](../commands/history.md) | 8 | Lists what each run did. |
| [`undo`](../commands/undo.md) | 8 | Puts each file of a run back in its place. |
| [`review`](../commands/review.md) | 9, 10 | Decides bursts and near duplicates in the browser. |
| [`purge`](../commands/purge.md) | 11 | Empties the quarantine: the space is freed. |
| [`status`](../commands/status.md) | 12 | Says where you are and the next step. |
| [`reports`](../commands/reports.md) | 12 | Lists the reports, deletes the old ones. |

The other commands file and find your photos: by year, event, place or person (`classify`,
`sort`, `places`, `people`), by a word ("Chloé in the mountains": `tags`, `search`), in albums or
in Excel (`album`, `xmp`, `inventory`). They have their own path: **[sort in
short](../sort/quick-guide.md)**. A word escapes you? [Words of this
guide](../reference-glossary.md). An error message? [Troubleshooting](../reference-troubleshooting.md).

<details>
<summary>Without <code>mh</code>: the full commands</summary>

Each `mh` command is a `docker run` with the same folders. For the ones that modify nothing
(`audit`, `config`, `crosscheck`, `history`, `status`, `reports`), read-only:

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene audit
```

For `clean`, `undo` and `purge`: `:ro` is gone, `/journal` and `/quarantine` are added; replace
`clean` with the command of the step:

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene clean
```

For `review`: the first command with `-p 127.0.0.1:8088:8088` after `-it`. Create the four
folders before the first run (`mkdir -Force "$HOME\media-hygiene\reports", …`): a folder Docker
creates by itself belongs to the administrator, and the tool could not write there.

</details>

---

[Documentation](../README.md) · Step by step: **[4. The HTML report](04-html-report.md)** →
