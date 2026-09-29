# 7. The configuration file

[Documentation](../README.md) › Cleaning, step 7 of 13 · 🇫🇷 [Français](../../fr/clean/07-configuration-file.md)

Your preferred folders, your excluded backup, your language: rather than typing them in every
command, write them once in a file, `config.toml`. The tool reads it at every run.

## Create the file

The tool only sees the folders you mount, so give it a folder of yours on `/config`, and run
the `config` command once:

```powershell
mkdir "$HOME\media-hygiene\config"
docker run --rm -it -v "$HOME\media-hygiene\config:/config" cavo789/media-hygiene config
```

The first line says what happened:

<!-- capture: config-first.txt|A commented configuration file| -->
```text
💡 A commented configuration file was created: /config/config.toml.
Effective settings
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ Setting                    ┃ Value                            ┃ Origin       ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━┩
│ general.locale             │ en                               │ command line │
│ general.verbosity          │ info                             │ default      │
│ general.color              │ never                            │ command line │
│ folders.preferred          │ []                               │ default      │
│ folders.protected          │ []                               │ default      │
│ folders.excluded           │ []                               │ default      │
│ scan.extensions            │ []                               │ default      │
│ keep.generated_names       │ ['_?(IMG|VID|MVI|MOV|SAM|DSC[NF] │ default      │
│                            │ ?|_DSC|PICT|CIMG)[_-]?\\d+',     │              │
│                            │ '(IMG|VID)[_-]\\d{8}[_-]\\d{6}([ │              │
│                            │ _-]\\d+)?',                      │              │
│                            │ '(IMG|VID|AUD)-\\d{8}-WA\\d+',   │              │
│                            │ '_?MG_\\d+', 'P\\d{7}',          │              │
│                            │ 'PXL_\\d{8}_\\d+.*',             │              │
│                            │ '\\d{8}_\\d{6}(_\\d+)?',         │              │
│                            │ '\\d{4}-\\d{2}-\\d{2}            │              │
│                            │ \\d{2}\\.\\d{2}\\.\\d{2}(-\\d+)? │              │
│                            │ ', '(GOPR|G[HX]\\d{2})\\d{4}',   │              │
│                            │ 'DJI_\\d+',                      │              │
│                            │ '(FB_IMG|received|Snapchat)[_-]\ │              │
│                            │ \d+', '(Screenshot|Screen        │              │
│                            │ Shot|Capture d.écran)([          │              │
│                            │ _-].*)?', 'image\\d*',           │              │
│                            │ '[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0 │              │
│                            │ -9a-f]{12}', '[0-9a-f]{16,}']    │              │
│ keep.generic_folders       │ ['DCIM', '\\d{3}[A-Z0-9_]{5}',   │ default      │
│                            │ 'Camera( Roll| Uploads)?',       │              │
│                            │ 'WhatsApp (Images|Video)',       │              │
│                            │ 'Sent',                          │              │
│                            │ 'Downloads?|Téléchargements',    │              │
│                            │ 'Screenshots|Captures d.écran',  │              │
│                            │ '(New folder|Nouveau dossier)(   │              │
│                            │ \\(\\d+\\))?',                   │              │
│                            │ 'Import(s|ed)?|Temp|tmp']        │              │
│ clean.confirm              │ True                             │ default      │
│ classify.target            │                                  │ default      │
│ classify.leave             │ []                               │ default      │
│ classify.timezone          │                                  │ default      │
│ classify.layout            │ {year}/{category}                │ default      │
│ classify.unsure_layout     │ {year}/To check/{category}       │ default      │
│ classify.manual_layout     │ {year}/To sort/{event}           │ default      │
│ classify.undated_layout    │ To sort/Undated                  │ default      │
│ classify.received_layout   │ To sort/Received and downloaded  │ default      │
│ classify.session_gap_hours │ 6.0                              │ default      │
│ classify.merge_gap_hours   │ 18.0                             │ default      │
│ classify.min_event_size    │ 5                                │ default      │
│ classify.event_year        │ start                            │ default      │
│ classify.sure              │ 80                               │ default      │
│ classify.unsure            │ 50                               │ default      │
│ classify.scores            │ {'existing-folder': 90,          │ default      │
│                            │ 'person-folder': 85,             │              │
│                            │ 'event-neighbour': 70,           │              │
│                            │ 'date-only': 90, 'no-signal': 0} │              │
│ classify.name_dates        │ ['(?:IMG|VID|PXL|MVIMG)?[_-]?(?P │ default      │
│                            │ <y>\\d{4})(?P<m>\\d{2})(?P<d>\\d │              │
│                            │ {2})[_-](?P<H>\\d{2})(?P<M>\\d{2 │              │
│                            │ })(?P<S>\\d{2}).*',              │              │
│                            │ '(?:IMG|VID|AUD)-(?P<y>\\d{4})(? │              │
│                            │ P<m>\\d{2})(?P<d>\\d{2})-WA\\d+' │              │
│                            │ , '(?:Screenshot|Capture)[       │              │
│                            │ _-]*(?P<y>\\d{4})-?(?P<m>\\d{2}) │              │
│                            │ -?(?P<d>\\d{2}).*',              │              │
│                            │ '(?P<y>\\d{4})-(?P<m>\\d{2})-(?P │              │
│                            │ <d>\\d{2})[                      │              │
│                            │ _](?P<H>\\d{2})(?P<M>\\d{2})[._] │              │
│                            │ (?P<S>\\d{2}).*']                │              │
│ classify.generic_folders   │ ['(My |Mes                       │ default      │
│                            │ )?(Photos|Pictures|Images|Videos │              │
│                            │ |Vidéos|Mes images)',            │              │
│                            │ '(Family|Famille|Photos de       │              │
│                            │ famille|Family photos)']         │              │
└────────────────────────────┴──────────────────────────────────┴──────────────┘

Mount points
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Mount            ┃ Folder on your computer ┃ State     ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ /data/c/Photos   │ C:\Photos               │ read-only │
│ /data/d/Old disk │ D:\Old disk             │ read-only │
│ /config          │ —                       │ mounted   │
│ /journal         │ —                       │ mounted   │
│ /quarantine      │ —                       │ mounted   │
│ /reports         │ —                       │ mounted   │
│ /cache           │ —                       │ mounted   │
└──────────────────┴─────────────────────────┴───────────┘

💡 Edit /config/config.toml to change these settings; command-line options win.
```

A commented `config.toml` has appeared in `C:\Users\<you>\media-hygiene\config`. Open it with any
text editor (Notepad is fine). Every setting is explained, for instance:

<!-- capture: config.toml|[general]|color =  -->
```toml
[general]
# Interface language: "en" or "fr".
# CLI: --locale
locale = "en"

# How much to log: "error", "warning", "info" or "debug".
# CLI: --verbosity
verbosity = "info"

# ANSI colours: "auto", "always" or "never".
# CLI: --color
color = "auto"
```

The file is never overwritten; delete it to get a fresh one.

> 💡 Its comments are written in the language of that first run, and that language is saved in
> it: created with `cavo789/media-hygiene --locale fr config`, the file is commented in French and
> holds `locale = "fr"`, so the next runs speak French without `--locale`.

## Fill it in

The settings of steps 5 and 6, in the file. Write Windows paths between **single quotes**:

```toml
[general]
locale = "en"          # en | fr

[folders]
preferred = ['C:\Photos\Old phone', 'C:\Photos\Family']
protected = []
excluded = ['D:\backup']

[scan]
extensions = []        # e.g. ["heic", "mp4"]; empty: every photo, RAW and video

[clean]
confirm = true         # clean asks before doing anything
```

- **`preferred`**: their copies are kept first, in this order (`--prefer`).
- **`protected`**: never modified, and their files are always the copies kept (`--protect`).
- **`excluded`**: never analysed, for a real backup (`--exclude`).
- **`extensions`**: only these file types (`--ext`).

Why single quotes? In double quotes, TOML turns the `\b` of `"D:\backup"` into a control
character; the tool refuses such a path rather than ignoring it.

Two advanced lists, `generated_names` and `generic_folders` (in `[keep]`), hold the regular
expressions of rules 5 and 6 of [the keep rules](05-choose-the-kept-copy.md#how-the-tool-chooses):
file names cameras and apps generate, folder names devices create. Leave them commented to use
the built-in lists; an empty list `[]` disables the rule.

## Use it

Add the same `-v …:/config` to every command, and the tool reads the file:

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v "D:\Old disk:/data/d/Old disk:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene audit
```

## Check what the tool uses: `config`

`config` shows every setting, where it comes from, and the state of each mount point. Run it
with the same `-v` options as your audit (here `config` instead of `audit`):

<!-- capture: config.txt -->
```text
Effective settings
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ Setting                    ┃ Value                            ┃ Origin       ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━┩
│ general.locale             │ en                               │ command line │
│ general.verbosity          │ info                             │ config.toml  │
│ general.color              │ never                            │ command line │
│ folders.preferred          │ []                               │ config.toml  │
│ folders.protected          │ []                               │ config.toml  │
│ folders.excluded           │ []                               │ config.toml  │
│ scan.extensions            │ []                               │ config.toml  │
│ keep.generated_names       │ ['_?(IMG|VID|MVI|MOV|SAM|DSC[NF] │ default      │
│                            │ ?|_DSC|PICT|CIMG)[_-]?\\d+',     │              │
│                            │ '(IMG|VID)[_-]\\d{8}[_-]\\d{6}([ │              │
│                            │ _-]\\d+)?',                      │              │
│                            │ '(IMG|VID|AUD)-\\d{8}-WA\\d+',   │              │
│                            │ '_?MG_\\d+', 'P\\d{7}',          │              │
│                            │ 'PXL_\\d{8}_\\d+.*',             │              │
│                            │ '\\d{8}_\\d{6}(_\\d+)?',         │              │
│                            │ '\\d{4}-\\d{2}-\\d{2}            │              │
│                            │ \\d{2}\\.\\d{2}\\.\\d{2}(-\\d+)? │              │
│                            │ ', '(GOPR|G[HX]\\d{2})\\d{4}',   │              │
│                            │ 'DJI_\\d+',                      │              │
│                            │ '(FB_IMG|received|Snapchat)[_-]\ │              │
│                            │ \d+', '(Screenshot|Screen        │              │
│                            │ Shot|Capture d.écran)([          │              │
│                            │ _-].*)?', 'image\\d*',           │              │
│                            │ '[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0 │              │
│                            │ -9a-f]{12}', '[0-9a-f]{16,}']    │              │
│ keep.generic_folders       │ ['DCIM', '\\d{3}[A-Z0-9_]{5}',   │ default      │
│                            │ 'Camera( Roll| Uploads)?',       │              │
│                            │ 'WhatsApp (Images|Video)',       │              │
│                            │ 'Sent',                          │              │
│                            │ 'Downloads?|Téléchargements',    │              │
│                            │ 'Screenshots|Captures d.écran',  │              │
│                            │ '(New folder|Nouveau dossier)(   │              │
│                            │ \\(\\d+\\))?',                   │              │
│                            │ 'Import(s|ed)?|Temp|tmp']        │              │
│ clean.confirm              │ True                             │ config.toml  │
│ classify.target            │                                  │ config.toml  │
│ classify.leave             │ []                               │ config.toml  │
│ classify.timezone          │                                  │ config.toml  │
│ classify.layout            │ {year}/{category}                │ config.toml  │
│ classify.unsure_layout     │ {year}/To check/{category}       │ config.toml  │
│ classify.manual_layout     │ {year}/To sort/{event}           │ config.toml  │
│ classify.undated_layout    │ To sort/Undated                  │ config.toml  │
│ classify.received_layout   │ To sort/Received and downloaded  │ config.toml  │
│ classify.session_gap_hours │ 6.0                              │ default      │
│ classify.merge_gap_hours   │ 18.0                             │ config.toml  │
│ classify.min_event_size    │ 5                                │ config.toml  │
│ classify.event_year        │ start                            │ default      │
│ classify.sure              │ 80                               │ default      │
│ classify.unsure            │ 50                               │ default      │
│ classify.scores            │ {'existing-folder': 90,          │ default      │
│                            │ 'person-folder': 85,             │              │
│                            │ 'event-neighbour': 70,           │              │
│                            │ 'date-only': 90, 'no-signal': 0} │              │
│ classify.name_dates        │ ['(?:IMG|VID|PXL|MVIMG)?[_-]?(?P │ default      │
│                            │ <y>\\d{4})(?P<m>\\d{2})(?P<d>\\d │              │
│                            │ {2})[_-](?P<H>\\d{2})(?P<M>\\d{2 │              │
│                            │ })(?P<S>\\d{2}).*',              │              │
│                            │ '(?:IMG|VID|AUD)-(?P<y>\\d{4})(? │              │
│                            │ P<m>\\d{2})(?P<d>\\d{2})-WA\\d+' │              │
│                            │ , '(?:Screenshot|Capture)[       │              │
│                            │ _-]*(?P<y>\\d{4})-?(?P<m>\\d{2}) │              │
│                            │ -?(?P<d>\\d{2}).*',              │              │
│                            │ '(?P<y>\\d{4})-(?P<m>\\d{2})-(?P │              │
│                            │ <d>\\d{2})[                      │              │
│                            │ _](?P<H>\\d{2})(?P<M>\\d{2})[._] │              │
│                            │ (?P<S>\\d{2}).*']                │              │
│ classify.generic_folders   │ ['(My |Mes                       │ default      │
│                            │ )?(Photos|Pictures|Images|Videos │              │
│                            │ |Vidéos|Mes images)',            │              │
│                            │ '(Family|Famille|Photos de       │              │
│                            │ famille|Family photos)']         │              │
└────────────────────────────┴──────────────────────────────────┴──────────────┘

Mount points
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Mount            ┃ Folder on your computer ┃ State     ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ /data/c/Photos   │ C:\Photos               │ read-only │
│ /data/d/Old disk │ D:\Old disk             │ read-only │
│ /config          │ —                       │ mounted   │
│ /journal         │ —                       │ mounted   │
│ /quarantine      │ —                       │ mounted   │
│ /reports         │ —                       │ mounted   │
│ /cache           │ —                       │ mounted   │
└──────────────────┴─────────────────────────┴───────────┘

💡 Edit /config/config.toml to change these settings; command-line options win.
```

- **Origin** says where each value comes from: `default`, `config.toml`, `environment` or
  `command line`.
- **Folder on your computer** shows the Windows folder behind each mount; `—` for a Docker
  volume such as the cache.

## Who wins?

From the strongest to the weakest: the command-line options, then the environment variables,
then `config.toml`, then the defaults. `--prefer` on the command line therefore replaces
`preferred` of the file for that run.

The environment variables are named `MEDIA_HYGIENE_<SECTION>__<KEY>` (two underscores),
for instance `-e MEDIA_HYGIENE_GENERAL__LOCALE=fr` in `docker run`; lists are written as JSON
arrays. Up to version 0.2 their prefix was `MEDIA_DEDUP_`: it still works until version 0.4.0,
with a warning.

---

← [6. Only some file types](06-file-types.md) · [Documentation](../README.md) · Next: **[8. Clean](08-clean.md)** →
