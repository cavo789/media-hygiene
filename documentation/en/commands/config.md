# `config`: every setting, and where it comes from

[Documentation](../README.md) › [Commands](../reference-commands.md) › `config` · 🇫🇷 [Français](../../fr/commands/config.md)

`config` shows every setting the tool will use, **where each one comes from** (the built-in
default, `config.toml`, an environment variable), and the state of each mount point. The first
time, it also creates a commented `config.toml` for you to fill in.

## At a glance

| | |
|---|---|
| Your photos | 🔒 Never changed. |
| Needs | Nothing. |
| Recommended | `/config`, and the same `-v` options as your usual command, to see their state. |
| Writes | A commented `config.toml` in `/config`, the first time only. |
| Undo | Delete `config.toml` to get the defaults back. |
| With `mh` | `mh config`. |

## When to use it

- **Once, at the start**, to get a commented `config.toml`.
- **When a setting does not seem to apply**: the *Origin* column tells which layer won.
- **When a folder is not seen**: the mount table says what is mounted, missing or read-only.

## Run it

```powershell
mkdir "$HOME\media-hygiene\config"
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

## Who wins?

From the weakest to the strongest: the built-in default, `config.toml`, an environment variable
(`-e MEDIA_HYGIENE_<SECTION>__<KEY>=…`, such as `-e MEDIA_HYGIENE_CLEAN__CONFIRM=false`), then
the option of the command line.

## Good to know

- `config` has no option of its own; the global ones apply (`--locale`, `--verbosity`).
- `/config` holds `config.toml` **only**: never put anything else there.
- A setting unknown to this version is said, with its line: see
  [troubleshooting](../reference-troubleshooting.md#a-setting-of-configtoml-is-unknown-to-this-version).

## Go further

- [7. The configuration file](../clean/07-configuration-file.md#check-what-the-tool-uses-config)
- [Mount points](../reference-mount-points.md)

## The built-in help

<details>
<summary><code>config --help</code></summary>

<!-- capture: help-config.txt -->
```text
 Usage: media-hygiene config [OPTIONS]

 🔒 Read-only: never changes your photos. Show every setting, where it comes
 from, and the mount points.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help  -h        Show this message and exit.                                │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [All commands](../reference-commands.md) · [Documentation](../README.md)
