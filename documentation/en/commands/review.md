# `review`: choose the best shots, in your browser

[Documentation](../README.md) › [Commands](../reference-commands.md) › `review` · 🇫🇷 [Français](../../fr/commands/review.md)

## In short

**Keep only the best shots of your bursts, and decide the near duplicates and the folder pairs,
by looking at them large, in your browser.**

Burst series (five, ten, twenty shots in a few seconds) and [near duplicates](../reference-glossary.md#near-duplicate) (a photo saved
again, smaller) are not identical files: only you can tell which ones to keep. `review` shows
them to you **one at a time** and you choose with the keyboard. Each choice is saved at once in
`decisions.json`; `clean --decisions` applies them later.

**When**: after an audit that found [burst series](../reference-glossary.md#burst-series) (or near duplicates, with `--near`; folder
pairs of identical files, with `--pairs`), before `clean --decisions`.

**Try it**:

```powershell
docker run --rm -it `
  -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene review
```

## At a glance

| | |
|---|---|
| Your photos | 🔒 Never changed: the page only shows them. Mount them `:ro`. |
| Needs | Your folders, `/reports` (where `decisions.json` is saved), and `-p 127.0.0.1:8088:8088`. |
| Recommended | `/cache` (the audit it starts with takes seconds), `/config`. |
| Writes | `decisions.json` in `/reports`, the cache. |
| Undo | Change your choices in the page, or delete `decisions.json`. |
| With `mh` | `mh review`, `mh review --near`, `mh review --pairs`, `mh review --junk`, `mh review --gone`: the port is published for you. |

## Five kinds of review

| Command | What you decide | Applied by |
|---|---|---|
| `review` | **Burst series**, one at a time: which shots go to the quarantine. The sharpest shot is first, the shots proposed aside are marked; `→` accepts what is shown. | `clean --decisions` |
| `review --near` | **Near duplicates and re-encoded videos**, group by group: as planned (`→`), keep the other version (`W`), leave alone (`L`), keep none (`X`). | `clean --tier near --decisions` |
| `review --pairs` | **Folder pairs** of identical files, the most space freed first: as planned (`→`), swap the folders (`W`), leave alone (`L`). | `clean --decisions` |
| `review --junk` | **Photos most likely unwanted** (tiny, screenshots, nearly black or white, the blurriest), group by group: each one kept or set aside by you. | `clean --decisions` |
| `review --gone` | **Photos and videos gone since an audit** (deleted in the Explorer?), by folder and day: deleted on purpose (`D`, remembered, set aside if they come back) or moved elsewhere (`M`, forgotten). [Cleaning, step 9](../clean/09-undo-history-purge.md#deleted-in-the-explorer) | `clean --decisions` |

## Run it

```powershell
docker run --rm -it -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v "D:\Old disk:/data/d/Old disk:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene review
```

It audits first, then prints *✅ Review ready, open http://127.0.0.1:8088/ in your browser*.
Ctrl+click it. Leave the window open: the page runs as long as it does; Ctrl+C, or closing its tab, stops it.

`-p 127.0.0.1:8088:8088` opens the page to your computer only, nobody else on the network.

## The main keys

Every review page has the same layout: what leads to the photos on the left (the table of
contents, the folder pairs, a short explanation), the keys at the bottom left (⌨ **Keyboard**, the
first ones always shown, the others under *More keys*) with the line saying where each choice is
saved; on the right, one bar on top (where you are, the totals, the choice read back from the
disk; *Apply now* on every review that moves files when the home page opened it), then the
photos.

| Key | Bursts (`review`) | Near duplicates (`review --near`) | Folder pairs (`review --pairs`) |
|---|---|---|---|
| `→` | Next series, as shown | As planned, then the next group | As planned, then the next pair |
| `←` | Previous series | Previous group | Previous pair |
| `N` | Next series still to see | Next group still undecided | Next pair still undecided |
| `Delete` | Set the picked shots aside | — | — |
| `S` / `X` | Keep only the sharpest / set the whole series aside (*Keep every shot*: a button) | — | — |
| `W` / `L` / `U` | — | Keep the other version / leave alone / back to undecided | Swap the folders / leave alone / back to undecided |
| `V` / `G` | Validate every obvious series at once | `G`: the whole folder pair as planned | — |
| `Z` | Undo the last choice | — | — |

`review --junk`: `→` the group as marked, then the next one; `Space` keeps or sets aside the
framed photo; `Delete` sets the picked photos aside; `←`, `N`, `U` as for the other reviews.

**Pick the shots as in [`browse`](browse.md)** (`review` and `review --junk`): a click picks one
shot; the ☑ box (or Ctrl+click) adds or removes one; Shift+click picks every shot from the last
one clicked; a rectangle dragged with the mouse picks what it touches (with Ctrl, it adds);
Ctrl+A the whole series or group; **Invert the picking** (or I) picks the others. `Delete` or
the bar's button sets the picked shots aside, *Take out of the set aside* takes them back. Since
`←`, `→` and Space change the series here, the frame moves with `↑` / `↓`.

**See a photo large** on every review: Enter or a double click; `←` / `→` the previous or next
one, `F` full screen, `?` every key, `Esc` closes. On `review` and `review --junk`, `Delete`
sets the photo shown aside and `⌫` takes it back; on `review`, `A` adds it to the album named
in the bar. On `--near`, `--gone` and `--pairs`, the large view only shows (nothing to pick).

`review --gone`: `D` deleted on purpose, `M` moved elsewhere (the file under the cursor, then the
next one), `G` the whole group deleted on purpose, `U` the group back to unanswered; `→`, `←`,
`N` as for the other reviews.

The complete lists: [cleaning, step 10](../clean/10-review-bursts.md#step-5-go-faster) and
[cleaning, step 11](../clean/11-near-duplicates.md#decide-in-your-browser-review---near),
[cleaning, step 12](../clean/12-decide-pair-by-pair.md),
[cleaning, step 14](../clean/14-unwanted-photos.md#step-2-choose).

## Options

| Option | What it does |
|---|---|
| `--near` | Review the near duplicates and re-encoded videos instead of the burst series. |
| `--pairs` | Review the folder pairs of the identical files instead of the burst series. |
| `--junk` | Review the photos most likely unwanted instead of the burst series; thresholds in `[review.unwanted]`. |
| `--gone` | Review the photos and videos gone since an audit instead of the burst series. One of `--near`, `--pairs`, `--junk`, `--gone` per run. |
| `--decisions FILE` | The file the choices are saved in, and resumed from; `decisions.json` of `/reports` by default. |
| `--port PORT` | Port of the page, 8088 by default; publish the same one: `-p 127.0.0.1:9000:9000` for `--port 9000`. |
| `--prefer`, `--protect`, `--exclude` | As for [`audit`](audit.md#options): give `review` the same ones as `clean`. |
| `--ext`, `--exclude-name` | As for [`audit`](audit.md#options): the audit `review` starts with then sees the same files. |

## Good to know

- **From the home page, at once**: *Settle the near duplicates* opens `review --near` in the
  home page's own server, without starting another container; the audit is read again from the
  cache each time the page opens. `mh review --near` typed alone works as before.
- **Proof, not promise**: after each choice, the page reads `decisions.json` back from the disk
  and shows what it holds (*✔ Saved, then read back from the disk at 14:32:05*).
- **Stop whenever you like**: the next `review` opens the first series still to see. Series you
  have not seen move nothing.
- **One file for everything**: `decisions.json` holds the burst shots (`bursts`), the near
  duplicates (`near`), the folder pairs (`pairs`, from `review --pairs` or the report's
  download) and the unwanted photos (`unwanted`); each review keeps the others.
- **Opened from the [home page](home.md)**, the reviews of bursts, near duplicates, folder
  pairs and unwanted photos show an **Apply now** button once something is set aside or
  decided (`--gone` has none: its answers move no file): the page closes and `mh` runs
  the home page's step that applies your choices (its usual question first), then the home
  page comes back. Opened by `mh review` alone: no button, type the `clean` command.
- A shot of a **protected folder** is never proposed nor set aside.
- **👤 this person**, under each shot, opens in a new tab every photo of someone on that shot,
  to set them all aside: see [`people`](people.md#from-any-page-set-a-person-aside).
- The burst review has an **Album** field too: **➕ Add to the album** puts the picked shots in
  that album, as in `browse`, apart from your decisions. See
  [Put photos in an album](search.md#put-photos-in-an-album).
- *port is already allocated*? Another program uses 8088: `-p 127.0.0.1:9000:9000` and
  `review --port 9000`.

## Go further

- [10. Sort burst series in your browser](../clean/10-review-bursts.md)
- [11. Near duplicates](../clean/11-near-duplicates.md#decide-in-your-browser-review---near)
- [12. Decide pair by pair](../clean/12-decide-pair-by-pair.md)
- [14. Unwanted photos](../clean/14-unwanted-photos.md)
- [Troubleshooting: the review page does not open](../reference-troubleshooting.md#the-review-page-does-not-open)
- Next: [`clean --decisions`](clean.md).

## The built-in help

<details>
<summary><code>review --help</code></summary>

<!-- capture: help-review.txt -->
```text
 Usage: media-hygiene review [OPTIONS]

 🔒 Read-only: never changes your photos. Set burst shots aside, one series at
 a time, with the keyboard in your browser; 'clean --decisions' then moves
 them.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --near             Review the near duplicates and re-encoded videos group by │
│                    group instead of the burst series: as planned, keep the   │
│                    other version, or leave alone; 'clean --tier near         │
│                    --decisions' applies it.                                  │
│ --pairs            Review the folder pairs of the exact duplicates one by    │
│                    one instead of the burst series: as planned, swap the     │
│                    folders, or leave alone; 'clean --decisions' applies it.  │
│ --junk             Review the photos most likely unwanted (tiny,             │
│                    screenshots, nearly black or white, the blurriest)        │
│                    instead of the burst series: nothing is set aside without │
│                    you; 'clean --decisions' moves what you set aside to the  │
│                    quarantine. Thresholds:  of config.toml.                  │
│ --gone             Review the photos and videos gone since an audit (deleted │
│                    in the Explorer?) instead of the burst series: say which  │
│                    ones you deleted on purpose, and 'clean --decisions'      │
│                    remembers them, so that they are set aside if they come   │
│                    back.                                                     │
│ --help   -h        Show this message and exit.                               │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Advanced options ───────────────────────────────────────────────────────────╮
│ --decisions        <path>              File the decisions are saved in, and  │
│                                        resumed from. A relative path lies in │
│                                        the folder mounted on /reports.       │
│                                        Default: decisions.json.              │
│ --port             <int range> [x>=1]  Port of the page. docker run          │
│                                        publishes it under the same number on │
│                                        your computer: -p 127.0.0.1:9000:9000 │
│                                        for --port 9000. Default:  port in    │
│                                        config.toml, 8088.                    │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Advanced: folders (override folders.* of config.toml) ──────────────────────╮
│ --prefer         <str>  Folder whose copies are kept first. Repeat it; the   │
│                         order matters.                                       │
│ --protect        <str>  Folder never modified; its files are the copies      │
│                         kept. Repeatable.                                    │
│ --exclude        <str>  Folder never analysed, not even read. Repeatable.    │
│ --backup         <str>  A backup or an old disk: compared, never changed.    │
│                         Says what it lacks and what only it holds.           │
│                         Repeatable.                                          │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Advanced: scan (override scan.* of config.toml) ────────────────────────────╮
│ --ext                 <str>  Only analyse these categories or extensions,    │
│                              e.g. --ext photo,video or --ext png,webp        │
│                              (repeatable). Categories: photo, raw, video,    │
│                              media and those of scan.categories in           │
│                              config.toml. Other types too, such as --ext     │
│                              pdf,docx: their copies are moved to the         │
│                              quarantine. Default: media (every photo, RAW    │
│                              and video).                                     │
│ --exclude-name        <str>  Folder name never analysed, wherever it is,     │
│                              case ignored; * and ? allowed, e.g.             │
│                              --exclude-name Thumbnails,.Trash-*              │
│                              (repeatable). Adds to the system folders        │
│                              already skipped. For one precise folder, use    │
│                              --exclude.                                      │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [All commands](../reference-commands.md) · [Documentation](../README.md)
