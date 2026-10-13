# 0128 — `config --upgrade`: add the settings of a newer version to an existing config.toml

- **Priority**: Medium — every user who created config.toml before an update
- **Batch**: config
- **Depends**: —
- **Files**: `src/media_hygiene/cli/cmd_config.py`, `src/media_hygiene/config/upgrade.py` (new), `src/media_hygiene/config/loader.py`, `src/media_hygiene/config/templates/config.toml.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/config.md`, `documentation/fr/commands/config.md`, `documentation/en/clean/07-configuration-file.md`, `documentation/fr/clean/07-configuration-file.md`, `tests/unit/test_config_upgrade.py` (new)

## Context

`write_default_config` (`config/loader.py`) writes the commented `config.toml` once, never over
an existing file. A missing key takes its default, so a file from two weeks ago still works, but
its owner never sees the comments of the settings added since. Today the only way to find them
is to generate a fresh file in an empty folder and diff it by hand.

Nothing in the file says which version wrote it either, so the tool cannot tell the user that
there is something new.

## What to do

### Record the version that wrote the file

- Add a machine-readable comment line to the header of `config.toml.j2`, e.g.
  `# media-hygiene-config: 0.4.0`, rendered with `importlib.metadata.version("media-hygiene")`.
  Use a comment, not a key: it is not a setting, so `Settings`, `known_keys` and the `config`
  table stay unchanged, and an older image reading the file does not reject it as an unknown key.
- A file without the line (created before this TODO) counts as "version unknown". The merge
  still works because it compares keys, not versions. The version only feeds the messages.

### `media-hygiene config --upgrade`

- Render the template in the file's language (`general.locale`, else the active one). Parse it
  and the user's file with tomlkit, which `places/config_file.py` and `people/config_file.py`
  already use.
- A missing table: copy it whole, with its comments, at its template position (after the
  previous table that the file already has).
- A missing key in an existing table: insert it with its comment block, after the previous
  template key that the file already has.
- **Never** change an existing value, never reorder, never remove. A key unknown to this version
  stays where it is: the loader already reports it, with its line (0081).
- Arrays of tables (`[[classify.rules]]`, `[[classify.places]]`, the people) are the user's own:
  leave them alone.
- Update the version line, or add it to the header.
- Check before writing: `load_settings` must accept the merged text, otherwise write nothing and
  explain why. Write atomically, as `places/config_file.py` does. **No `.bak` in `/config`**,
  since that mount holds config.toml only. Offer `--dry-run` (list what would be added, write
  nothing) instead.
- Proof, not promise: re-read the file from disk and list what it now contains that it did not
  contain before (`[review] port`, `[tags] …`), or "already up to date (0.4.0)".
- Refuse clearly when `/config` is not persistent or is mounted read-only (reuse
  `runtime.persistent(MountKind.CONFIG)` and `is_read_only`).
- A Typer option with help text, translated. Reason with `--locale fr`: the comments added are
  in the file's language, even when the run is in another one.

### Tell the user, once per run

- When the file's version is older than the image's (or unknown) **and** the template has keys
  the file lacks, print one tip from `config` (and possibly at the start of every command, if it
  stays a single line): "💡 config.toml was written by 0.3.0: 3 new settings since. `config
  --upgrade` adds them with their explanation; your values are kept."

## Acceptance

- Unit tests (tmp_path): a file missing a key, missing a whole table, with a user comment and a
  changed value (both kept byte for byte), with an unknown key (kept), with `[[classify.rules]]`
  (untouched), already up to date (nothing written, mtime unchanged), without a version line
  (upgraded and stamped), `--dry-run` (nothing written), read-only `/config` (refused, no
  traceback).
- After the upgrade, every key of the template is in the file and `load_settings` gives the same
  effective values as before.
- `commands/config.md` (en + fr) documents `--upgrade` and `--dry-run` with the refreshed `--help`
  capture. `07-configuration-file.md` (en + fr) gets a short "After an update" section, Windows
  paths first. `i18n_update`, then the French translation.
