# `people`: find the faces and group those alike

[Documentation](../README.md) › [Commands](../reference-commands.md) › `people` · 🇫🇷 [Français](../../fr/commands/people.md)

`people` finds the **faces** in your photos, groups those that look alike (probably one person
per group), and shows the groups in your browser, largest first. Everything runs on your
computer: the faces stay in the cache, never sent anywhere. This first version finds and groups;
naming the groups comes next.

## At a glance

| | |
|---|---|
| Your photos | 🔒 Never changed: mount them `:ro`. |
| Needs | Your folders, `/cache` (writable: the faces are kept there), and `-p 127.0.0.1:8088:8088`. |
| Writes | The faces and the two face models (39 MB, once), in the cache. |
| Undo | `people --forget` deletes every face from the cache. |
| With `mh` | `mh people`: the port is published for you. |

## Run it

```powershell
docker run --rm -it -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  cavo789/media-hygiene people
```

The first run downloads the two face models into the cache, once. Each photo is analysed once;
the next runs analyse only the new ones. Then it prints the groups found and the address of the
page: a click on a face opens its photo. Ctrl+C stops it.

## Options

| Option | What it does |
|---|---|
| `--path PATH` | Only the photos below this folder (host path, as you mounted it); repeat it for several. |
| `--sample N` | Analyse N random photos, print the time per photo and the estimate of a full run, and stop. |
| `--forget` | Delete every face from the cache, then show that none is left. |
| `--port PORT` | Port of the page, 8088 by default; publish the same one. |

## Your privacy

The numbers that describe a face are **biometric data**. They stay in the cache, never in your
photos nor in the reports; the page is served on `127.0.0.1` only and cuts the faces out of the
photos on request, never saved. The only network access is the one-time download of the two
models from OpenCV Zoo, checked by their SHA-256: it sends nothing about your photos.

## Good to know

- The settings `[people]` (`similarity`, `min_face`, `min_sharpness`) only change the grouping:
  nothing is analysed again.
- Videos are not analysed yet.
- Without network, the error names the two model files to save by hand into the `models` folder
  of the cache.

## Go further

- [People](../reference-people.md): how it works, the settings, what comes next.

## The built-in help

<details>
<summary><code>people --help</code></summary>

<!-- capture: help-people.txt -->
```text
 Usage: media-hygiene people [OPTIONS]

 🔒 Read-only: never changes your photos. Find the faces in the photos and
 group those alike, shown in your browser. Kept in the cache, never sent
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
│                                       show that none is left.                │
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
