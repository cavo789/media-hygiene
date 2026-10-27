# `purge`: empty the quarantine for good

[Documentation](../README.md) › [Commands](../reference-commands.md) › `purge` · 🇫🇷 [Français](../../fr/commands/purge.md)

## In short

**Get the space back for good, once you have checked what the quarantine holds.**

`clean` never erases: it moves the extra copies to the [quarantine](../reference-glossary.md#quarantine). `purge` deletes the
quarantine of a run, or of every run, **for good**. It is the only command that erases content
(with `clean --delete`, if you use it), and it says so before asking.

**When**: once you have opened the quarantine folder in the Explorer, checked what it holds, and
need the space; [`status`](status.md) reminds you of a quarantine older than 30 days.

**Try it**:

```powershell
docker run --rm -it -v "$HOME\media-hygiene\quarantine:/quarantine" cavo789/media-hygiene purge
```

## At a glance

| | |
|---|---|
| Your photos | ⚠️ Erases the files of the quarantine; your folders themselves are not touched. |
| Needs | `/quarantine`, writable. |
| Recommended | The same `-v` options as your `clean` (or `mh purge`). |
| Writes | Nothing: it deletes the quarantine folders. |
| Undo | **None**: after a purge, `undo` can no longer bring those files back. |
| With `mh` | `mh purge`, `mh purge <run>`. |

## Run it

```powershell
docker run --rm -it `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene purge
```

It warns that the files cannot come back, gives how many files and how much space, then asks:
*Erase the quarantine of 20261011-100607 (41 files, 16.4 MB)? [y/N]*. With `y`: *✅ Quarantine
purged: 16.4 MB freed.*

## Options

| Option | What it does |
|---|---|
| `RUN` | Only the quarantine of this run (see [`history`](history.md)); every run by default. |
| `--yes`, `-y` | Do not ask. |
| `--to FOLDER` | Copy the quarantine to `FOLDER` first, check every byte of the copy, and only then erase it. |

## Keep a copy elsewhere: `--to`

Rather than erasing, `purge --to` moves the quarantine off the PC: a NAS share, an external disk,
or a cloud's synced folder (OneDrive, Dropbox…), mounted in the container:

```powershell
docker run --rm -it `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  -v "\\NAS\archives_quarantaine:/archive" `
  cavo789/media-hygiene purge --to /archive
```

- Each run goes to `<folder>/<run>/<drive>/…` (`C` for the default quarantine, `D` for `D:`'s…):
  two quarantines never mix.
- The free space of the folder is checked first; one file missing, of another size or with other
  bytes, or changed during the copy, and that run is **not** erased.
- A cloud's synced folder proves the local copy only, not the upload: it is as safe as your sync.
- To get a run back: copy each `<drive>` folder of it back into that drive's quarantine
  (`<folder>/<run>/C` → `quarantine\<run>`), then run [`undo <run>`](undo.md).
- Without `--to` (and without `--yes`), `purge` reminds you of this option before its question.

## Good to know

- An empty quarantine says *The quarantine is empty* and does nothing.
- A run name without a quarantine is refused: *Run … has no quarantine*.
- The quarantine holds what `clean` moved (extra copies, unreadable files, orphan sidecars, near
  duplicates and burst shots you set aside) and what `sort` set aside (`Thumbs.db` and the like).
  The burst shots and near duplicates are **not** copies: once purged, nothing can rebuild them.

## Go further

- [9. Undo, history, purge](../clean/09-undo-history-purge.md#empty-the-quarantine-purge)
- [How your photos stay safe](../reference-safety.md#nothing-is-erased-unless-you-run-purge)

## The built-in help

<details>
<summary><code>purge --help</code></summary>

<!-- capture: help-purge.txt -->
```text
 Usage: media-hygiene purge [OPTIONS] [run_id]

 Erase the quarantine of a run for good: with 'clean --delete', the only way
 the tool removes content.

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│   run_id      <str>  Run whose quarantine is erased; every run by default.   │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --yes   -y        Do not ask for confirmation (overrides clean.confirm).     │
│ --help  -h        Show this message and exit.                                │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [All commands](../reference-commands.md) · [Documentation](../README.md)
