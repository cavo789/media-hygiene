# `inventory`: every photo and video in a spreadsheet

[Documentation](../README.md) › [Commands](../reference-commands.md) › `inventory` · 🇫🇷 [Français](../../fr/commands/inventory.md)

## In short

**Answer your own questions about your photos in Excel: how many per year or per camera, which
are blurry or tiny, which camera had its clock wrong, which hold a GPS position.**

`inventory` exports every photo, RAW file and video the audits have seen to an Excel [workbook](../reference-glossary.md#workbook),
with everything they learnt about it: size, dates, device, settings, place, quality, duplicates,
words. It reads **the cache alone**: no file of your folders is opened, it takes seconds even
for tens of thousands of photos.

**When**: any time after an audit run with the [cache](../reference-glossary.md#cache); again after the next audit, to stay up to
date.

**Try it**:

```powershell
docker run --rm -it `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene inventory
```

## At a glance

| | |
|---|---|
| Your photos | 🔒 Never changed, not even read. |
| Needs | `/cache` (filled by an earlier [`audit`](audit.md)) and `/reports` (where the workbook goes). |
| Writes | `/reports/<date>-inventory/inventory.xlsx` (or `inventory.csv`). |
| Undo | Delete the folder. |
| With `mh` | `mh inventory`. |

## Run it

```powershell
docker run --rm -it `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene inventory
```

No photo folder is needed. The console says where the workbook is, and when each folder was last
audited completely.

## Options

| Option | What it does |
|---|---|
| `--format xlsx` | The default: a workbook with two sheets, **Files** (one row per file) and **Summary**. |
| `--format csv` | The Files sheet only, as a CSV file, like `plan.csv`. |

## Good to know

- The inventory is **as fresh as the last audit**: a photo added since is missing, a photo deleted
  by hand is still listed. Audit again, then export again.
- After [`tags`](tags.md), the last column, **Tags**, holds the words of each photo.
- The CSV file opens in Excel as is: in French, `;` between the columns and a decimal comma.

## Go further

- [Find in short](../find/quick-guide.md)
- [The inventory workbook](../reference-inventory.md): every column, the quality and exposure
  labels.
- [2. Keep the cache](../start/02-keep-the-cache.md)

## The built-in help

<details>
<summary><code>inventory --help</code></summary>

<!-- capture: help-inventory.txt -->
```text
 Usage: media-hygiene inventory [OPTIONS]

 🔒 Read-only: never changes your photos. Export every photo and video with
 what the audits learnt to Excel, from the cache alone: no file is read.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --format          <xlsx|csv>  xlsx: an Excel workbook (Files and Summary     │
│                               sheets). csv: the Files sheet only, like       │
│                               plan.csv. Default: xlsx.                       │
│ --help    -h                  Show this message and exit.                    │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [All commands](../reference-commands.md) · [Documentation](../README.md)
