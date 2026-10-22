# `share`: an album ready to send, a folder and a zip

[Documentation](../README.md) › [Commands](../reference-commands.md) › `share` · 🇫🇷 [Français](../../fr/commands/share.md)

## In short

**The holiday photos to the family by mail, or onto a social network, without sending 8 MB
photos that say where the house is.**

`share` takes an [album](search.md#put-photos-in-an-album) (a named list of photos from any
folders, made in `search`, `browse` or the burst `review`) and makes a copy of each photo,
ready to send: turned upright, its long side brought down to 2048 pixels, saved as a JPEG, and
**without its GPS position**. The date, the camera and the description stay. The copies go into
one folder named after the album, with a zip of it next to it: attach the zip to a mail, or add
the photos of the folder to an album you create on your social network, or copy the folder to a
USB stick. No account, no password: the tool sends nothing itself.

**Where to start it**: in the home page, the **Share** area (outside the cycle, in the sidebar),
the *Prepare an album for sending* step; or the **📨 Prepare for sending** button next to the
album in `search` or `browse`, which gives the command, copied; or `mh menu`, under *Share*.

**When**: once the album exists, after an [`audit`](audit.md) (an album's photo moved since is
found again by what the audit read).

**Try it**:

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/[cache](../reference-glossary.md#cache) `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  -v "$HOME\media-hygiene\Shares:/shares" `
  cavo789/media-hygiene share --album "Crete 2023"
```

## At a glance

| | |
|---|---|
| Your photos | 🔒 Only read, never changed: mount them `:ro`. |
| Needs | `/reports` (the albums, `albums.json`), your folders (to read the photos), `/shares` (where the copies go); `/cache` to find a photo moved since. |
| Writes | In `/shares` only: the folder of the album and its zip. Prepared again, the album replaces its folder and its zip. |
| Reaches | Nothing outside your PC: the tool sends no mail and publishes nothing. |
| With `mh` | `mh share --album "Crete 2023"`: `mh` mounts `$HOME\media-hygiene\Shares` for this command only, then opens it in the Explorer. |

## Run it

In Windows PowerShell:

```powershell
mh share --album "Crete 2023"
```

The window says what is on the disk once done, read back from it: how many photos are ready,
their total size, where the folder is (`C:\Users\<you>\media-hygiene\Shares\Crete 2023`), and the
zip (`Crete 2023.zip`, next to it) with its size. Then the Explorer opens on the `Shares` folder:
the album's folder and its zip side by side.

What the album holds but the folder does not is counted, never hidden:

- **The videos are left out**: *3 videos not included*. One video alone may be larger than what a
  mail accepts; share a video another way (a USB stick, a shared drive).
- A photo of the album found nowhere (deleted, or in the quarantine) is counted as missing.
- A photo that cannot be read (damaged) is counted too.

Prepared again (after adding photos to the album), the album **replaces** its folder and its zip;
the window says so in one line. The folder is made apart first: stopped half way (Ctrl+C), the
earlier folder stays as it was.

### The size of the zip

Above **25 MB**, the window warns you: some webmails refuse an attachment that large. The limit
depends on your mail: check its own. Measured here on synthetic photos of 12 megapixels, a copy
weighs 0.3 to 0.8 MB, so about 30 to 80 photos per 25 MB (estimated; real photos may differ).
Above the limit, send the folder another way, or make an album of fewer photos.

## The GPS position

A photo taken with a phone usually holds the place it was taken, to a few metres: shared as is,
the photos of the garden say where the house is. `share` **removes the position** from every
copy by default, and the window says so. Your original photos keep theirs: only the copies lose
it. To keep it (holiday photos sent to the family, the places being the point):

```powershell
mh share --album "Crete 2023" --keep-gps
```

The maker's notes (a block private to each camera brand, which may hold its serial number) and
the XMP block are never copied either.

## Settings

In `config.toml`, `[share]`:

| Key | Default | What it does |
|---|---|---|
| `long_side_px` | `2048` | The long side of each copy, in pixels (320 to 8192). A smaller photo is never enlarged. |
| `quality` | `85` | The JPEG quality of the copies (30 to 95). |
| `keep_gps` | `false` | Keep the GPS position in the copies, every time; `--keep-gps` does it for one run. |

## Options

| Option | What it does |
|---|---|
| `--album "Crete 2023"` | The album to send, made in `search`, `browse` or the burst review. |
| `--keep-gps` | Keep the GPS position in the copies, for this run. |

## Good to know

- The copies are named after the photos (`IMG_1234.jpg`); two photos of the same name from two
  folders become `IMG_1234.jpg` and `IMG_1234_1.jpg`. A HEIC or a RAW photo gives a JPEG (a RAW
  file, the preview it holds, without its EXIF).
- The folder is always `<your home>\media-hygiene\Shares`: no folder to type, and no photo
  folder is ever opened for writing. Delete what you sent once it is sent: the album itself
  (`albums.json`) stays.
- To keep the album as a folder of the Explorer instead, without a copy:
  [`album "Crete 2023"`](album.md) (hard links, on the disk of the photos).

## Go further

- [`search`: put photos in an album](search.md#put-photos-in-an-album)
- [`slideshow`: the album on the TV](slideshow.md)
- [`home`: the album on your phone, at home](home.md#your-albums-on-the-phone)

## The built-in help

<details>
<summary><code>share --help</code></summary>

<!-- capture: help-share.txt -->
```text
 Usage: media-hygiene share [OPTIONS]

 🔒 Read-only: never changes your photos. Prepare an album for sending: resized
 copies without the GPS position, a folder and a zip, for a mail or a social
 network.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ *  --album             <str>  The album to send, made in search, browse or   │
│                               the burst review: "Crete 2023".                │
│                               [required]                                     │
│    --keep-gps                 Keep the GPS position in the copies; removed   │
│                               by default, a photo sent must not say where    │
│                               the house is.                                  │
│    --help      -h             Show this message and exit.                    │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [All commands](../reference-commands.md) · [Documentation](../README.md)
