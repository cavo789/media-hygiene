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

**Where to start it**: in the home page, the **Share** area (outside the cycle, in the
sidebar), or `mh menu`, under *Share*.

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
| Needs | `/cache` (the files of the last audit), your folders (to show the photos), the page's port; `/reports` for `--album`. |
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
`--album "Crete 2023"` (an [album](search.md#put-photos-in-an-album) made in `search`,
[`browse`](browse.md) or the burst [`review`](review.md): photos of several folders; its
**📺 Share on the TV** button gives this command, copied). `--chosen` is gone: it showed the
files set aside, meant for the quarantine; given, it says to use `--album`. From the
[home page](home.md) opened by `mh --lan`, the *Show your photos on the TV* step asks for the
folder and opens the show the same way; *Show an album on the TV* asks for the album's name
and opens the show **in the home page's own server**: the home page keeps running, the remote
opens at once (`/slideshow/`). A paired phone starts it too, from the sofa: on the phone's home
page, **Show an album on the TV** lists the albums saved on the PC; a tap opens the remote at once
(no code). The TV, at its bookmark, waits for a show while none runs and shows it by itself; it
is paired once (its code typed on the remote) and **stays paired while `mh` runs**: another album
reaches it without a new code. No album saved: the phone says to make one on the PC.

### On the TV, once

1. **A Chromecast with Google TV** (recommended: faster than a 2012 TV's own browser): install a
   web browser app on it, open it.
   **The TV's own browser** (a Samsung *Smart Hub*: the **Internet** app) works too, slower, and
   shows the photos only: the videos need the Chromecast's browser.
2. Type the address the window gives, for example `http://192.168.1.20:8089/screen` (port **8089**: the
   phone's remote is on 8088, in `https`). It is plain `http`, on your home network: a TV cannot
   install the PC's certificate, and nothing goes on the internet. That address serves the TV's
   pages only, never the remote.
3. **Bookmark it**: next time, the bookmark is enough (see [A stable address](#a-stable-address)).
4. The TV shows a code of six digits. On the phone's remote, type it in **The code the TV shows**,
   then **Pair the TV**: the first photo appears. The TV is paired until the slideshow stops; when
   the show runs in the home page (an album started there), until `mh` stops.
5. Press **OK** on the TV's remote (or click) for full screen.

Typing a code with a TV remote is painful: here the TV only shows one, the phone types it.

### On the phone

Open the address the window gives, in `https`, for example `https://192.168.1.20:8088/` (or scan
the QR code on the PC's page) and type the code of eight digits: the remote opens, and the phone is
paired for good, as on the home page. A phone already
paired on the [home page](home.md#from-a-phone-on-the-home-wi-fi-mh---lan) opens it without a
code, from its browser or the installed app. A phone that says the connection is not private
installs the PC's certificate first, once: the window gives where (`http://192.168.1.20:8089/phone`),
the steps are the [home page's](home.md#once-per-phone-install-the-certificate). Then:

- **◀** and **▶**: the previous and next photos; **▶ Play** / **❚❚ Pause**, and **Each photo**: how
  long a photo stays while playing.
- A tap on a thumbnail shows that photo on the TV.
- **Do not show** sets the photo on the TV out of the show (the TV moves on); a thumbnail's own
  button does the same for any photo, and **Show again** sets it back.
- A video's thumbnail is marked **▶**. On the TV, it plays to its end, then the show moves on;
  **❚❚ Pause** pauses it too. A video the TV cannot play is labelled under its thumbnail
  (*Not on the TV: its format (hevc) does not play there.*) and passed over.
- **The event's name**: at each new event (a new folder, in the show's order), the TV shows a
  title card for 3 seconds (one of its photos blurred, the name large, the month and the place
  under it), then a banner on its first photo for a few seconds. The name is the folder's
  (`2026\2026-10\Walk in Valkenburg` → *Walk in Valkenburg*: years, months, dates and camera
  folders are passed over); the month is the photos' date taken; the place is one of yours
  (`places`), else the nearest town of their GPS, found offline (with its country when it is not your
  home country, e.g. *Valkenburg, Netherlands*: the country of your place marked `home`, else of
  your first place, else where most of the photos were taken). One tap chooses where it is
  told: **TV and phone** (the default), **Phone only** (under the controls; the storyteller's notes then open by themselves),
  **Nowhere**.
- **The storyteller's notes** (unfold them under the controls): while the family watches the TV,
  the phone shows the photo on screen larger, its day and time, the event and its place, its
  description and words (when `describe` gave some), the next photo, and a small drawing of
  where the event's photos were taken (the red dot: this one), over the names of the nearby
  towns and villages (read from the towns built into the tool: nothing goes to the internet).
  If you set `[places] tiles` in `config.toml` (the map of [`places`](places.md)), real map
  tiles are drawn under the points instead: the phone's browser downloads them, so the tile
  server sees the area viewed (never a photo). Three buttons: **Pause while I talk**, **Back to the start of this event**,
  **Next event**. They only move the show: nothing is changed on the PC.

The TV loads the next photo in advance, behind the one shown, and swaps once it is decoded: you
never see a photo drawn in bands.

Ctrl+C in the PowerShell window stops the slideshow; the TV keeps its last photo.

## A stable address

The TV's bookmark names the PC's address on your home network and the port. The port is fixed
(`[review] port`, 8088; the TV's, 8089). The address is given by your router, and may change after a while: in
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
| `--album "Crete 2023"` | An album made in `search`, `browse` or the burst review; its files missing (deleted, in the quarantine) are counted, not shown. |
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
- [`share`: the album ready to send by mail](share.md)

## The built-in help

<details>
<summary><code>slideshow --help</code></summary>

<!-- capture: help-slideshow.txt -->
```text
 Usage: media-hygiene slideshow [OPTIONS]

 🔒 Read-only: never changes your photos. Show photos on the TV, the phone
 choosing the next one: a folder, a search or an album.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --folder          <str>               Show the photos of this folder and its │
│                                       subfolders, as the Explorer shows it:  │
│                                       "C:\Photos\2026 Holidays".             │
│ --search          <str>               Show the photos a search finds, as     │
│                                       typed in search: "noel 2025".          │
│ --album           <str>               Show an album, made in search, browse  │
│                                       or the burst review: "Crete 2023".     │
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
