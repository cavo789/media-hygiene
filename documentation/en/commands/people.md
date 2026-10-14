# `people`: find the faces, group those alike, name them

[Documentation](../README.md) › [Commands](../reference-commands.md) › `people` · 🇫🇷 [Français](../../fr/commands/people.md)

## In short

**Find the photos of someone by their name, and file them by who is on them, without a single
face leaving your computer.**

`people` finds the **faces** in your photos, groups those that look alike (probably one person
per group), and shows the groups in your browser, largest first, where you **name** them. Then
`search Chloé` finds the photos of Chloé, and a `person` rule of [`classify`](classify.md) files
them. The faces stay in the [cache](../reference-glossary.md#cache), never sent anywhere; the names go into your `config.toml`.

**When**: after an audit run with the cache, or right after it with `audit --people`; again
after new photos: only those are analysed.

**Try it**:

```powershell
docker run --rm -it `
  -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene people
```

## At a glance

| | |
|---|---|
| Your photos | 🔒 Never changed: mount them `:ro`. |
| Needs | Your folders, `/cache` (writable: the faces are kept there), `/config` (writable, to save the names) and `-p 127.0.0.1:8088:8088`. |
| Writes | The faces and the two face models (39 MB, once), in the cache; the names, in `config.toml`. |
| Undo | `people --forget` deletes every face from the cache, then asks whether the names go too. |
| With `mh` | `mh people`: the port is published for you. |

## Run it

```powershell
docker run --rm -it -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene people
```

With WSL or Linux:

```bash
docker run --rm -it -p 127.0.0.1:8088:8088 \
  -v "/mnt/c/Photos:/data/c/Photos:ro" \
  -v media-hygiene-cache:/cache \
  -v "$HOME/media-hygiene/config:/config" \
  cavo789/media-hygiene people
```

The first run downloads the two face models into the cache, once. Each photo is analysed once;
the next runs analyse only the new ones. Then it prints the groups found, the people already
named, and the address of the page: a click on a face opens its photo. Ctrl+C stops it.

<!-- capture: people.txt|re:^✅| -->
```text
✅ 33 photos analysed: 13 faces, 0.05 s per photo.
✅ 17 faces in 43 photos: 3 groups of faces alike, the largest 7, 5, 4; 1 seen
once.
✅ Faces ready, open http://127.0.0.1:8088/ in your browser to name them; each
name is saved at once in config.toml. Ctrl+C stops it; the photos are not
changed.
💡 The page does not open? docker run must publish the same port on both sides:
-p 127.0.0.1:8088:8088.

✅ Page stopped; nothing was changed.
```

## Name the groups

On the page, type a name on a group and press Enter: the name is saved into `config.toml`, read
back and shown. `x` picks several groups to name at once, × takes a wrong face out, `i` ignores
a group of strangers, `y` confirms a suggestion ("Chloé?"). The next runs keep every name, and
[`search`](search.md) finds the people by name: `search Chloé montagne`, `search person:chloe`.
The names follow the photos [`sort`](sort.md) moves (and `undo` moves back); `config.toml` is
updated the next time the page saves a name.
Each name is a `[[people.person]]` entry of `config.toml`. Details:
[People](../reference-people.md#name-the-groups).

## Options

| Option | What it does |
|---|---|
| `--path PATH` | Only the photos below this folder (host path, as you mounted it); repeat it for several. |
| `--sample N` | Analyse N random photos, print the time per photo and the estimate of a full run, and stop. |
| `--forget` | Delete every face from the cache, then show that none is left; asks before deleting the names of `config.toml` too. |
| `--port PORT` | Port of the page, 8088 by default; publish the same one. |

## Your privacy

The numbers that describe a face are **biometric data**. They stay in the cache, never in your
photos nor in the reports; the page is served on `127.0.0.1` only and cuts the faces out of the
photos on request, never saved. The only network access is the one-time download of the two
models from OpenCV Zoo, checked by their SHA-256: it sends nothing about your photos.

## Good to know

- The settings `[people]` (`similarity`, `min_face`, `min_sharpness`) only change the grouping:
  nothing is analysed again.
- `audit --people` looks for the faces right after an audit, once you agreed to the time it
  takes; `with_audit = true` in `[people]` does it at every audit.
- Videos are not analysed yet.
- Without network, the error names the two model files to save by hand into the `models` folder
  of the cache.

## Go further

- [People](../reference-people.md): how it works, naming, the settings, what comes next.
- [Sorting, step 10: sort by person](../sort/10-sort-by-person.md): from the named groups to
  sorted folders.

## The built-in help

<details>
<summary><code>people --help</code></summary>

<!-- capture: help-people.txt -->
```text
 Usage: media-hygiene people [OPTIONS]

 🔒 Read-only: never changes your photos. Find the faces in the photos, group
 those alike and name them in your browser. Faces kept in the cache, never sent
 anywhere.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --path            <str>               Only the photos below this folder      │
│                                       (host path, as you mounted it); repeat │
│                                       it for several. Default: every photo   │
│                                       of the index.                          │
│ --sample          <int range> [x>=0]  Analyse this many random photos, print │
│                                       the time per photo and the estimate of │
│                                       a full run, and stop.                  │
│ --forget                              Delete every face from the cache, then │
│                                       show that none is left; asks before    │
│                                       deleting the names of config.toml too. │
│ --port            <int range> [x>=1]  Port of the page. docker run publishes │
│                                       it under the same number on your       │
│                                       computer: -p 127.0.0.1:9000:9000 for   │
│                                       --port 9000. Default: 8088.            │
│ --help    -h                          Show this message and exit.            │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [All commands](../reference-commands.md) · [Documentation](../README.md)
