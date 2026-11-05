# `upkeep`: the regular chores in one go

[Documentation](../README.md) › [Commands](../reference-commands.md) › `upkeep` · 🇫🇷 [Français](../../fr/commands/upkeep.md)

## In short

**One click, or one command, for what you do every few weeks.**

`upkeep` runs the steps listed in `[routine]` of `config.toml`, in this order: `audit` (reads the
library again, only what changed), `copies` (`clean`: the exact copies to the quarantine, after its
question; `mh undo` puts them back), `reports` (the list refreshed); `purge` (the quarantine runs
older than `purge_hint_days`, after the question of `purge` for each) runs only if you add it to
`steps`, otherwise run [`purge`](purge.md) on its own. It ends on one 👉 line:
what still waits for you. On the [home page](home.md): *Run the regular upkeep*, in Clean up.

## At a glance

| | |
|---|---|
| Your photos | ⚠️ `copies` moves files to the quarantine, `purge` erases old quarantine runs: each asks first. |
| Needs | The same `-v` options as `clean` (or `mh upkeep`). |
| Writes | What each step writes. |
| Undo | `mh undo` for the copies; **none** after a purge. |
| With `mh` | `mh upkeep`. |

## Run it

```powershell
mh upkeep
```

To switch a step off, remove it from the list:

```toml
[routine]
steps = ["audit", "copies", "reports"]
```

A step that fails stops the chain; what came before stays done.

## Good to know

Before each step that changes files, a line gives its count and the page that shows them:
*Next, 'clean' sets about 12 copies aside: the report shows them first*, *Next, 'purge' erases 41
files for good: 'mh undo --pick' shows them as photos first*. Going straight on stays one key: the
step's own question.

Answering *no* to a question skips that step only.

## Go further

- [`clean`](clean.md), [`purge`](purge.md), [`audit`](audit.md)

## The built-in help

<details>
<summary><code>upkeep --help</code></summary>

<!-- capture: help-upkeep.txt -->
```text
 Usage: media-hygiene upkeep [OPTIONS]

 Run the regular chores in one go, as listed in config.toml: audit, copies set
 aside, old quarantine purged, reports; each asks as usual.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help  -h        Show this message and exit.                                │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>
