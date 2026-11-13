# `undo`: put a run back

[Documentation](../README.md) › [Commands](../reference-commands.md) › `undo` · 🇫🇷 [Français](../../fr/commands/undo.md)

## In short

**Changed your mind? Put back every file of a run, exactly where it was.**

`undo` restores every file of a run, as the [journal](../reference-glossary.md#journal) recorded it: the files of a `clean` come
back from the [quarantine](../reference-glossary.md#quarantine) (or are rebuilt from the copy kept), the files of a `sort` go back to
their folders, the links of an `album` and the sidecars of `xmp` are taken away.

**When**: after a `clean`, a `sort`, an `album` or an `xmp --apply` you regret: a photo you
wanted is in the quarantine, say. Before any `purge` of that run.

**Try it**:

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene undo
```

## At a glance

| | |
|---|---|
| Your photos | ✋ Acts: moves files back where they were, never over another file. |
| Needs | `/journal`, your folders **without** `:ro`, and `/quarantine` when the run moved files there. |
| Recommended | The same `-v` options as the run you undo. |
| Writes | Each restore, in the journal of the run (`history` counts them). |
| Undo | To do it again, run the command again ([`clean`](clean.md), [`sort`](sort.md)…). |
| With `mh` | `mh undo`, `mh undo <run>`. |

## Run it

The same command as the run, with `undo` as the last word:

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v "D:\Old disk:/data/d/Old disk" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene undo
```

Without a name, `undo` restores the **latest** run; `undo <run>` restores that one. The names of
the runs come from [`history`](history.md), [`status`](status.md) and the last lines of each run.

## What it does, run by run

| Run | What `undo` does |
|---|---|
| `clean` | Each quarantined file moves back to its place; each copy deleted (`--delete`) or empty file is rebuilt from the copy kept, date included. Each copy made a link (a pair keeping both names) becomes an independent file again, its date back. The quarantine folders it leaves empty go. |
| `sort` | The files move back, the folders the sort removed come back, those it created go. A sort run again after an interruption is undone **whole**, newest first, after one question. |
| `album` | Its links, its `.media-hygiene-album` file and its folders go; the originals are not touched. |
| `xmp` | The sidecars it created go; those it completed are put back byte for byte. |

## Put back a few photos

`mh undo --pick` opens the quarantine in the browser, as tiles: every file the runs set aside and
still there (each drive's quarantine), grouped by run, newest first. Pick photos as on every page
of tiles: a click picks one, Ctrl+click adds or takes out one, Shift+click every file from the
last one clicked, a drag draws a rectangle, Ctrl+A picks every file shown, I inverts the
picking, Enter or a double click shows a photo large. **↩ Restore the picked files** puts them
back where they were: a partial undo of their runs, journaled, with the same guards as `undo` (a
drive whose quarantine is not mounted is refused). The page then shows the quarantine as read
again from the disk; `mh undo <run>` later still brings back the rest of the run. Each run of the
*Runs* list says how many of its files exist nowhere else (*3 nowhere else*: near duplicates,
burst shots, junk, not exact copies), counted from the index, and the status line the total;
without an index, no figure.

```powershell
mh undo --pick
```

## Options

| Option | What it does |
|---|---|
| `RUN` | The run to undo (see `history`); the latest one by default. For a sort, every run of the same workbook. |
| `--yes`, `-y` | Do not ask before undoing several runs of a sort. |
| `--pick` | Open the quarantine as tiles and put back only the photos picked ([above](#put-back-a-few-photos)). |
| `--port` | The port of that page (default: `[review] port`). |
| `--from-quarantine` | The run's journal is lost: rebuild its moves from the layout of its quarantine, list them, ask, then bring each file back, never over a file. The copies a `clean --delete` erased cannot come back this way. |

## Good to know

- **Never over another file, never a guess**: a file that is back already, or whose copy is gone,
  is left alone and listed with the reason.
- **The reason in plain words**: "not allowed (the owner or the permissions of the file)", "the
  disk is full"... When many files fail for the same reason, the first five are named, then one
  line says how many more (`... and 3,980 more: <reason>`); `--verbosity debug` lists every
  file with the system's own error.
- `undo` checks the mounts **before** changing anything: without the same `/journal`, with
  folders mounted `:ro`, or without the `/quarantine` the run used, it refuses and names the run.
- An album link whose original was deleted or moved since may be the last copy of the photo:
  `undo` keeps it and says so. A sidecar edited since `xmp` wrote it is kept as well.
- A copy made a link that is no link any more (saved since through a new file), or whose kept
  file is gone, is left as it is: `undo` says why.
- After a [`purge`](purge.md), the files of that quarantine can no longer come back.

## Go further

- [9. Undo, history, purge](../clean/09-undo-history-purge.md#undo-a-clean-undo)
- [Sorting, step 7: change your mind](../sort/07-sort.md#change-your-mind),
  [sorting, step 12: undo an album](../sort/12-albums.md#undo-it)
- [How your photos stay safe](../reference-safety.md)

## The built-in help

<details>
<summary><code>undo --help</code></summary>

<!-- capture: help-undo.txt -->
```text
 Usage: media-hygiene undo [OPTIONS] [run_id]

 Restore every file of a run, from the kept copy, the quarantine or where it
 was moved; remove the links of an album.

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│   run_id      <str>  Run to undo (see 'history'); the latest one by default. │
│                      For a sort, every run of the same workbook.             │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --yes   -y                          Do not ask for confirmation before       │
│                                     undoing several runs of a sort           │
│                                     (overrides sort.confirm).                │
│ --pick                              Open the quarantine in the browser, as   │
│                                     tiles, and put back only the photos you  │
│                                     pick; 'undo' of their run still brings   │
│                                     back the rest.                           │
│ --port          <int range> [x>=1]  Port of the page. docker run publishes   │
│                                     it under the same number on your         │
│                                     computer: -p 127.0.0.1:9000:9000 for     │
│                                     --port 9000. Default:  port in           │
│                                     config.toml, 8088.                       │
│ --help  -h                          Show this message and exit.              │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Advanced: folders (override folders.* of config.toml) ──────────────────────╮
│ --backup        <str>  A backup or an old disk, mounted read-only: never     │
│                        changed, and not refused for being read-only (mh      │
│                        passes your backups). Repeatable.                     │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [All commands](../reference-commands.md) · [Documentation](../README.md)
