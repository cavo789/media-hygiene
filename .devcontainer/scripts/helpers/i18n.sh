# .devcontainer/scripts/helpers/i18n.sh
#
# Category "i18n" — keep the gettext catalogs in sync with the source code.
#
# Sourced by ../interactive.sh — no shebang, never executed directly.
# shellcheck shell=bash

# @cat i18n
# @cmd i18n_extract
# @desc Extract _() strings into media_hygiene.pot
function i18n_extract() {
    (
        cd "$(_repo_root)" || return 1
        pybabel extract --omit-header --no-location --sort-output \
            --mapping-file .config/babel.cfg \
            --output-file src/media_hygiene/i18n/locales/media_hygiene.pot src
    )
}

# @cat i18n
# @cmd i18n_update
# @desc Extract + merge into every .po (then translate)
function i18n_update() {
    i18n_extract || return 1
    (
        cd "$(_repo_root)" || return 1
        pybabel update --ignore-pot-creation-date --ignore-obsolete --domain media_hygiene \
            --input-file src/media_hygiene/i18n/locales/media_hygiene.pot \
            --output-dir src/media_hygiene/i18n/locales
    )
}

# @cat i18n
# @cmd i18n_todo
# @desc List the French entries still untranslated or fuzzy
function i18n_todo() {
    (
        cd "$(_repo_root)" || return 1
        uv run --frozen --quiet python - <<'PY'
import polib

catalog = polib.pofile("src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po")
left = catalog.untranslated_entries() + catalog.fuzzy_entries()
for entry in left:
    print(("fuzzy  " if entry.fuzzy else "empty  ") + entry.msgid.replace("\\n", " "))
print(f"✅ Nothing left to translate ({catalog.percent_translated()} %)" if not left else
      f"{len(left)} entr{'y' if len(left) == 1 else 'ies'} left")
PY
    )
}
