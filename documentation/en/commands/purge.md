# `purge`: empty the quarantine for good

[Documentation](../README.md) › [Commands](../reference-commands.md) › `purge` · 🇫🇷 [Français](../../fr/commands/purge.md)

`clean` never erases: it moves the extra copies to the quarantine. Their space comes back only
when you have checked them and run `purge`, which deletes the quarantine of a run, or of every
run, **for good**. It is the only command that erases content (with `clean --delete`, if you use
it), and it says so before asking.

## At a glance

| | |
|---|---|
| Your photos | ⚠️ Erases the files of the quarantine; your folders themselves are not touched. |
| Needs | `/quarantine`, writable. |
| Recommended | The same `-v` options as your `clean` (or `mh purge`). |
| Writes | Nothing: it deletes the quarantine folders. |
| Undo | **None**: after a purge, `undo` can no longer bring those files back. |
| With `mh` | `mh purge`, `mh purge <run>`. |

## When to use it

Once you have opened the quarantine folder in the Explorer and checked what it holds, and you
need the space. [`status`](status.md) reminds you of a quarantine older than 30 days.

## Run it

```powershell
docker run --rm -it `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene purge
```

It warns that the files cannot come back, gives how many files and how much space, then asks:
*Erase the quarantine of 20261011-100607 (41 files, 16.3 MB)? [y/N]*. With `y`: *✅ Quarantine
purged: 16.3 MB freed.*

## Options

| Option | What it does |
|---|---|
| `RUN` | Only the quarantine of this run (see [`history`](history.md)); every run by default. |
| `--yes`, `-y` | Do not ask. |

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
