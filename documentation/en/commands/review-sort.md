# `review-sort`: name the events in your browser

[Documentation](../README.md) › [Commands](../reference-commands.md) › `review-sort` · 🇫🇷 [Français](../../fr/commands/review-sort.md)

## In short

**Name your events while looking at their photos, one event at a time, with the keyboard, rather
than in a spreadsheet.**

The [workbook](../reference-glossary.md#workbook) of [`classify`](classify.md) is good for renaming in bulk, not for *looking* at
photos. `review-sort` shows **one event at a time** in your browser, with its photos, its
proposal and a field to name it. Your choices are saved next to the proposal; [`sort`](sort.md)
applies them on top of the workbook.

**When**: optional, between `classify` and `sort`, when there are many events to name. The
workbook alone is enough, and both can be used together.

**Try it**:

```powershell
docker run --rm -it `
  -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene review-sort
```

## At a glance

| | |
|---|---|
| Your photos | 🔒 Never changed, nor the workbook: mount the photos `:ro`. |
| Needs | `/reports` (the `classify` run), your folders (to show the photos), and `-p 127.0.0.1:8088:8088`. |
| Writes | `sort-decisions.json`, next to `plan.json` in the folder of the `classify` run. |
| Undo | `Delete` in the page takes a choice back; the workbook then decides again. |
| With `mh` | `mh review-sort`: the port is published for you. |

## Run it

```powershell
docker run --rm -it -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene review-sort
```

It counts the events (*412 events to decide: 260 with a sure proposal (one click), 152 to look
at*), then prints the address of the page: Ctrl+click it. Ctrl+C stops it; the next run resumes.

## The main keys

| Key | What it does |
|---|---|
| `Enter` | Accept the name and category, then go to the next event still to decide. |
| `N` / `P` | Next or previous event, without deciding. `U`: next event still to decide. |
| `V` | Accept every sure proposal at once; `Shift`+`Z` takes that batch back. |
| `E` / `C` | Type in the name / the category field; `Esc` leaves it. |
| `Shift`+`S` | Leave the whole event where it is. |
| `Space`, `O`, `S` | Select photos, send them to another category, or leave them where they are. |
| `Delete` | Take back the choice made here. |
| `Z` | Enlarge the photo. |

## Options

| Option | What it does |
|---|---|
| `WORKBOOK` | The `classify` workbook; the latest `classify` run's by default. |
| `--port PORT` | Port of the page, 8088 by default; publish the same one. |

## Good to know

- **The workbook is never changed** (Excel may have it open). You may keep editing it: each
  choice of the page remembers what the workbook said when you made it.
- **A conflict is never settled silently**: if the workbook was changed since, on the same event
  or file, to something else, `sort` refuses and lists both values; the page shows them in red.
- **Run `classify` again**: your choices of the page are carried over to the yellow cells of the
  new workbook, like your edits.

## Go further

- [Sorting, step 11: name the events in your browser](../sort/11-name-events-in-the-browser.md)
- Next: [`sort`](sort.md).

## The built-in help

<details>
<summary><code>review-sort --help</code></summary>

<!-- capture: help-review-sort.txt -->
```text
 Usage: media-hygiene review-sort [OPTIONS] [workbook]

 🔒 Read-only: never changes your photos. Name the events of the classify
 proposal one by one in your browser.

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│   workbook      <str>  The classify workbook; the latest classify run's by   │
│                        default.                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --port          <int range> [x>=1]  Port of the page. docker run publishes   │
│                                     it under the same number on your         │
│                                     computer: -p 127.0.0.1:9000:9000 for     │
│                                     --port 9000. Default: 8088.              │
│ --help  -h                          Show this message and exit.              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [All commands](../reference-commands.md) · [Documentation](../README.md)
