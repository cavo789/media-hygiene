# Développement

[Documentation](README.md) › Pour les développeurs · 🇬🇧 [English](../en/development.md)

Utile seulement pour modifier l'outil. Pour l'utiliser, le [guide](README.md#pour-commencer)
suffit.

## Construire l'image depuis les sources

Partout où la documentation indique `cavo789/media-hygiene`, utilisez alors votre image locale
`media-hygiene` :

```bash
git clone https://github.com/cavo789/media-hygiene.git
cd media-hygiene
docker build --tag media-hygiene .
```

L'image compile son propre `ffprobe`, environ 1 Mo au lieu de 141 Mo pour une version complète :
l'outil demande seulement si le conteneur d'une vidéo s'ouvre, donc l'étape `ffprobe` du
`Dockerfile` ne garde que les démultiplexeurs des extensions vidéo analysées. Une nouvelle
extension vidéo demande aussi son démultiplexeur à cet endroit ; un test vérifie que les deux
listes concordent.

Elle compile aussi son propre `ffmpeg`, environ 6 Mo : pour trouver les [vidéos
réencodées](clean/11-near-duplicates.md#les-vidéos-aussi--les-copies-réencodées), l'audit décode
quelques images de chaque vidéo ; l'étape `ffmpeg` ajoute donc les décodeurs des vidéos de
téléphones, d'appareils photo et d'anciens PC (H.264, HEVC, MPEG-4, VP8/VP9, WMV/VC-1, ProRes,
…), les filtres de mise à l'échelle et de rotation et la sortie brute, rien d'autre. Les deux
outils partagent la liste `VIDEO_DEMUXERS`. AV1 est laissé de côté : son décodeur demande une
bibliothèque externe, et une telle vidéo n'est simplement pas comparée.

## Le devcontainer

Ouvrez le dépôt dans le devcontainer (VS Code, *Reopen in Container*). Chaque nouveau terminal
affiche la liste des commandes d'aide (`welcome` la réaffiche) :

| Commande | Rôle |
|---|---|
| `check` | La barrière qualité complète : pre-commit (ruff, mypy strict, pylint, shellcheck, shfmt, hadolint), puis les tests avec au moins 90 % de couverture des branches. |
| `lint`, `format`, `tests` | Pre-commit seul (nouveaux fichiers compris) ; corrige la mise en forme ; lance des tests ciblés. |
| `hygiene …`, `demo` | Lance l'outil depuis les sources sur `/tmp/media-hygiene/` ; `demo` crée une arborescence d'exemple et l'audite, `demo_clean` vide `/tmp/media-hygiene/`. |
| `reports`, `reports_stop` | Sert les rapports HTML sur un port libre choisi par le système. |
| `build`, `e2e`, `dive`, `dive_ci` | Construit l'image, lance les tests de bout en bout (sortie gardée dans `/tmp/media-hygiene/e2e.log`), inspecte ou contrôle ses couches. |
| `release` | Crée le tag `vX.Y.Z` (la version de `pyproject.toml`) et le pousse : la CI publie l'image. |
| `i18n_extract`, `i18n_update`, `i18n_todo` | Met à jour les catalogues gettext après la modification d'un texte affiché ; liste les entrées françaises encore à traduire. |
| `geonames_update` | Télécharge à nouveau GeoNames et reconstruit les villes hors ligne de `src/media_hygiene/geo/data/` (CC BY 4.0 : la date est notée dans son `ATTRIBUTION.txt`). |
| `todos` | Liste les TODOs ouverts (`.todos/`, voir `/todo` et `/todo-plan`), puis les partiels et les bloqués. |
| `ci`, `ci_logs`, `ci_watch` | Dernières exécutions de la CI sur la branche ; logs des étapes en échec de la dernière exécution ratée. Suit la dernière exécution en direct. La CLI GitHub demande `gh auth login` une fois. |
| `git_doctor`, `docker_doctor`, `docker_clean`, `deps` | Après un plantage : vérifie les objets git (`--fix` répare ceux restés vides) ; vérifie Docker et liste ce que les exécutions e2e/docs ont laissé, puis le supprime ; liste les dépendances directes qui ont une version plus récente. |

`check`, `lint`, `tests`, `e2e`, `docs_screenshots` et `hygiene` tournent en douceur : priorité
basse, la moitié des processeurs (`DEV_CPUS=8 check` pour changer), une part dont héritent les
conteneurs e2e et docs. Les exécutions à pleine charge ont fait planter la VM WSL sous Windows.

Les réglages et connexions des outils (`~/.config`, p. ex. le jeton de la CLI GitHub) sont dans
le volume Docker `media-dedup-config`, hors de l'espace de travail : ils survivent aux
reconstructions et ne peuvent jamais être commités. N'écrivez jamais de jeton dans un fichier
suivi par git (`devcontainer.json` compris) : ce dépôt est public.

## Règles de code

Appliquées par l'outillage : tout est typé, 200 lignes maximum par fichier et 3 paramètres
maximum par fonction, code en anglais, chaque texte affiché passe par gettext. Les caches
n'atterrissent jamais dans le dépôt : ils vivent dans `/tmp`.

## Documentation

La documentation utilisateur se trouve dans `documentation/en/` et `documentation/fr/`, avec les
mêmes noms de fichiers et les mêmes captures (`images/`) dans chaque langue ; `README.md` et
`README_FR.md` ne gardent que le démarrage rapide et le sommaire. Mettez à jour les deux langues à
chaque changement visible par l'utilisateur. Un test vérifie que chaque lien et chaque image des
README et de la documentation existe, et que les deux langues ont les mêmes pages.

`docs_screenshots` régénère les captures d'écran (`images/`) et les sorties console des deux
langues (`docs_screenshots fr` : le français seulement). Il reconstruit l'image, dessine une
bibliothèque de démonstration d'images synthétiques (paysages dessinés par
`tests/support/docs/`, jamais une vraie photo), rejoue l'histoire du guide avec la vraie image
dans ses propres volumes Docker, et prend les captures avec un Chromium sans interface (l'image
Playwright). Une sortie console est régénérée là où un commentaire HTML, invisible sur GitHub,
l'annonce :

    <!-- capture: clean.txt|re:^1 |❓ -->
    ```text
    …
    ```

Le commentaire nomme une capture et, au besoin, les lignes à garder : de la première qui
contient le deuxième champ (`re:` pour une expression régulière) à la suivante qui contient le
troisième (le détail est dans `tests/support/docs/pages.py`). Tout le reste des pages s'écrit à
la main ; relisez le résultat avec `git diff documentation/`.

## Intégration continue et versions

Chaque push et chaque pull request lancent la barrière qualité et les tests de bout en bout sur
GitHub Actions ([`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)). Pour publier une
nouvelle version, augmentez `version` dans `pyproject.toml`, commitez et poussez `main`, puis
lancez `release`. Il crée le tag `vX.Y.Z` et le pousse. La CI construit alors l'image pour amd64
et arm64, lance les tests de bout en bout, puis pousse `cavo789/media-hygiene:<version>` et
`:latest` sur Docker Hub, avec un SBOM et une attestation de provenance. Il faut pour cela deux
secrets dans le dépôt : `DOCKERHUB_USERNAME` et `DOCKERHUB_TOKEN` (un jeton d'accès Docker Hub en
lecture/écriture).

La feuille de route se trouve dans [.todos/plan.md](../../.todos/plan.md).
