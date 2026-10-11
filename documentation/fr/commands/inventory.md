# `inventory` : chaque photo et vidéo dans un tableur

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `inventory` · 🇬🇧 [English](../../en/commands/inventory.md)

`inventory` exporte vers un classeur Excel chaque photo, fichier RAW et vidéo que les audits ont
vus, avec tout ce qu'ils en ont appris : taille, dates, appareil, réglages, lieu, qualité,
doublons, mots. Il lit **le cache seul** : aucun fichier de vos dossiers n'est ouvert, il prend
quelques secondes même pour des dizaines de milliers de photos.

## En bref

| | |
|---|---|
| Vos photos | 🔒 Jamais modifiées, même pas lues. |
| Il faut | `/cache` (rempli par un [`audit`](audit.md) précédent) et `/reports` (où va le classeur). |
| Écrit | `/reports/<date>-inventory/inventory.xlsx` (ou `inventory.csv`). |
| Annuler | Supprimez le dossier. |
| Avec `mh` | `mh inventory`. |

## Quand l'utiliser

Pour répondre à vos propres questions avec les filtres d'Excel : combien de photos par année ou
par appareil, quelles images sont floues ou minuscules, quel appareil avait son horloge fausse,
combien de photos ont une position GPS.

## Lancer

```powershell
docker run --rm -it `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene --locale fr inventory
```

Aucun dossier de photos n'est nécessaire. La console dit où est le classeur, et quand chaque
dossier a été audité complètement pour la dernière fois.

## Options

| Option | Rôle |
|---|---|
| `--format xlsx` | Par défaut : un classeur à deux feuilles, **Fichiers** (une ligne par fichier) et **Résumé**. |
| `--format csv` | La feuille Fichiers seule, en fichier CSV, comme `plan.csv`. |

## Bon à savoir

- L'inventaire est **aussi frais que le dernier audit** : une photo ajoutée depuis manque, une
  photo supprimée à la main est encore listée. Refaites l'audit, puis l'export.
- Après [`tags`](tags.md), la dernière colonne, **Tags**, contient les mots de chaque photo.
- Le fichier CSV s'ouvre tel quel dans Excel : en français, `;` entre les colonnes et une virgule
  décimale.

## Pour aller plus loin

- [Le classeur d'inventaire](../reference-inventory.md) : chaque colonne, les étiquettes de
  qualité et d'exposition.
- [2. Garder le cache](../start/02-keep-the-cache.md)

## L'aide intégrée

<details>
<summary><code>inventory --help</code></summary>

<!-- capture: help-inventory.txt -->
```text
 Utilisation : media-hygiene inventory [OPTIONS]

 🔒 Lecture seule : ne modifie jamais vos photos. Exporter vers Excel chaque
 photo et vidéo avec ce que les audits en ont appris, depuis le cache seul :
 aucun fichier n'est lu.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --format          <xlsx|csv>  xlsx : un classeur Excel (feuilles Fichiers et │
│                               Résumé). csv : la feuille Fichiers seule,      │
│                               comme plan.csv. Par défaut : xlsx.             │
│ --help    -h                  Affiche ce message et quitte.                  │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
