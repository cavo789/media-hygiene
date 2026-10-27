# `history`: what each run did

[Documentation](../README.md) › [Commands](../reference-commands.md) › `history` · 🇫🇷 [Français](../../fr/commands/history.md)

## In short

**See what each run did, and find the name to give to `undo` or `purge`.**

`history` reads the [journal](../reference-glossary.md#journal) and lists the runs, the newest first: the command that made each
one, what it deleted, freed, moved and set aside, and how many files were restored since.

**When**: after a `clean`, a `sort`, an `album` or an `xmp --apply`, before an `undo` or a
`purge`.

**Try it**:

```powershell
docker run --rm -it -v "$HOME\media-hygiene\journal:/journal" cavo789/media-hygiene history
```

## At a glance

| | |
|---|---|
| Your photos | 🔒 Never changed: it only reads the journal. |
| Needs | `/journal`, the folder `clean` writes to. |
| Writes | Nothing. |
| Undo | Nothing to undo. |
| With `mh` | `mh history`; from the home page, *History and undo* › **See what each run did** shows the same table in the page itself (nothing is printed in the terminal), with the `mh undo <run>` line to copy for each run. |

## Run it

```powershell
docker run --rm -it -v "$HOME\media-hygiene\journal:/journal" cavo789/media-hygiene history
```

No photo folder is needed. Without `/journal`, it says *No journal mount: no history to show*.

## Read the table

| Column | What it means |
|---|---|
| Run | The name of the run, its date and time (`20261011-100607`): what `undo` and `purge` take. |
| Command | `clean`, `sort`, `album`, `xmp`… |
| Deleted, Freed | The files deleted (empty files, `--delete`) and the space they freed. |
| Quarantined | The files moved to the quarantine: their space is freed by `purge`. |
| Moved, Linked, Sidecars | Shown once a run has moved files to another of your folders (`sort`), made links (`album`) or written sidecars (`xmp`). |
| Folders removed | Shown once a run removed the folders it left empty (`clean`, `sort`); `undo` recreates them. |
| Restored | How many files `undo` brought back since. |

For example, after a clean, its undo, then a new clean:

```text
Runs (newest first)
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Run             ┃ Command ┃ Deleted ┃ Freed ┃ Quarantined ┃ Restored ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ 20261011-100607 │ clean   │       1 │     0 │          41 │        0 │
│ 20261011-100601 │ clean   │       1 │     0 │          35 │       36 │
└─────────────────┴─────────┴─────────┴───────┴─────────────┴──────────┘
```

## Good to know

- `history` has no option.
- The journal is small and makes `undo` possible: never delete it while you might still restore a
  run.
- [`status`](status.md) gives a shorter view: what is still undoable, and the next step.

## Go further

- [9. Undo, history, purge](../clean/09-undo-history-purge.md#see-what-was-done-history)
- Next: [`undo`](undo.md) a run, [`purge`](purge.md) its quarantine.

## The built-in help

<details>
<summary><code>history --help</code></summary>

<!-- capture: help-history.txt -->
```text
 Usage: media-hygiene history [OPTIONS]

 🔒 Read-only: never changes your photos. List the runs and what they did.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help  -h        Show this message and exit.                                │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [All commands](../reference-commands.md) · [Documentation](../README.md)
