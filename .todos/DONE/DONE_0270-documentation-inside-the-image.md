# 0270 — The documentation inside the image: the version of the tool, offline, in the home page's look

- **Priority**: Medium — asked by the maintainer (2026-10-20)
- **Batch**: docs
- **Depends**: 0265, 0266
- **Files**: `Dockerfile`, `.dockerignore`, `src/media_hygiene/docs/` (new: `render.py`, `nav.py`, `pages.py`, `templates/doc.html.j2`), `src/media_hygiene/review/home_app.py`, `src/media_hygiene/review/templates/home.html.j2`, `src/media_hygiene/review/templates/home.js.j2`, `src/media_hygiene/cli/home_state.py`, `.config/mkdocs/hooks.py`, `tests/unit/test_docs_render.py` (new), `tests/unit/test_documentation.py`, `documentation/en/development.md`, `documentation/fr/development.md`, `CLAUDE.md`

## Context

The home page (0266) links each action to its chapter on the public site (MkDocs Material on
GitHub Pages). A click leaves the tool's look, "a visual shock" (the maintainer, 2026-10-20).
The site also shows the docs of `main`, which may describe a command the user's image does not
have yet: 0177's "a command the guide shows is unknown". The maintainer asked whether the
documentation could ship inside the image, in the tool's own look.

Measured on 2026-10-20:

- 128 pages (64 per language), 1.38 MB of Markdown and 4.69 MB of screenshots (WebP), in
  `documentation/{en,fr}`;
- the image is 142 MB (Docker Hub's `full_size` of `latest`, amd64);
- the engine of the public site is already installed with the `docs` dependency group:
  Python-Markdown 3.11 and pymdown-extensions 12.2;
- `.config/mkdocs/mkdocs.yml` lists its extensions (admonition, attr_list, md_in_html, tables,
  toc with permalinks, pymdownx details, highlight and superfences);
- `hooks.py` gives GitHub's anchors (`pymdownx.slugs.slugify(case="lower")`) and rewrites the
  links that leave a language;
- `.dockerignore` is an allowlist: `documentation/` does not enter the build context today.

## What to do

1. **Render when the image is built, never at run time.** A `docs` stage in the Dockerfile:
   - installs the `docs` group only, from `uv.lock`;
   - renders `documentation/en` and `documentation/fr` with the site's extensions and anchors,
     sharing one module with `hooks.py` (link rewriting, slugs) so the two can never drift;
   - writes one HTML fragment per page (the body only) and one index per language. The index
     holds the `nav` of `mkdocs.yml` and each page's title, `h2` and `h3` with their anchors.

   The runtime stage copies the result and the images. The renderer and its libraries stay out
   of the runtime image. `.dockerignore` lets `documentation/` and `.config/mkdocs/mkdocs.yml`
   in.
2. **Served by the home server** at `/docs/<lang>/<page>/`, inside 0266's shell (sidebar, top
   bar, theme, the meerkat). Each page gets:
   - its table of contents, and previous and next in the `nav` order;
   - the FR/EN switch to the same page in the other language;
   - its images under `/docs/<lang>/images/`.

   Internal links are rewritten to these routes, anchors kept; outside links open a new tab.
   The quick guides keep their look (`overrides/stylesheets/guide.css`, ported). The
   `<!-- capture: … -->` blocks keep the terminal look.
3. **The links.** On the tool's own pages, every "Doc" link (0265's `doc`) opens the page served
   here, so the help has the version of the tool that runs. In the terminal (the CLI's tips and
   errors) and in the HTML reports opened from disk, the links stay on the public site: no
   server answers there.
4. **The palette** (<kbd>Ctrl</kbd>+<kbd>K</kbd>) also finds the doc's sections, read from the
   index: a "Documentation" group under the actions.
5. **The public site stays**: for reading before installing, for search engines and for the
   README's links.
6. **Development.** `hygiene home` from the sources renders into `/tmp` on first use when the
   built docs are missing; the devcontainer has the `docs` group.

## Decisions (proposed defaults, for `/todo:iterate` to ask first)

1. **The public site's own look.** Give it the same tokens and the meerkat? The site already has
   its own stylesheet (`overrides/stylesheets/guide.css`). Proposed: a separate, smaller TODO
   after this one.
2. **A verb `mh docs [page]`** opening the local docs without the home page. Proposed: no; the
   home page's links and the palette are enough.

## Acceptance

- `tests/unit/test_docs_render.py`:
  - every page of both languages renders;
  - every internal link of the rendered HTML leads to an existing route and anchor;
  - a doc page asks nothing outside (CSP `self`, no outside URL in a `src`);
  - the index lists every page of the `nav`.
- `test_documentation.py`'s parity and link checks stay as they are.
- The image builds; `dive_ci` still passes; the added size is said, measured.

## Gain (estimated)

- **The help.** From a click that leaves the tool, to another look and maybe another version's
  text, to the chapter of the running version, in the same look, offline.
- **The cost.** About 5 MB more in a 142 MB image, +3.5 %. Estimated: the 4.69 MB of WebP do
  not compress further, and 1.38 MB of Markdown is about 0.4 MB compressed at 3:1.

## Decided (2026-10-20)

- Decision 1: the public site's look is **a separate, smaller TODO** filed after this one.
- Decision 2: **no `mh docs` verb**; the home page's links and the palette are enough.
  By the maintainer, at the start of `/todo:iterate`.

## Status — PARTIAL (2026-10-20)

### Done
- Items 1–6: the `docs` stage of the `Dockerfile` (the `docs` group only, `uv sync --only-group docs`)
  renders `documentation/{en,fr}` with `python -m media_hygiene.docs.render` (fragments, screenshots,
  `index.json` with the `nav`, titles, `h2`/`h3`); `links.py` is shared with `.config/mkdocs/hooks.py`
  (loaded by path: the site's CI installs the docs group only). The runtime copies the result to
  `/usr/share/media-hygiene/docs`; Markdown and MkDocs stay out (e2e test
  `test_the_documentation_is_inside_without_its_renderer`).
- Every page's server (not only the home page's: `review/shared_routes.py`) answers `/docs/…`;
  the "Doc"/"Documentation" links of the home page and of the review pages' bar open the served
  chapter; the terminal and the reports keep the site. The palette lists the docs' sections under
  the actions (a "Documentation" group, opened in a new tab).
- Development: `MEDIA_HYGIENE_DOCS_DIR` (set by the `hygiene` helper) renders the sources into
  `/tmp/media-hygiene/docs` on first use and when a page changed; `docs` is a default uv group
  (the builder uses `--no-default-groups`).
- Measured: the docs stage alone builds (`docker build --target docs`, 1.0 s to render 128
  pages); the output is 6.9 MB (6 912 KB, `du -sk` in the stage), 5.1 MB gzip-compressed
  (`tar czf`): +3.6 % of the 142 MB image, estimated from the compressed size.

### Not done
- The full image build and `dive_ci`, and a look at a page in a browser (light, dark, narrow).
  **Reason:** heavy on the maintainer's PC (image build) and no browser in the devcontainer; CI's
  image job builds the image and runs the new e2e test. To do: `build`, `dive_ci`, then
  `hygiene home` and open a Doc link.

## Closed (2026-10-21)

The remaining checks (`dive_ci`, a look in a browser) are TODO 0283; the image build and its e2e
test passed in CI on PR #32. Closed DONE by the maintainer (`/todo:inbox`).
