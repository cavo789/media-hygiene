# `search` : retrouver une photo par ses mots

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `search` · 🇬🇧 [English](../../en/commands/search.md)

## En bref

**Retrouver une photo par ce dont vous vous souvenez : un mot, un lieu, une année, une
personne.**

`search` retrouve des photos par les mots que [`tags`](tags.md) leur a donnés et les noms donnés
dans [`people`](people.md), dans une page de votre navigateur : un champ, une grille des photos
trouvées, les meilleures d'abord, chacune avec son dossier, sa date et ses mots. Avec des mots
après la commande, il affiche à la place les premiers résultats en tableau. Les photos choisies
dans la page peuvent être **mises de côté** : le prochain [`clean --decisions`](clean.md) les
déplace en quarantaine, journalisé et annulable.

**Quand** : après [`tags`](tags.md) (et [`people`](people.md) pour les noms) ; à nouveau une
fois les nouvelles photos passées par `tags`.

**Essayer** :

```powershell
docker run --rm -it `
  -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/[cache](../reference-glossary.md#cache) `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene --locale fr search
```

## D'un coup d'œil

| | |
|---|---|
| Vos photos | 🔒 Rien ne bouge sans votre GO : *J'ai vérifié : trier ces N fichiers* déplace les fichiers d'une règle vérifiés sur la page, notés au journal ; `undo` les remet. `mh search` les monte accessibles en écriture, avec `/journal` ; montées en `:ro`, la page reste en lecture seule et le GO est refusé. |
| Il faut | `/cache` (les mots de `tags`), vos dossiers (pour montrer les photos), et `-p 127.0.0.1:8088:8088` pour la page ; `/reports` pour mettre des photos de côté. |
| Écrit | Les petits aperçus de la grille, dans le cache ; les photos mises de côté, dans `decisions.json` des rapports ; vos albums, dans `albums.json` à côté. |
| Annuler | Rien à annuler dans la page : [`clean --decisions`](clean.md) déplace les photos mises de côté, [`undo`](undo.md) les remet. |
| Avec `mh` | `mh search`, `mh search durbuy ours`. |

## Lancer

```powershell
docker run --rm -it -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene --locale fr search
```

Ouvrez <http://127.0.0.1:8088/>. La page a l'aspect et le fonctionnement de
[`browse`](browse.md) : le champ de recherche et ses filtres (une période, une partie du chemin, les mots
d'une seule source) dans la colonne de gauche, les touches ⌨ en dessous, une seule barre au-dessus
de la grille, puis les photos trouvées. **🔎 Mots** vient d'abord, **📁 Dossiers** ensuite : il
ouvre `browse`, le même serveur. Ctrl+C, ou fermer son onglet, arrête la page.

- **Dans un dossier** : sous le formulaire, l'arbre de vos dossiers, comme sur la vue des dossiers
  (ouvert à la demande). Un clic limite la recherche à ce dossier et en dessous, **sans taper de
  mot** : des mots vides listent tout le dossier ; ✕ à côté de son nom recherche à nouveau dans
  tous les dossiers.

- **Chercher** : tapez les mots, puis Entrée ; les touches vont alors à la grille, `/` revient au
  champ. *Comment écrire une recherche* rappelle les expressions ("bord de mer"), les débuts de
  mots (anniv\*) et les mots d'une seule source (place:durbuy).
- **Suivre un mot** : un clic sur un mot sous une photo (*Mechelen*, *2026*, le nom d'une
  personne) le cherche comme expression dans toutes les sources, les filtres vidés : d'une photo à
  toutes les autres qui ont ce mot. Il ne choisit jamais la photo.
- **Choisir**, comme dans `browse` : un clic choisit un fichier ; la case ☑ (ou Ctrl+clic) en
  ajoute ou en retire un ; Maj+clic choisit tous les fichiers depuis le dernier cliqué ; un
  rectangle tracé à la souris choisit ce qu'il touche (avec Ctrl, il ajoute) ; Ctrl+A tous les
  fichiers affichés, puis **Choisir les N fichiers trouvés** dans la barre prend tous les fichiers
  que la recherche trouve, pas seulement les 240 affichés ; **Inverser la sélection** (ou I) choisit
  les autres.
- **Regarder** : Entrée ou un double clic montre la photo en grand (avec un lien vers
  l'original) ; ← → la précédente ou la suivante, Suppr la met de côté puis montre la suivante, F
  plein écran, ? toutes les touches, Échap la ferme. **👤 Mettre une personne de côté** trouve
  toutes les photos de quelqu'un depuis celle qui est montrée
  ([`people`](people.md#depuis-nimporte-quelle-page--mettre-une-personne-de-côté)).

- **Une période** : *Du* et *Au* sont des calendriers, un jour chacun, inclus ; un seul est une
  période d'un jour. Le jour est celui de la prise de vue, tel que `classify` le date.
- **Trier par** et **Afficher**, dans la barre comme sur la [vue des dossiers](browse.md) :
  *meilleure correspondance* (par défaut ; la plus récente d'abord sans mots), *nom*, *date* (la
  plus ancienne d'abord) ou *taille* (la plus grande d'abord) ; **Afficher** garde les photos ou
  les vidéos seulement. La recherche trie et filtre avant de montrer ses premiers fichiers :
  *Afficher : vidéos*, *Trier par : taille* donne les plus grosses vidéos trouvées. Chaque vignette
  dit sa date et sa taille.
- **Triées** : *toutes les photos*, *pas encore triées* ou *triées (année, puis année-mois)*, lu
  dans les dossiers seuls ([la convention](../sort/04-classify.md#la-convention--année-mois-événement)) :
  une photo dans `2009\2009-11\…` est triée, où que soit cette paire de dossiers et quoi qui l'y
  ait mise. *Pas encore triées*, puis choisir et **📂 Déplacer vers un événement…** : la page
  devient le moyen de trier ce qui reste, dossier après dossier.

Sans navigateur (WSL, un script), donnez les mots : `search durbuy ours` affiche les 20 premiers
fichiers en tableau.

## Déplacer des photos vers un événement, sans règle

Pour un événement unique, une règle n'est pas nécessaire : cherchez ses jours (ou des mots),
**choisissez** les photos (comme partout : clic, Ctrl, Maj, un rectangle, Ctrl+A), puis
**📂 Déplacer vers un événement…** dans la barre. Tapez le nom de l'événement, un seul nom sans
`/` : la ligne en dessous montre le dossier créé, tel que l'Explorateur le montrera, sous l'année
et le mois de la plus ancienne photo choisie (*→ C:\Photos\2009\2009-11\Anniversaire de Tom*,
[la convention](../sort/04-classify.md#la-convention--année-mois-événement)). Le nom proposé est
celui de **votre dossier qui contient le plus de photos choisies** : ses photos vont dans le
dossier du même nom sous la convention, jamais dans un second à côté.

Avant le déplacement, les photos sont listées **par dossier source**, une case chacun, avec leur
nombre. Un dossier que vous avez nommé d'après un **autre** événement (`Saint Nicolas 2009` : un
nom, une soirée) est **décoché** : ses photos restent où elles sont, sauf si vous le cochez. Un
dossier de dates, le dossier d'un membre de la famille, le `DCIM` d'un téléphone sont cochés.
**Déplacer ces N fichiers maintenant** déplace exactement ceux cochés, noté au journal, vérifié à
leur nouvelle place, dit tel que relu (*'mh undo …' les remet*). Aucune règle n'est écrite : le
prochain `classify` les trouve à leur place.

## Faire d'une période une règle

Une fois une période cherchée, **📌 En faire une règle** ouvre, à côté de la grille, la boîte de
*Retenir comme règle* de [`review-sort`](review-sort.md), remplie avec la période : tapez son nom
et son dossier (*Garder mes dossiers en dessous* est coché). Pendant que vous tapez, la grille montre
**les photos que la règle prendrait, chacune avec l'endroit où elle irait**
(*→ 2017\Fêtes\Mariages\Mariage d'Hervé et Magda*), calculé par le moteur de `classify` avec vos
règles et celle tapée (rien n'est écrit, rien ne bouge) ; puis les photos de ces jours qu'elle
laisse à une autre règle (une capture d'écran, une photo d'un autre événement), grisées, et dites
en mots au-dessus de la grille (*30 photos de ces jours restent avec la règle 'Anniversaire de Tom
2009'*). En les voyant, corrigez les jours (seulement le 5 août) ou le dossier, puis
**Enregistrer la règle** : elle est écrite dans `config.toml`, au-dessus de *Dossiers existants*,
relue sur le disque et affichée. Le prochain `classify` l'applique.

**Mettre à jour une règle…**, dans la même boîte, liste les règles de dates de `config.toml`, la
plus récente d'abord : en choisir une remplit la boîte, et l'enregistrer la remplace sur place (sa
place dans la liste, qui décide, est gardée). Échap ou *Annuler* ferme la boîte et remontre la
recherche.

Un fichier que la recherche ne connaît pas encore (aucun mot : lancez une fois
`mh tags --no-describe`) manque à la grille.

**Les trier maintenant, petit à petit.** Une fois vérifiées, **J'ai vérifié : trier ces N
fichiers** déplace exactement les photos que la règle prend, chacune vers le dossier affiché.
Pour en laisser de côté, choisissez-les et appuyez sur **Laisser les fichiers choisis où ils
sont** (grisées, barrées). Quand les photos viennent de plusieurs dossiers, elles sont listées par
dossier source, une case chacun, un dossier que vous avez nommé d'après un autre événement
décoché. **Dès qu'une photo est laissée de côté, *Enregistrer la règle* est désactivé** : une
sélection avec des exceptions est un déplacement, pas une règle (enregistrée, la règle les
reprendrait à chaque `classify`) ; la boîte dit combien ont été laissées. La page demande une fois (le nombre, les dossiers, la ligne
d'annulation), puis les écrit comme vos choix du dernier passage de `classify`
(`sort-decisions.json`) et lance `sort` limité à ces fichiers : noté au journal, vérifié à leur
nouvelle place, dit tel que relu sur le disque (*14 déplacés, 14 vérifiés à leur nouvelle place
(passage …) : 'mh undo …' les remet*) ; les vignettes montrent ensuite leur nouvelle place. Une
photo que le dernier `classify` ne connaît pas (ajoutée depuis) est laissée en place et comptée :
relancez `classify`. Rien ne bouge sans ce GO.

*Ces dossiers sont montés en lecture seule* : votre `mh` a été écrit avant que les pages puissent
trier (il les monte en `:ro`). Tapez une fois `mh update` : il réécrit `mh`, depuis votre image,
avec les mêmes dossiers.

## Mettre des photos de côté

Pour retirer toutes les photos de quelqu'un, la page
[`people`](people.md#retirer-toutes-les-photos-de-quelquun) le fait depuis son groupe de visages.
Pour celles d'un évènement, ou tout autre choix : cherchez-les (`person:"Anne"`, une année, un
mot), choisissez-les (Ctrl+A, puis **Choisir les N fichiers trouvés** : tous les fichiers que la
recherche trouve, pas seulement les 240 affichés), puis Suppr ou **Mettre de côté les fichiers
choisis**.

- Rien n'est supprimé depuis la page. Le choix est enregistré aussitôt dans `decisions.json` de
  vos rapports, relu sur le disque et affiché avec son nombre et sa taille : *37 fichiers mis de
  côté (412 Mo), enregistrés dans … : 'clean --decisions' les déplace en quarantaine, et s'en
  souvient : si l'un d'eux revient (une nouvelle copie depuis le téléphone), l'audit le propose à
  nouveau.* Les photos
  mises de côté portent une étiquette rouge *à mettre de côté*.
- **Retirer de la mise de côté**, affiché dès qu'un fichier choisi est mis de côté, en retire les
  fichiers choisis.
- Quand vous arrêtez la page, `search` propose l'étape suivante : `mh clean --decisions`. Il
  demande d'abord combien de fichiers et d'octets partent (à part des doublons), les déplace en
  quarantaine, journalisé ; [`undo`](undo.md) les remet, [`purge`](purge.md) libère la place.
- Un fichier modifié depuis votre choix (autre taille ou date) est laissé en place et listé dans
  le rapport du nettoyage ; un fichier d'un dossier protégé fait refuser tout le fichier, comme
  partout.
- Le même `decisions.json` garde ce que [`review`](review.md) a décidé : les deux sont gardés, et
  un seul `clean --decisions` applique tout.

## Un mauvais nom sous une photo

Le nom d'une personne sous une photo porte une **×** : cliquez-la quand cette personne n'est pas
sur la photo. Les visages de la photo qui ont donné ce nom vont dans la liste `rejected` de la
personne (dans son fichier sous `/config/people/`, relié depuis `config.toml`), exactement comme
la × de la page [`people`](people.md) ; un visage que vous aviez confirmé quitte aussi ses
`faces`. Le fichier est relu et la barre dit ce qu'il contient maintenant (*Enregistré dans
config.toml, relu : 1 visage de cette photo n'est pas Chloé.*), avec **Remettre** pour annuler.
La × ne choisit jamais la photo, et la carte reste à sa place. La grande vue montre les mêmes
noms, avec la même ×, sous ses informations (`I`).

`W` dans la grande vue ouvre **Pourquoi ce nom ?** : le visage
de la photo découpé, comment il a reçu le nom (*confirmé par vous*, ou *proche d'un visage que
vous avez confirmé*, avec ce visage, son fichier et le score face à `[people] similarity`), et la
personne suivante quand elle est proche aussi. **Oui, c'est …** confirme ce visage, **Pas …**
retire le nom de ce visage seulement ; les deux sont enregistrés, relus et dits de la même façon.
Échap ferme le panneau et laisse la grande vue ouverte. Comment lire le score :
[Les personnes](../reference-people.md#les-retrouver--search).

Seule cette photo perd le nom dans cette recherche. Les autres photos nommées parce qu'elles
ressemblent à un visage que vous venez de retirer gardent le leur jusqu'à ce que vous le leur
retiriez aussi ; `classify`, l'inventaire et les fichiers XMP relisent les noms à leur prochaine
exécution. Sans `/config` accessible en écriture, rien n'est enregistré et la barre dit pourquoi.

## Mettre des photos dans un album

Pour montrer des photos à d'autres (sur la télé avec [`slideshow`](slideshow.md)), rassemblez-les
dans un **album** : une liste nommée, *Crète 2023*, de photos de n'importe quels dossiers. Tapez son
nom dans **Album** (les albums déjà faits sont proposés), choisissez les photos (ou **Choisir les N
fichiers trouvés**), puis **➕ Ajouter à l'album**.

- Un album est une liste de références, rien d'autre : aucune photo n'est copiée, déplacée ni
  modifiée. Il est enregistré aussitôt dans `albums.json` de vos rapports, à côté de
  `decisions.json` (pas dans le cache : supprimer le cache garde vos albums), relu sur le disque et
  affiché : *Crète 2023 : 42 fichiers, enregistrés dans …. Seul ce fichier a changé : aucune photo
  n'a été copiée ni déplacée.*
- Ce n'est **pas** la mise de côté : *Mettre de côté* prépare un retrait, *Ajouter à l'album* un
  partage. Aucun des deux ne touche jamais la liste de l'autre.
- **Retirer de l'album** retire les photos choisies de l'album tapé ; un album laissé vide est
  supprimé.
- Une photo déplacée depuis, par [`sort`](sort.md), par [`undo`](undo.md), ou dans un dossier
  renommé dans l'Explorateur (une fois qu'un audit l'a vu), est retrouvée par son contenu :
  l'album la suit. Une photo introuvable (supprimée, ou en quarantaine) reste dans l'album, listée
  comme manquante, jusqu'à ce qu'elle revienne.
- **📺 Partager sur la télé** donne la commande qui montre l'album tapé, copiée pour vous :
  arrêtez la page, puis `mh slideshow --album "Crète 2023" --lan` ([`slideshow`](slideshow.md)).
- **📨 Préparer pour l'envoi** donne la commande qui prépare l'album pour un mail : des copies
  réduites sans la position GPS, un dossier et un zip, `mh share --album "Crète 2023"`
  ([`share`](share.md)).
- Au plus 3 000 photos ajoutées d'un coup : affinez une recherche qui en trouve plus.

Un album peut aussi devenir un dossier de l'Explorateur : [`album "Crète 2023"`](album.md) le
crée, en seconds noms (liens physiques), sans copie.

## Ce que vous pouvez taper

| Vous tapez | Il trouve |
|---|---|
| `Durbuy ours` | Les photos qui ont les deux mots, quelle que soit leur source. |
| `noel`, `gateau` | `Noël`, `gâteau` : la casse et les accents ne comptent pas. |
| `bougies` | `bougie` aussi : les mots sont gardés au singulier. |
| `anniv*` | Chaque mot qui commence ainsi. |
| `"bord de mer"` | L'expression, ses mots dans cet ordre. |
| `place:durbuy` | Le mot parmi les lieux seulement ; aussi `vision`, `caption`, `folder`, `name` (le nom du fichier), `date`, `person`. |
| `anniversaire` | Aussi `Anniversaire Léa.mp4` : les mots d'un nom de fichier choisi comptent aussi (`IMG_1234` n'en donne aucun). |
| `neige 2008` | L'année est un mot de la date : la neige de 2008. |
| `Papy dans le jardin` | Une phrase : les petits mots s'en vont (`dans`, `le`, les mots vides de `[tags]`, comme dans l'index), et un nom qu'une personne porte sur une photo est cherché parmi les personnes : lu `Papy (personne) + jardin`, dit sous la recherche. Une expression entre guillemets est gardée telle quelle. |
| `Chloé montagne` | Les photos de Chloé avec « montagne » venu de n'importe quelle source, une fois son groupe nommé dans [`people`](people.md). |
| `person:chloe`, `person:"Mamie Jeanne"` | Le nom parmi les personnes seulement. Un nom que personne ne porte encore est signalé en une ligne. |
| `un chat sur un canapé` | Après [`tags --meaning`](tags.md) : les photos qui le montrent d'abord, même sans aucun de ces mots ([recherche par le sens](../reference-tags.md#retrouver-une-photo-par-ce-quelle-montre----meaning)). |
| `Chloé cuisine` | Après `tags --meaning` : les photos de Chloé seulement, les cuisines d'abord. |

## D'où vient chaque mot

Le menu *Mots de* limite une recherche à une source ; taper son préfixe fait la même chose
(`place:durbuy`). Une source qui n'a encore aucun mot affiche *— aucun pour l'instant* dans le
menu et dans *Comment écrire une recherche*.

| Mots de | Préfixe | Ce qu'elle contient |
|---|---|---|
| toutes les sources | | N'importe laquelle (par défaut). |
| vus par le modèle | `vision:` | Les mots que le modèle de vision a donnés à ce que montre la photo (🤖 [`tags`](tags.md)). |
| la phrase du modèle | `caption:` | Sa phrase entière : pour une expression entre guillemets. |
| dossier | `folder:` | Les mots parlants des noms des dossiers. |
| nom du fichier | `name:` | Les mots d'un nom choisi par quelqu'un (aucun pour `IMG_1234`). |
| nom d'une copie retirée | `former:` | Les dossiers et le nom qu'avait un doublon avant que [`clean`](clean.md) ne le retire, gardés sur la copie restée. |
| date | `date:` | L'année, le mois, la saison et les fêtes de la date de prise de vue. |
| lieu | `place:` | La ville et vos propres lieux où la photo a été prise. |
| personne | `person:` | Les noms donnés aux visages sur la page [`people`](people.md). |
| description Google Photos | `takeout:` | La description tapée dans Google Photos (un export Takeout). |

## Conseils pour retrouver une photo

Tant que presque aucune photo n'est décrite, une ligne sous le champ le dit : *Ce que montrent
les photos n'est pas encore connu : 0 fichiers décrits sur 44 488…*, avec l'étape qui y remédie
(🤖 `tags`). Avant `tags`, une recherche ne trouve que les mots des dossiers, des noms, des
dates, des lieux et des personnes.

| Recherché | Ne trouve rien parce que | Essayez plutôt |
|---|---|---|
| `un vieil homme` | **Chaque mot doit être trouvé** : `un` et `vieil` et `homme` ; un petit mot compte aussi. | `homme`, puis moins de mots. |
| `vieil homme`, `grand-mère`, `femme` | **Le modèle n'écrit jamais d'âge, de sexe ni de lien de parenté** : pour les personnes, il n'écrit que *adulte*, *enfant*, *bébé* ou *groupe*. | `person:` et le nom de la personne (nommée sur la page [`people`](people.md)), ou `adulte`. |
| `un vieil homme dans un jardin` | **Une phrase entière demande la recherche par le sens** (`tags --meaning`) ; sans elle, des mots seulement. | `jardin` ; ou lancez une fois 🤖 `tags --meaning` : les phrases marchent alors. |
| `plage` pendant un `tags` | **Les mots du modèle arrivent dans la recherche à la fin du run** (ou après un seul Ctrl+C, qui écrit ceux des photos déjà décrites). | Attendez la fin de `tags`, ou un Ctrl+C. |

Rien trouvé ? Moins de mots, le début d'un mot (`anniv*`), une autre source dans *Mots de*, ou
la recherche par le sens. La page garde ces conseils courts, dans *Comment écrire une
recherche*.

## Options

| Option | Rôle |
|---|---|
| `MOTS` | Les mots à trouver, affichés en tableau au lieu d'ouvrir la page. |
| `--limit N` | Avec des mots : combien de fichiers le tableau liste au plus (20 par défaut). |
| `--folder DOSSIER` | Sans mots : la page s'ouvre sur ce dossier, comme *Chemin contient* le prend (un dossier que `status` liste comme restant à trier). |
| `--port PORT` | Port de la page, 8088 par défaut ; publiez le même. |

## Bon à savoir

- **Ouverte depuis la page d'accueil** (`mh` seul) : la page s'ouvre aussitôt, dans le même onglet,
  servie par la page d'accueil elle-même : aucun autre conteneur ne démarre, l'index reste ouvert
  pour la session. *⌂ Retour à l'accueil* est un simple lien (le bouton Précédent du navigateur
  marche aussi). Tapée seule (`mh search`), elle démarre toujours sa propre page.
- Sans `/reports` (ou avec un dossier où l'outil ne peut pas écrire), **Mettre de côté les fichiers choisis** dit
  pourquoi et n'enregistre rien ; la recherche elle-même fonctionne.
- La recherche ne lit que le cache : relancez [`audit`](audit.md) puis [`tags`](tags.md) pour
  trouver les nouvelles photos.
- Sans `/cache`, ou avec un cache qu'aucun audit n'a encore rempli, il s'arrête et dit pourquoi.
- **Par le sens** : une fois que [`tags --meaning`](tags.md) a donné leurs vecteurs aux photos,
  la recherche les classe aussi par ce qu'elles montrent, et le dit au lancement (*Recherche par
  le sens : 52 318 photos peuvent être trouvées par ce qu'elles montrent.*). Le modèle est lu
  dans le cache, jamais téléchargé par `search`.
- Les noms des personnes viennent des visages du cache et des noms de `config.toml`, à chaque
  lancement : montez aussi `/config` pour les trouver. Rien d'autre à lancer après avoir nommé un
  groupe.

## Pour aller plus loin

- [Retrouver en bref](../find/quick-guide.md)
- [Les tags : retrouver une photo par ses mots](../reference-tags.md#retrouver-une-photo-par-ses-mots--search)

## L'aide intégrée

<details>
<summary><code>search --help</code></summary>

<!-- capture: help-search.txt -->
```text
 Utilisation : media-hygiene search [OPTIONS] [words]...

 🔒 Lecture seule : ne modifie jamais vos photos. Retrouver des photos par
 leurs mots dans votre navigateur (ou en tableau) : les mots que 'tags' leur a
 donnés.

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│   words      <str>  Mots à trouver, affichés en tableau au lieu d'ouvrir la  │
│                     page : "bord de mer" une expression, anniv* un début de  │
│                     mot, place:durbuy parmi les lieux seulement (aussi       │
│                     vision, caption, folder, name, date, person).            │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --limit          <int range> [x>=1]  Nombre maximal de fichiers listés dans  │
│                                      le tableau. Par défaut : 20.            │
│ --port           <int range> [x>=1]  Port de la page. docker run le publie   │
│                                      sous le même numéro sur votre           │
│                                      ordinateur, par exemple -p              │
│                                      127.0.0.1:9000:9000 pour --port 9000.   │
│                                      Par défaut :  port dans config.toml,    │
│                                      8088.                                   │
│ --help   -h                          Affiche ce message et quitte.           │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
