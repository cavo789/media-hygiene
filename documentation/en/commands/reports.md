# `reports`: list and tidy the HTML reports

[Documentation](../README.md) › [Commands](../reference-commands.md) › `reports` · 🇫🇷 [Français](../../fr/commands/reports.md)

## In short

**Find every report again from one page, and delete the old ones in one command.**

Every audit, clean and crosscheck writes its own report folder in `/reports`. `reports` lists
them, newest first, and refreshes `index.html`, the page that links them all. With `--prune`, it
keeps the most recent ones and deletes the others.

**When**: to find an older report, or when the reports folder grows too large.

**Try it**:

```powershell
docker run --rm -it -v "$HOME\media-hygiene\reports:/reports" cavo789/media-hygiene reports
```

## At a glance

| | |
|---|---|
| Your photos | 🔒 Never changed: only the reports folder is read (and, with `--prune`, tidied). |
| Needs | `/reports`, the folder of your reports. |
| Writes | `index.html`; `--prune` deletes old report folders. |
| Undo | A pruned report is gone; run the audit again to get a new one. |
| With `mh` | `mh reports`, `mh reports --prune 10`. |

## Run it

```powershell
docker run --rm -it -v "$HOME\media-hygiene\reports:/reports" cavo789/media-hygiene reports
```

No photo folder is needed. Then open `index.html` in that folder with a double-click: each line is
a run, its date opens its report.

## Options

| Option | What it does |
|---|---|
| `--prune N` | Keep the N most recent reports, delete the others. |

## Good to know

- Each run folder is named after its date and kind (`20261003-180936-audit`) and holds
  `report.html`, its previews and `plan.csv`.
- `--prune` deletes only the report folders the tool wrote (named like `20261003-180936-audit`,
  holding their `summary.json`): never a photo, nor the `decisions.json` you are working on, nor
  the folders of `classify`, `sort` and `inventory`.
- Without `/reports` mounted, there is nothing to list: the commands then show their results on
  screen only.

## Go further

- [4. The HTML report](../clean/04-html-report.md#list-and-tidy-the-reports)
- [Mount points](../reference-mount-points.md)

## The built-in help

<details>
<summary><code>reports --help</code></summary>

<!-- capture: help-reports.txt -->
```text
 Usage: media-hygiene reports [OPTIONS]

 🔒 Read-only: never changes your photos. List the HTML reports of previous
 audits and cleans.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --prune          <int range> [x>=0]  Delete all reports but the N most       │
│                                      recent ones.                            │
│ --help   -h                          Show this message and exit.             │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [All commands](../reference-commands.md) · [Documentation](../README.md)
