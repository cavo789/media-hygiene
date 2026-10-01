# 0042 — Extension categories: `--ext photo`, and user-defined ones in `config.toml`

- **Priority**: Medium
- **Batch**: scan
- **Depends**: —
- **Files**: `src/media_hygiene/config/categories.py` (new), `src/media_hygiene/config/settings.py`, `src/media_hygiene/config/layers.py`, `src/media_hygiene/services/policy.py`, `src/media_hygiene/services/crosscheck.py`, `src/media_hygiene/services/data_checks.py`, `src/media_hygiene/cli/options.py`, `src/media_hygiene/cli/cmd_config.py`, `src/media_hygiene/config/templates/config.toml.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/06-file-types.md`, `documentation/fr/06-file-types.md`, `documentation/en/07-configuration-file.md`, `documentation/fr/07-configuration-file.md`, `documentation/en/reference-commands.md`, `documentation/fr/reference-commands.md`, `tests/unit/test_config.py`, `tests/unit/test_scan_basics.py`

## Context

`[scan] extensions` and `--ext` only take extensions. To analyse "the videos", the user has to
type the 15 video extensions; to find duplicate documents, `--ext pdf,docx,doc,odt,txt,xlsx` on
every run. [sorta](https://github.com/shinKatana0/sorta/blob/main/config.example.yaml#L50-L53)
names its lists (`photo`, `raw`, `video`). The same idea here gives:

```powershell
media-hygiene audit --ext video
media-hygiene audit --ext photo,raw
media-hygiene audit --ext documents   # defined in config.toml
```

```toml
[scan]
extensions = ["photo", "video"]

[scan.categories]
documents = ["pdf", "docx", "doc", "odt", "txt"]
```

## Proposal

- **Built-in categories**, derived from the constants (never a second list to keep in sync):
  `photo` (`IMAGE_EXTENSIONS`), `raw`, `video`, and `media` (the three: today's default scope,
  still used when `extensions` is empty).
- **Built-in categories are read-only.** A category is only a name for a list of extensions: what
  happens to a file (Pillow / LibRaw / `ffprobe` check, deleted or quarantined) still follows
  its extension, never its category. Letting `photo` gain `jxl` would mean decoding a type the
  code does not support: that is a code change with its test, not a setting. Redefining
  `photo`, `raw`, `video` or `media` in `[scan.categories]` is a validation error that says so.
- **User categories** in `[scan.categories]`: names `[a-z0-9_-]+` (case ignored), values
  validated like `extensions` today (normalised, sidecars refused). They may mix media and other
  extensions (`web = ["png", "webp", "svg"]`): the PNG files stay images, the SVG files are other
  files (quarantined, see 0018 and 0023). One level only: a category does not list categories.
- **Resolving `--ext` / `extensions`**: a value with a leading dot is always an extension; a
  value without one is a category when that name exists, otherwise an extension (`--ext pdf`
  keeps working). `raw` now means the category; `.raw` still asks for the extension.
- **Typo guard**: a dotless value that is not a category but is close to one
  (`difflib.get_close_matches`: `photos`, `videos`) is an error: *"photos: unknown category, did
  you mean photo? For the extension, write .photos."* Without it, `--ext photos` silently
  analyses nothing.
- **Where**: keep what the user asked for (names as written) for the messages, and expose the
  resolved extensions; the consumers use the resolved set: `ScanFilters` (`services/policy.py`),
  the Czkawka command (`services/crosscheck.py`, `-x` needs real extensions),
  `ScanSettings.other_files`. `settings.py` (193 lines) and `constants.py` (200 lines) are at the
  size limit: the category table and its validation go in `config/categories.py`.
- **Env layer**: `MEDIA_HYGIENE_SCAN__CATEGORIES` holds a JSON object
  (`{"documents": ["pdf", "docx"]}`); `read_env_layer` only parses JSON arrays today. It replaces
  the whole table from the file (the merge is per key), which is documented.
- **Messages**:
  - `--ext` help: *"e.g. --ext photo,video or --ext png,webp; categories: photo, raw, video,
    media and those of config.toml [scan.categories]"* (the help is built before the settings are
    read: user categories are not listed there);
  - the audit's scope warning (`data_checks.py`) names the categories:
    *"Only analysed: video, documents (pdf, docx, txt)."* rather than 20 extensions;
  - `media-hygiene config` lists every category (built-in and user) with its extensions, like
    it shows the built-in `generated_names`.
- `config.toml.j2`: the `extensions` comment mentions the categories; a commented
  `[scan.categories]` example (`# documents = ["pdf", "docx", "txt"]`).

Later, the classify/sort backlog (0026, 0028) can reuse the same categories (sort only the
photos), out of scope here.

## Acceptance

- [ ] `--ext video`, `--ext photo,raw`, `--ext media` analyse exactly those extensions;
  `--ext pdf` and `--ext .raw` still mean extensions.
- [ ] A user category from `config.toml` and from `MEDIA_HYGIENE_SCAN__CATEGORIES` works with
  `--ext`; one mixing `png` and `svg` decodes the PNG files and quarantines the SVG copies.
- [ ] Errors: redefining a built-in category, a sidecar in a category, a malformed name, a close
  typo (`photos`) — each message says how to fix it.
- [ ] `crosscheck` passes the resolved extensions to Czkawka.
- [ ] `--ext` help, `config.toml` template, `media-hygiene config` and the scope warning show the
  categories; strings translated (`i18n_update`).
- [ ] Step 6 (file types), step 7 (configuration file) and the command reference updated in
  `documentation/en` and `documentation/fr`; the `audit-ext.txt` capture refreshed
  (`docs_screenshots`).
