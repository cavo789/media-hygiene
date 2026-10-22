# `launcher` : écrire vos dossiers une fois, puis taper `mh`

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `launcher` · 🇬🇧 [English](../../en/commands/launcher.md)

## En bref

**Taper `mh audit` au lieu d'un long `docker run` : vos dossiers sont écrits une fois, avec les
bons montages pour chaque commande.**

Les commandes `docker run` s'allongent à chaque dossier, et chaque commande demande des montages
un peu différents (`:ro` ou non, le [journal](../reference-glossary.md#journal), un port pour le navigateur). `launcher` affiche un
court script qui définit `mh`, une commande qui retient vos dossiers, donnés tels que
l'Explorateur les montre : aucun `-v` à écrire. Ensuite, `mh audit`, `mh clean`, `mh review`…
suffisent.

**Quand** : une fois que vous savez sur quels dossiers vous travaillez. Plus tard, `mh folders add`
en ajoute un et `mh update` apporte la nouvelle version : les deux réécrivent le fichier pour vous.

**Essayer** :

```powershell
mkdir -Force "$HOME\media-hygiene"
docker run --rm cavo789/media-hygiene --locale fr launcher --photos "C:\Photos" > "$HOME\media-hygiene\mh.ps1"
. "$HOME\media-hygiene\mh.ps1"
mh audit
```

## D'un coup d'œil

| | |
|---|---|
| Vos photos | 🔒 Jamais modifiées : il affiche seulement un script. |
| Il faut | Vos dossiers, un `--photos` chacun. |
| Bon à savoir | Chaque disque de photos a sa propre quarantaine : ce que `clean` met de côté reste sur son disque. |
| Écrit | Rien lui-même : vous redirigez ce qu'il affiche vers un fichier. |
| Annuler | Supprimez le fichier. |

## Lancer

**Sans `-it`**, et avec `>` pour enregistrer ce qu'il affiche :

```powershell
mkdir -Force "$HOME\media-hygiene"
docker run --rm cavo789/media-hygiene --locale fr launcher `
  --photos "C:\Photos" `
  --photos "D:\Ancien disque" `
  > "$HOME\media-hygiene\mh.ps1"
. "$HOME\media-hygiene\mh.ps1"
mh audit
```

Depuis WSL :

```bash
mkdir -p ~/media-hygiene
docker run --rm cavo789/media-hygiene --locale fr launcher --photos /mnt/c/Photos > ~/media-hygiene/mh.sh
source ~/media-hygiene/mh.sh
mh audit
```

## Ce que `mh` fait pour chaque commande

- **Il démarre Docker Desktop s'il ne tourne pas** (Windows) : `mh` seul, le raccourci et
  l'entrée du clic droit l'attendent, puis ouvrent l'accueil ; après toute autre commande qui a
  échoué parce que Docker Desktop était arrêté, `mh` le démarre et vous demande de retaper la
  commande, sans jamais la relancer tout seul
  ([dépannage](../reference-troubleshooting.md#docker-répond-à-la-place-de-loutil)).
- **Il vérifie d'abord vos dossiers** : un disque pas branché est signalé, et rien n'est lancé
  (Docker monterait un dossier vide à sa place).
- **Vos dossiers en lecture seule** (`:ro`) pour chaque commande qui ne les modifie jamais, en
  écriture seulement pour `clean`, `sort`, `album`, `undo`, `purge` et `xmp`.
- **Vos sauvegardes en lecture seule pour chaque commande**, `clean` compris (`launcher --backup`,
  `mh folders add --backup`) : Windows lui-même y refuse toute modification. Les commandes qui
  comparent (`audit`, `review`, `clean`, `crosscheck`) reçoivent chacune en `--backup`.
- **Le cache** (le volume `media-hygiene-cache`) et les dossiers `reports`, `config`, `journal`
  et `quarantine` de `$HOME\media-hygiene`, créés s'ils manquent ; le dossier de `--quarantine`,
  ou un dossier de l'outil que vous avez monté vous-même avec `-v` en lançant `launcher`, est gardé
  à la place.
- **Une quarantaine par disque de photos** (sans `--quarantine`) : pour chaque disque de vos
  dossiers de photos autre que celui de la quarantaine (`C:`), `X:\media-hygiene\quarantine` monté sur `/quarantine/x` et
  créé s'il manque. `clean` met chaque fichier de côté sur son propre disque : nettoyer `E:` ne
  remplit jamais `C:`
  ([nettoyer, étape 8](../clean/08-clean.md#photos-sur-un-autre-disque-que-la-quarantaine)). Un
  dossier de photos qui est un disque entier (`E:\`) a aussi la sienne : l'analyse ne lit jamais
  un dossier `media-hygiene`. `mh folders add` avec un dossier d'un nouveau disque ajoute aussi sa
  quarantaine.
- **Le port de la page du navigateur** (`-p 127.0.0.1:8088:8088`) pour `review`, `review-sort`,
  `places`, `search` et `people`, et **votre navigateur s'ouvre sur cette page** dès qu'elle
  répond : aucune adresse à copier. Ctrl+C dans la fenêtre l'arrête toujours.
- **Votre ordinateur reste éveillé pendant les commandes longues** (`audit`, `clean`,
  `inventory`, `classify`, `sort`, `tags`, `people`, `undo`) : Windows ne se met pas en veille
  avant leur fin, et peut à nouveau après (l'écran peut toujours s'éteindre). Sous Linux, `mh.sh`
  utilise `systemd-inhibit`, sous macOS `caffeinate` ; sous WSL, Windows décide.
- **Le titre de la fenêtre dit quand une commande longue se termine** : `mh audit...` pendant
  qu'elle tourne, puis `mh audit : terminé` (ou `échec`) avec un son : une fenêtre réduite le
  montre dans la barre des tâches. Votre propre titre revient au `mh` suivant.
- **Accents et emojis lisibles** dans chaque console, l'ancienne de Windows PowerShell 5.1
  aussi : `mh.ps1` lit la sortie de l'outil en UTF-8, puis rend à la console son propre encodage.
- **Les commandes que l'outil propose** à la fin d'une exécution s'écrivent `mh …` elles aussi.
- **Votre fuseau horaire, demandé à chaque lancement** : `mh.ps1` le demande à Windows
  (`Get-TimeZone`), `mh.sh` au système (`/etc/localtime`) : les rapports sont datés à votre heure,
  à l'étranger aussi. Un `[general] timezone` dans `config.toml`, ou un `-e TZ=…` donné à
  `launcher`, l'emporte.
- **Votre langue** : un `--locale fr` donné à `launcher` est écrit dans le script : `mh` parle
  français. Une langue réglée dans `config.toml` est laissée au fichier (une modification de celui-ci
  compte toujours). `launcher` finit par une ligne qui dit ce que `mh` retient : dossiers, sauvegardes (lecture seule),
  langue, fuseau horaire.

## Ce que `mh` fait lui-même

Ces commandes ne sont pas des commandes de l'image : `mh` les lance sur votre ordinateur, sans
Docker. Le `--help` de l'image ne les liste donc pas ; cette page et le menu de `mh`, si.

| Commande | Ce qu'elle fait |
|---|---|
| `mh open` | Ouvre `index.html`, la liste de tous les rapports, dans votre navigateur (le plus récent en haut). Pas encore de rapport : elle dit de lancer d'abord `mh audit`. |
| `mh shortcut` | Windows : pose une icône *Media Hygiene* sur votre Bureau et dans le menu Démarrer. Un double-clic ouvre la page d'accueil dans votre navigateur et une fenêtre PowerShell, réduite dans la barre des tâches : gardez-la ouverte (la fermer arrête Media Hygiene, et la page le dit dans les 10 secondes) ; chaque étape choisie sur la page s'y lance. Relancée, elle réécrit les deux ; un raccourci fait par un `mh` plus ancien est réécrit réduit au prochain chargement de `mh.ps1`. |
| `mh explorer` | Windows : ajoute *Media Hygiene* au clic droit de chaque dossier dans l'Explorateur, et de l'espace vide d'un dossier ouvert : la page d'accueil s'ouvre sur ce dossier. Pour votre compte seulement, sans administrateur. `mh explorer --remove` retire les deux. Sous Windows 11, il peut se trouver sous *Afficher d'autres options*. |
| `mh folders` | Liste vos dossiers de photos et les quarantaines, chacun *présent* ou *introuvable* (un disque pas branché) ; une quarantaine pas encore créée est dite telle : le premier `clean` la crée. `add` et `remove` les changent : [plus bas](#changer-vos-dossiers--mh-folders). |
| `mh update` | Télécharge la nouvelle version de l'image, puis réécrit `mh` avec les mêmes dossiers : [plus bas](#une-nouvelle-version--mh-update). |
| `mh phone` | Windows : copie uniquement les **nouvelles** photos et vidéos d'un téléphone branché en USB ; avec `--free`, supprime ensuite du téléphone ce que le PC détient, prouvé par son contenu : [plus bas](#un-téléphone--copiez-seulement-ses-nouvelles-photos--mh-phone). |
| `mh backup` | Windows : copie vos dossiers de photos dans un dossier rien qu'à eux sur le NAS, seulement ce qui lui manque ; Windows l'écrit (robocopy), le conteneur décide : [`backup`](backup.md). |
| `mh --lan` | Windows : la page d'accueil, comme `mh` seul, qu'un téléphone du même Wi-Fi peut aussi ouvrir avec un code (ou son QR code), jusqu'à l'arrêt de `mh` ; depuis le téléphone, l'audit et les rapports seulement : [`home`](home.md#depuis-un-téléphone-du-wi-fi-de-la-maison--mh---lan). |
| `mh slideshow --folder "C:\…" --lan` | Windows : le [diaporama](slideshow.md) ouvert à la télé et aux téléphones du réseau de la maison, pour ce lancement ; la télé est appairée par un code qu'elle affiche, tapé sur le téléphone. |

`mh shortcut` et `mh explorer` relisent ce qu'ils ont écrit (les fichiers `.lnk`, les clés de
registre `HKCU\Software\Classes\Directory\shell\MediaHygiene` et
`HKCU\Software\Classes\Directory\Background\shell\MediaHygiene`) et le confirment en une ligne. Un échec est dit
avec sa raison ; un *accès refusé* vient souvent d'un antivirus, qui peut bloquer un chemin qu'il a
signalé jusqu'au redémarrage de Windows. Les deux montrent l'icône *Media Hygiene* : Docker la
copie depuis l'image dans `media-hygiene.ico`, à côté de `mh.ps1` ; s'il n'y arrive pas, ils le
disent en une ligne et gardent l'icône de PowerShell. Depuis WSL,
Linux ou macOS, `mh open` utilise `wslview`, `explorer.exe`, `xdg-open` ou `open` ;
`mh shortcut`, `mh explorer` et `mh phone` disent qu'elles sont pour Windows ; `mh backup` dit
pourquoi (Windows écrit sur le NAS 7 fois plus vite) et la commande à taper dans Windows PowerShell.

**Ce que lancent l'icône et le clic droit** : Windows PowerShell, `-NoExit -Command`, qui charge
`mh.ps1` selon votre propre stratégie d'exécution (la ligne `Set-ExecutionPolicy -Scope
CurrentUser RemoteSigned` de l'étape 1), puis `mh`. Rien ne contourne cette stratégie : un
antivirus n'a donc aucune raison de l'arrêter, et vous n'avez jamais à ajouter d'exception. Si
PowerShell refuse quand même le fichier, la fenêtre dit cette ligne à taper. Un raccourci ou une
entrée de clic droit faits par un `mh` plus ancien lançaient PowerShell avec
`-ExecutionPolicy Bypass`, qu'un antivirus peut arrêter
([dépannage](../reference-troubleshooting.md#un-antivirus-a-arrêté-mh-lancé-par-le-raccourci-ou-le-clic-droit)) :
au prochain chargement de `mh.ps1` (après `mh update`, `mh folders add` ou la ligne `launcher`),
chacun de ceux qui lancent ce même `mh.ps1` est réécrit, relu et dit en une ligne :
*Mis à jour, relu depuis … : il lance ce mh.*

**`mh --photos "E:\Dossier"` seul** ouvre la page d'accueil sur ce dossier : *Où vous en êtes* le nomme (*Cette page analyse
aussi : E:\Dossier*), et l'étape
choisie l'analyse aussi, comme le ferait `mh --photos "E:\Dossier" audit`. C'est ce que lance le
clic droit de `mh explorer`.

## Changer vos dossiers : `mh folders`

```powershell
mh folders                          # vos dossiers, présents ou non
mh folders add                       # un de plus, choisi dans une fenêtre (Windows)
mh folders add "D:\Ancien disque"    # un de plus, tapé
mh folders remove "D:\Ancien disque" # un de moins
mh folders add --backup "E:\Sauvegarde" # une sauvegarde : en lecture seule, quelle que soit la commande
```

**`mh folders add` seul** (Windows) ouvre la fenêtre de choix de dossier de Windows, devant la
console, à partir de *Ce PC* : choisissez le dossier, puis *OK* ; aucun chemin à taper, aucun
guillemet. *Annuler* dit *Aucun dossier choisi : rien n'a changé.* Le dossier choisi est vérifié
comme un dossier tapé : une bibliothèque, un téléphone ou un emplacement réseau sans lettre de
lecteur est refusé, comme un dossier déjà dans la liste. `mh.sh` (WSL, Linux, macOS) n'a pas de
fenêtre : donnez le dossier.

`add` et `remove` relancent `launcher`, par l'image, avec les dossiers que `mh` contient plus ou
moins celui-là, et la même quarantaine, la même langue, les mêmes réglages. Le nouveau script va
dans un fichier à côté de `mh.ps1`, qu'il ne remplace que si `launcher` l'a accepté : un dossier
refusé (à l'intérieur d'un autre, un dossier réseau) laisse votre `mh` tel quel, avec la raison à
l'écran. `mh` charge ensuite le nouveau fichier dans ce terminal et affiche les dossiers qu'il y a
relus : ce que vous voyez est ce qui est enregistré. Les autres terminaux le voient dès qu'ils
rechargent le fichier (un nouveau terminal le fait, avec la ligne de votre profil).

- **Un dossier renommé ou déplacé** (dans l'Explorateur) : `mh` dit qu'il ne le trouve pas.
  `mh folders remove` l'ancien nom, même disparu, puis `mh folders add` le nouveau. L'audit
  suivant relit ses fichiers : le cache les connaît par leur chemin.
- **Le dernier dossier** ne peut pas être retiré : `mh` en veut au moins un. Ajoutez d'abord le
  nouveau.
- **Le dossier d'un disque pas branché** peut être retiré ; celui à ajouter doit être là.
- Windows ignore la casse : `C:\photos` est `C:\Photos`, déjà un de vos dossiers.

## Une nouvelle version : `mh update`

```powershell
mh update
```

Il télécharge la nouvelle image (`docker pull`, sa progression affichée telle quelle), réécrit
`mh` avec les mêmes dossiers exactement comme `mh folders`, puis dit les versions : *Mis à jour :
media-hygiene 0.5.0 → media-hygiene 0.6.0*, ou *Déjà la dernière version*. L'image précédente
occupe encore de la place sur votre disque : `mh update` dit combien, et la commande qui la
libère, `docker image prune` ; il ne la lance jamais à votre place.

**Quand** : quand l'outil vous le dit. Une fois par jour au plus, la [page d'accueil](home.md)
et `mh menu` demandent à Docker Hub si une version plus récente est publiée ; quand c'est le
cas, la page d'accueil l'affiche à côté de la version, avec *Voir ce qui change* et *Mettre à
jour*, et `mh menu` se termine par *Une nouvelle version, 0.5.0 : mh update*. Cette demande ne
porte aucune donnée sur vos photos : Docker Hub voit votre adresse et le nom de l'image, comme
pour un `docker pull`. Sans réseau, rien ne s'affiche et rien n'attend ; `check_updates = false`
dans `[general]` de `config.toml` la coupe ([le
réglage](../clean/07-configuration-file.md#une-nouvelle-version--check_updates)). Les notes de
chaque version sont sur [GitHub](https://github.com/cavo789/media-hygiene/releases) ; `mh update`
affiche ce lien après une mise à jour.

Un `mh` écrit avant que `mh update` existe ne le connaît pas : relancez une fois la ligne
`launcher` des guides, avec vos dossiers ; ensuite, `mh update` suffit. Une image que vous avez
construite vous-même (`media-hygiene`) n'a rien à télécharger : `mh update` le dit, puis
réécrit `mh` à partir de cette image telle quelle, avec les mêmes dossiers, et les liste tels
qu'il les relit dans le fichier.

**Un `mh` plus ancien que son image le dit.** L'image peut changer sans `mh update` : tirée par
Docker Desktop ou `docker pull`, ou reconstruite sur votre ordinateur. `mh.ps1` reste alors tel
que l'image précédente l'a écrit, et une partie de ce qu'il fait (les étapes de la page
d'accueil, la fenêtre d'une longue exécution) peut ne plus correspondre. `mh` transmet donc, à
chaque commande, l'empreinte de l'image qui l'a écrit, et l'image la compare à la sienne, sans
aucun appel Docker de plus. Quand elles diffèrent, chaque commande commence par une ligne, et
rien n'est bloqué :

```text
⚠️  Ce mh a été écrit par l'image 0.5.0 (construction 1a2b3c4d5e6f), celle-ci est 0.6.0
(construction 4d5e6f7a8b9c) : tapez mh update pour le réécrire, avec les mêmes dossiers.
```

L'empreinte est la version et une construction : le début du condensé de tous les fichiers que
l'image installe. La même version reconstruite avec un autre code est une autre construction ;
le même code construit deux fois reste la même. Un `mh` écrit avant cette vérification ne
transmet aucune empreinte : la ligne dit *écrit par une image plus ancienne* (cela couvre aussi
un `mh.ps1` qui ne comprend plus les étapes de la page d'accueil) ; avec une image construite
par vous-même, le `mh update` d'un `mh` aussi ancien dit seulement *rien à télécharger* :
relancez une fois la ligne `launcher`. Après `mh update`, la ligne disparaît. Tirer de nouveau `latest` sans changement garde la même construction : rien n'est
dit.

## Un téléphone ? Copiez seulement ses nouvelles photos : `mh phone`

```powershell
mh phone                              # dans <votre premier dossier de photos>\Phone\<nom du téléphone>
mh phone --to "D:\Depuis les téléphones" # ailleurs, puis un dossier par téléphone
mh phone --only Camera                # seulement le dossier DCIM\Camera du téléphone
mh phone --free                       # puis libérer le téléphone : plus bas
```

Branchez le téléphone en USB, déverrouillez-le et choisissez *Transfert de fichiers* (iPhone :
*Faire confiance à cet ordinateur*). `mh phone` le trouve (plusieurs téléphones : il demande
lequel), liste son dossier `DCIM` (environ 30 secondes par tranche de 1 000 fichiers), puis copie
**uniquement** ce que votre photothèque n'a pas encore :

- **déjà dans votre photothèque** : un fichier de même nom (sans tenir compte de la casse) et de
  même taille qu'un audit a vu, sur n'importe lequel de vos disques, branché ou non ;
- **écarté volontairement auparavant** : une photo de rafale, une quasi-copie, une photo que vous
  avez choisi de retirer (*De retour après avoir été écartés* dans [`clean`](clean.md)), que sa
  quarantaine soit encore là ou purgée ;
- **déjà copié** dans ce dossier par un `mh phone` précédent.

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
  dit combien ont été copiés. Tapez de nouveau `mh phone` : ce qui est déjà copié est passé.
- **Jamais une question de Windows** : chaque fichier est copié dans un dossier vide
  (`.mh-phone-<date>`), puis déplacé à sa place ; un nom déjà pris reçoit `_1`, dit à l'écran. Ce
  dossier est supprimé à la fin.
- Les dossiers du téléphone sous `DCIM` sont gardés (`Camera`, `Screenshots`). Les autres dossiers
  du téléphone (WhatsApp) ne sont pas lus. Avec `--to` hors de vos dossiers de photos,
  ajoutez-le par `mh folders add` pour que les audits le voient.
- Windows uniquement : depuis WSL, Linux ou macOS, ni Docker ni bash n'atteignent un téléphone en
  USB.

### Libérer le téléphone : `mh phone --free`

Après l'import, une page s'ouvre dans votre navigateur avec ce que le PC peut détenir, en trois
groupes :

- **📚 Déjà dans votre photothèque** et **📥 Copiés par `mh phone`** (maintenant ou avant) : cochés
  pour vous ;
- **⚠️ Mis de côté avant, exprès** : jamais cochés pour vous. Tant que sa quarantaine est là, la
  vignette montre la photo elle-même (sa copie en quarantaine, seulement lue) et dit *Mis de côté
  le <date>, encore récupérable avec `mh undo <run>` jusqu'à `mh purge`* ; une fois purgé, *Purgé
  le <date> : il n'est nulle part ailleurs. Supprimé du téléphone, il est perdu pour de bon* (une
  purge plus ancienne que cette version ne donne pas de date : *purgé depuis*).

Chaque coche est enregistrée aussitôt dans `phone-decisions.json` (dans votre dossier des
rapports), relue depuis le disque et affichée. **Rien ne quitte le téléphone avant que vous
appuyiez sur *Supprimer N fichiers du téléphone*** ; *Tout laisser sur le téléphone* la termine
sans rien supprimer. Ensuite, pour chaque fichier coché :

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
  sur le téléphone. Tapez de nouveau `mh phone --free` : il repart d'une liste fraîche.

## Options

| Option | Rôle |
|---|---|
| `--photos "C:\Photos"` | Un dossier de photos et vidéos, tel que l'Explorateur le montre (`/mnt/c/Photos` depuis WSL). Répétez-la pour plusieurs dossiers ; pas un dossier à l'intérieur d'un autre. |
| `--quarantine "D:\quarantaine"` | Où vont les copies mises de côté, de tous les disques. Par défaut : `$HOME\media-hygiene\quarantine`, avec une quarantaine par disque de photos. |
| `--backup "E:\Sauvegarde"` | Une sauvegarde ou un ancien disque : monté en lecture seule pour chaque commande, `clean` compris, et donné en `--backup` aux commandes qui comparent ([comparé, jamais modifié](../start/03-several-folders.md#une-sauvegarde-ou-un-ancien-disque--comparez-le)). Répétable ; pas un dossier de photos, ni dedans ni autour. |
| `--shell powershell` | Un script PowerShell (`mh.ps1`), pour Windows. |
| `--shell bash` | Un script bash (`mh.sh`), pour WSL, Linux, macOS. |

Par défaut, le shell est deviné d'après les dossiers : un dossier Windows (`C:\…`) donne
PowerShell. Les `-v` des guides précédents fonctionnent toujours, à côté de `--photos`.

## Bon à savoir

- **Dans un nouveau terminal**, rechargez-le : `. "$HOME\media-hygiene\mh.ps1"`. Pour avoir `mh`
  dans chaque terminal, écrivez cette ligne dans votre profil PowerShell, une fois (le profil et
  son dossier sont créés s'ils manquent ; `notepad $PROFILE` montre ensuite la ligne) :

  ```powershell
  New-Item -ItemType Directory -Force (Split-Path $PROFILE) | Out-Null
  Add-Content $PROFILE '. "$HOME\media-hygiene\mh.ps1"'
  ```

  En bash, ajoutez la ligne `source` à `~/.bashrc`.
- **Un nouveau `mh.ps1` écrit ?** Une fenêtre garde le `mh` qu'elle a chargé : après `launcher` ou
  `mh update` depuis une autre fenêtre, le fichier sur le disque est plus récent que celui que
  cette fenêtre exécute. Avant chaque commande, `mh` compare la date d'écriture du fichier à celle
  notée au chargement (une vérification, aucun appel à Docker) et dit, en une ligne, `mh a changé
  sur le disque depuis que cette fenêtre l'a chargé : tapez . 'C:\...\mh.ps1' (ou ouvrez une
  nouvelle fenêtre).` La commande s'exécute quand même ; tapez la ligne, ou ouvrez une nouvelle
  fenêtre, pour lancer la nouvelle version. Rien n'est dit si le fichier a été déplacé ou
  supprimé. `mh folders` et `mh update` rechargent le fichier eux-mêmes.
- **Un autre dossier ?** `mh folders add "E:\Dossier"` : `mh` se réécrit lui-même. Pour une
  seule commande : `mh --photos "E:\Clé USB" audit` l'ajoute à vos dossiers.
- **Un dossier réseau** (`\\NAS\photos`) est refusé par `--photos` : copiez les photos sur un
  disque local, ou montez-le vous-même avec `-v`.
- **Un dossier refusé** (dans un autre, réseau, relatif) : `launcher` dit pourquoi à l'écran, et
  le chargement du fichier s'arrête sur la même phrase.
- **Avec `-it`**, Docker envoie aussi les messages dans le fichier : `launcher` n'écrit pas de
  lanceur, et le chargement du fichier s'arrête sur la bonne commande (sans `-it`).
- PowerShell refuse de charger le fichier (*l'exécution de scripts est désactivée*) ? Une fois :
  `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`. La fenêtre qu'ouvrent le raccourci
  ou le clic droit dit aussi cette ligne.
- **Les dossiers accentués** (`C:\Photos\Vidéos`) ne craignent rien : `mh.ps1` ne contient que
  des caractères ASCII, que `>` ne peut pas abîmer, quelle que soit la page de codes de la
  console. Un `é` de dossier y est écrit `$([char]0x00E9)`, que PowerShell retransforme en `é` ;
  les commentaires perdent leurs accents.

## Pour aller plus loin

- [1. Votre premier audit : écrire `mh`](../start/01-first-audit.md#écrire-mh-une-fois)
- [3. Plusieurs dossiers et disques : `mh folders add`](../start/03-several-folders.md#ajouter-un-dossier--mh-folders-add)
- [Points de montage](../reference-mount-points.md)

## L'aide intégrée

<details>
<summary><code>launcher --help</code></summary>

<!-- capture: help-launcher.txt -->
```text
 Utilisation : media-hygiene launcher [OPTIONS]

 🔒 Lecture seule : ne modifie jamais vos photos. Écrit 'mh', une commande
 courte qui retient vos dossiers : mh audit, mh clean.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --shell               <powershell|bash>  Le shell du script : 'powershell'   │
│                                          (Windows) ou 'bash' (WSL, Linux,    │
│                                          macOS). Par défaut : deviné d'après │
│                                          les dossiers montés.                │
│ --photos              <str>              Un dossier de photos et vidéos, tel │
│                                          que l'Explorateur le montre :       │
│                                          "C:\Photos" (ou /mnt/c/Photos sous  │
│                                          WSL). Répétez-la pour plusieurs     │
│                                          dossiers. Pas besoin de -v.         │
│ --quarantine          <str>              Où vont les copies mises de côté,   │
│                                          une seule fois : de préférence sur  │
│                                          le disque des photos (un            │
│                                          déplacement, pas une copie). Par    │
│                                          défaut : le dossier quarantine de   │
│                                          votre dossier personnel.            │
│ --backup              <str>              Une sauvegarde ou un ancien disque, │
│                                          tel que l'Explorateur le montre :   │
│                                          "E:\Sauvegarde". Monté en lecture   │
│                                          seule pour chaque commande, clean   │
│                                          compris, et donné en --backup :     │
│                                          comparé, jamais modifié. Répétable. │
│ --help        -h                         Affiche ce message et quitte.       │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
