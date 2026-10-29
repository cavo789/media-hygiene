# Points de montage

[Documentation](README.md) › Référence · 🇬🇧 [English](../en/reference-mount-points.md)

L'outil tourne dans un conteneur : il ne voit que les dossiers que vous lui donnez avec
`-v "<le vôtre>:<le sien>"`. Chaque emplacement du conteneur a un rôle.

| Montage | Contenu | Nécessaire | Guide |
|---|---|---|---|
| `/data/<lecteur>/<chemin>` | Les dossiers à analyser : `/data`, puis la lettre du lecteur et le chemin d'un dossier Windows (`C:\Photos`, ou `/mnt/c/Photos` dans WSL → `/data/c/Photos`), ou le chemin complet d'un dossier Linux (`/home/moi/Images` → `/data/home/moi/Images`). | toujours ; `:ro` pour `audit` et `review` | [1](start/01-first-audit.md), [3](start/03-several-folders.md) |
| `/cache` | Index SQLite : les audits suivants ne relisent que les fichiers nouveaux ou modifiés ; les descriptions d'un modèle local ([étape 8 du tri](sort/08-subjects-from-a-local-model.md)) y sont gardées aussi, ainsi que le cache de Czkawka pour [`crosscheck`](commands/crosscheck.md) ; `inventory` l'exporte ([inventaire](reference-inventory.md)). | facultatif, recommandé ; **obligatoire** pour `inventory` | [2](start/02-keep-the-cache.md) |
| `/reports` | Un dossier par exécution (`report.html`, une page par paire de dossiers, vignettes, `plan.csv`), `index.html`, le `decisions.json` de `review`, les dossiers `<date>-classify` ([classeur et rapport](sort/05-review-the-proposal.md), et le `sort-decisions.json` de [l'onglet 🗂 Événements de `search`](sort/11-name-events-in-the-browser.md)) et les dossiers `<date>-inventory` ([inventaire](reference-inventory.md)). | facultatif ; **obligatoire** pour `review`, `review-sort`, `sort`, `album` et `inventory` | [Nettoyer, 4](clean/04-html-report.md) |
| `/config` | `config.toml` uniquement, créé et commenté au premier lancement ; `places` y enregistre vos lieux. | facultatif ; **obligatoire** pour `places` | [Nettoyer, 7](clean/07-configuration-file.md) |
| `/journal` | Un journal JSONL par nettoyage, tri ou album. | **obligatoire** pour `clean`, `sort`, `album`, `undo`, `history` | [Nettoyer, 8](clean/08-clean.md) |
| `/quarantine` | Fichiers illisibles, fichiers compagnons orphelins, quasi-doublons, photos de rafale écartées et copies d'autres types de fichiers déplacés par `clean`. | pour les traiter | [Nettoyer, 8](clean/08-clean.md) |
| `/quarantine/<disque>` | La quarantaine d'un disque (`E:\media-hygiene\quarantine` sur `/quarantine/e`) : les fichiers de ce disque mis de côté y restent ; `/quarantine` reçoit ceux des autres disques. `mh` en monte une pour chaque disque de photos autre que `C:`. | facultatif, conseillé pour des photos hors de `C:` | [Nettoyer, 8](clean/08-clean.md#photos-sur-un-autre-disque-que-la-quarantaine) |

## Bon à savoir

- **Les vérifier** : `config` montre chaque point de montage, le dossier Windows derrière lui, et
  s'il est en lecture seule, monté ou absent ([étape 7 du nettoyage](clean/07-configuration-file.md#vérifier-ce-que-loutil-utilise--config)).
- **Les montages manquants ou non accessibles en écriture** sont expliqués par des astuces 💡.
  `clean` s'arrête avant l'analyse sans `/journal`, avec un dossier en `:ro`, ou quand il ne peut
  pas écrire dans l'un de ses dossiers.
- **Créez vos dossiers avant `docker run`** : un dossier que Docker crée lui-même appartient à
  l'administrateur, et l'outil ne peut pas y écrire
  ([dépannage](reference-troubleshooting.md#dossiers-où-loutil-ne-peut-pas-écrire)).
- **`/config` ne contient que `config.toml`** : rien d'autre n'y est jamais écrit.
- **Seule la quarantaine va par disque** : configuration, journal, rapports et cache restent
  uniques (un seul index trouve les doublons d'un disque à l'autre ; un seul journal note où est
  allé chaque fichier, et `undo` le suit). Gardez la quarantaine d'un disque montée jusqu'à ce que
  ses exécutions soient purgées ou annulées : sinon `undo` et `purge <exécution>` refusent, en
  nommant le disque à brancher, et `purge` garde ces exécutions.
- **Lancements durcis** : l'image fonctionne aussi avec `--read-only --tmpfs /tmp`.
