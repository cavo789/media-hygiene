# `import` : rapatrier ce que seul un dossier contient (NAS, disque USB, carte SD)

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `import` · 🇬🇧 [English](../../en/commands/import.md)

## En bref

**Copier dans vos photos les photos et vidéos qu'un dossier est seul à avoir : votre NAS, un
disque USB, une carte SD, un ancien disque. Jamais celles que vous avez mises de côté ou
supprimées exprès.**

Votre NAS (ou un ancien disque) est un [dossier de sauvegarde](../clean/05-choose-the-kept-copy.md#comparer-une-sauvegarde-ou-un-ancien-disque) :
l'audit le compare à vos photos et dit ce qu'il est seul à contenir. `import` copie ces fichiers
dans vos photos, chacun vérifié, pour ne plus dépendre du NAS pour les garder. Reconnus par leur
contenu (SHA-256), quels que soient leur nom et leur place.

**Quand** : une fois un dossier de sauvegarde ajouté (`mh folders add --backup \\NAS\Photos`),
après un [`audit`](audit.md) qui dit *fichiers sont seulement là, jamais dans vos photos*. Ou
tout de suite, pour un dossier branché maintenant (une carte SD, le disque USB d'un ami) :
nommez-le sur la commande, rien à ajouter avant. Un téléphone en USB n'a pas de lettre de
lecteur : [`mh import --phone`](#depuis-un-téléphone--mh-import---phone) copie ses nouvelles
photos, Windows le lisant lui-même.

**Essayez** :

```powershell
mh import            # vos dossiers de sauvegarde (le NAS)
mh import E:\DCIM    # ce dossier seulement : lu, jamais ajouté à mh
mh import --phone    # un téléphone en USB, Windows seulement : plus bas
```

## D'un coup d'œil

| | |
|---|---|
| Vos photos | ✋ Agit : copie des fichiers **dans** vos photos (sous `From NAS`, `From E`…), n'en modifie jamais un. |
| Le dossier | Seulement lu (monté `:ro`) : rien n'est écrit, déplacé ni supprimé sur le NAS, le disque ou la carte. |
| Besoin | Un dossier de sauvegarde, ou un dossier nommé sur la commande ; vos dossiers de photos **sans** `:ro` ; `/journal` ; `/cache`. |
| Annuler | [`undo <run>`](undo.md) retire les copies (une copie modifiée depuis est gardée). |
| Avec `mh` | `mh import`, `mh import E:\DCIM`, `mh import --yes`. |

## Ce qui est copié, ce qui ne l'est pas

`import` fait d'abord un audit, avec la sauvegarde, puis trie ce qu'elle est seule à contenir :

- **Copiés** : les fichiers dont le contenu n'a jamais été dans vos photos.
- **Pas proposés, comptés à part** : ceux que vous avez **mis de côté** avant (une photo de
  rafale, une quasi-copie, une photo choisie ou indésirable, en quarantaine ou purgée depuis), et
  ceux que vous avez **supprimés** dans l'Explorateur, confirmés ou en attente de
  [`review --gone`](review.md). L'audit dit combien : *2 autres fichiers sont des fichiers que
  vous avez mis de côté ou supprimés avant : pas proposés.* Une suppression par erreur ? Le
  fichier est toujours sur le NAS : copiez-le à la main.
- **Listés à part** : une photo dont une **quasi-copie** est dans vos photos (une autre taille ou
  un autre format, un HEIC sur le NAS et son JPG sur le PC) : *probablement déjà dans vos
  photos*, pas copiée.
- **Une seule fois** : deux fichiers identiques de la sauvegarde (même taille, même début et même
  fin) sont copiés une fois.

Les copies vont dans **`From <source>`** dans votre premier dossier de photos : `From NAS` pour
un partage réseau, `From E` pour un dossier du lecteur `E:`, ses dossiers gardés en dessous
(`C:\Photos\From NAS\2019\Été\IMG_0007.jpg`, `C:\Photos\From E\100CANON\IMG_0008.jpg`), ou dans
le dossier de `--to`. Un fichier déjà copié par un import précédent, où qu'il soit maintenant,
est dans vos photos : jamais copié deux fois.
Triez-les ensuite avec [`classify`](classify.md) et [`sort`](sort.md), comme n'importe quel
dossier.

## Comment une copie est faite

Chaque fichier est d'abord noté dans le journal, copié sous un nom temporaire (le NAS est lu une
seule fois, l'empreinte calculée pendant la lecture), relu et comparé à la source (SHA-256), puis
reçoit son nom et sa date de modification. Un nom pris entre-temps n'est jamais remplacé. L'audit
suivant voit les copies comme vos photos : il ne reste rien à importer.

## Vitesse

Par le réseau, seule la liste des fichiers du NAS est lue pour la plupart d'entre eux (taille,
date : 253 fichiers en 0,1 s, mesuré). D'un fichier de même taille qu'une de vos photos, seuls
ses 64 premiers et 64 derniers Ko sont lus : même taille, même début et même fin, il est dans
vos photos. Le NAS n'est jamais lu en entier, seuls les fichiers vraiment copiés le sont. À
travers Docker Desktop, un NAS se lit à environ **15 Mo/s** (mesuré sur un Synology en
Ethernet) : 300 Go de photos de 5 Mo, environ 8 minutes pour une première comparaison au lieu
de 5 h 30 en lisant tout (estimé à partir de ce débit) ; les suivantes ne lisent que ce qui a
changé.

Le compromis : un fichier du NAS dont le début et la fin sont ceux d'une de vos photos mais dont
le milieu diffère compte comme présent dans vos photos. Il reste sur le NAS : rien n'est perdu.

## Depuis un téléphone : `mh import --phone`

```powershell
mh import --phone                              # dans <votre premier dossier de photos>\Phone\<nom du téléphone>
mh import --phone --to "D:\Depuis les téléphones" # ailleurs, puis un dossier par téléphone
mh import --phone --only Camera                # seulement le dossier DCIM\Camera du téléphone
mh import --phone --free                       # puis libérer le téléphone : plus bas
```

**Un dossier par téléphone** : les copies vont dans un dossier au nom du téléphone, celui que
Windows montre dans *Ce PC* (le nom d'appareil du téléphone). Deux téléphones du même modèle
laissés à leur nom d'usine (*Galaxy A71*) partageraient un dossier : donnez d'abord à chacun
son propre nom (Samsung : *Paramètres › À propos du téléphone › Modifier* ; Pixel :
*Paramètres › À propos du téléphone › Nom de l'appareil*), puis rebranchez-le. `mh` le dit
(💡) quand le nom ressemble à un nom d'usine. Les dossiers déjà créés ne sont pas renommés.

Branchez le téléphone en USB, déverrouillez-le et choisissez *Transfert de fichiers* (iPhone :
*Faire confiance à cet ordinateur*), et **gardez-le déverrouillé, écran allumé** jusqu'à la fin
de `mh` : en veille ou verrouillé, un téléphone ne montre aucun stockage à Windows. `mh import --phone`
dit alors *répond mais ne montre aucun stockage : réveillez-le et déverrouillez-le…* et
l'attend, jusqu'à une minute. Il trouve le téléphone (plusieurs téléphones : il demande
lequel), liste son dossier `DCIM` (environ 30 secondes par tranche de 1 000 fichiers), puis copie
**uniquement** ce que votre photothèque n'a pas encore :

- **déjà dans votre photothèque** : un fichier de même nom (sans tenir compte de la casse) et de
  même taille qu'un audit a vu, sur n'importe lequel de vos disques, branché ou non ;
- **écarté volontairement auparavant** : une photo de rafale, une quasi-copie, une photo que vous
  avez choisi de retirer (*De retour après avoir été écartés* dans [`clean`](clean.md)), que sa
  quarantaine soit encore là ou purgée ;
- **déjà copié** dans ce dossier par un `mh import --phone` précédent.

Il termine par ce qu'il a relu dans le dossier : *Nouvelles photos et vidéos copiées : 212
(1,40 Go, 18,5 Mo/s)*, puis chaque nombre laissé de côté, et *👉 Et maintenant : `mh audit`*.
🔒 Sans `--free`, le téléphone est seulement lu : rien n'y est supprimé, déplacé ni renommé.

- **Lancez d'abord une fois `mh audit`** : la photothèque est ce que le cache connaît. Sans audit,
  chaque photo du téléphone est nouvelle (il le dit).
- **Le téléphone ne donne qu'un nom et une taille**, pas son contenu. Une autre photo qui aurait
  par hasard le nom et la taille d'une des vôtres reste sur le téléphone, non copiée ; une photo
  copiée deux fois sous un autre nom est trouvée par l'audit suivant comme copie identique, que
  `clean` traite.
- **Débranché en cours de route ?** Le fichier en cours de copie est supprimé, l'import s'arrête et
  dit combien ont été copiés. Tapez de nouveau `mh import --phone` : ce qui est déjà copié est passé.
- **Jamais une question de Windows** : chaque fichier est copié dans un dossier vide
  (`.mh-phone-<date>`), puis déplacé à sa place ; un nom déjà pris reçoit `_1`, dit à l'écran. Ce
  dossier est supprimé à la fin.
- Les dossiers du téléphone sous `DCIM` sont gardés (`Camera`, `Screenshots`). Les autres dossiers
  du téléphone (WhatsApp) ne sont pas lus. Avec `--to` hors de vos dossiers de photos,
  ajoutez-le par `mh folders add` pour que les audits le voient.
- Windows uniquement : depuis WSL, Linux ou macOS, ni Docker ni bash n'atteignent un téléphone en
  USB.

### Libérer le téléphone : `mh import --phone --free`

Après l'import, une page s'ouvre dans votre navigateur avec ce que le PC peut détenir, **groupé
par dossier du téléphone** (`Camera`, `WhatsApp`, un dossier que vous avez créé…, dans l'ordre de
leurs noms ; seul le `DCIM` du téléphone est listé). Un badge sur chaque vignette dit pourquoi le
PC le détient, expliqué en haut de la colonne de gauche :

- **📚 Déjà dans votre photothèque** et **📥 Copiés par `mh import --phone`** (maintenant ou avant) : cochés
  pour vous ;
- **⚠️ Mis de côté avant, exprès** : jamais cochés pour vous. Tant que sa quarantaine est là, la
  vignette montre la photo elle-même (sa copie en quarantaine, seulement lue) et dit *Mis de côté
  le <date>, encore récupérable avec `mh undo <run>` jusqu'à `mh purge`* ; une fois purgé, *Purgé
  le <date> : il n'est nulle part ailleurs. Supprimé du téléphone, il est perdu pour de bon* (une
  purge plus ancienne que cette version ne donne pas de date : *purgé depuis*).

Un fichier coché porte une étiquette rouge *🗑️ quitte le téléphone*. Pour changer ce qui est coché,
la page fonctionne comme [`browse`](browse.md) :

- **Choisir** : un clic choisit un fichier ; la case ☑ de chaque vignette (ou Ctrl+clic) en
  ajoute ou en retire un ; Maj+clic choisit tous les fichiers depuis le dernier cliqué ; un
  rectangle tiré à la souris sur la grille choisit ce qu'il touche, sur plusieurs lignes (avec
  Ctrl, il s'ajoute au choix) ; Ctrl+A tous les fichiers de la page. **Inverser la sélection** (ou
  I) choisit les autres. Puis, dans la barre, **🗑️ Cocher : quitte le téléphone** ou **Décocher :
  reste sur le téléphone**. Un fichier mis de côté avant n'est jamais coché avec d'autres : la
  barre dit *1 fichier mis de côté auparavant est resté décoché* ; cochez-le seul, après avoir lu
  son avertissement.
- **Un dossier entier** : la case à côté de son nom coche tous ses fichiers (pas ceux mis de côté
  avant), ou les décoche tous ; ▣ quand seuls certains sont cochés. ▾ replie un long dossier
  (retenu pour la prochaine visite dans ce navigateur) ; la liste des dossiers, à gauche, mène à
  chacun.
- **Vue en grand** : un double clic ou Entrée, ← → le précédent ou le suivant, **Espace coche ou
  décoche le fichier affiché**, F plein écran, Échap ferme. Elle montre la copie du PC ; *Ouvrir
  l'original* l'ouvre tel quel.
- Pas de touche Suppr ici : la seule suppression est le bouton rouge. Les touches sont listées en
  bas à gauche (⌨ **Clavier**, puis *Plus de touches*).

Chaque coche est enregistrée aussitôt dans `phone-decisions.json` (dans votre dossier des
rapports), relue depuis le disque et affichée. **Rien ne quitte le téléphone avant que vous
appuyiez sur *Supprimer N fichiers du téléphone*** ; *Tout laisser sur le téléphone* la termine
sans rien supprimer. Ouverte depuis l'accueil (*Faire de la place sur le téléphone*), la page a
**⌂ Retour à l'accueil** en haut à droite, comme toutes les pages : il la termine de la même
façon, sans rien supprimer, et l'accueil revient dans le même onglet ; après *Supprimer*,
l'onglet dit de passer à la fenêtre PowerShell et compte les minutes écoulées face à
l'estimation (*2 min écoulées, sur environ 4*), puis montre l'accueil tout seul quand `mh` le
rouvre, même si `mh.ps1` a été écrit par une image plus ancienne ; tapé dans une console, il dit
que la fenêtre PowerShell indique quand c'est fini. Si la page s'est arrêtée entre-temps (terminée dans un autre onglet, la
fenêtre de `mh` fermée), une coche le dit clairement — *La page ne tourne plus* — et le bouton
rouge est refusé : plus rien n'y est enregistré. Ensuite, pour chaque fichier coché :

1. il est **copié à nouveau** depuis le téléphone dans un dossier vide (`.mh-phone-<date>`) ;
2. son **contenu est prouvé** (SHA-256) égal à un fichier de votre photothèque encore là, à la
   copie de l'import, ou à ce que vous aviez mis de côté ; **sinon il reste sur le téléphone**, avec
   sa raison (*Pas le même contenu que `2025\07\IMG_0001.jpg`*). Un nom et une taille ne suffisent
   jamais ;
3. seulement alors il est **déplacé hors du téléphone** vers un dossier du PC (`.mh-moved-<date>`),
   le dossier du téléphone relu pour le voir parti, et cette copie déplacée supprimée une fois
   égale à celle prouvée (une qui diffère y est gardée, dit à l'écran).

Il annonce d'abord la durée (chaque fichier est lu deux fois depuis le téléphone, environ 24 Mo/s :
*environ 6 min pour 4,2 Go*), et termine par ce qu'il a vu parti : *Téléphone libéré : 4 980
fichiers supprimés (21,3 Go)*, puis les fichiers gardés sur le téléphone et pourquoi. Chaque
suppression est écrite au journal avant et après (un passage de type `phone` dans `mh history`).

- ⚠️ **Supprimé par USB, un fichier disparaît pour de bon du téléphone** : la galerie du téléphone
  n'a pas de corbeille pour lui, et `undo` ne peut pas remettre un fichier sur un téléphone (il le
  dit). Son contenu est sur le PC : c'est ce qui a été prouvé.
- **Débranché en cours de route ?** Il s'arrête et dit ce qui a été supprimé ; le reste est encore
  sur le téléphone. Tapez de nouveau `mh import --phone --free` : il repart d'une liste fraîche.

## Options

| Option | Ce qu'elle fait |
|---|---|
| `DOSSIER` | Le dossier d'où importer (chemin de l'hôte), au lieu de vos dossiers de sauvegarde : une carte SD, un disque USB. Seulement lu pour ce passage, jamais ajouté à `mh`. |
| `--to CHEMIN` | Dossier qui reçoit les copies (chemin de l'hôte) ; par défaut : `From <source>` dans votre premier dossier de photos. |
| `--yes`, `-y` | Copier sans demander. |
| `--backup CHEMIN` | Le dossier de sauvegarde d'où importer, s'il n'est pas dans `config.toml` (`mh` passe les vôtres). |
| `--phone` | Un téléphone en USB au lieu d'un dossier, Windows seulement : le `mh` de PowerShell copie lui-même ses nouvelles photos ([plus haut](#depuis-un-téléphone--mh-import---phone)) ; avec lui, `--only <dossier de DCIM>` et `--free`. |

## Bon à savoir

- **Un NAS avec un ancien SMB** : Docker Desktop ne lit un NAS qu'en SMB 3. Si `mh` dit que le NAS
  propose une version plus ancienne, dans DSM (Synology) : *Panneau de configuration → Services
  de fichiers → SMB → Paramètres avancés → Protocole SMB maximum : SMB3*.
- **Le NAS éteint** : `import` le dit ; l'audit continue sans lui.
- **Sûr** : refusé sans journal, ou avec vos dossiers de photos en lecture seule, comme toute
  commande qui modifie des fichiers.

## Pour aller plus loin

- [Comparer une sauvegarde ou un ancien disque](../clean/05-choose-the-kept-copy.md#comparer-une-sauvegarde-ou-un-ancien-disque)
- [Plusieurs dossiers](../start/03-several-folders.md)

## L'aide intégrée

<details>
<summary><code>import --help</code></summary>

<!-- capture: help-import.txt -->
```text
 Utilisation : media-hygiene import [OPTIONS]

 Copie dans vos photos ce qu'une sauvegarde (un NAS) est seule à contenir,
 jamais ce que vous avez mis de côté ou supprimé avant ; chaque copie prouvée
 (journalisé, annulable).

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --to            <str>  Dossier qui reçoit les copies (chemin de l'hôte) ;    │
│                        par défaut : « From NAS » dans votre premier dossier  │
│                        de photos, les dossiers de la sauvegarde gardés en    │
│                        dessous.                                              │
│ --yes   -y             Copier sans demander d'abord.                         │
│ --help  -h             Affiche ce message et quitte.                         │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Avancé : dossiers (remplacent folders.* de config.toml) ────────────────────╮
│ --backup        <str>  Une sauvegarde ou un ancien disque : comparé, jamais  │
│                        modifié. Dit ce qui lui manque et ce que lui seul     │
│                        contient. Répétable.                                  │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
