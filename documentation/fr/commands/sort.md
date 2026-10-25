# `sort` : déplacer les fichiers comme le dit le classeur

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `sort` · 🇬🇧 [English](../../en/commands/sort.md)

## En bref

**Déplacer vos photos dans l'arborescence que vous avez approuvée, avec la preuve que rien n'a
été perdu, et revenir en arrière quand vous voulez.**

`sort` applique le [classeur](../reference-glossary.md#classeur) de [`classify`](classify.md), avec vos modifications : il le
vérifie, dit ce qu'il va faire, **demande**, puis déplace chaque fichier vers son dossier. Sur
un même disque, un déplacement est un renommage : rien n'est copié, aucune place n'est prise.
Chaque déplacement est journalisé et `undo` remet tout en place.

**Quand** : une fois la proposition relue ([trier, étape 5](../sort/05-review-the-proposal.md))
et, si vous le voulez, les événements nommés avec [`review-sort`](review-sort.md). **Enregistrez
et fermez d'abord le classeur.**

**Essayer** :

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene --locale fr sort
```

## D'un coup d'œil

| | |
|---|---|
| Vos photos | ✋ Agit : déplace les photos et vidéos, supprime les dossiers sources qu'il laisse vides. Jamais par-dessus un autre fichier, jamais de photo supprimée. |
| Il faut | Vos dossiers **sans** `:ro`, `/journal`, et `/reports` (l'exécution de `classify`). |
| Conseillé | `/quarantine` (pour les `Thumbs.db` et consorts des dossiers laissés vides), `/cache` (il suit les déplacements). |
| Écrit | Le journal, les déplacements, la preuve dans `/reports/<exécution>-sort/manifest.json`. |
| Annuler | [`undo`](undo.md) : les fichiers reviennent, les dossiers supprimés aussi. |
| Avec `mh` | `mh sort`. |

## Lancer

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene --locale fr sort
```

Avant que rien ne bouge, il dit ce qu'il a lu (les modifications, la date d'enregistrement du
classeur, les choix de la page du navigateur appliqués par-dessus), ce qu'il va déplacer, les
fichiers déjà à leur place et les dossiers sources qu'il va supprimer, puis demande.

## Ce qui est vérifié d'abord

- **Tout le classeur**, face à son `plan.json`, tout ou rien : feuilles, en-têtes, lignes, chaque
  cellule verrouillée. La première différence refuse le fichier, en nommant la cellule, la valeur
  attendue et la valeur trouvée.
- **Les cellules jaunes** : un nom que Windows refuse, un dossier qui sort de la cible (`..`) ou un
  chemin trop long est refusé avec sa cellule.
- **Les montages**, comme pour `clean` : un journal est exigé, les dossiers en lecture seule sont
  refusés ; la cible doit être montée et pas dans un dossier protégé.
- **Chaque fichier, juste avant qu'il bouge** : celui qui a changé ou disparu depuis `classify`
  est ignoré et listé.

## Options

| Option | Rôle |
|---|---|
| `CLASSEUR` | Le classeur modifié à appliquer (dans un dossier monté) ; celui du dernier `classify` par défaut. |
| `--yes`, `-y` | Ne pas demander (ou `confirm = false` dans `[sort]`). |
| `--keep-empty-folders` | Garder les dossiers sources que le tri laisse vides. |
| `--event ID` | Trier seulement les fichiers de cet événement (son identifiant : la première colonne de la feuille Événements) ; le reste du classeur attend. |

## Bon à savoir

- **Les compagnons voyagent ensemble** : une Live Photo (`IMG_1.HEIC` + `IMG_1.MOV`), un fichier
  RAW et son JPEG, et leurs fichiers compagnons vont dans le même dossier.
- **D'un disque à l'autre** (deux `-v` sont deux disques), un fichier est copié, comparé, et
  seulement ensuite retiré.
- **Un fichier existant n'est jamais écrasé** : `IMG_1.jpg` devient `IMG_1 (2).jpg`.
- **Arrêté en plein milieu ?** Relancez la même commande : les fichiers déjà déplacés comptent
  comme faits. `undo` annule alors d'un coup toutes les exécutions de ce classeur.
- **Rien de perdu, preuve à l'appui** : les fichiers et tailles des dossiers sources et cibles
  sont comptés avant et après, et doivent correspondre.
- **Un événement à la fois** : `--event` (ou *Trier cet événement maintenant* dans
  [`review-sort`](review-sort.md)) trie un seul événement ; un `sort` ultérieur de tout le classeur
  saute ses fichiers, déjà déplacés. Chaque exécution a son propre `undo`.
- **Tout reste lié** : juste après les déplacements, `sort` réécrit chacun de vos fichiers qui
  nomment des photos par leur chemin — les noms donnés aux visages (`people\*.toml`),
  `albums.json`, `decisions.json` (rafales, fichiers choisis dans `search` ; une paire de dossiers
  dont un dossier a disparu est retirée) et les vidéos choisies dans `shrink --try` — puis les
  relit et le dit en une ligne. Ils ne dépendent plus du cache : vous pouvez le supprimer. `undo`
  remet les anciens chemins de la même façon. Un dossier de `config.toml` (`[folders] preferred`,
  un dossier placé sur la carte) que l'exécution a vidé est nommé, pour que vous l'orientiez vers
  le nouveau dossier.

## Pour aller plus loin

- [Trier, étape 7 : trier](../sort/07-sort.md)
- [Trier, étape 5 : le classeur](../sort/05-review-the-proposal.md#le-classeur--modifier-les-cellules-jaunes)
- [Trier en bref](../sort/quick-guide.md)

## L'aide intégrée

<details>
<summary><code>sort --help</code></summary>

<!-- capture: help-sort.txt -->
```text
 Utilisation : media-hygiene sort [OPTIONS] [workbook]

 Déplacer les photos et vidéos comme le dit le classeur de classify modifié
 (journalisé, annulable).

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│   workbook      <str>  Le classeur de classify, modifié ; celui du dernier   │
│                        classify par défaut.                                  │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --yes                 -y        Ne pas demander de confirmation (remplace    │
│                                 sort.confirm).                               │
│ --keep-empty-folders            Garder les dossiers sources que le tri       │
│                                 laisse vides.                                │
│ --help                -h        Affiche ce message et quitte.                │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Avancé : dossiers (remplacent folders.* de config.toml) ────────────────────╮
│ --backup        <str>  Une sauvegarde ou un ancien disque, monté en lecture  │
│                        seule : jamais modifié, et jamais refusé pour cela    │
│                        (mh passe vos sauvegardes). Répétable.                │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
