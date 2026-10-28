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
- `keep_folders = true` (facultatif) : les dossiers que vous avez nommés restent sous la
  catégorie (plus bas).

> 💡 Les règles se lisent dans `config.toml` seulement : contrairement aux autres réglages,
> aucune variable d'environnement `MEDIA_HYGIENE_*` ne les remplace.

## Ce qu'une règle peut reconnaître

| `match` | Lit | Exemple |
|---|---|---|
| `existing_folder` | Un nom de dossier que vous avez choisi (`2019/Vacances à la mer`, `Mars 2005 - Travaux maison`). | — |
| `event_neighbour` | Les fichiers isolés d'un événement rejoignent le seul dossier que vous avez nommé pour lui. | — |
| `same_moment` | Les photos du dossier d'une personne, ou isolées, rejoignent votre dossier du même moment (plus bas). | — |
| `calendar` | Des jours qui reviennent chaque année, `dates = "MM-JJ..MM-JJ"`. | `dates = "12-24..12-26"` |
| `date_range` | Des jours qui n'arrivent qu'une fois, `dates = "AAAA-MM-JJ..AAAA-MM-JJ"`. | `dates = "2023-07-01..2023-07-15"` |
| `kind` | Un genre de fichier, `kind = "screenshot"`, `"received"` ou `"download"`. | `kind = "screenshot"` |
| `path` | Une expression régulière cherchée dans le chemin sur votre ordinateur, dossiers et nom. | `pattern = '(?i)kermesse'` |
| `camera` | Une expression régulière cherchée dans la marque et le modèle. | `pattern = '(?i)dji'` |
| `subject` | Ce que voit un modèle de vision local, pour les photos qu'aucune autre règle n'a décidées ([étape 8](08-subjects-from-a-local-model.md)). | `categories = ["École", "Animaux"]` |
| `person` | Quelqu'un que vous avez nommé dans la page [`people`](../reference-people.md) apparaît dans l'événement (plus bas). | `names = ["Chloé"]` |
| `place` | La position GPS est dans un de vos lieux ([étape 9](09-places-from-gps.md)), ou la photo a été donnée à ce lieu sur la carte de [`places`](../commands/places.md) (son GPS étant faux). | — |
| `trip` | Un événement loin de la maison, nommé d'après son pays et sa ville, hors ligne ([étape 9](09-places-from-gps.md)). | — |
| `other_category` | Les fichiers qu'aucune règle au-dessus n'a reconnus. | `category = "Autres"` |

`existing_folder`, `event_neighbour` et `same_moment` donnent comme catégorie le nom du dossier
lui-même : ils ne prennent pas de `category`. Une règle absente de la liste ne s'applique pas : une liste vide,
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

**Écrite depuis le navigateur.** Sur la page des événements, *📌 Retenir comme règle* écrit une
telle règle pour l'événement affiché, après avoir dit ce qu'elle prendrait
([étape 11](11-name-events-in-the-browser.md#retenir-un-événement-comme-règle)).

**Vue avant d'être écrite.** Sur la page de recherche, deux calendriers donnent une période au
jour près ; *📌 En faire une règle* montre alors les photos que la règle prendrait, chacune avec
l'endroit où elle irait, et celles des mêmes jours qu'elle laisse à une autre règle : corrigez les
jours ou le dossier en les voyant, puis enregistrez
([`search`](../commands/search.md#faire-dune-période-une-règle)). *Mettre à jour une règle…* fait de
même pour une règle de dates déjà écrite.

**Un voyage déjà trié dans vos dossiers.** Une règle de dates au-dessus de *Dossiers existants*
prend toutes les photos de ses jours, celles de vos propres dossiers aussi : écrite seule, elle
mettrait `2019/Montenegro/Budva` et `2019/Montenegro/Cetinje` à plat dans sa catégorie. Avec
`keep_folders = true`, la catégorie devient leur parent et vos dossiers restent dessous :

```toml
[[classify.rules]]
name = "Monténégro"
match = "date_range"
dates = "2019-07-12..2019-07-19"
category = "Vacances et sorties/Monténégro"
keep_folders = true
```

donne `2019/Vacances et sorties/Monténégro/Budva` et `…/Monténégro/Cetinje` ; les photos du
dossier d'une personne prises les mêmes jours suivent le dossier de leur moment
([plus bas](#les-dossiers-de-votre-famille)), les autres vont dans `…/Monténégro`.

Seuls le **dossier principal** de l'événement (celui qui en contient le plus de photos) et les
dossiers qui partagent un parent avec lui sont gardés : un mariage trié dans
`2017/Août 2017/Mariage Hervé et Magda` devient la catégorie elle-même, jamais
`…/Mariage d'Hervé et Magda/Mariage Hervé et Magda` ; un dossier qui ne partage rien avec lui
(`2017/Développement Sep`) va dans la catégorie à plat, jamais dessous. Le dossier d'une
personne pris le même soir (`Manon\…`) est un tel dossier sans lien : écrivez son nom dans
`person_folders` ([plus bas](#les-dossiers-de-votre-famille)) et ses photos rejoignent le
mariage par leur moment.

**Une règle de dates ne prend jamais une capture d'écran.** Les fichiers qu'une règle `kind`
reconnaît (captures d'écran, images reçues, téléchargements) ne sont pas des souvenirs du jour,
où que cette règle soit dans la liste : ils gardent la règle qu'ils auraient sans la règle de
dates.

### Les noms de dossiers et de fichiers

Une règle `path` cherche son motif dans tout le chemin, tel que Windows l'écrit
(`C:\Photos\Chris & Fred\foto020601214749_957.jpg`) : un nom de dossier, un nom de fichier,
ou les deux. `(?i)` ignore les majuscules. Un vieil appareil nommait ses photos `foto` + date
+ heure (`foto020601214749_957` : le 1er juin 2002, 21:47:49) ; toutes celles de ce jour
commencent par `foto020601` :

```toml
[[classify.rules]]
name = "Mariage de Chris et Fred"
match = "path"
pattern = '(?i)chris ?& ?fred|\bfoto020601'
category = "Fêtes/Mariages/Mariage de Chris et Fred 2002"
```

`|` veut dire « ou » : le dossier `Chris & Fred` ou un nom qui commence par `foto020601`.
`\b` marque le début d'un mot : `mafoto020601…` ne convient pas. Écrivez le motif entre
apostrophes : une barre oblique inverse reste alors telle quelle.

### Les genres de fichiers

Reconnus par le nom et les métadonnées seulement :

- `screenshot` : un nom de capture d'écran (`Screenshot_…`, `Capture d'écran …`), ou, sans
  marque, modèle ni position d'un appareil, un PNG ou une image de moins de 400 pixels. Un PNG nommé comme un appareil photo
  (`IMG_20190123_202218.png`) est pris pour une photo retouchée, pas pour une capture.
- `received` : une image reçue par une messagerie (`IMG-20200105-WA0003`, `received_…`), qui a
  perdu sa date d'appareil en route.
- `download` : une vidéo dont le nom contient une saison, une résolution ou un codec (`S01E05`,
  `1080p`, `x264`) : un film ou une série téléchargés. Ce ne sont pas des souvenirs : la liste
  d'exemples ne leur donne pas de catégorie, ils restent donc où ils sont.

### Les dossiers de votre famille

Vous avez trié un voyage vous-même, `2019/Montenegro/Budva`, `…/Cetinje` ; les photos de vos
filles des mêmes jours sont dans `2019/Photos Chloé` et `Manon 2023/dcim`. Un dossier est
**celui d'une personne** quand le nom de quelqu'un s'y trouve, comme un mot, sans tenir compte
des majuscules ni des accents (`Photos Chloé`, `Backup Manon`, `iPhone Manon` ; pas
`Chloéville`). Les noms sont ceux de la page [`people`](../reference-people.md), plus une liste
pour les personnes qui n'y sont pas nommées :

```toml
[classify]
person_folders = ["Chloé", "Manon"]
```

Avec une règle `same_moment` (dans la liste d'exemples), chaque photo du dossier d'une personne,
et chaque photo isolée (`DCIM`), prise pendant une **séance** (des photos sans pause de 6 heures,
`session_gap_hours`) où vos propres dossiers ont des photos rejoint votre dossier : `Photos
Chloé` du 12 irait dans `2019/2019-07/Montenegro/Budva`, celle du 13 dans `…/Cetinje`. Deux de
vos dossiers dans la même séance : celui dont une photo est la plus proche dans le temps. Une
photo d'aucune de ces séances va dans le dossier du voyage, le parent commun de vos dossiers
(`Montenegro`), sauf s'ils n'en ont aucun (ou seulement une année). Elles sont **à vérifier** :
regardez-les dans le rapport. Une photo d'un dossier que vous avez nommé vous-même ne bouge
jamais. `score = 0` sur la règle la désactive.

### Les personnes

Une règle `person` lit les visages nommés avec [`people`](../reference-people.md) : les visages
confirmés dans la page, et ceux qui leur ressemblent assez, comme `search` les trouve. Lancez
d'abord `people` et nommez les groupes : l'[étape 10](10-sort-by-person.md) montre tout le
chemin.

```toml
[[classify.rules]]
name = "Avec Chloé"
match = "person"
names = ["Chloé"]
category = "Personnes/Chloé"
```

- Un événement va à la règle quand au moins `min_share` pour cent de ses photos montrent la
  personne : **10** par défaut, car celle qui prend les photos y figure rarement.
  `min_share = 30` garde les événements où on la voit souvent ; une photo hors de tout
  événement y va quand elle la montre.
- `names = ["Chloé", "Manon"]` : les événements avec l'une ou l'autre. Ajoutez `all = true`
  pour ceux où chacune atteint la part.
- La casse et les accents ne comptent pas. Un nom que personne ne porte dans la page arrête
  `classify` avant toute lecture, et nomme la règle : une faute de frappe, ou un groupe pas
  encore nommé.

Placez-la **sous** les règles dont vous êtes plus sûr (dates, lieux) : avec 10 %, quelqu'un
présent sur la plupart de vos événements les prend presque tous, comme le ferait une catégorie
« Famille ».

### Les catégories

Une catégorie peut utiliser `{year}`, `{month}`, `{month_name}`, `{day}`, `{event}` et
`{event_start}`, pris au début de l'événement (le mois vaut `00` quand seule l'année est
connue) : `category = "Fêtes/Noël {year}"` ; les règles
GPS y ajoutent `{place}`, `{country}`, `{region}` et `{city}`
([étape 9](09-places-from-gps.md#écrire-les-règles)). Les caractères que Windows refuse dans un
nom de dossier sont refusés.

Les catégories d'exemple sont des occasions et des activités : Fêtes, Vacances et sorties,
École, Sport et loisirs, À la maison, Animaux, Nature et paysages, Documents et captures
d'écran, Autres. Remplacez-les par les vôtres. Évitez une catégorie « Famille » ou
« Portraits » : dans une collection familiale, elle avale la plupart des photos.

## Un appareil dont l'horloge était fausse

En voyage à l'étranger, le téléphone se met à l'heure locale ; l'appareil photo, non. Ses
photos ont une heure de retard sur celles du téléphone, et un événement photographié avec les
deux est coupé ou mélangé. Écrivez le décalage une fois dans `config.toml`, dans une table
`[[classify.clocks]]`, à côté des règles :

```toml
[[classify.clocks]]
camera = '(?i)canon eos 550d'      # cherché dans la marque et le modèle, comme la règle camera
dates = "2010-07-01..2010-07-15"   # les jours de l'appareil lui-même, les faux
shift = "+1h"                      # ce qu'il faut ajouter : + ou -, puis jours d, heures h, minutes m
```

`classify` et `tags` lisent les dates EXIF de cet appareil, ces jours-là, une heure plus tard :
les photos des deux appareils forment un seul événement, dans le bon ordre. Rien n'est écrit
dans les photos. La feuille Fichiers du classeur le dit dans la colonne **Date tirée de**
(`appareil (EXIF), +1h : règle (?i)canon eos 550d`). Un décalage combine les unités
(`-1d`, `+1d2h30m`) ; un décalage ou une plage illisible arrête l'exécution en nommant la
règle, tout comme deux règles d'un même appareil qui partagent un jour.

Une date **postérieure au jour de l'exécution** ne peut pas être juste : une horloge mal
réglée. Le fichier va dans « à vérifier » (**Date tirée de** se termine par
`dans le futur : à vérifier`), comme quand son dossier contredit l'année.

## Quelle règle l'emporte

Les règles sont lues **dans l'ordre**, et la première dont le score atteint `sure` (80 par
défaut) décide. Quand aucune ne l'atteint, la meilleure trouvée est une supposition : le fichier
reste où il est jusqu'à ce que vous la confirmiez. Quand aucune règle ne reconnaît le fichier, il
reste aussi : « à trier » veut dire « on ne sait pas », alors qu'`other_category` veut dire
« sûr que rien au-dessus ne correspond ».

Chaque `match` a un score par défaut, qu'une règle peut changer par son propre `score` ;
`score = 0` désactive une règle :

| `match` | Score |
|---|---|
| `date_range` | 95 : vous l'avez écrite, elle est sûre |
| `existing_folder` | 90 (85 pour le dossier d'une personne, `Papa/2018/…`, `Photos Chloé`) |
| `path`, `camera` | 90 |
| `calendar`, `kind`, `other_category` | 85 |
| `subject` | 85 quand les échantillons de l'événement sont d'accord ; sinon « à vérifier » |
| `person` | 85 |
| `event_neighbour`, `same_moment` | 70 : à vérifier |

La table `[classify] scores` fixe ces valeurs par défaut pour toutes les règles d'un même
`match`. Une photo dont la date est douteuse (son dossier dit une autre année) reste « à
vérifier » quelle que soit sa règle.

## Voir ce que chaque règle a fait

Le tableau *Pourquoi* de `classify` compte les fichiers que chaque règle a décidés, par son nom :

<!-- capture: classify.txt|Pourquoi|Vérifiez leurs dates -->
```text
Pourquoi
┌───────────────────────────────┬────┐
│ Dossiers existants            │ 76 │
│ Aucun indice                  │  5 │
│ Sans date                     │  4 │
│ Captures d'écran et documents │  1 │
└───────────────────────────────┴────┘

Catégories les plus remplies
┌─────────────────────┬────┐
│ Vacances à la mer   │ 13 │
│ Photos 2019         │ 12 │
│ Randonnée           │ 10 │
│ Anniversaire        │  8 │
│ Ancien téléphone    │  8 │
│ Noël                │  6 │
│ Lac                 │  6 │
│ Téléphone           │  6 │
│ Noël 2020           │  4 │
│ WhatsApp            │  3 │
└─────────────────────┴────┘

⚠️  Règles qui n'ont rien décidé : Films et séries, Voisins d'événement, Noël,
Nouvel An, Saint-Nicolas.
💡 Vérifiez leurs dates, leurs expressions et leur ordre dans config.toml.
```

Les règles qui n'ont rien décidé sont nommées après le tableau : une faute de frappe dans une
expression régulière, une mauvaise année, ou simplement rien de ce genre dans vos dossiers.

**Garder la liste vivante : *Vos règles*.** Sur la page des événements
([`review-sort`](../commands/search.md#les-événements-du-dernier-classify)), **📌 Vos règles** liste chaque règle de
`config.toml`, avec les fichiers qu'elle a décidés lors du `classify` que montre la page et, pour
une règle sur un nom de dossier, les jours de l'événement qui contient la plupart de ses
fichiers. Elles sont affichées par type (*Dates*, *Noms de dossiers et de fichiers*, *Jours de
chaque année*… vos propres dossiers en dernier), chaque type sous son titre avec son nombre, puis
par période, la plus récente d'abord ; une règle qui n'a rien décidé vient en dernier dans son
type. Un clic sur *Règle* ou *Fichiers* trie selon cette colonne, un deuxième inverse, un
troisième revient. `config.toml` garde son propre ordre, qui décide : la boîte ne le change
jamais.

- une règle qui n'a rien décidé est affichée en rouge, avec **Supprimer** (ou *Supprimer les N
  règles qui n'ont rien décidé*, après une question) : elle est retirée de `config.toml`, vos
  commentaires conservés, et la liste est relue sur le disque ;
- une règle sur un nom de dossier (`path`) ne sert qu'une fois : une fois que `sort` a rangé ses
  fichiers dans `Vacances et sorties/Turin 2018`, l'ancien nom de dossier qu'elle cherche a
  disparu. **Convertir en dates** la remplace, à sa place dans la liste, par une règle
  `date_range` avec les jours de cet événement et `keep_folders = true` ; la boîte dit d'abord ce
  qui change (« 450 fichiers : 92 de cet événement, 358 d'autres dossiers les mêmes jours.
  Ailleurs : Photos Chloé (358) », et les fichiers que décidait l'ancienne règle et que la
  nouvelle ne prendrait pas). Une règle à la fois : les jours sont ceux de l'événement qui
  contient la plupart de ses fichiers, jamais ses dates extrêmes (un motif attrape aussi des
  photos mal datées).

Les nombres sont ceux du dernier `classify` : relancez-le pour voir à l'œuvre les règles que vous
avez changées. Une
règle qui ne peut pas fonctionner arrête l'exécution avant toute lecture, et se nomme
(les règles sont comptées depuis le haut du fichier) :

```text
❌ [[classify.rules]] n° 1 dans config.toml : règle « Anniversaire » : « 02-30 » n'est pas un jour qui existe.
💡 Corrigez la valeur, puis relancez la même commande.
```

Un réglage oublié ou mal écrit est désigné de la même façon, le `name` de la règle à côté de son
numéro :

```text
❌ « match » dans [[classify.rules]] n° 3 (« Vacances ») de config.toml : ce réglage est obligatoire.
💡 Corrigez la valeur, puis relancez la même commande.
```

Le classeur montre les mêmes noms dans la colonne *Raison* de sa feuille Fichiers, et les compte
sur sa feuille Résumé.

Une règle changée après avoir modifié le classeur ? Relancez `classify` : vos modifications sont
reprises dans le nouveau classeur ([étape 5](05-review-the-proposal.md#améliorer-la-proposition-sans-perdre-votre-travail)).

---

← [5. Revoir la proposition](05-review-the-proposal.md) · [Documentation](../README.md) · Suivant : **[7. Trier](07-sort.md)** →
