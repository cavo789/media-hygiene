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

- **Il vérifie d'abord vos dossiers** : un disque pas branché est signalé, et rien n'est lancé
  (Docker monterait un dossier vide à sa place).
- **Vos dossiers en lecture seule** (`:ro`) pour chaque commande qui ne les modifie jamais, en
  écriture seulement pour `clean`, `sort`, `album`, `undo`, `purge` et `xmp`.
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
  compte toujours). `launcher` finit par une ligne qui dit ce que `mh` retient : dossiers, langue,
  fuseau horaire.

## Ce que `mh` fait lui-même

Ces commandes ne sont pas des commandes de l'image : `mh` les lance sur votre ordinateur, sans
Docker. Le `--help` de l'image ne les liste donc pas ; cette page et le menu de `mh`, si.

| Commande | Ce qu'elle fait |
|---|---|
| `mh open` | Ouvre `index.html`, la liste de tous les rapports, dans votre navigateur (le plus récent en haut). Pas encore de rapport : elle dit de lancer d'abord `mh audit`. |
| `mh shortcut` | Windows : pose une icône *Media Hygiene* sur votre Bureau et dans le menu Démarrer. Un double-clic ouvre une fenêtre PowerShell sur le menu de `mh`, qui reste ouverte. Relancée, elle réécrit les deux. |
| `mh explorer` | Windows : ajoute *Media Hygiene* au clic droit de chaque dossier dans l'Explorateur : le menu de `mh` s'ouvre sur ce dossier. Pour votre compte seulement, sans administrateur. `mh explorer --remove` le retire. Sous Windows 11, il peut se trouver sous *Afficher d'autres options*. |
| `mh folders` | Liste vos dossiers de photos et les quarantaines, chacun *présent* ou *introuvable* (un disque pas branché) ; une quarantaine pas encore créée est dite telle : le premier `clean` la crée. `add` et `remove` les changent : [plus bas](#changer-vos-dossiers--mh-folders). |
| `mh update` | Télécharge la nouvelle version de l'image, puis réécrit `mh` avec les mêmes dossiers : [plus bas](#une-nouvelle-version--mh-update). |

`mh shortcut` et `mh explorer` relisent ce qu'ils ont écrit (les fichiers `.lnk`, la clé de
registre `HKCU\Software\Classes\Directory\shell\MediaHygiene`) et le montrent. Un échec est dit
avec sa raison ; un *accès refusé* vient souvent d'un antivirus, qui peut bloquer un chemin qu'il a
signalé jusqu'au redémarrage de Windows. Les deux montrent l'icône *Media Hygiene* : Docker la
copie depuis l'image dans `media-hygiene.ico`, à côté de `mh.ps1` ; s'il n'y arrive pas, ils le
disent en une ligne et gardent l'icône de PowerShell. Depuis WSL,
Linux ou macOS, `mh open` utilise `wslview`, `explorer.exe`, `xdg-open` ou `open` ; les deux
autres disent qu'elles sont pour Windows.

**`mh --photos "E:\Dossier"` seul** ouvre le menu sur ce dossier : il dit lequel, et l'étape
choisie l'analyse aussi, comme le ferait `mh --photos "E:\Dossier" audit`. C'est ce que lance le
clic droit de `mh explorer`.

## Changer vos dossiers : `mh folders`

```powershell
mh folders                          # vos dossiers, présents ou non
mh folders add "D:\Ancien disque"    # un de plus
mh folders remove "D:\Ancien disque" # un de moins
```

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

**Quand** : une fois par mois, ou quand un guide montre une commande que votre `mh` ne connaît
pas. L'outil ne cherche jamais une nouvelle version de lui-même : rien ne quitte votre ordinateur
sans que vous le demandiez. Les notes de chaque version sont sur
[GitHub](https://github.com/cavo789/media-hygiene/releases) ; `mh update` affiche ce lien après
une mise à jour.

Un `mh` écrit avant que `mh update` existe ne le connaît pas : relancez une fois la ligne
`launcher` des guides, avec vos dossiers ; ensuite, `mh update` suffit. Une image que vous avez
construite vous-même (`media-hygiene`) n'a rien à télécharger : `mh update` le dit.

## Options

| Option | Rôle |
|---|---|
| `--photos "C:\Photos"` | Un dossier de photos et vidéos, tel que l'Explorateur le montre (`/mnt/c/Photos` depuis WSL). Répétez-la pour plusieurs dossiers ; pas un dossier à l'intérieur d'un autre. |
| `--quarantine "D:\quarantaine"` | Où vont les copies mises de côté, de tous les disques. Par défaut : `$HOME\media-hygiene\quarantine`, avec une quarantaine par disque de photos. |
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
- **Un autre dossier ?** `mh folders add "E:\Dossier"` : `mh` se réécrit lui-même. Pour une
  seule commande : `mh --photos "E:\Clé USB" audit` l'ajoute à vos dossiers.
- **Un dossier réseau** (`\\NAS\photos`) est refusé par `--photos` : copiez les photos sur un
  disque local, ou montez-le vous-même avec `-v`.
- **Un dossier refusé** (dans un autre, réseau, relatif) : `launcher` dit pourquoi à l'écran, et
  le chargement du fichier s'arrête sur la même phrase.
- **Avec `-it`**, Docker envoie aussi les messages dans le fichier : `launcher` n'écrit pas de
  lanceur, et le chargement du fichier s'arrête sur la bonne commande (sans `-it`).
- PowerShell refuse de charger le fichier (*l'exécution de scripts est désactivée*) ? Une fois :
  `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
- **Les dossiers accentués** (`C:\Photos\Vidéos`) ne craignent rien : `mh.ps1` ne contient que
  des caractères ASCII, que `>` ne peut pas abîmer, quelle que soit la page de codes de la
  console. Un `é` de dossier y est écrit `$([char]0x00E9)`, que PowerShell retransforme en `é` ;
  les commentaires perdent leurs accents.

## Pour aller plus loin

- [3. Plusieurs dossiers et disques : `mh`](../start/03-several-folders.md#écrire-vos-dossiers-une-fois--mh)
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
│ --help        -h                         Affiche ce message et quitte.       │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
