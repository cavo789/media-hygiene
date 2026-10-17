# `browse`: walk through your folders and set photos aside

[Documentation](../README.md) › [Commands](../reference-commands.md) › `browse` · 🇫🇷 [Français](../../fr/commands/browse.md)

## In short

**Look through your folders as in Explorer, and set aside the photos you no longer want.**

`browse` opens your library in your browser: the tree of your folders on the left (each with
its number of photos and videos and its size), the photos and videos of the folder chosen on the
right. Pick some and set them aside: the next [`clean --decisions`](clean.md) moves them to the
quarantine, journaled and undoable. Deleting in Explorer leaves no trace; here, every removal can
be undone.

**When**: after an [`audit`](audit.md): the page shows what the audit has read. No
[`tags`](tags.md) needed.

**Try it**:

```powershell
docker run --rm -it `
  -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/[cache](../reference-glossary.md#cache) `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene browse
```

## At a glance

| | |
|---|---|
| Your photos | 🔒 Never changed by the page: mount them `:ro`. |
| Needs | `/cache` (the files of the last audit), your folders (to show the photos), `/reports` (to keep what you set aside), and `-p 127.0.0.1:8088:8088` for the page. |
| Writes | The small previews of the grid, in the cache; the photos you set aside, in `decisions.json` of the reports. |
| Undo | Nothing to undo on the page: [`clean --decisions`](clean.md) moves the photos set aside, [`undo`](undo.md) brings them back. |
| With `mh` | `mh browse`. |

## Run it

```powershell
mh browse
```

Your browser opens on the page (if not: `http://127.0.0.1:8088/`).

- **The tree**: your mounted folders, open; the folders below them, closed (▸ opens one). Click a
  folder: its photos and videos appear, sorted by name or by date (**Sort by**).
- **Look**: Enter or a double click shows a picture large, a video plays; ← and → go to the
  previous and next ones, as in the Photos app; Escape closes.
- **Pick**: a click picks one file, Ctrl+click adds or removes one, Shift+click a range, Space
  the file at hand, Ctrl+A the whole folder.
- **Set aside**: Delete, or **Set aside the picked files**. The choice is saved at once in
  `decisions.json` of your reports, read back from the disk and shown with its count and size:
  *37 files set aside (412 MB), saved in …: 'clean --decisions' moves them to the quarantine.*
  Those files carry a red *marked to set aside* label; **Take out of the set aside** takes
  picked files back out.
- **Search by words** opens the [`search`](search.md) page, on the same server: what you set
  aside there and here goes to the same file.

Ctrl+C stops the page; when files are set aside, `browse` proposes the next step:

```powershell
mh clean --decisions
```

It says how many files and bytes go (apart from the duplicates), asks, then moves them to the
quarantine, journaled: `mh undo` brings them back, `mh purge` frees the space.

## Options

| Option | What it does |
|---|---|
| `--port PORT` | Port of the page, 8088 by default; publish the same one. |

## Good to know

- Nothing is deleted from the page, and nothing moves until `clean --decisions`. A file changed
  since you picked it is left where it is and listed in the clean report; a file of a protected
  folder refuses the whole file, as everywhere.
- The page lists what the last [`audit`](audit.md) has read: audit again to see new files.
- Without `/reports` (or with a folder the tool cannot write to), setting aside says why and
  saves nothing; looking still works.
- A video shows its first images in the grid when your browser can play its format (MP4, MOV);
  the others show "No preview" and open as originals.

## Go further

- [Find in short](../find/quick-guide.md)
- [`search`: set photos aside found by a word, a person, a year](search.md#set-photos-aside)

## The built-in help

<details>
<summary><code>browse --help</code></summary>

<!-- capture: help-browse.txt -->
```text
 Usage: media-hygiene browse [OPTIONS]

 🔒 Read-only: never changes your photos. Walk through your folders in your
 browser, as in Explorer, and set photos aside; 'clean --decisions' then moves
 them.

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
