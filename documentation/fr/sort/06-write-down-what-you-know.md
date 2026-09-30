# 6. Écrire ce que vous savez : les règles

[Documentation](../README.md) › Trier, étape 6 · 🇬🇧 [English](../../en/sort/06-write-down-what-you-know.md)

Le classeur ([étape 5](05-review-the-proposal.md)) corrige une proposition. Une **règle** corrige
toutes les suivantes : « nous étions en Italie du 1er au 15 juillet 2023 », « l'anniversaire de
mamy tombe le 12 mars », « les photos du drone vont dans Drone ». Vous l'écrivez une fois dans
`config.toml`, et `classify` l'applique à chaque exécution, aux photos de l'an prochain aussi.

## Où vivent les règles

Dans `config.toml` ([étape 7 du guide de nettoyage](../clean/07-configuration-file.md)), après
les réglages de `[classify]`, un bloc `[[classify.rules]]` par règle. Le fichier créé à la
première exécution contient déjà une liste d'exemples, écrite dans votre langue : modifiez-la,
réordonnez-la, retirez ce qui ne vous sert pas.

```toml
[[classify.rules]]
name = "Italie 2023"
match = "date_range"
dates = "2023-07-01..2023-07-15"
category = "Vacances et sorties/Italie 2023"

[[classify.rules]]
name = "Dossiers existants"
match = "existing_folder"

[[classify.rules]]
name = "Noël"
match = "calendar"
dates = "12-24..12-26"
category = "Fêtes/Noël"
```

- `name` : affiché comme raison des fichiers que la règle décide, dans le résumé et le classeur.
- `match` : ce que la règle lit (le tableau ci-dessous).
- `category` : où vont les fichiers, par le `{category}` du modèle. Sans catégorie, les fichiers
  que la règle reconnaît **restent où ils sont**.
- `score` (facultatif) : à quel point la règle est sûre, de 0 à 100 (plus bas).

> 💡 Les règles se lisent dans `config.toml` seulement : contrairement aux autres réglages,
> aucune variable d'environnement `MEDIA_HYGIENE_*` ne les remplace.

## Ce qu'une règle peut reconnaître

| `match` | Lit | Exemple |
|---|---|---|
| `existing_folder` | Un nom de dossier que vous avez choisi (`2019/Vacances à la mer`, `Mars 2005 - Travaux maison`). | — |
| `event_neighbour` | Les fichiers isolés d'un événement rejoignent le seul dossier que vous avez nommé pour lui. | — |
| `calendar` | Des jours qui reviennent chaque année, `dates = "MM-JJ..MM-JJ"`. | `dates = "12-24..12-26"` |
| `date_range` | Des jours qui n'arrivent qu'une fois, `dates = "AAAA-MM-JJ..AAAA-MM-JJ"`. | `dates = "2023-07-01..2023-07-15"` |
| `kind` | Un genre de fichier, `kind = "screenshot"`, `"received"` ou `"download"`. | `kind = "screenshot"` |
| `path` | Une expression régulière cherchée dans le chemin sur votre ordinateur, dossiers et nom. | `pattern = '(?i)kermesse'` |
| `camera` | Une expression régulière cherchée dans la marque et le modèle. | `pattern = '(?i)dji'` |
| `other_category` | Les fichiers qu'aucune règle au-dessus n'a reconnus. | `category = "Autres"` |

`existing_folder` et `event_neighbour` donnent comme catégorie le nom du dossier lui-même : ils
ne prennent pas de `category`. Une règle absente de la liste ne s'applique pas : une liste vide,
`rules = []`, trie par dates seulement.

### Les dates

Un seul jour s'écrit seul : `dates = "03-12"` pour un anniversaire. `12-31..01-01` passe le
Nouvel An. Un jour qui n'existe pas, comme `02-30`, est refusé à la lecture du fichier.

Une règle de dates prend des **événements entiers** (des photos prises à peu d'écart,
[étape 4](04-classify.md#lire-le-résultat)) : un événement va à la règle quand au moins la moitié
de ses photos tombent sur ses jours. Un réveillon qui se termine à 3 heures du matin reste
entier ; une semaine de ski qui contient un anniversaire reste une semaine de ski. Deux règles
`date_range` qui partagent un jour donnent un avertissement : ces jours-là, la première de la
liste l'emporte.

### Les genres de fichiers

Reconnus par le nom et les métadonnées seulement :

- `screenshot` : un nom de capture d'écran (`Screenshot_…`, `Capture d'écran …`), ou, sans
  marque, modèle ni position d'un appareil, un PNG ou une image de moins de 400 pixels.
- `received` : une image reçue par une messagerie (`IMG-20200105-WA0003`, `received_…`), qui a
  perdu sa date d'appareil en route.
- `download` : une vidéo dont le nom contient une saison, une résolution ou un codec (`S01E05`,
  `1080p`, `x264`) : un film ou une série téléchargés. Ce ne sont pas des souvenirs : la liste
  d'exemples ne leur donne pas de catégorie, ils restent donc où ils sont.

### Les catégories

Une catégorie peut utiliser `{year}`, `{month}`, `{month_name}`, `{day}`, `{event}` et
`{event_start}`, pris au début de l'événement : `category = "Fêtes/Noël {year}"`. Les
caractères que Windows refuse dans un nom de dossier sont refusés.

Les catégories d'exemple sont des occasions et des activités : Fêtes, Vacances et sorties,
École, Sport et loisirs, Maison et travaux, Animaux, Nature et paysages, Documents et captures
d'écran, Autres. Remplacez-les par les vôtres. Évitez une catégorie « Famille » ou
« Portraits » : dans une collection familiale, elle avale la plupart des photos.

## Quelle règle l'emporte

Les règles sont lues **dans l'ordre**, et la première dont le score atteint `sure` (80 par
défaut) décide. Quand aucune ne l'atteint, la meilleure trouvée est une supposition, rassemblée
dans `année/À vérifier/catégorie`. Quand aucune règle ne reconnaît le fichier, il va dans
`année/À trier/<événement>` : « à trier » veut dire « on ne sait pas », alors
qu'`other_category` veut dire « sûr que rien au-dessus ne correspond ».

Chaque `match` a un score par défaut, qu'une règle peut changer par son propre `score` ;
`score = 0` désactive une règle :

| `match` | Score |
|---|---|
| `date_range` | 95 : vous l'avez écrite, elle est sûre |
| `existing_folder` | 90 (85 pour le dossier d'une personne, `Papa/2018/…`) |
| `path`, `camera` | 90 |
| `calendar`, `kind`, `other_category` | 85 |
| `event_neighbour` | 70 : à vérifier |

La table `[classify] scores` fixe ces valeurs par défaut pour toutes les règles d'un même
`match`. Une photo dont la date est douteuse (son dossier dit une autre année) reste « à
vérifier » quelle que soit sa règle.

## Voir ce que chaque règle a fait

Le tableau *Pourquoi* de `classify` compte les fichiers que chaque règle a décidés, par son nom :

<!-- capture: classify.txt|Pourquoi|Vérifiez leurs dates -->
```text
Pourquoi
┌─────────────────────┬────┐
│ Dossiers existants  │ 74 │
│ no-signal           │  3 │
│ undated             │  3 │
│   Vacances à la mer │ 13 │
│   Photos 2019       │ 12 │
│   Randonnée         │ 10 │
│   Anniversaire      │  8 │
│   Ancien téléphone  │  8 │
│   Noël              │  6 │
│   Lac               │  6 │
│   Téléphone         │  6 │
│   Noël 2020         │  4 │
│   WhatsApp          │  1 │
└─────────────────────┴────┘

⚠️  Règles qui n'ont rien décidé : Films et séries, Captures d'écran et
documents, Voisins d'événement, Noël, Nouvel An, Saint-Nicolas.
💡 Vérifiez leurs dates, leurs expressions et leur ordre dans config.toml.
```

Les règles qui n'ont rien décidé sont nommées après le tableau : une faute de frappe dans une
expression régulière, une mauvaise année, ou simplement rien de ce genre dans vos dossiers. Une
règle qui ne peut pas fonctionner arrête l'exécution avant toute lecture, et se nomme
(`classify.rules.0` est la première règle) :

```text
❌ Configuration invalide (classify.rules.0: Value error, rule 'Anniversaire': '02-30' is not a day that exists).
```

Le classeur montre les mêmes noms dans la colonne *Raison* de sa feuille Fichiers, et les compte
sur sa feuille Résumé.

Une règle changée après avoir modifié le classeur ? Relancez `classify` : vos modifications sont
reprises dans le nouveau classeur ([étape 5](05-review-the-proposal.md#améliorer-la-proposition-sans-perdre-votre-travail)).

---

← [5. Revoir la proposition](05-review-the-proposal.md) · [Documentation](../README.md) · Suivant : **[7. Trier](07-sort.md)** →
