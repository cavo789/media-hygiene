# 11. Albums : une photo dans plusieurs dossiers, sans copie

[Documentation](../README.md) › Trier, étape 11 · 🇬🇧 [English](../../en/sort/11-albums.md)

Une arborescence donne à chaque photo **une** place : `2016/Fêtes/Noël` ou `2016/Grand-mère`,
jamais les deux. Vous voulez pourtant peut-être « tous les Noëls depuis 2003 », « mes plus belles
photos » ou « tout ce qui montre Grand-mère » dans un seul dossier, sans défaire l'arborescence
que `sort` a construite.

`album` rassemble une telle sélection dans un dossier de **liens physiques**. Un lien physique est
un second nom pour le même fichier : la photo n'est ni copiée ni déplacée, et ne prend pas de
place en plus. C'est facultatif, et rien ne change tant que vous n'ajoutez pas `--apply`.

## Ce qu'est un lien physique, dans Windows

- Dans l'Explorateur, l'album contient des fichiers ordinaires : ouvrez-les, imprimez-les,
  envoyez-les.
- Ce sont **les mêmes fichiers** que les originaux : une photo modifiée (pivotée, retouchée) dans
  l'album l'est aussi dans son dossier trié.
- Supprimer une photo de l'album laisse l'original où il est ; supprimer tout le dossier de
  l'album est sans danger aussi.
- Les *Propriétés* d'un dossier qui contient à la fois l'album et les originaux comptent chaque
  photo deux fois : le disque, non. C'est son espace libre qui fait foi.

## Où vont les albums

Dans `config.toml` ([le fichier de configuration](../clean/07-configuration-file.md)), la section
`[album]` nomme le dossier qui reçoit les albums ; chaque album est un dossier dedans :

```toml
[album]
root = 'C:\Photos\Albums'
```

Laissé vide, les albums vont dans un dossier `Albums` du `target` de `[classify]`
([étape 4](04-classify.md#votre-propre-structure)).

Un lien physique ne quitte jamais son disque, **ni le dossier monté avec `-v`** : deux dossiers
montés séparément sont deux endroits différents pour Docker, même sur le même lecteur. Montez le
dossier qui contient à la fois vos photos et les albums (`C:\Photos` pour `C:\Photos\Albums`).
`album` le vérifie avant de créer quoi que ce soit, et met à part les fichiers qu'il ne peut pas
lier.

## Choisir ce que l'album rassemble

La sélection vient du plan du dernier `classify` ([étape 4](04-classify.md)), lu avec vos
modifications du classeur et de [la page du navigateur](10-name-events-in-the-browser.md) :

| Option | Rassemble |
|---|---|
| `--category Noël` | Les fichiers de cette catégorie, d'après le classeur modifié : une catégorie que vous avez renommée se demande sous son nouveau nom ; un événement que vous avez nommé donne son nom à ses fichiers. |
| `--event Kermesse` | Les fichiers d'un événement : son nom, ou son identifiant (la première colonne de la feuille Événements). |
| `--rule Vacances` | Les fichiers qu'une règle de l'[étape 6](06-write-down-what-you-know.md) a décidés, par son `name`. |
| `--rating 4` | Les fichiers qui ont au moins 4 étoiles dans Windows (1 à 5), telles que l'audit les a lues : montez le cache. |

Les majuscules ne comptent pas. Données ensemble, toutes les options doivent correspondre :
`--category Noël --rating 4` rassemble les plus belles photos de Noël. `--workbook CHEMIN` lit un
autre classeur de `classify` que le dernier.

## Le créer

Montez vos dossiers **sans** `:ro`, avec le cache, le journal, le dossier des rapports de
`classify` et votre configuration :

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene --locale fr album "Noël" --category Noël
```

`album` montre d'abord ce qu'il ferait, et ne change rien :

```text
────────────────────────────────── Album Noël ──────────────────────────────────
Classeur : C:\Users\vous\media-hygiene\reports\20261002-123210-classify\classify.xlsx
┌────────────────────────────────┬───────────────────────┐
│ Dossier de l'album             │ C:\Photos\Albums\Noël │
│ Fichiers choisis               │                   212 │
│ Liens à créer                  │                   212 │
│ Déjà dans l'album              │                     0 │
│ Introuvables                   │                     0 │
│ Sur un autre disque ou montage │                     0 │
└────────────────────────────────┴───────────────────────┘
💡 Rien n'a été modifié : ajoutez --apply pour créer les liens.
```

- *Introuvables* : des fichiers qui ne sont plus là où le plan les a vus, ni là où un `sort` de
  ce plan les a déplacés (renommés, supprimés depuis). Ils ne sont jamais liés au hasard :
  relancez `classify`.
- *Sur un autre disque ou montage* : voir [où vont les albums](#où-vont-les-albums).

Ajoutez `--apply` pour créer les liens. Chaque photo garde son nom dans l'album ; deux photos du
même nom reçoivent ` (2)`, ` (3)`… (`IMG_0001 (2).jpg`).

## Le relancer

La même commande, plus tard, n'ajoute que les nouvelles photos : une photo déjà dans l'album, sous
n'importe quel nom, n'est pas liée deux fois. Un album ne retire jamais une photo de lui-même ;
pour le recommencer, annulez-le ou supprimez son dossier.

## Jamais vu comme des doublons

Un dossier d'album contient un petit fichier, `.media-hygiene-album`. `audit`, `clean`, `classify`
et `sort` ignorent tout dossier qui le contient : les photos d'un album ne sont jamais proposées
comme doublons de leurs originaux, ni triées une seconde fois. Gardez ce fichier dans l'album.

## L'annuler

Une exécution d'`album` est journalisée comme un tri : `history` la liste (colonne *Liés*), et
`undo <exécution>` ([undo](../clean/09-undo-history-purge.md)) supprime ses liens, son fichier
`.media-hygiene-album` et les dossiers qu'elle a créés. Les originaux ne sont pas touchés.

`undo` ne supprime un lien que tant que la photo a encore un autre nom. Si l'original a été
supprimé depuis (à la main, ou par `clean`), la photo de l'album est la dernière qui reste :
`undo` la garde et le dit.

## Avec sort et clean

- Un `sort` sur le même disque renomme les originaux : l'album montre toujours les mêmes photos,
  et `album` les retrouve là où le tri les a mises.
- Un `sort` vers un **autre** disque y copie chaque fichier : l'album garde alors l'ancienne copie,
  qui reprend de la place. Créez vos albums sur le disque de l'arborescence triée.
- `clean` qui supprime une photo aussi présente dans un album ne libère pas de place tant que
  l'album la garde.
- Un disque qui refuse les liens physiques (une clé USB en FAT ou exFAT, certains partages
  réseau) : `album` s'arrête au premier refus et dit pourquoi ; `undo` supprime le dossier vide
  qu'il a laissé.
- Les fichiers compagnons (`.xmp`, `.aae`) ne sont pas liés : l'album ne contient que les photos
  et les vidéos.

---

← [10. Nommer les événements dans le navigateur](10-name-events-in-the-browser.md) · [Documentation](../README.md)
