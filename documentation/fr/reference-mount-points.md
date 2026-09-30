# Points de montage

[Documentation](README.md) › Référence · 🇬🇧 [English](../en/reference-mount-points.md)

L'outil tourne dans un conteneur : il ne voit que les dossiers que vous lui donnez avec
`-v "<le vôtre>:<le sien>"`. Chaque emplacement du conteneur a un rôle.

| Montage | Contenu | Nécessaire | Guide |
|---|---|---|---|
| `/data/<lecteur>/<chemin>` | Les dossiers à analyser (`C:\Photos` → `/data/c/Photos`). | toujours ; `:ro` pour `audit` et `review` | [1](start/01-first-audit.md), [3](start/03-several-folders.md) |
| `/cache` | Index SQLite : les audits suivants ne relisent que les fichiers nouveaux ou modifiés. | facultatif, recommandé | [2](start/02-keep-the-cache.md) |
| `/reports` | Un dossier par exécution (`report.html`, une page par paire de dossiers, vignettes, `plan.csv`), `index.html`, le `decisions.json` de `review`, et les dossiers `<date>-classify` ([classeur et rapport](sort/05-review-the-proposal.md)). | facultatif ; **obligatoire** pour `review` | [4](clean/04-html-report.md) |
| `/config` | `config.toml` uniquement, créé et commenté au premier lancement. | facultatif | [7](clean/07-configuration-file.md) |
| `/journal` | Un journal JSONL par nettoyage ou tri. | **obligatoire** pour `clean`, `sort`, `undo`, `history` | [8](clean/08-clean.md) |
| `/quarantine` | Fichiers illisibles, fichiers compagnons orphelins, quasi-doublons, photos de rafale écartées et copies d'autres types de fichiers déplacés par `clean`. | pour les traiter | [8](clean/08-clean.md) |

## Bon à savoir

- **Les vérifier** : `config` montre chaque point de montage, le dossier Windows derrière lui, et
  s'il est en lecture seule, monté ou absent ([étape 7](clean/07-configuration-file.md#vérifier-ce-que-loutil-utilise--config)).
- **Les montages manquants ou non accessibles en écriture** sont expliqués par des astuces 💡.
  `clean` s'arrête avant l'analyse sans `/journal`, avec un dossier en `:ro`, ou quand il ne peut
  pas écrire dans l'un de ses dossiers.
- **Créez vos dossiers avant `docker run`** : un dossier que Docker crée lui-même appartient à
  l'administrateur, et l'outil ne peut pas y écrire
  ([dépannage](reference-troubleshooting.md#dossiers-où-loutil-ne-peut-pas-écrire)).
- **`/config` ne contient que `config.toml`** : rien d'autre n'y est jamais écrit.
- **Lancements durcis** : l'image fonctionne aussi avec `--read-only --tmpfs /tmp`.
