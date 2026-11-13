# `config`: every setting, and where it comes from

[Documentation](../README.md) › [Commands](../reference-commands.md) › `config` · 🇫🇷 [Français](../../fr/commands/config.md)

## In short

**Check what the tool will use before it acts: every setting with where it comes from, every
folder with its state.**

`config` shows every setting, **where each one comes from** (the built-in default,
`config.toml`, an environment variable, the command line), and the state of each mount point.
The first time, it also creates a commented `config.toml` for you to fill in.

**When**: once at the start, to get that `config.toml`; then whenever a setting does not seem to
apply or a folder is not seen.

**Try it**:

```powershell
mkdir -Force "$HOME\media-hygiene\config"
docker run --rm -it -v "$HOME\media-hygiene\config:/config" cavo789/media-hygiene config
```

## At a glance

| | |
|---|---|
| Your photos | 🔒 Never changed. |
| Needs | Nothing. |
| Recommended | `/config`, and the same `-v` options as your usual command, to see their state. |
| Writes | A commented `config.toml` in `/config`, the first time only; with `--upgrade`, the settings it lacks; with `--convention`, the layouts of the sort convention, once you say yes; with `tidy --apply`, the entries removed (a copy in `/cache/config-backups/` first). |
| Undo | Delete `config.toml` to get the defaults back. |
| With `mh` | `mh config`. From the home page, this step shows what it prints in the page itself (nothing in the terminal); typed, it prints as before. |

## Run it

```powershell
mkdir -Force "$HOME\media-hygiene\config"
docker run --rm -it -v "$HOME\media-hygiene\config:/config" cavo789/media-hygiene config
```

The first run says *💡 A commented configuration file was created: /config/config.toml*. Open it
in `C:\Users\<you>\media-hygiene\config` with any text editor. With
`cavo789/media-hygiene --locale fr config`, its comments are in French.

## Read the result

- **Effective settings**: one line per setting (`general.timezone`, `folders.preferred`,
  `clean.confirm`…), its value and its *Origin*: `default`, `config.toml`, `environment` or
  `command line`.
- **Extension categories (--ext)**: what `photo`, `raw`, `video`, `media` and your own
  categories hold.
- **Mount points**: `/data/…`, `/config`, `/journal`, `/quarantine`, `/reports`, `/cache`, each
  *mounted*, *read-only* or *not mounted* (*nothing kept after the run* for a tool folder), with
  the folder of your computer behind it when Docker Desktop tells it.

## After an update: `--upgrade`

A newer version may bring new settings. Your `config.toml` still works without them (each one
takes its default value), but its comments do not tell you about them. `config` says so in one
line, *💡 config.toml was written by 0.3.0: 3 new settings since.*, then:

```powershell
# List what would be added, write nothing
docker run --rm -it -v "$HOME\media-hygiene\config:/config" cavo789/media-hygiene config --dry-run

# Add them, each with its explanation
docker run --rm -it -v "$HOME\media-hygiene\config:/config" cavo789/media-hygiene config --upgrade
```

Each missing setting is added with its comment, after the setting that comes before it; a
missing table is added whole. **Your values, your comments and your rules are kept**, nothing is
moved or removed, and the comments added are in the language of your file. The file is read back
from the disk and the console lists what it now holds. `/config` mounted with `:ro` is refused
(`--dry-run` still works); no backup is left in `/config`.

## The sort convention: `--convention`

`config.toml` is written whole on the first run, so a newer default layout never reaches it. A
file written before the [sort convention](../sort/04-classify.md#the-convention-year-month-event)
keeps `{year}/{category}` and its *To check* / *To sort* folders; `classify` says so in one line.
`config --convention` lists each layout that differs, old → new, **asks**, then writes them
(comments kept) and reads the file back:

```powershell
mh config --convention --dry-run   # list only
mh config --convention             # list, ask, write
```

Nothing is rewritten without your yes. Your rules are not touched: a rule whose category has
several folder levels (`Parties/Christmas`) is named by `classify`, for you to shorten.

## Tidy it: `config tidy`

Over the years `config.toml` keeps entries that point at nothing any more: a rule
`match = "path"` whose photos `sort` moved away, a `[[places.folders]]` whose folder was
renamed. `config tidy` lists them, each with its reason, **without changing anything** 🔒:

```powershell
mh config tidy           # list only
mh config tidy --apply   # remove the ticked entries
```

| Entry | Pointing at nothing when |
|---|---|
| `[folders]` `preferred`, `protected`, `excluded`, `backups` | the folder does not exist, or is listed twice |
| `[[places.folders]]` | its folder does not exist, or is listed twice |
| `[[classify.rules]]` `match = "path"` / `"camera"` | no path / no camera of the index matches its `pattern` |
| `[[classify.rules]]` `match = "date_range"` | no indexed photo was taken on its dates: shown **unticked** (a rule written before an import); `--dates` ticks it too |
| `[[classify.rules]]` `match = "path"` (superseded) | every file it matches already sits in a folder you named (`2017\2017-04\Bruges`): `sort` would move them out of it. Shown **unticked** (a rule may rename a folder on purpose); `--superseded` ticks it too |
| `[[classify.clocks]]` | no photo of that camera on its dates |

A folder on a drive that is not mounted (a USB stick) is **not judged**, and said so. An
empty index judges no rule: run `audit` on all your folders first. A `path` rule whose pattern
starts with a folder no audit ever covered (`^E:\\Stick\\…`) is left alone too. Your hand-drawn places
and the spots set aside are never proposed.

`--apply` first copies `config.toml` to `/cache/config-backups/` (dated), removes the ticked
entries (comments and order kept), then reads the file back and says how many are gone. To
undo, copy that file back over `config.toml`: the console gives the line. At the end of
`sort`, one 💡 line says when entries point at nothing.

The events remembered by the pages live in `/config/events/<year>.toml`, not in `config.toml`.
Those an older version wrote into `config.toml` (a `date_range` rule named after its category,
such as `Turin` or `Turin (July 2019)`) are listed by `config tidy` and moved there by `--apply`,
once, after the same dated copy; your hand-written rules stay in `config.toml`.

## Who wins?

From the weakest to the strongest: the built-in default, `config.toml`, an environment variable
(`-e MEDIA_HYGIENE_<SECTION>__<KEY>=…`, such as `-e MEDIA_HYGIENE_CLEAN__CONFIRM=false`), then
the option of the command line.

## Good to know

- `config` has the action `tidy` and the options `--upgrade`, `--convention`, `--dry-run`, `--apply`
  `--dates` and `--superseded`; the global ones apply too
  (`--locale`, `--verbosity`).
- `/config` holds `config.toml` **only**: never put anything else there.
- A setting unknown to this version is said, with its line: see
  [troubleshooting](../reference-troubleshooting.md#a-setting-of-configtoml-is-unknown-to-this-version).
  Several problems are listed one per line; one in a rule or a place names it by its number and
  its `name` (`[[classify.rules]] number 2 ('Birthday')`).

## Go further

- [7. The configuration file](../clean/07-configuration-file.md#check-what-the-tool-uses-config)
- [Mount points](../reference-mount-points.md)

## The built-in help

<details>
<summary><code>config --help</code></summary>

<!-- capture: help-config.txt -->
```text
 Usage: media-hygiene config [OPTIONS] [action]

 🔒 Read-only: never changes your photos. Show every setting, where it comes
 from, and the mount points.

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│   action      <tidy>  tidy: list the entries of config.toml that point at    │
│                       nothing any more (folders gone, rules matching no      │
│                       photo).                                                │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --apply               <bool>  With tidy: remove the ticked entries, after a  │
│                               copy of config.toml.                           │
│ --dates               <bool>  With tidy: tick the date_range rules with no   │
│                               photo too.                                     │
│ --superseded          <bool>  With tidy: tick the path rules whose files     │
│                               already sit in folders you named too.          │
│ --upgrade             <bool>  Add the settings of this version to your       │
│                               config.toml, with their explanation; your      │
│                               values and comments are kept.                  │
│ --convention          <bool>  Move the  layouts of your config.toml to the   │
│                               sort convention year/year-month/event: shows   │
│                               each change, asks, writes.                     │
│ --dry-run             <bool>  With --upgrade or --convention: list what      │
│                               would change, write nothing.                   │
│ --help        -h      <bool>  Show this message and exit.                    │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [All commands](../reference-commands.md) · [Documentation](../README.md)
