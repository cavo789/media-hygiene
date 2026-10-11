# 0074 — Write the tags into XMP sidecars, journaled and undoable

- **Priority**: Low — opt-in; after 0072 has run on the real collection
- **Batch**: tags
- **Depends**: 0072
- **Files**: `src/media_hygiene/tags/xmp.py` (new: read, merge, write), `src/media_hygiene/actions/` (journal kind, undo), `src/media_hygiene/scan/sidecars.py`, `src/media_hygiene/plan/keeper.py`, `src/media_hygiene/services/policy.py`, `src/media_hygiene/cli/` (`cmd_tags.py` option or subcommand), `src/media_hygiene/config/settings.py`, `src/media_hygiene/config/templates/config.toml.j2`, `pyproject.toml`, `documentation/en/`, `documentation/fr/`

## Context

The maintainer wants (2026-10-10) the tags of 0072 to travel with the photos, readable by any
application, so the work of several nights does not live in our index alone. The Gemini answer
proposed writing them into the image (EXIF `ImageDescription`, IPTC `Keywords`, XMP `Subject`)
with ExifTool. Not in the image itself (see 0072): it changes the bytes, hence the digests and
the duplicate groups, and risks the originals.

**XMP sidecars** (`IMG_1.jpg.xmp` or `IMG_1.xmp` next to the photo) carry the same fields
without touching the photo. digiKam, darktable and Lightroom read them; Immich reads them in
an external library (0009). This tool already knows them: `scan/sidecars.py` (`.xmp`, `.aae`,
`.thm`), `clean` moves a sidecar with its photo, `KeepPolicy` prefers a copy with a sidecar.

## Proposal

- **Fields**: `dc:subject` (tags, a bag), `dc:description` (the sentence, `x-default` +
  language), `photoshop:City` / `Iptc4xmpCore:Location` from `place` tags, later
  `Iptc4xmpExt:PersonInImage` from 0058. Which sources go into the file: `[tags] xmp_sources`
  (default `vision`, `place`; folder and date words are already visible in the path).
- **Never overwrite somebody else's sidecar**:
  - no sidecar → create one, marked `xmp:CreatorTool = "media-hygiene <version>"`;
  - a sidecar from another tool (Lightroom edits, darktable history) → merge: add our values
    to `dc:subject`, set `dc:description` only when empty, keep every other element and
    namespace byte for byte where possible; refuse (and list) a sidecar that does not parse;
  - our values are tracked so a re-run replaces them instead of piling up, and a tag the user
    removed in another application is not added back (compare with what we wrote last time).
- **Our sidecars must not change which copy is kept**: today a sidecar counts as "edits" in
  `KeepPolicy`. A sidecar created by media-hygiene (only our `CreatorTool`, only our fields)
  does not count; a merged one still does.
- **Only on the kept copy**: tag files after `clean`, or skip files that belong to a duplicate
  group, so that two copies do not get diverging sidecars.
- **Safety, like every write into the data folders**:
  - refused on `:ro` data mounts and without a persistent `/journal`;
  - protected folders never written;
  - write-ahead journal (new run kind), atomic write (temporary file + rename), the new file
    read back and parsed before the entry is marked `done` (proof, not promise);
  - `undo` deletes the sidecars we created and restores the previous content of the merged
    ones (kept in the journal or `/quarantine`);
  - dry run by default: `tags --write-xmp` lists what would change; `--yes` writes.
- **Library**: XML with the standard library (`xml.etree`) is enough for RDF/XMP of this size;
  parse untrusted sidecars safely (no external entities: `defusedxml` if a test shows the
  standard parser is exposed). No ExifTool.

## Acceptance

- [ ] Round-trip tests: create, merge into a Lightroom-like and a darktable-like sidecar
      (synthetic fixtures), re-run idempotent, user-removed tag not added back, undo.
- [ ] `KeepPolicy` test: a media-hygiene sidecar does not change the kept copy.
- [ ] Check by hand that digiKam (or exiftool) reads the tags of a generated sidecar; note the
      tool and version here.
- [ ] Documentation en + fr (what is written, where, how to undo); `.po` translated.

## Status — PARTIAL (2026-10-11)

### Done
- New command `media-hygiene xmp` (`cli/cmd_xmp.py`, panel "Act", not read-only): shows the
  sidecars it would write (dry run, the photo folders may stay `:ro`); `--apply` writes;
  `--path` limits to host folders. A separate command rather than `tags --write-xmp`: `tags`
  is read-only (help marker, `mh` launcher mounting the photos `:ro`), a writer must not be.
- Fields (`tags/xmp_doc.py`, `tags/xmp_merge.py`): `dc:subject` (bag) from
  `[tags] xmp_sources` (default `vision`, `place`), `dc:description` (`x-default`) from the
  model's sentence (`caption`), `xmp:CreatorTool` = `media-hygiene <version>` on new files;
  our own namespace (`mh:subjects`, `mh:description`) remembers what we wrote last.
- Merge rules: words already there kept first; ours no longer produced taken back; a word we
  wrote that the user removed elsewhere is not added again; the sentence only when empty or
  still ours; every other element, attribute, namespace prefix and the `xpacket` lines kept
  (ElementTree, prefixes re-registered). DOCTYPE, non-UTF-8 or broken XML refused and listed.
  Re-run idempotent (semantic comparison, no rewrite).
- Where: `IMG_1.jpg.xmp` (any case) or `IMG_1.xmp` when it belongs to that photo alone;
  otherwise a new `IMG_1.jpg.xmp`.
- Left out: protected folders, files with an identical copy (SHA-256 in the index: `clean`
  first), files without words, stale index rows.
- Safety (`actions/xmp_write.py`, `actions/xmp_undo.py`): `ensure_can_act` (persistent
  `/journal`, no `:ro` data mount); new phase `xmp` and kinds `create-xmp` / `merge-xmp`
  journaled pending → write → done; temporary file + `renameat2(RENAME_NOREPLACE)` (fallback
  `O_EXCL`) for new files, `os.replace` only if the old bytes are unchanged for merges; the
  previous bytes copied (verified) into `/quarantine/<run>/…` first; read back, SHA-256
  checked and parsed before `done`. `undo` removes ours / restores the previous bytes only
  while the sidecar still holds what the run wrote (else kept, with the reason); a `pending`
  write whose content is absent counts as never done. `history` shows a *Sidecars* column;
  `status` counts an `xmp` run as undoable.
- `KeepPolicy`: the audit ignores sidecars written by `xmp` alone (`tags/xmp_owner.py`,
  `services/audit.py`): our sidecar never changes the copy kept; a merged one still counts.
- Checked by hand: exiftool 13.25 reads `Subject`, `Description`, `CreatorTool` of a created
  sidecar, and keeps Lightroom's `crs:Exposure2012` / darktable's history after a merge.
- No new dependency (`defusedxml`): a DOCTYPE is refused before parsing, so no entity can be
  declared; `pyproject.toml` untouched.
- Tests: `tests/unit/test_xmp_merge.py`, `test_xmp_owner.py`, `test_xmp_actions.py`,
  `tests/integration/tags/test_xmp_command.py` (fixtures `tests/support/sidecars.py`).
- Docs en + fr (`reference-tags.md`, `reference-commands.md`, `reference-safety.md`,
  `reference-sidecars.md`, documentation README); `.po` translated.

### Not done
- `photoshop:City` / `Iptc4xmpCore:Location` from the `place` tags.
  **Reason:** a `place` tag does not say whether it is a personal place, a town or a country
  (0072 stores the word only); writing the right field needs that kind on the tag (a column or
  a sub-source in `index/tag_rows.py`). The place words go into `dc:subject` meanwhile.
- `Iptc4xmpExt:PersonInImage`.
  **Reason:** depends on 0058 (people from faces), not done.
- Help captures of `reference-commands.md` (`xmp`, `search`).
  **Reason:** `docs_screenshots` needs a Docker build, not run during the night session.
