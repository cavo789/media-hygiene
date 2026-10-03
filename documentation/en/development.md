# Development

[Documentation](README.md) › For developers · 🇫🇷 [Français](../fr/development.md)

Only needed to change the tool. To use it, the [user guide](README.md#start-here)
is enough.

## Build the image from the sources

Anywhere the documentation says `cavo789/media-hygiene`, use your local `media-hygiene` instead:

```bash
git clone https://github.com/cavo789/media-hygiene.git
cd media-hygiene
docker build --tag media-hygiene .
```

The image compiles its own `ffprobe`, about 1 MB instead of 141 MB for a full build: the tool
only asks whether a video container opens, so the `ffprobe` stage of the `Dockerfile` keeps the
demuxers of the video extensions it analyses and nothing else. A new video extension needs its
demuxer there too; a test checks that both lists agree.

It compiles its own `ffmpeg` too, about 6 MB: to find [re-encoded
videos](clean/11-near-duplicates.md#videos-too-re-encoded-copies), the audit decodes a few
frames of each video, so the `ffmpeg` stage adds the decoders of phone, camera and older PC
videos (H.264, HEVC, MPEG-4, VP8/VP9, WMV/VC-1, ProRes, …), the scale and rotation filters and
raw output, nothing else. Both tools share the `VIDEO_DEMUXERS` list. AV1 is left out: its
decoder needs an external library, and such a video is simply not compared.

## The devcontainer

Open the repository in the devcontainer (VS Code, *Reopen in Container*). Every new terminal
shows the cheatsheet of helper commands (`welcome` redraws it):

| Helper | Purpose |
|---|---|
| `check` | The full quality gate: pre-commit (ruff, mypy strict, pylint, shellcheck, shfmt, hadolint) then the tests with ≥ 90 % branch coverage. |
| `lint`, `format`, `tests` | Pre-commit alone (new files included); auto-fix formatting; run targeted tests. |
| `hygiene …`, `demo` | Run the tool from the sources against `/tmp/media-hygiene/`; `demo` builds a sample tree and audits it, `demo_clean` empties `/tmp/media-hygiene/`. |
| `reports`, `reports_stop` | Serve the HTML reports on a free port chosen by the OS. |
| `build`, `e2e`, `dive`, `dive_ci` | Build the image, run the end-to-end tests (output kept in `/tmp/media-hygiene/e2e.log`), inspect or gate its layers. |
| `release` | Tag `vX.Y.Z` (the `pyproject.toml` version) and push it: CI publishes the image. |
| `i18n_extract`, `i18n_update`, `i18n_todo` | Refresh the gettext catalogs after changing a user-facing string; list the French entries still to translate. |
| `geonames_update` | Download GeoNames again and rebuild the offline towns of `src/media_hygiene/geo/data/` (CC BY 4.0: the date lands in its `ATTRIBUTION.txt`). |
| `todos` | List the open backlog (`.todos/`, see `/todo` and `/todo-plan`), then the partial and blocked ones. |
| `ci`, `ci_logs`, `ci_watch` | Latest CI runs of the branch; logs of the failed steps of the latest failed run; follow the latest run live. The GitHub CLI asks for `gh auth login` once. |
| `git_doctor`, `docker_doctor`, `docker_clean`, `deps` | After a crash: check the git objects (`--fix` repairs the empty ones); check Docker and list what e2e/docs runs left behind, then remove it; list the direct dependencies with a newer release. |

`check`, `lint`, `tests`, `e2e`, `docs_screenshots` and `hygiene` run gently: lower priority, half
the processors (`DEV_CPUS=8 check` to change it), a share the e2e and docs containers inherit.
Runs at full load crashed the WSL VM on Windows.

Settings and logins of the tools (`~/.config`, e.g. the GitHub CLI token) live in the
`media-dedup-config` Docker volume, outside the workspace: they survive rebuilds and can never be
committed. Never write a token in a tracked file (`devcontainer.json` included): this repository
is public.

## Code rules

Enforced by the tooling: everything typed, at most 200 lines per file and 3 parameters per
function, code in English, every user-facing string translated through gettext. Caches never land
in the repository (they live in `/tmp`).

## Documentation

The user documentation lives in `documentation/en/` and `documentation/fr/`, with the same file
names and the same screenshots (`images/`) in each language; `README.md` and `README_FR.md` only
hold the quick start and the table of contents. Update both languages with every user-facing
change. A test checks that every link and image of the READMEs and of the documentation exists,
and that both languages have the same pages.

`docs_screenshots` refreshes the screenshots (`images/`) and the console outputs of both
languages (`docs_screenshots fr`: French only). It rebuilds the image, draws a demo library of
synthetic pictures (landscapes drawn by `tests/support/docs/`, never a real photo), plays the
story of the guide with the real image in Docker volumes of its own, and takes the
screenshots with a headless Chromium (the Playwright image). A console output is regenerated
where an HTML comment, invisible on GitHub, announces it:

    <!-- capture: clean.txt|re:^1 |❓ -->
    ```text
    …
    ```

The comment names a capture, and optionally the lines to keep: from the first one containing
the second field (`re:` for a regular expression) to the next one containing the third
(`tests/support/docs/pages.py` has the details). Everything else in the pages is written by
hand; review the result with `git diff documentation/`.

## Continuous integration and releases

Every push and pull request runs the quality gate and the end-to-end tests on GitHub Actions
([`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)). To publish a new version, bump
`version` in `pyproject.toml`, commit and push `main`, then run `release`. It tags `vX.Y.Z` and
pushes the tag. CI then builds the image for amd64 and arm64, runs the end-to-end tests, and
pushes `cavo789/media-hygiene:<version>` and `:latest` to Docker Hub, with an SBOM and a provenance
attestation. This needs two repository secrets: `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` (a
Docker Hub access token with read/write scope).

The roadmap is in [.todos/plan.md](../../.todos/plan.md).
