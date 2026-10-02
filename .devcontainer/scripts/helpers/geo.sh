# .devcontainer/scripts/helpers/geo.sh
#
# Category "Data" — refresh the data shipped in the package.
#
# Sourced by ../interactive.sh — no shebang, never executed directly.
# shellcheck shell=bash

# @cat Data
# @cmd geonames_update
# @desc Download GeoNames, rebuild the offline towns of src/media_hygiene/geo/data
function geonames_update() {
    # The dumps live in /tmp only; GeoNames is CC BY 4.0: the date lands in ATTRIBUTION.txt.
    (
        cd "$(_repo_root)" || return 1
        uv run --frozen --quiet python -m tests.support.geonames
    )
}
