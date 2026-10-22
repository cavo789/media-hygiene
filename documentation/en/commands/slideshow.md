# `slideshow`: your photos on the TV, the phone as a remote

[Documentation](../README.md) › [Commands](../reference-commands.md) › `slideshow` · 🇫🇷 [Français](../../fr/commands/slideshow.md)

## In short

**The holiday photos on the living-room TV, the family on the sofa, the next photo chosen from
the phone.**

`slideshow` serves two pages from your PC. The **screen**, opened once in the browser of the TV
(or of a Chromecast plugged into it): black, one photo at a time, fitted to the screen, never a
file name. The **remote**, on your phone: the thumbnails of the selection, ◀ and ▶, play and pause
with the time each photo stays, **Do not show** to skip one tonight, and a tap on a thumbnail shows
that photo on the TV. The videos of the selection play too, as they are. The PC holds the show: a
TV reloaded or a phone gone to sleep loses nothing.

**When**: after an [`audit`](audit.md): it shows what the audit has read. A search needs
[`tags`](tags.md) first.

**Try it** (on the PC only; for the TV, see [Run it](#run-it)):

```powershell
docker run --rm -it `
  -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/[cache](../reference-glossary.md#cache) `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene slideshow --folder "C:\Photos\2026 Holidays"
```

## At a glance

| | |
|---|---|
| Your photos | 🔒 Never changed: mount them `:ro`. |
| Needs | `/cache` (the files of the last audit), your folders (to show the photos), the page's port; `/reports` for `--chosen`. |
| Writes | The TV's pictures and the phone's thumbnails, in the cache. Nothing else: the show lives in memory. |
| Reaches | The PC only; with `--lan`, the TV and the phones of your home network, never the internet. |
| With `mh` | `mh slideshow --folder "C:\Photos\2026 Holidays" --lan`. |

## Run it

In Windows PowerShell, on the PC:

```powershell
mh slideshow --folder "C:\Photos\2026 Holidays" --lan
```

`--lan` opens the show to your home network for this run only, as
[`mh --lan`](home.md#from-a-phone-on-the-home-wi-fi-mh---lan) does for the home page: the window says the address of the screen and the
phone's address and code; the PC's browser opens the remote with the same lines and a QR code.
Windows may ask whether Docker Desktop may accept connections: allow it on **private** networks
only. Without `--lan`, only the PC can open the show (useful to try it, or for plan B below).

Instead of a folder: `--search "noel 2025"` (the photos a [`search`](search.md) finds) or
`--chosen` (the files set aside in `search` or [`browse`](browse.md)). From the
[home page](home.md) opened by `mh --lan`, the *Show your photos on the TV* step asks for the
folder and opens the show the same way.

### On the TV, once

1. **A Chromecast with Google TV** (recommended: faster than a 2012 TV's own browser): install a
   web browser app on it, open it.
   **The TV's own browser** (a Samsung *Smart Hub*: the **Internet** app) works too, slower, and
   shows the photos only: the videos need the Chromecast's browser.
2. Type the address the window gives, for example `http://192.168.1.20:8088/screen`. It is plain
   `http`, on your home network: no certificate, nothing on the internet.
3. **Bookmark it**: next time, the bookmark is enough (see [A stable address](#a-stable-address)).
4. The TV shows a code of six digits. On the phone's remote, type it in **The code the TV shows**,
   then **Pair the TV**: the first photo appears. The TV is paired until the slideshow stops.
5. Press **OK** on the TV's remote (or click) for full screen.

Typing a code with a TV remote is painful: here the TV only shows one, the phone types it.

### On the phone

Open the address the window gives (or scan the QR code on the PC's page) and type the code of
eight digits: the remote opens. Then:

- **◀** and **▶**: the previous and next photos; **▶ Play** / **❚❚ Pause**, and **Each photo**: how
  long a photo stays while playing.
- A tap on a thumbnail shows that photo on the TV.
- **Do not show** sets the photo on the TV out of the show (the TV moves on); a thumbnail's own
  button does the same for any photo, and **Show again** sets it back.
- A video's thumbnail is marked **▶**. On the TV, it plays to its end, then the show moves on;
  **❚❚ Pause** pauses it too. A video the TV cannot play is labelled under its thumbnail
  (*Not on the TV: its format (hevc) does not play there.*) and passed over.

The TV loads the next photo in advance, behind the one shown, and swaps once it is decoded: you
never see a photo drawn in bands.

Ctrl+C in the PowerShell window stops the slideshow; the TV keeps its last photo.

## A stable address

The TV's bookmark names the PC's address on your home network and the port. The port is fixed
(`[review] port`, 8088). The address is given by your router, and may change after a while: in
the router's page, **reserve** the PC's address (often *DHCP › Static lease* or *Address
reservation*, by the PC's MAC address). The tool does not do it for you.

## Plan B: casting a tab

If neither the Chromecast's browser nor the TV's opens the screen: start without `--lan`, open
`http://127.0.0.1:8088/screen` in Chrome or Edge on the PC, then **Cast** that tab to the
Chromecast from the browser's menu. The remote then works on the PC itself, at
`http://127.0.0.1:8088/`.

## Settings

In `config.toml`, `[slideshow]`:

| Key | Default | What it does |
|---|---|---|
| `screen_px` | `1920` | The width of the TV's pictures: each photo is fitted into `screen_px` × 9/16 of it (1920 × 1080). `3840` for a 4K TV; smaller loads faster on an old TV. |
| `interval_seconds` | `8` | How long a photo stays while playing (2 to 600); the phone changes it for the evening. |

The port is `[review] port`, the one of every page.

## Options

| Option | What it does |
|---|---|
| `--folder "C:\…"` | The photos of this folder and its subfolders, as the Explorer shows it. |
| `--search "words"` | The photos a search finds, as typed in [`search`](search.md). |
| `--chosen` | The files set aside in `search` or `browse`. |
| `--port PORT` | Port of the page, 8088 by default; publish the same one. |
| `--lan` (`mh` only) | Opens the show to the TV and the phones of your home network, for this run (Windows PowerShell). |

## Good to know

- Videos play as they are, never converted: H.264 (most phone videos), VP8 and VP9, in `.mp4`,
  `.m4v`, `.mov` or `.webm`. Others (HEVC, an `.avi`…) are passed over: converting them would take
  minutes per video for a handful of files (4 of about 1,200 in a measured collection). The codec
  is the one the last audit read; the TV's own browser of a 2012 TV shows the photos only.
- Oldest first, by the date the photo or the video was taken; the undated ones last. At most 3,000
  files: the first ones by date.
- The TV gets each photo upright, at the size of its screen (300 to 500 KB, estimated), made
  once and kept in the cache with the other previews.
- Only the files of the show are served: a TV or a phone never reaches another file of your
  library, nor the original of a photo (a video is sent as it is).
- A phone paired by the code may drive the show; a TV paired by its code may only show it. Too
  many wrong codes close the pairing until the slideshow starts again.

## Go further

- [`home`: the home page, and `mh --lan`](home.md)
- [Find in short](../find/quick-guide.md)

## The built-in help

<details>
<summary><code>slideshow --help</code></summary>

<!-- capture: help-slideshow.txt -->
```text
 Usage: media-hygiene slideshow [OPTIONS]

 🔒 Read-only: never changes your photos. Show photos on the TV, the phone
 choosing the next one: a folder, a search or the files set aside.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --folder          <str>               Show the photos of this folder and its │
│                                       subfolders, as the Explorer shows it:  │
│                                       "C:\Photos\2026 Holidays".             │
│ --search          <str>               Show the photos a search finds, as     │
│                                       typed in search: "noel 2025".          │
│ --chosen                              Show the files set aside in search or  │
│                                       browse.                                │
│ --port            <int range> [x>=1]  Port of the page. docker run publishes │
│                                       it under the same number on your       │
│                                       computer: -p 127.0.0.1:9000:9000 for   │
│                                       --port 9000. Default:  port in         │
│                                       config.toml, 8088.                     │
│ --help    -h                          Show this message and exit.            │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [All commands](../reference-commands.md) · [Documentation](../README.md)
