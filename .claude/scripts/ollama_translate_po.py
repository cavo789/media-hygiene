#!/usr/bin/env python3
"""Fill the empty entries of a French gettext catalog with a local Ollama model.

A first draft, never the last word: every entry the model fills is marked `fuzzy`, so
`i18n_todo` lists it and the completeness test fails until a person (or Claude) has read
it and removed the flag. What is checked by machine before anything is written: the
answer is one JSON string per entry, and it keeps the same placeholders (`{name}`,
`%s`, `%(name)s`) as the English text. A batch that fails a check is skipped and named.

Measured (2026-11-07, code-fast, 25 strings): 5 s per batch, format and placeholders
25/25; meaning mostly right, with terms off the glossary and an untranslated sentence
(`.claude/plans/ollama-delegation-report.md`, §5.1).

Usage: ollama_translate_po.py [--model NAME] [--batch N] [po-file]
Environment: OLLAMA_URL (default http://host.docker.internal:11434).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

import polib

PO_FILE = "src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po"
DEFAULT_MODEL = "code-quality:latest"
DEFAULT_BATCH = 25
TIMEOUT_S = 300
MAX_TOKENS = 8192
PLACEHOLDER = re.compile(r"\{[^{}]*\}|%\([^)]*\)[sd]|%[sd]")
GLOSSARY = (
    "place = lieu, review = tri, set aside = mettre de côté, keeper = copie gardée, "
    "quarantine = quarantaine, burst = rafale, near duplicate = quasi-doublon, "
    "folder = dossier, TV = télé, workbook = classeur, tag = tag"
)
INSTRUCTION = (
    "Translate each line (a JSON string, UI text of a photo de-duplication CLI) from "
    "English to French. Output exactly one JSON string per line, same order, nothing "
    "else. Translate every line, never leave English. Keep {placeholders}, %s, markup, "
    "emoji, backticks, quotes around commands and command names unchanged. Use "
    f'"vous". Glossary: {GLOSSARY}.'
)


def ask(model: str, lines: list[str]) -> str:
    """Send one batch to Ollama and return its raw answer.

    Args:
        model: The Ollama model name.
        lines: The English texts, one per entry.

    Returns:
        The model's answer, unparsed.
    """
    body = {
        "model": model,
        "system": INSTRUCTION,
        "prompt": "\n".join(json.dumps(line, ensure_ascii=False) for line in lines),
        "stream": False,
        "think": False,
        "options": {"temperature": 0, "num_ctx": 32768, "num_predict": MAX_TOKENS},
    }
    url = os.environ.get("OLLAMA_URL", "http://host.docker.internal:11434")
    request = urllib.request.Request(  # noqa: S310 - a local http URL chosen by the developer
        f"{url}/api/generate",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT_S) as reply:  # noqa: S310
        return str(json.load(reply)["response"])


def checked(sources: list[str], answer: str) -> list[str] | None:
    """Return the translations when the answer passes every check, else None.

    Args:
        sources: The English texts sent.
        answer: The model's raw answer.

    Returns:
        One French text per source, or None when the count, the JSON or a
        placeholder does not match.
    """
    rows = [row.strip() for row in answer.splitlines() if row.strip().startswith('"')]
    if len(rows) != len(sources):
        return None
    try:
        texts = [str(json.loads(row)) for row in rows]
    except json.JSONDecodeError:
        return None
    for source, text in zip(sources, texts, strict=True):
        same = sorted(PLACEHOLDER.findall(source)) == sorted(PLACEHOLDER.findall(text))
        if not same or text == source:
            return None
    return texts


def write_drafts(po_file: Path, drafts: dict[int, str]) -> None:
    """Write each draft as text, flagged fuzzy, leaving every other line as it is.

    `polib`'s own save re-wraps the whole catalog (project rule): only the empty
    `msgstr ""` of each entry and its flags line change; `i18n_update` re-wraps later.

    Args:
        po_file: The catalog.
        drafts: French text by the entry's first line number (polib's `linenum`).
    """
    lines = po_file.read_text(encoding="utf-8").splitlines()
    for linenum in sorted(drafts, reverse=True):
        first = linenum - 1
        end = next(i for i in range(first, len(lines)) if lines[i] == 'msgstr ""')
        lines[end] = f'msgstr "{polib.escape(drafts[linenum])}"'
        if lines[first].startswith("#, "):
            lines[first] = "#, fuzzy, " + lines[first].removeprefix("#, ")
        else:
            lines.insert(first, "#, fuzzy")
    po_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    """Translate the empty singular entries batch by batch, then save the catalog.

    Returns:
        0 when every entry was drafted, 1 when one was skipped or Ollama failed
        (the batches already checked are written all the same).
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--batch", type=int, default=DEFAULT_BATCH)
    parser.add_argument("po_file", nargs="?", default=PO_FILE)
    options = parser.parse_args()
    catalog = polib.pofile(options.po_file)
    todo = [entry for entry in catalog.untranslated_entries() if not entry.msgid_plural]
    drafts: dict[int, str] = {}
    for start in range(0, len(todo), options.batch):
        batch = todo[start : start + options.batch]
        sources = [entry.msgid for entry in batch]
        try:
            texts = checked(sources, ask(options.model, sources))
        except OSError as error:
            sys.stderr.write(f"Ollama did not answer: {error}\n")
            break
        if texts is None:
            sys.stderr.write(f"skipped (failed a check): {sources[0][:60]}…\n")
            continue
        drafts.update(
            (entry.linenum, text)
            for entry, text in zip(batch, texts, strict=True)
            if entry.linenum is not None
        )
    write_drafts(Path(options.po_file), drafts)
    skipped = len(todo) - len(drafts)
    plural = sum(1 for entry in catalog.untranslated_entries() if entry.msgid_plural)
    sys.stdout.write(
        f"{len(drafts)} filled as fuzzy, {skipped} skipped, "
        f"{plural} plural entries left to translate by hand\n"
    )
    return 1 if skipped else 0


if __name__ == "__main__":
    sys.exit(main())
