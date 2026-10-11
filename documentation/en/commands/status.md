# `status`: where am I?

[Documentation](../README.md) › [Commands](../reference-commands.md) › `status` · 🇫🇷 [Français](../../fr/commands/status.md)

Back after a few days, you no longer remember which run is in the quarantine, nor whether a
review was applied? `status` reads the tool's own folders, without scanning your photos (about a
second), and tells you where you stand, then **one** next step, as a full command.

## At a glance

| | |
|---|---|
| Your photos | 🔒 Never changed, not even read: no scan. |
| Needs | Nothing; it reads what you mount. |
| Recommended | The same tool folders as for `clean`: `/reports`, `/journal`, `/quarantine`, `/cache`. |
| Writes | Nothing. |
| Undo | Nothing to undo. |
| With `mh` | `mh status`: every folder is mounted for you. |

## Run it

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene status
```

## What it says

Under the title *Where you are*:

- **the last audit or clean**: when, and what it found;
- **the quarantine**: how many files, how much space, since when;
- **the runs `undo` can still restore**, with the full `undo` command;
- **the burst series still to see** and the decisions of `review` not applied yet;
- **the last `classify` proposal**, and whether `sort` applied it;

then **one** next step, as a full command ready to paste. A quarantine older than 30 days is the
first thing it suggests to [`purge`](purge.md).

## Good to know

- `status` has no option.
- A folder not mounted is said, never an error: mount the one it names to learn more.
- The 30 days are `purge_hint_days`, in the `[clean]` section of `config.toml`.

## Go further

- [9. Undo, history, purge: Where am I?](../clean/09-undo-history-purge.md#where-am-i-status)
- [`history`](history.md): every run, in detail.

## The built-in help

<details>
<summary><code>status --help</code></summary>

<!-- capture: help-status.txt -->
```text
 Usage: media-hygiene status [OPTIONS]

 🔒 Read-only: never changes your photos. Where am I? The last audit, the
 quarantine, what is left: no scan.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help  -h        Show this message and exit.                                │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [All commands](../reference-commands.md) · [Documentation](../README.md)
