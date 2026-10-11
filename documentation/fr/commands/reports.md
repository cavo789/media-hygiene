# `reports` : lister et ranger les rapports HTML

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `reports` · 🇬🇧 [English](../../en/commands/reports.md)

Chaque audit, nettoyage et contre-vérification écrit son propre dossier de rapport dans
`/reports`. `reports` les liste, du plus récent au plus ancien, et régénère `index.html`, la page
qui les relie tous. Avec `--prune`, il garde les plus récents et supprime les autres.

## En bref

| | |
|---|---|
| Vos photos | 🔒 Jamais modifiées : seul le dossier des rapports est lu (et, avec `--prune`, rangé). |
| Il faut | `/reports`, le dossier de vos rapports. |
| Écrit | `index.html` ; `--prune` supprime les anciens dossiers de rapport. |
| Annuler | Un rapport supprimé ne revient pas ; relancez l'audit pour en obtenir un nouveau. |
| Avec `mh` | `mh reports`, `mh reports --prune 10`. |

## Lancer

```powershell
docker run --rm -it -v "$HOME\media-hygiene\reports:/reports" cavo789/media-hygiene --locale fr reports
```

Aucun dossier de photos n'est nécessaire. Ouvrez ensuite `index.html` dans ce dossier d'un double
clic : chaque ligne est une exécution, sa date ouvre son rapport.

## Options

| Option | Rôle |
|---|---|
| `--prune N` | Garde les N rapports les plus récents, supprime les autres. |

## Bon à savoir

- Chaque dossier d'exécution porte sa date et son type (`20261003-180936-audit`) et contient
  `report.html`, ses aperçus et `plan.csv`.
- `--prune` ne supprime que les dossiers de rapport écrits par l'outil (nommés comme
  `20261003-180936-audit`, avec leur `summary.json`) : jamais une photo, ni le `decisions.json`
  sur lequel vous travaillez, ni les dossiers de `classify`, `sort` et `inventory`.
- Sans `/reports` monté, il n'y a rien à lister : les commandes montrent alors leurs résultats à
  l'écran seulement.

## Pour aller plus loin

- [4. Le rapport HTML](../clean/04-html-report.md#lister-et-ranger-les-rapports)
- [Points de montage](../reference-mount-points.md)

## L'aide intégrée

<details>
<summary><code>reports --help</code></summary>

<!-- capture: help-reports.txt -->
```text
 Utilisation : media-hygiene reports [OPTIONS]

 🔒 Lecture seule : ne modifie jamais vos photos. Liste les rapports HTML des
 audits et nettoyages précédents.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --prune          <int range> [x>=0]  Supprime tous les rapports sauf les N   │
│                                      plus récents.                           │
│ --help   -h                          Affiche ce message et quitte.           │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
