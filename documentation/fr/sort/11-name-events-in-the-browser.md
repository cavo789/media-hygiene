# 11. Nommer les événements dans le navigateur

[Documentation](../README.md) › Trier, étape 11 · 🇬🇧 [English](../../en/sort/11-name-events-in-the-browser.md)

**Pourquoi nommer un événement ?** Un [événement](../reference-glossary.md#événement), ce sont les
photos d'un même moment (une kermesse, un week-end). Son nom devient **le dossier où vont ses
photos** : nommé `Kermesse`, il va dans `2016/2016-07/Kermesse`. Ce qui bouge sur le disque :
[l'onglet 🗂 Événements de `library`, à quoi ça sert](../commands/library.md#les-événements-du-dernier-classify).

L'onglet 🗂 Événements de `library` montre **un événement à la fois, ses photos, et où elles
vont**, dans votre navigateur, au clavier. Il regroupe les fichiers **pas encore triés** (hors
d'un dossier `AAAA/AAAA-MM/<nom>`) de la période cherchée, coupés là où aucune photo n'a été
prise pendant plusieurs heures. Il ne demande ni `classify` ni classeur : le classeur de
l'[étape 5](05-review-the-proposal.md) reste la voie rapide des grandes collections.

## Lancer la page

```powershell
mh library
```

<details>
<summary>Sans <code>mh</code> : la commande complète</summary>

```powershell
docker run --rm -it -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\cache:/cache" `
  cavo789/media-hygiene --locale fr library
```

</details>

Comme pour [le tri des rafales](../clean/10-review-bursts.md#étape-1--lancer-le-tri),
`mh` ouvre la page à votre ordinateur seulement, sur le port 8088. Cliquez l'onglet
**🗂 Événements** en haut de la colonne de gauche. Donnez une période (*Du*, *Au*) pour ne
regarder qu'une année ou un mois.

## Lire la page

La colonne de gauche liste les événements, par date, chacun avec ses jours et son nombre de
fichiers (⏸ marque celui que vous avez choisi de ne pas trier). Cliquez-en un : sa **fiche** dit
en une phrase où vont ses fichiers, calculé comme le fera le déplacement (les fichiers mis de côté
jamais comptés), et ses photos remplissent la grille. Ensuite :

- **Trier ici maintenant** : ses fichiers vont dans ce dossier, notés au journal (`undo` les
  remet en place), puis l'événement suivant à décider s'affiche ;
- **Un autre dossier…** : le **📂 Déplacer vers un événement…** de la barre, sur les photos
  choisies, sinon sur tout l'événement ;
- **Ne pas trier cet événement** : ses fichiers restent où ils sont, l'événement compte comme
  décidé (enregistré dans `/config/events/left.toml`, relu) ; **Annuler mon choix** le remet à
  décider. Le passer avec → n'est pas cela : un événement passé reste à décider ;
- **📚 Faire un album**, **📺 Sur la télé** (une fois une télé appairée) : les fichiers de
  l'événement, rien de déplacé ;
- **📌 Retenir comme règle**, sous les boutons (voir plus bas).

## Les touches

| Touche | Ce qu'elle fait |
|---|---|
| <kbd>N</kbd> / <kbd>P</kbd> (ou Page suivante / Page précédente) | Événement suivant ou précédent, sans décider : les boutons ← → autour de *Événement 1 sur 137*. |
| <kbd>U</kbd> | Événement suivant à décider. |
| <kbd>M</kbd> | Trier ici maintenant. |
| <kbd>O</kbd> | Un autre dossier… : les photos choisies, sinon tout l'événement. |
| <kbd>Maj</kbd>+<kbd>S</kbd> | Ne pas trier cet événement. |
| <kbd>T</kbd> | Annuler mon choix : l'événement est de nouveau à décider. |
| <kbd>Suppr</kbd> / <kbd>⌫</kbd> | Mettre de côté les fichiers choisis / les en ressortir, comme sur toute page de vignettes. |

Les photos se choisissent comme dans [les dossiers de `library`](../commands/library.md#parcourir-vos-dossiers) : un clic choisit une photo ;
la case ☑ de chaque vignette (ou Ctrl+clic) en ajoute ou en retire une ; Maj+clic choisit toutes
les photos depuis la dernière cliquée ; un rectangle tiré à la souris sur la grille choisit ce
qu'il touche ; Ctrl+A toutes les photos de l'événement. **Inverser le choix** (ou I) choisit les
autres. Entrée (ou un double clic) ouvre en grand la photo encadrée.

## Des événements faits sur les pages, jamais à la main

Un événement que vous nommez est **retenu** pour chaque `classify` suivant : son nom, ses jours et
les appareils de ses photos. Vous ne l'écrivez jamais vous-même dans `config.toml` : trois gestes
des pages le font, et chacun dit ce qu'il a enregistré, relu sur le disque.

- **Déplacer vers un événement…** Sur la page de recherche, donnez une période ou ouvrez un
  dossier, choisissez les photos, puis *Déplacer vers un événement…* et tapez son nom. Avant le
  déplacement, la fenêtre dit ce qui sera retenu : « Il sera retenu comme l'événement « Turin »
  (events/) », ou « Il sera ajouté à l'événement « Turin » » quand les photos élargissent un
  événement déjà connu, et les appareils (« Appareils : Apple iPhone 12. »). Après le
  déplacement : « L'événement « Turin » est retenu : 2019-07-12..2019-07-19. »
- **Les événements trouvés dans vos dossiers.** Les dossiers que vous avez déjà rangés à la main
  (`2019\2019-07\Monténégro`) sont aussi des événements. En haut de l'onglet 🗂 Événements,
  *N événements trouvés dans vos dossiers* les liste, chacun avec ses jours et son nombre de
  fichiers, tous cochés : décochez ceux qui ne méritent pas d'être retenus, puis **Confirmer
  ces N**. Confirmer n'agit que sur les lignes affichées : avec un filtre tapé, ou un groupe
  replié, les lignes masquées restent à décider, intactes.
  Les cochés sont retenus ; les décochés sont notés « pas des événements » et jamais reproposés
  (*N dossiers indiqués comme n'étant pas des événements*, replié en dessous, permet d'en recocher
  un). Un dossier dont les photos sont très espacées dans le temps (`Tirages jan10`) est un lot,
  pas un événement : il est listé à part, jamais proposé.
- **De nouvelles photos pendant un événement.** Le téléphone d'un conjoint, une clé USB, les
  photos d'un ami : des fichiers des jours d'un événement retenu qui ne sont dans aucun de ses
  dossiers. L'onglet Événements et la page d'accueil disent « N nouvelles photos pendant
  « Turin » — les voir ? ». *Les voir* les montre dans la grille, celles de l'appareil de
  l'événement cochées ; puis **Ajouter les photos choisies à l'événement…** (le déplacement
  ci-dessus, journalisé : `undo` les remet en place) ou **Refuser les photos choisies** (jamais
  reproposées à cet événement).

**Le même nom, plusieurs événements.** `Turin` tous les deux ou trois ans, c'est un événement à
chaque fois : un déplacement vers `Turin` rejoint le `Turin` dont les jours touchent ceux des
photos (un jour d'écart au plus), sinon il en commence un autre, enregistré comme
`Turin (avril 2022)`. La page le dit avant le déplacement (« Il sera retenu comme un nouvel
événement « Turin (avril 2022) » : « Turin » est un autre événement ») et nomme chacun avec son
mois quand plusieurs partagent un nom : `Turin (juillet 2019)`.

**Deux événements les mêmes jours.** Vous à la mer, votre fille en camp scout la même semaine :
deux événements dont les jours se chevauchent. Leurs appareils séparent leurs photos (votre
téléphone, le sien) : ils vivent côte à côte, sans avertissement. Une photo arrivée plus tard est
classée par son appareil : celui de l'événement (*✔ Probablement : l'appareil de l'événement*),
un autre (*Pendant l'événement, mais un autre appareil : ailleurs ?*), celui de l'autre événement
de ces jours (*Plutôt l'événement « Camp » (son appareil)*). Une photo sans appareil dans ses
EXIF (un scan, une image reçue) n'est jamais devinée : *Aucun appareil dans ce fichier : est-il
de l'événement ?*

**Où vont vos « non ».** Pas dans `config.toml`, qui ne doit pas grossir sans fin : les photos
refusées pour un événement vont dans `/config/events/<début>-<nom>.toml`
(`C:\Users\vous\media-hygiene\config\events\2019-07-12-Turin.toml`), les dossiers qui ne sont
pas des événements dans `/config/events/not-events.toml`. Les deux listent le contenu des fichiers
(leur SHA-256), pas leurs chemins : un refus tient toujours après que la photo a été déplacée ou
renommée.

**Où vont vos événements.** Pas dans `config.toml` non plus : chaque événement est une table
`[[rules]]` de `/config/events/<année>.toml`, l'année où il commence
(`…\config\events\2019.toml`), lue avec les règles de `config.toml` par `classify` et les
pages, juste au-dessus de *Dossiers existants*. Vous pouvez renommer ce fichier (tout
`events\*.toml` contenant des `[[rules]]` est lu) ou le modifier ; le supprimer oublie ses
événements. Les événements écrits dans `config.toml` par une version plus ancienne y sont
déplacés par [`mh config tidy --apply`](../commands/config.md#le-faire-maigrir--config-tidy), une
seule fois, une copie gardée d'abord.

## Retenir un événement comme règle

Un déplacement vaut pour les fichiers déplacés ; une **règle** vaut pour tous les `classify`
suivants, photos ajoutées plus tard comprises (une nouvelle copie du téléphone, le dossier d'une
personne des mêmes jours). **📌 Retenir comme règle** ouvre la fenêtre des règles de la page de
recherche sur les jours de l'événement
([`library`](../commands/library.md#faire-dune-période-une-règle)) : son nom, ses jours (que vous
pouvez élargir), son dossier. Avant d'enregistrer, la fenêtre montre les photos que la règle
prendrait ; enregistrée, la règle est écrite dans `/config/events/<année>.toml` (`config.toml`
reste tel que vous l'avez écrit), relue du disque et annoncée avec son heure.

## Où vont vos choix

- **Trier ici maintenant** et **Un autre dossier…** déplacent les fichiers aussitôt, notés au
  journal : chaque passage a son `undo` ([`undo`](../commands/undo.md)), et `mh status` les
  compte triés.
- **Ne pas trier cet événement** est gardé dans `/config/events/left.toml`, relu du disque.
- Plus rien n'est écrit à côté d'un plan de `classify`. Un `sort-decisions.json` qu'une version
  plus ancienne y a écrit est toujours lu par `sort`, **par-dessus** le classeur, et une
  modification du classeur faite depuis sur le même événement ou fichier est un conflit que
  `sort` liste, jamais tranché en silence.

---

← [10. Trier par personne](10-sort-by-person.md) · [Documentation](../README.md) · Suite : **[12. Albums](12-albums.md)** →
