# 3. Plusieurs dossiers et disques

[Documentation](../README.md) › Pour commencer, étape 3 sur 3 · 🇬🇧 [English](../../en/start/03-several-folders.md)

Les doublons restent rarement dans un seul dossier : un ancien disque, la sauvegarde d'un
téléphone, une copie sur `D:`. Donnez à l'outil tous les dossiers à comparer, et il trouve les
copies entre eux en une seule fois.

## Ajouter un dossier : `mh folders add`

Donnez le dossier tel que l'Explorateur le montre :

```powershell
mh folders add "D:\Ancien disque"
mh audit
```

Ou tapez `mh folders add` seul : la fenêtre de choix de dossier de Windows s'ouvre, choisissez-y
le dossier, puis *OK* (ni guillemets, ni chemin à taper).

`mh` se réécrit avec ce dossier, puis montre vos dossiers relus depuis son fichier.
`mh folders` seul les liste, chacun *présent* ou *introuvable* (un disque pas branché) ;
`mh folders remove "D:\Ancien disque"` en retire un, un dossier renommé aussi. Plusieurs dossiers
dès le départ ? Un `--photos` chacun dans la ligne `launcher` de l'[étape 1](01-first-audit.md#écrire-mh-une-fois) :
`--photos "C:\Photos" --photos "D:\Ancien disque"`.

Le résultat compare maintenant les deux disques :

<!-- capture: audit.txt|Résumé de l'audit|└ -->
```text
Résumé de l'audit
┌─────────────────────────────────────────────────────────────┬─────────┐
│ Fichiers média analysés                                     │      89 │
│ Groupes de fichiers identiques                              │      20 │
│ Copies en trop, à mettre de côté                            │      32 │
│ Espace libérable                                            │ 14,0 Mo │
│ Fichiers cassés (vides ou illisibles)                       │       3 │
│ Fichiers compagnons orphelins (.xmp, .aae, .thm) à déplacer │       1 │
│ Quasi-doublons (déplacés seulement avec --tier near)        │       3 │
│ Vidéos réencodées (déplacées seulement avec --tier near)    │       1 │
│ Rafales (déplacées seulement si écartées avec 'review')     │       3 │
│ Durée                                                       │     2 s │
└─────────────────────────────────────────────────────────────┴─────────┘
```

<!-- capture: audit.txt|Dossiers partageant|<blank> -->
```text
Dossiers partageant des fichiers identiques
• 12 fichiers sont à la fois dans C:\Photos\2019\Vacances à la mer (gardés) et
  dans D:\Ancien disque\Photos 2019 (des copies que 'clean' déplace en
  quarantaine), 3,6 Mo à libérer avec 'purge'. D:\Ancien disque\Photos 2019 ne
  contient rien d'autre : c'est entièrement une copie de C:\Photos\2019\Vacances
  à la mer.
• 3 fichiers sont à la fois dans C:\Photos\Téléphone (gardés) et dans D:\Ancien
  disque\Téléphone (des copies que 'clean' déplace en quarantaine), 3,0 Mo à
  libérer avec 'purge'. D:\Ancien disque\Téléphone ne contient rien d'autre :
  c'est entièrement une copie de C:\Photos\Téléphone.
• 1 fichier est à la fois dans C:\Photos\Vidéos (gardé) et dans D:\Ancien
  disque\Vidéos (une copie que 'clean' déplace en quarantaine), 2,9 Mo à libérer
  avec 'purge'.
• 8 fichiers sont à la fois dans C:\Photos\2019\Vacances à la mer (gardés) et
  dans C:\Photos\Ancien téléphone (des copies que 'clean' déplace en
  quarantaine), 2,3 Mo à libérer avec 'purge'. C:\Photos\Ancien téléphone ne
  contient rien d'autre : c'est entièrement une copie de C:\Photos\2019\Vacances
  à la mer.
• 4 fichiers sont à la fois dans C:\Photos\2020\Noël (gardés) et dans D:\Ancien
  disque\Noël 2020 (des copies que 'clean' déplace en quarantaine), 1,2 Mo à
  libérer avec 'purge'. D:\Ancien disque\Noël 2020 ne contient rien d'autre :
  c'est entièrement une copie de C:\Photos\2020\Noël.
• 3 fichiers sont à la fois dans C:\Photos\2019\Vacances à la mer (gardés) et
  dans C:\Photos\2019\Nouveau dossier (des copies que 'clean' déplace en
  quarantaine), 872,9 Ko à libérer avec 'purge'. C:\Photos\2019\Nouveau dossier
  ne contient rien d'autre : c'est entièrement une copie de
  C:\Photos\2019\Vacances à la mer.
• 1 fichier est présent plusieurs fois dans C:\Photos\2019\Vacances à la mer :
  un exemplaire est gardé (292,0 Ko à libérer).
```

Chaque chemin est affiché comme Windows l'écrit : `/data/d/Ancien disque` s'affiche
`D:\Ancien disque`.

Chaque disque de vos photos a sa propre quarantaine (`D:\media-hygiene\quarantine`) : ce que
`clean` mettra de côté reste sur son disque, un simple renommage. Plutôt une seule quarantaine pour
tout ? Ajoutez `--quarantine "D:\quarantaine"` à la ligne `launcher` : elle reçoit les fichiers de
tous les disques.

## Juste une fois : `mh --photos`

Pour une seule commande, `mh --photos "E:\Clé USB" audit` ajoute un dossier aux vôtres : les copies
de vos photos sur la clé sont trouvées aussi, et vos dossiers restent tels quels.
`mh --photos "E:\Clé USB"` seul ouvre le menu sur elle ; `mh explorer` met cela au clic droit de
chaque dossier dans l'Explorateur : clic droit, *Media Hygiene*, puis choisissez l'étape.

Un disque pas branché ? `mh` dit quel dossier il ne trouve pas et ne lance rien : Docker monterait
sinon un dossier vide, et l'audit ne trouverait rien.

## Donnez chaque dossier une seule fois

Un dossier inclut déjà ses sous-dossiers : `C:\Photos` suffit pour `C:\Photos\2019`. Donner les
deux montrerait chaque photo deux fois, et l'outil le **refuse** plutôt que de prendre une photo
pour un doublon d'elle-même.

## Une sauvegarde ou un ancien disque ? Comparez-le

Ajouté comme n'importe quel dossier (ci-dessus), `D:\sauvegarde` serait vu, à raison, comme des
doublons de vos photos. Marquez-le plutôt comme **sauvegarde** : l'outil le lit et le compare, ne
le modifie jamais, et ne met jamais une copie de côté parce que la sauvegarde l'a aussi.

```powershell
mh folders add --backup "D:\sauvegarde"
mh audit
```

`mh` se réécrit avec cette sauvegarde : dès lors, elle est montée **en lecture seule pour chaque
commande, `clean` compris**, Windows lui-même y refuse donc toute modification, et donnée aux
commandes qui comparent (`audit`, `review`, `clean`, `crosscheck`). `mh folders` la liste à part,
sous *Vos sauvegardes, comparées, jamais modifiées* ; `mh folders remove "D:\sauvegarde"` la
retire. Dès le départ : `--backup "D:\sauvegarde"` dans la ligne `launcher` de l'[étape 1](01-first-audit.md#écrire-mh-une-fois).

L'audit répond alors aux deux questions, en deux lignes :

```text
🗄️ D:\sauvegarde : 37 fichiers de vos photos ne sont pas dans cette sauvegarde (412,0 Mo).
   5 fichiers sont seulement là, jamais dans vos photos (18,3 Mo) : 'import' les copie dedans.
   2 autres fichiers sont des fichiers que vous avez mis de côté ou supprimés avant : pas proposés.
```

- **Ma sauvegarde est-elle complète ?** La première ligne : les fichiers de vos photos qui lui
  manquent.
- **Puis-je effacer cet ancien disque ?** La seconde ligne : ses fichiers qui ne sont nulle part
  ailleurs. [`mh import`](../commands/import.md) les copie dans vos photos, chacun vérifié ;
  ceux que vous avez mis de côté ou supprimés exprès ne sont jamais proposés.

### Votre NAS : récupérer ce que lui seul contient

Un partage d'un NAS est aussi une sauvegarde : `mh folders add --backup \\NAS\Photos` (son
adresse, puis le nom du dossier partagé). `mh` demande une fois le nom d'utilisateur et le mot de
passe, vérifie qu'il peut lire le partage, et propose de garder le mot de passe, chiffré pour
votre seul compte Windows, sur ce PC. Avant chaque commande, il monte le partage en lecture seule
(SMB 3) et le démonte après ; un NAS éteint est signalé en une ligne, et la commande se fait sans
lui. `mh folders` dit s'il répond ; `mh folders remove \\NAS\Photos` l'oublie, avec son mot de
passe.

À travers Docker Desktop, un NAS se lit à environ 15 Mo/s (mesuré). Une sauvegarde n'est jamais
lue en entier : d'un fichier de même taille qu'une de vos photos, l'audit lit les 64 premiers et
64 derniers Ko (128 Ko par fichier), un premier audit d'un gros NAS prend donc des minutes, pas
des heures ; les suivants ne lisent que ce qui a changé. Un Synology qui ne propose qu'un
ancien SMB : *Panneau de configuration → Services de fichiers → SMB → Paramètres avancés →
Protocole SMB maximum : SMB3*.

Le rapport liste les deux, et `backup-missing.csv` et `backup-only.csv`, à côté de `plan.csv`,
listent chaque fichier ([Comparer une sauvegarde ou un ancien disque](../clean/05-choose-the-kept-copy.md#comparer-une-sauvegarde-ou-un-ancien-disque)).
Un dossier qui ne doit même pas être lu est plutôt [exclu](../clean/05-choose-the-kept-copy.md#exclure-un-dossier).

## Un téléphone ? Copiez seulement ses nouvelles photos

Brancher un téléphone et tout copier à chaque fois ramène toutes les photos que vous avez déjà, et
le nettoyage qui suit. Sous Windows, `mh phone` copie uniquement les photos et vidéos que votre
photothèque n'a pas encore, ni celles que vous avez écartées volontairement auparavant :

```powershell
mh phone
mh audit
```

Elles arrivent dans `<votre premier dossier de photos>\Phone\<nom du téléphone>` (`--to` choisit
un autre dossier) ; le téléphone lui-même est seulement lu. Comment il décide, et que faire si le
câble se débranche : [`mh phone`](../commands/launcher.md#un-téléphone--copiez-seulement-ses-nouvelles-photos--mh-phone).

Pour faire aussi de la place sur le téléphone, `mh phone --free` montre ensuite sur une page ce que
le PC détient, et ne supprime du téléphone que ce que vous cochez, chaque fichier d'abord prouvé
sur le PC par son contenu : [libérer le téléphone](../commands/launcher.md#libérer-le-téléphone--mh-phone---free).

## Bon à savoir

- **Un Takeout Google Photos** est un dossier de plus : extrayez ses fichiers ZIP, puis ajoutez
  le dossier extrait. Ses fichiers `.json` suivent leurs photos et datent celles qui n'ont pas
  de date propre ([Google Photos Takeout](../reference-sidecars.md#google-photos-takeout)).
- **Un nouveau terminal** connaît `mh` grâce à votre profil PowerShell (étape 1). Sans cette
  ligne, rechargez-le : `. "$HOME\media-hygiene\mh.ps1"`.
- **Une nouvelle version** : `mh update` la télécharge et réécrit `mh` avec vos dossiers.
- PowerShell refuse de charger le fichier (*l'exécution de scripts est désactivée*) ? Une fois :
  `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

??? note "Sans `mh` : un `-v` par dossier, depuis PowerShell, WSL ou Linux"

    Chaque dossier a son propre `-v`. La règle : **`X:\chemin` devient `/data/x/chemin`**, la
    lettre du lecteur en minuscule. Grâce aux guillemets, les chemins avec des espaces
    fonctionnent :

    | Sur votre ordinateur | Dans la commande |
    |---|---|
    | `C:\Photos` | `-v "C:\Photos:/data/c/Photos:ro"` |
    | `D:\Ancien disque` | `-v "D:\Ancien disque:/data/d/Ancien disque:ro"` |

    ```powershell
    docker run --rm -it `
      -v "C:\Photos:/data/c/Photos:ro" `
      -v "D:\Ancien disque:/data/d/Ancien disque:ro" `
      -v media-hygiene-cache:/cache `
      cavo789/media-hygiene --locale fr audit
    ```

    Attention à la casse : Windows voit `C:\Photos` et `C:\photos\2019` comme le même dossier,
    Docker non. Le dossier courant de PowerShell est `${PWD}` (`-v "${PWD}:/data/current:ro"`) ;
    dans l'ancienne console `cmd.exe`, `%cd%`.

    **Depuis WSL**, écrivez les chemins Linux, `\` continue une ligne, et ajoutez
    `--user "$(id -u):$(id -g)"` pour que les fichiers que l'outil créera ensuite vous
    appartiennent :

    ```bash
    docker run --rm -it --user "$(id -u):$(id -g)" \
      -v "/mnt/c/Photos:/data/c/Photos:ro" \
      -v "/mnt/d/Ancien disque:/data/d/Ancien disque:ro" \
      -v media-hygiene-cache:/cache \
      cavo789/media-hygiene --locale fr audit
    ```

    **Depuis Linux**, la règle est la même : `/data` suivi du **chemin complet** du dossier. Vos
    photos dans `~/Images` et un disque USB sous `/media` :

    ```bash
    docker run --rm -it --user "$(id -u):$(id -g)" \
      -v "$HOME/Images:/data$HOME/Images:ro" \
      -v "/media/$USER/Disque/Photos:/data/media/$USER/Disque/Photos:ro" \
      -v media-hygiene-cache:/cache \
      cavo789/media-hygiene --locale fr audit
    ```

    L'outil affiche alors `/home/<vous>/Images/…` et `/media/<vous>/Disque/…`, les chemins que
    vous connaissez. Monté ailleurs (`-v "$HOME/Images:/data/images"`), l'analyse est la même,
    mais les chemins affichés ne sont plus les vôtres. `mh` existe aussi pour bash : donnez les
    dossiers tels que bash les voit (`launcher --shell bash --photos /mnt/c/Photos`), enregistrez
    dans `~/media-hygiene/mh.sh`, puis `source ~/media-hygiene/mh.sh` (dans `~/.bashrc` pour chaque
    terminal).

---

← [2. Garder le cache](02-keep-the-cache.md) · [Documentation](../README.md) · Suivant, pour nettoyer : **[4. Le rapport HTML](../clean/04-html-report.md)** → · pour trier : **[4. Proposer une arborescence](../sort/04-classify.md)** →
