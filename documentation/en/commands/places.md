# `places`: name your places on a map

[Documentation](../README.md) › [Commands](../reference-commands.md) › `places` · 🇫🇷 [Français](../../fr/commands/places.md)

## In short

**Name the places that matter to you on a map (home, grandpa's, a village), so that `classify`
sorts your photos by place and by trip.**

Recent phones write **where** each photo was taken. `places` shows those positions on a map in
your browser, grouped in circles, and saves the places you name into `config.toml`, where the
`place` and `trip` rules of [`classify`](classify.md) use them.

**When**: before [`classify`](classify.md), once an audit run with the cache has read the
positions; again whenever a new place matters.

**Try it**:

```powershell
docker run --rm -it `
  -p 127.0.0.1:8088:8088 `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene places
```

## At a glance

| | |
|---|---|
| Your photos | 🔒 Never changed: the positions come from the cache. No photo folder is needed. |
| Needs | `/cache` (the positions the audits recorded), `/config` (where the places are saved), and `-p 127.0.0.1:8088:8088`. |
| Writes | `[[classify.places]]` entries in `config.toml`, keeping your comments and the rest of the file. |
| Undo | Delete a place on the map, or its lines in `config.toml`. |
| With `mh` | `mh places`: the port is published for you. |

## Run it

```powershell
docker run --rm -it -p 127.0.0.1:8088:8088 `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene places
```

Ctrl+click the address it prints, `http://127.0.0.1:8088/`. Ctrl+C stops the map.

## On the map

- **The circles** are your photos with a GPS position, grouped by about 200 metres. The list on
  the left gives the largest clusters without a name first: home is usually the first one.
- **Click a circle, or anywhere**, to name a place; set its radius with the slider, drag its
  marker. Tick **Home** for your home: trips are measured from it.
- **Find a town** searches the towns shipped with the image, offline.
- **Search OpenStreetMap** finds a village, a district or a park with its outline: the photo then
  belongs to it when it was taken inside.
- **Save** writes the place into `config.toml` at once. Click a place to move, rename or delete it.

## Options

| Option | What it does |
|---|---|
| `--port PORT` | Port of the page, 8088 by default; publish the same one. |

## What leaves your computer

No position, no photo, no list of places. The map loads **tiles** (the areas you look at) from
the server of `[places] tiles`; **Search OpenStreetMap** sends the **text you typed**, on your
click only, to `[places] nominatim_url` (empty turns that search off). `classify` never goes
online.

## Good to know

- A place name becomes a folder name: two places cannot share one, and the characters Windows
  refuses are refused.
- The places do nothing on their own: add a `place` or a `trip` rule in `[[classify.rules]]`. A
  `trip` rule needs a place with `home = true`.
- Places can also be written by hand in `config.toml`, the latitude and longitude copied from any
  map.

## Go further

- [Sorting, step 9: places and trips from the GPS](../sort/09-places-from-gps.md)
- [Sorting, step 6: the rules](../sort/06-write-down-what-you-know.md)

## The built-in help

<details>
<summary><code>places --help</code></summary>

<!-- capture: help-places.txt -->
```text
 Usage: media-hygiene places [OPTIONS]

 🔒 Read-only: never changes your photos. Name your places on a map of where
 the photos were taken; saved into config.toml for the 'place' and 'trip'
 rules.

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
