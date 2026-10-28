# `classify` : proposer une arborescence bien rangée

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `classify` · 🇬🇧 [English](../../en/commands/classify.md)

## En bref

**Obtenir une arborescence bien rangée pour toutes vos photos, par année, événement, lieu ou
personne, et la corriger avant que rien ne bouge.**

`classify` propose une place à chaque photo et vidéo, `année/année-mois/événement` par défaut :
`2019/2019-08/Vacances à la mer` ([la convention](../sort/04-classify.md#la-convention--année-mois-événement)).
Ce qui n'est pas décidé reste où il est. Il **ne fait que proposer** : rien ne bouge. Vous corrigez la proposition dans un [classeur](../reference-glossary.md#classeur), puis [`sort`](sort.md) l'applique.

**Quand** : après avoir nettoyé les doublons (sinon les deux copies sont triées) ; à nouveau
après de nouvelles photos ou une règle modifiée : vos modifications du classeur précédent sont
reprises.

**Essayer** :

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene --locale fr classify
```

## D'un coup d'œil

| | |
|---|---|
| Vos photos | 🔒 Jamais modifiées : montez-les en `:ro`. |
| Il faut | Vos dossiers. |
| Conseillé | `/cache` (les dates, appareils et lieux en viennent), `/reports` (le classeur et le rapport), `/config` (votre disposition et vos règles). |
| Écrit | `/reports/<date>-classify/` : `classify.xlsx`, `report.html`, `plan.json`. Sans `/reports`, la proposition reste à l'écran seulement. |
| Annuler | Rien à annuler : rien n'a bougé. |
| Avec `mh` | `mh classify`. |

## Lancer

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene --locale fr classify
```

## Lire le résultat

- **Déjà à leur place** : les fichiers déjà là où la proposition les veut.
- **Proposition**, par bande : **sûrs** (un dossier que vous avez nommé, une règle :
  `année/année-mois/événement`), **à vérifier** (une supposition : reste jusqu'à ce que vous la
  confirmiez), **à trier** (rien ne le dit : reste, regroupé par événement pour que vous le
  nommiez), **sans date** (reste), **laissés tels quels** (dossiers protégés et `--leave`,
  fichiers posés directement dans leur dossier `année/année-mois`).
- Un `config.toml` qui range autrement que la convention, ou une règle dont la catégorie a
  plusieurs niveaux de dossiers, est signalé en une ligne.
- **Pourquoi** : la règle ou la raison de chaque proposition, puis les catégories les plus trouvées.
- La fin donne le chemin du classeur et du rapport.

## Options

| Option | Rôle |
|---|---|
| `--path DOSSIER` | Seulement les fichiers sous ce dossier (chemin de l'hôte, tel que monté), répétable : `--path "C:\Photos\2015"`. Les événements restent entiers : formés à partir de tous les fichiers, seuls ceux sous le dossier reçoivent une proposition. Avec `--year` : les deux. |
| `--year ANNÉE[-ANNÉE]` | Seulement les fichiers de cette année ou de ces années : `2016`, `2015-2017`. Une soirée à la fois. Les fichiers datés seulement par le disque (copies, téléchargements) sont mis de côté et comptés : un classify sans `--year` les propose. Les règles écrites pour d'autres années sont comptées en une ligne, sans leurs noms. |
| `--layout DISPOSITION` | Où vont les fichiers sûrs : `{year}/{year_month}/{category}` par défaut, `{year}/{month}`… Aussi `{year_month}` (`2009-11` ; `1985-00` quand seule l'année est connue), `{quarter}`, `{month_name}`, `{day}`, `{event}`, `{event_start}`, `{place}`, `{country}`, `{region}`, `{city}`. |
| `--target CHEMIN` | Dossier de l'hôte qui reçoit l'arborescence (il doit être monté) ; chaque dossier monté, sur place, par défaut. |
| `--leave CHEMIN` | Dossier de l'hôte jamais trié, toujours analysé et nettoyé. |
| `--carry-over CLASSEUR` | Reprendre les modifications de ce classeur ; celui du dernier `classify` par défaut. |
| `--no-carry-over` | Repartir de zéro. |
| 🤖 `--sample N` | **Avec une IA locale seulement.** Décrire N photos prises au hasard avec le modèle de vision local, afficher le temps par photo et l'estimation d'une exécution complète, puis s'arrêter. |
| 🤖 `--no-describe` | **Avec une IA locale seulement.** Ne rien demander de nouveau au modèle local : les règles `subject` lisent les descriptions déjà dans le cache. |
| 🤖 `--yes`, `-y` | **Avec une IA locale seulement.** Décrire les photos avec le modèle local sans demander, quel que soit leur nombre. |

Chaque option a sa ligne dans la section `[classify]` de `config.toml` ; les règles
(`[[classify.rules]]`) s'y écrivent seulement.

## Exemples

```powershell
# Une année, rangée par mois sans catégorie
cavo789/media-hygiene --locale fr classify --year 2016 --layout "{year}/{month}"

# Construire l'arborescence dans un autre dossier (monté), laisser les albums tranquilles
cavo789/media-hygiene --locale fr classify --target "D:\Photos triées" --leave "C:\Photos\Albums"

# Combien de temps prendrait le modèle local ?
cavo789/media-hygiene --locale fr classify --sample 20
```

## Bon à savoir

- **D'où viennent les dates**, la première source fiable l'emportant : l'appareil (EXIF), les
  balises de la vidéo, le nom du fichier, le dossier, et en dernier la date sur le disque.
- **Vos modifications sont reprises** dans le nouveau classeur : un fichier par son contenu, un
  événement par la plupart de ses fichiers, une catégorie par son nom. Rien n'est perdu en
  silence : ce qui ne peut pas être repris est listé.
- Si le dernier classeur ne peut pas être ouvert du tout, `classify` s'arrête avant d'écrire quoi
  que ce soit, pour que vos modifications ne soient pas enterrées sous un classeur plus récent et
  vide.
- Le modèle de vision local (facultatif) se règle dans `[classify.ai]` : les photos sont envoyées
  à son `url`, et seulement là. Les photos que [`tags`](tags.md) a déjà décrites avec le même
  `model` ne sont pas renvoyées.
- Une règle `person` range les événements où figurent les personnes nommées dans
  [`people`](people.md) ([trier, étape 10](../sort/10-sort-by-person.md)).

## Pour aller plus loin

- Trier, [étape 4](../sort/04-classify.md), [étape 5](../sort/05-review-the-proposal.md),
  [étape 6 : les règles](../sort/06-write-down-what-you-know.md),
  [étape 8 : un modèle local](../sort/08-subjects-from-a-local-model.md),
  [étape 9 : le GPS](../sort/09-places-from-gps.md), [étape 10 : par personne](../sort/10-sort-by-person.md)
- [Trier en bref](../sort/quick-guide.md)
- Ensuite : [`review-sort`](search.md#les-événements-du-dernier-classify) (facultatif), puis [`sort`](sort.md).

## L'aide intégrée

<details>
<summary><code>classify --help</code></summary>

<!-- capture: help-classify.txt -->
```text
 Utilisation : media-hygiene classify [OPTIONS]

 🔒 Lecture seule : ne modifie jamais vos photos. Propose où ranger chaque
 photo et vidéo : année, événement, catégorie, et ce que montrent les photos
 isolées avec une IA locale facultative 🤖

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --year            <str>  Seulement les fichiers de cette année, ou de ces    │
│                          années : 2016 ou 2015-2017.                         │
│ --path            <str>  Seulement les fichiers sous ce dossier (chemin de   │
│                          l'hôte, tel que vous l'avez monté) ; répétez-la     │
│                          pour plusieurs. Les événements restent entiers :    │
│                          ils sont formés à partir de tous les fichiers, et   │
│                          seuls les fichiers sous ces dossiers reçoivent une  │
│                          proposition. Avec --year : les fichiers des deux.   │
│ --layout          <str>  Où vont les fichiers sûrs, par exemple              │
│                          '{year}/{month} - {month_name}'.                    │
│ --target          <str>  Dossier de l'hôte qui reçoit l'arborescence ; sur   │
│                          place par défaut.                                   │
│ --help    -h             Affiche ce message et quitte.                       │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options avancées ───────────────────────────────────────────────────────────╮
│ --leave                <str>  Dossier de l'hôte jamais trié (analysé et      │
│                               nettoyé comme d'habitude).                     │
│ --carry-over           <str>  Classeur dont les modifications sont reprises  │
│                               ; celui du dernier classify par défaut.        │
│ --no-carry-over               Repartir de zéro : ne reprendre aucune         │
│                               modification d'un classeur précédent.          │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ 🤖 IA locale (Ollama), facultative : un modèle indiqué dans config.toml ────╮
│ --sample               <int range> [x>=0]  Estimer d'abord une exécution     │
│                                            complète : décrire ce nombre de   │
│                                            photos prises au hasard avec le   │
│                                            modèle local, afficher le temps   │
│                                            par photo et l'estimation d'une   │
│                                            exécution complète, puis          │
│                                            s'arrêter.                        │
│ --no-describe                              Ne rien demander de nouveau au    │
│                                            modèle local : les règles subject │
│                                            lisent les descriptions déjà dans │
│                                            le cache.                         │
│ --yes          -y                          Décrire les photos sans demander, │
│                                            quel que soit leur nombre.        │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
