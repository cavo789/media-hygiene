# 3. Plusieurs dossiers et disques

[Documentation](../README.md) › Pour commencer, étape 3 sur 3 · 🇬🇧 [English](../../en/start/03-several-folders.md)

Les doublons restent rarement dans un seul dossier : un ancien disque, la sauvegarde d'un
téléphone, une copie sur `D:`. Donnez à l'outil tous les dossiers à comparer, et il trouve les
copies entre eux en une seule fois.

## Un `-v` par dossier

Chaque dossier a son propre `-v`. La règle : **`X:\chemin` devient `/data/x/chemin`**, la lettre
du lecteur en minuscule.

| Sur votre ordinateur | Dans la commande |
|---|---|
| `C:\Photos` | `-v "C:\Photos:/data/c/Photos:ro"` |
| `D:\Ancien disque` | `-v "D:\Ancien disque:/data/d/Ancien disque:ro"` |

Grâce aux guillemets, les chemins avec des espaces fonctionnent. Voici les deux dossiers, avec le
cache de l'étape 2 :

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v "D:\Ancien disque:/data/d/Ancien disque:ro" `
  -v media-hygiene-cache:/cache `
  cavo789/media-hygiene --locale fr audit
```

Le résultat compare maintenant les deux disques :

<!-- capture: audit.txt|Résumé de l'audit|└ -->
```text
Résumé de l'audit
┌─────────────────────────────────────────────────────────────┬─────────┐
│ Fichiers média analysés                                     │      85 │
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

## Montez chaque dossier une seule fois

Un dossier inclut déjà ses sous-dossiers : `C:\Photos` suffit pour `C:\Photos\2019`. Monter les
deux montrerait chaque photo deux fois, et l'outil le **refuse** plutôt que de prendre une photo
pour un doublon d'elle-même. Attention à la casse : Windows voit `C:\Photos` et `C:\photos\2019`
comme le même dossier, Docker non.

## Une vraie sauvegarde ? Laissez-la de côté

Si `D:\sauvegarde` doit rester une seconde copie de vos photos, ne la montez pas, ou
[excluez-la](../clean/05-choose-the-kept-copy.md#exclure-un-dossier). Sinon l'outil voit ses fichiers comme
des doublons, ce qui est exact.

## Le dossier courant

Dans PowerShell, placez-vous dans un dossier avec `cd`, puis utilisez `${PWD}` (le dossier
courant) comme source :

```powershell
docker run --rm -it -v "${PWD}:/data/current:ro" cavo789/media-hygiene --locale fr audit
```

L'outil affiche quand même le vrai chemin Windows. Dans l'ancienne console `cmd.exe`, écrivez
`%cd%` au lieu de `${PWD}`.

## Depuis WSL

Dans un terminal WSL (ou Linux), écrivez les chemins Linux, `\` continue une ligne, et ajoutez
`--user "$(id -u):$(id -g)"` pour que les fichiers que l'outil créera ensuite vous appartiennent :

```bash
docker run --rm -it --user "$(id -u):$(id -g)" \
  -v "/mnt/c/Photos:/data/c/Photos:ro" \
  -v "/mnt/d/Ancien disque:/data/d/Ancien disque:ro" \
  -v media-hygiene-cache:/cache \
  cavo789/media-hygiene --locale fr audit
```

## Depuis Linux

Sur un ordinateur Linux, la règle est la même : `/data` suivi du **chemin complet** du dossier.
Vos photos dans `~/Images` et un disque USB sous `/media` :

```bash
docker run --rm -it --user "$(id -u):$(id -g)" \
  -v "$HOME/Images:/data$HOME/Images:ro" \
  -v "/media/$USER/Disque/Photos:/data/media/$USER/Disque/Photos:ro" \
  -v media-hygiene-cache:/cache \
  cavo789/media-hygiene --locale fr audit
```

L'outil affiche alors `/home/<vous>/Images/…` et `/media/<vous>/Disque/…`, les chemins que vous
connaissez, et les commandes qu'il propose (👉 *Et maintenant*, le lanceur `mh`) retapent les
mêmes `-v`, même quand `/home` ou le disque est une partition à part. Monté ailleurs
(`-v "$HOME/Images:/data/images"`), l'analyse est la même, mais les chemins affichés ne sont plus
les vôtres.

La suite de ce guide montre les commandes PowerShell ; les versions WSL et Linux suivent le même
modèle.

## Écrire vos dossiers une fois : `mh`

Les commandes s'allongent à chaque dossier, et chaque étape des guides en demande une un peu
différente (`:ro` ou non, le journal, la quarantaine, un port pour le navigateur). Écrivez-les
**une fois** : la commande `launcher` écrit une commande PowerShell courte, `mh`, qui retient vos
dossiers. Donnez-les tels que l'Explorateur les montre, un `--photos` chacun : pas de `-v`, `mh`
les écrit pour vous.

```powershell
mkdir -Force "$HOME\media-hygiene"
docker run --rm -e MEDIA_HYGIENE_GENERAL__LOCALE=fr cavo789/media-hygiene launcher `
  --photos "C:\Photos" `
  --photos "D:\Ancien disque" `
  --quarantine "D:\quarantaine" `
  > "$HOME\media-hygiene\mh.ps1"
. "$HOME\media-hygiene\mh.ps1"
mh audit
```

Pas de `-it` ici : ce qu'affiche `launcher` va dans le fichier. `--quarantine` est facultatif (par
défaut `$HOME\media-hygiene\quarantine`) : sur le disque des photos, mettre de côté est un
renommage, pas une copie. Le `-e …LOCALE=fr` est retenu : `mh` parle français. Et il date ses
rapports à votre heure : il demande votre fuseau horaire à Windows à chaque lancement. Ensuite chaque commande est courte : `mh audit`, `mh clean`,
`mh review`, `mh undo`, `mh status`… `mh` choisit les bons montages pour chacune : vos dossiers
en lecture seule (`:ro`) sauf si la commande les modifie (`clean`, `sort`, `album`, `undo`,
`purge`, `xmp`), le cache, et les dossiers `reports`, `config`, `journal` et `quarantine` de
`$HOME\media-hygiene` (créés s'ils manquent), plus le port des pages du navigateur pour `review`,
`review-sort`, `places`, `search` et `people`. Les commandes que l'outil propose à la fin d'une exécution deviennent
elles aussi `mh …`.

- **Dans un nouveau terminal**, rechargez-la : `. "$HOME\media-hygiene\mh.ps1"`. Pour avoir `mh`
  dans chaque terminal, écrivez cette ligne dans votre profil PowerShell, une fois (le profil et
  son dossier sont créés s'ils manquent ; `notepad $PROFILE` montre ensuite la ligne) :

  ```powershell
  New-Item -ItemType Directory -Force (Split-Path $PROFILE) | Out-Null
  Add-Content $PROFILE '. "$HOME\media-hygiene\mh.ps1"'
  ```
- **Un autre dossier ?** Relancez la commande `launcher` avec un `--photos` de plus. Pour une
  seule commande, `mh --photos "E:\Clé USB" audit` l'ajoute à vos dossiers : les copies de vos
  photos sur la clé sont trouvées aussi. `mh --photos "E:\Clé USB"` seul ouvre le menu sur
  elle ; `mh explorer` met cela au clic droit de chaque dossier dans l'Explorateur : clic droit,
  *Media Hygiene*, puis choisissez l'étape.
- **Un disque pas branché ?** `mh` dit quel dossier il ne trouve pas et ne lance rien (sinon Docker
  monterait un dossier vide, et l'audit ne trouverait rien).
- PowerShell refuse de charger le fichier (*l'exécution de scripts est désactivée*) ? Une fois :
  `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
- **Depuis WSL ou Linux** : donnez les dossiers tels que bash les voit (`--photos /mnt/c/Photos`),
  enregistrez dans `~/media-hygiene/mh.sh`, puis
  `source ~/media-hygiene/mh.sh` (dans `~/.bashrc` pour chaque terminal).

---

← [2. Garder le cache](02-keep-the-cache.md) · [Documentation](../README.md) · Suivant, pour nettoyer : **[4. Le rapport HTML](../clean/04-html-report.md)** → · pour trier : **[4. Proposer une arborescence](../sort/04-classify.md)** →
