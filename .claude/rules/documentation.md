---
paths:
  - "documentation/**"
  - "README.md"
  - "README_FR.md"
---

# User documentation — always apply

Two audiences, in this order: the end user who runs the published image (Windows, `mh`, no
clone), then the developer. "What is not documented does not exist." Checked by
`tests/unit/test_documentation.py`, `test_docs_commands.py`, `test_docs_site.py`, `test_docs_pages.py`.

- ✅ DO: **both languages in the same change**: `documentation/en/` and `documentation/fr/`
  keep the same file names and the same `images/`; a page or screenshot added in one exists in
  the other. French command captures carry `--locale fr`. ❌ DON'T: an English-only page "for
  now".
- ✅ DO: step by step, the simplest command first with the minimum of options, one option
  introduced at a time, `mh` first (Windows PowerShell 5.1: `mkdir -Force`, no `&&`); raw
  `docker run` lines and WSL/Linux in folded "without mh" boxes. References (every option,
  mounts) after the guide. One guide per goal after the shared `start/`: `clean/`, `sort/`,
  `find/`.
- ✅ DO: one page per CLI verb in `commands/`, listed in `reference-commands.md`, named in
  `COMMANDS_TOO` (`tests/support/docs/scenario.py`), in `nav` of `.config/mkdocs/mkdocs.yml`
  and in `cli/menu_catalog_*.py`; its `--help` block is a capture.
- ✅ DO: hand-write the prose; never edit the body of a `<!-- capture: … -->` block or a
  screenshot by hand: `docs_screenshots` regenerates them (synthetic pictures only, never
  real photos; host paths as a Windows reader sees them, `C:\Users\you\media-hygiene\…`). A
  changed console output or page makes them stale: say so, do not run it unasked (image build
  + browser).
- ✅ DO: every relative link reaches a file, every `#anchor` a heading (GitHub's slug); links
  the tool prints go to the site (GitHub Pages), never to GitHub's file view; no image in the
  repository without a page showing it.
- ✅ DO: flag 🤖 every command that needs a local AI model (Ollama), where it is pasted; mark
  read-only commands 🔒; end a step on the one 👉 What next line the CLI prints.
- ✅ DO: the glossary terms of `reference-glossary.md` (FR: lieu, tri, mettre de côté, événement);
  neutral examples only (`C:\Photos`, `C:\Family Photos`), no personal data (public repository).
- ✅ DO: help reached from a phone or TV: a few task lines, the full command page only on the
  PC. A feature reachable only through `config.toml` or a CLI flag is missing for the user:
  document where the pages expose it.
