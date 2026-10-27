# 8. Nettoyer

[Documentation](../README.md) › Nettoyer, étape 8 sur 14 · 🇬🇧 [English](../../en/clean/08-clean.md)

Vous avez fait l'audit, lu les paires de dossiers, peut-être choisi quels dossiers restent. Place
au ménage. `clean` déplace les copies en trop en quarantaine — rien n'est effacé — et garde une
trace écrite de tout, pour que vous puissiez changer d'avis. Une fois que vous avez vérifié,
`purge` libère la place ([étape 9](09-undo-history-purge.md)).

## Avant le premier nettoyage

- **Commencez petit** : nettoyez d'abord un sous-dossier, vérifiez le résultat, puis élargissez.
- **Mettez en pause la synchronisation cloud** (OneDrive, Google Drive, Dropbox, iCloud) pendant
  le nettoyage. Sinon, chaque changement est recopié dans le cloud et sur vos autres appareils.
- **Refaites un audit juste avant**, avec les mêmes options, et lisez les paires de dossiers.
- Si vous le pouvez, une sauvegarde sur un disque externe est le filet de plus contre ce
  qu'aucun logiciel ne peut empêcher (un disque qui lâche, une erreur en dehors de l'outil).
  Bienvenue, pas obligatoire : [comment vos photos restent en sécurité](../reference-safety.md).

## Deux dossiers de plus : le journal et la quarantaine

`clean` a besoin de deux de vos dossiers :

- **le journal** (`/journal`) : un fichier par nettoyage, qui liste chaque action. Sans lui, pas
  d'`undo` : `clean` refuse donc de s'exécuter.
- **la quarantaine** (`/quarantine`) : là où les fichiers sont *déplacés* au lieu d'être
  supprimés : les copies en trop, les fichiers illisibles, les fichiers compagnons orphelins, et
  plus tard quasi-doublons et photos de rafale. Sans elle, `clean` refuse de s'exécuter (sauf
  avec `--delete`, plus bas).

`mh` les crée tous les deux dans `$HOME\media-hygiene` la première fois. Pour la commande
complète, créez-les d'abord :

```powershell
mkdir -Force "$HOME\media-hygiene\journal", "$HOME\media-hygiene\quarantine"
```

### Photos sur un autre disque que la quarantaine

Avec `mh`, chaque disque de photos a sa propre quarantaine : `E:\media-hygiene\quarantine` pour
les photos de `E:` (montée sur `/quarantine/e`), `$HOME\media-hygiene\quarantine` pour celles de
`C:`. Un fichier mis de côté reste sur son disque : nettoyer `E:` ne remplit jamais `C:`. `mh`
crée ces dossiers avant chaque lancement, et `mh folders add` avec un dossier d'un nouveau disque
donne aussi à ce disque sa propre quarantaine. Avec la commande complète, ajoutez un `-v` par
disque : `-v "E:\media-hygiene\quarantine:/quarantine/e"`.

Un disque sans quarantaine à lui (un dossier de photos qui est un disque entier, `E:\`, qui la
contiendrait ; un dossier donné à une seule commande avec `mh --photos`) envoie ses fichiers dans
`/quarantine` : ils sont alors *copiés* sur `C:`, la place revient sur `E:` et `C:` se remplit
d'autant. Avant de demander, `clean` le dit en une ligne :

```text
⚠️ 32 fichiers (14,0 Go) seront copiés de E: vers la quarantaine sur C: (40,2 Go libres là-bas).
```

S'ils ne tiennent pas, en gardant 1 Go libre sur ce disque ([`quarantine_headroom_gb`](07-configuration-file.md)), `clean` s'arrête avant de déplacer quoi
que ce soit et dit combien il manque. Libérez de la place (`purge` efface les fichiers des
nettoyages précédents), ou donnez à ce disque sa propre quarantaine. La ligne demande Docker
Desktop, qui indique le disque de chaque dossier ; ailleurs (Linux, un volume Docker), rien n'est
dit.

Gardez un disque branché jusqu'à ce que ses fichiers soient vérifiés : `undo` et
`purge <exécution>` refusent une exécution dont les fichiers sont dans la quarantaine d'un disque
qui n'est pas monté, et nomment le disque à brancher ; `purge` seul efface les autres exécutions
et dit lesquelles il a gardées.
Un disque rebranché sous une autre lettre (`E:` devenu `F:`) est retrouvé : le dossier de
l'exécution dans la quarantaine de `F:` est utilisé, et `undo` le dit ; chaque fichier ne revient
que si son dossier existe sur `F:`.

## Lancer le nettoyage

Un mot avec `mh` : il monte vos dossiers **sans `:ro`** pour `clean` (l'outil doit avoir le droit
de déplacer des fichiers) et ajoute le journal et la quarantaine. La commande complète est celle de
votre audit avec ces trois changements, et `clean` au lieu d'`audit` :

```powershell
mh clean
```

<details>
<summary>Sans <code>mh</code> : la commande complète</summary>

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v "D:\Ancien disque:/data/d/Ancien disque" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene --locale fr clean
```

</details>

`clean` refait l'audit (rapidement, grâce au cache), affiche le même résumé et les mêmes paires
de dossiers, puis **demande avant de faire quoi que ce soit** :

<!-- capture: clean.txt|re:^🛟|❓ -->
```text
🛟 Rien ne sera effacé : chaque copie est d'abord comparée octet par octet avec
celle gardée, puis déplacée en quarantaine (/quarantine). 'undo' la remet en
place ; 'purge' l'efface une fois que vous avez vérifié.
1 fichier compagnon orphelin (.xmp, .aae, .thm) sera déplacé en quarantaine.
❓ Déplacer 32 copies en double (14,0 Mo) en quarantaine et traiter 3 fichiers
cassés ? [o/N] o
```

Toute autre réponse que `o` arrête tout ici, et rien ne change. Avec `o` :

<!-- capture: clean.txt|re:^─+ Nettoyage| -->
```text
────────────────────────────────── Nettoyage ───────────────────────────────────
Nettoyage 20261025-084936
┌───────────────────────────┬─────────┐
│ Fichiers traités          │      36 │
│ Taille                    │ 15,6 Mo │
│ Déplacés en quarantaine   │      35 │
│ Ignorés (laissés intacts) │       0 │
│ En échec                  │       0 │
│ Durée                     │     0 s │
└───────────────────────────┴─────────┘
7 dossiers laissés vides ont été supprimés.
✅ Rapport HTML :
C:\Users\you\media-hygiene\reports\20261025-084936-clean\report.html
💡 Vous changez d'avis ? 'media-hygiene undo 20261025-084936' restaure tout :
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v "D:\Ancien disque:/data/d/Ancien disque" `
  -v "$HOME\media-hygiene\config:/config" `
  -v "media-hygiene-cache:/cache" `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene --locale fr undo 20261025-084936
👉 Et maintenant : une fois vérifié, 'purge' libère la place des fichiers mis de
côté.
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v "D:\Ancien disque:/data/d/Ancien disque" `
  -v "$HOME\media-hygiene\config:/config" `
  -v "media-hygiene-cache:/cache" `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene --locale fr purge 20261025-084936
💡 Ouvrez index.html dans le dossier monté sur /reports : il liste tous les
rapports.
```

| Ligne | Ce qu'elle veut dire |
|---|---|
| Fichiers traités | Chaque fichier sur lequel l'outil a agi : ici 32 copies en trop et 3 autres fichiers déplacés, 1 fichier vide supprimé. |
| Taille | Leur taille totale. |
| Déplacés en quarantaine | Les copies en trop, les fichiers illisibles et les fichiers compagnons orphelins : mis de côté, pas supprimés. |
| Ignorés (laissés intacts) | Fichiers refusés par la dernière vérification (voir ci-dessous). Rien n'est forcé. |
| En échec | Fichiers que le système n'a pas laissé l'outil traiter. Le rapport les liste. |

## Ce qui est arrivé à chaque fichier

| Fichier | Ce que `clean` a fait |
|---|---|
| Copie en trop d'une photo ou d'une vidéo | **Déplacée** en quarantaine, juste après une nouvelle comparaison octet par octet avec la copie gardée. La moindre différence ? Ignorée. |
| Fichier vide (0 octet) | Supprimé : il ne contient rien (`undo` le recrée). |
| Fichier illisible (tronqué, abîmé) | **Déplacé** en quarantaine. |
| [Fichier compagnon](../reference-sidecars.md) orphelin | Déplacé en quarantaine. |
| Quasi-doublons, photos de rafale | **Pas touchés** : seulement si vous le demandez ([étape 10](10-review-bursts.md), [étape 11](11-near-duplicates.md)). |
| Photos mises de côté dans [`search`](../commands/search.md#mettre-des-photos-de-côté) ou [`people`](../commands/people.md#retirer-toutes-les-photos-de-quelquun) | **Déplacées** en quarantaine par `clean --decisions`, qui les applique avec les décisions de `review` ; la question dit combien et leur taille, à part des doublons. Une photo modifiée depuis votre choix est ignorée. |
| Fichiers d'un dossier protégé | Pas touchés, jamais. |
| Un dossier laissé vide | **Supprimé**, puis son parent s'il est vide à son tour ; `Thumbs.db`, `desktop.ini` ou `.DS_Store` seuls ne le gardent pas (déplacés d'abord en quarantaine). `undo` le recrée. Jamais un dossier que vous avez monté, protégé, de sauvegarde ou exclu, ni un dossier déjà vide avant. [Plus](../commands/clean.md#ce-qui-arrive-à-chaque-fichier) |

La quarantaine contient un dossier par nettoyage, au nom de l'exécution (sa date et son heure),
et garde en dessous les chemins d'origine :
`quarantine\<exécution>\d\Ancien disque\2020\IMG_1203.jpg`.

**Ce que disait le dossier d'une copie retirée reste cherchable sur la photo gardée.** Quand
`clean` retire une copie, la photo conservée se souvient du dossier et du nom de cette copie
(`Mariage Julie 2015`) : [`tags`](../reference-tags.md#doù-viennent-les-mots) en fait des mots
que [`search`](../commands/search.md) retrouve (`former:julie`), et
[`classify`](../sort/04-classify.md) lit ce dossier quand celui de la photo ne dit rien
(`DCIM`). `undo` les retire : la copie a de nouveau son propre nom.

## Le rapport de nettoyage

Chaque nettoyage écrit son propre rapport, listé dans `index.html` à côté des audits : ce qui a
été libéré, les paires de dossiers telles qu'elles ont été nettoyées, et les fichiers laissés
intacts, s'il y en a. Il dit ce qui a été fait, en deux blocs :

- **✅ Ce que ce nettoyage a fait** : les copies exactes retirées, les quasi-doublons déplacés
  (seulement avec `--tier near`), les photos de rafale mises de côté (seulement avec
  `--decisions`), les fichiers abîmés traités, et la ligne `mh undo` qui remet tout en place. Les
  quasi-doublons montrés plus bas sont ceux que ce nettoyage a déplacés, rien d'autre.
- **⏸️ Laissé par ce nettoyage** : une ligne par type laissé pour plus tard (quasi-doublons,
  rafales) avec la commande qui les décide (`mh review --near`, `mh review`) ; le rapport d'audit
  les montre.

![Le haut d'un rapport de nettoyage : 85 fichiers média analysés, 32 copies en double dans 20 groupes, 16,4 Mo retirés de vos dossiers, 3 fichiers cassés, puis les paires de dossiers nettoyées](../images/clean-report.webp)

## Besoin de la place tout de suite ? `--delete`

`clean --delete` supprime pour de bon les copies en trop au lieu de les déplacer, après la même
comparaison octet par octet avec la copie gardée. La copie gardée reste : `undo` reconstruit
chaque copie supprimée à partir d'elle. C'est, avec `purge`, la seule façon dont l'outil supprime
du contenu, et il le dit avant de demander.

## Bon à savoir

- **Sans question** : ajoutez `--yes` (`clean --yes`), ou mettez `confirm = false` dans la section
  `[clean]` de `config.toml`. Sans `-it`, `clean` ne peut pas demander et s'arrête : utilisez
  alors `--yes`.
- **Que fait-il ?** Une ligne sous la barre nomme le fichier en cours et ce qui lui arrive. La
  barre et son estimation suivent les octets : les grosses vidéos passent en premier.
- **Quelques fichiers à la fois** : `clean` et `undo` traitent 4 fichiers à la fois. Sur un disque
  dur USB lent, mettez `workers = 1` dans la section `[clean]` de `config.toml`
  ([étape 7](07-configuration-file.md#le-remplir)).
- **Interrompu ?** Ctrl+C, une coupure de courant : chaque action est écrite dans le journal
  *avant* et *après* avoir eu lieu, `undo` restaure donc ce qui a été fait. Un fichier que
  l'exécution n'avait pas encore touché reste où il est.
- **Des refus qui vous protègent** : `clean` s'arrête avant l'analyse sans `/journal` ni
  `/quarantine`, avec un dossier en `:ro`, avec un dossier où il ne peut pas écrire, ou avec un
  dossier de l'outil (quarantaine, journal, cache, rapports) placé dans un dossier de photos. Le
  message dit lequel. Juste avant la question, il s'arrête aussi quand les fichiers copiés depuis
  un autre disque ne tiendraient pas dans la quarantaine
  ([plus haut](#photos-sur-un-autre-disque-que-la-quarantaine)).

---

← [7. Le fichier de configuration](07-configuration-file.md) · [Documentation](../README.md) · Suivant : **[9. Annuler, historique, purge](09-undo-history-purge.md)** →
