# Les albums

[Documentation](README.md) › Référence · 🇬🇧 [English](../en/reference-albums.md)

Un **album** est une liste nommée de photos et de vidéos, *Crète 2023*, rassemblées depuis
n'importe quels dossiers. C'est ce qu'on montre aux autres : sur la télé avec
[`slideshow`](commands/slideshow.md), sur un téléphone, prêt à envoyer avec
[`share`](commands/share.md), ou en dossier de l'Explorateur avec [`album`](commands/album.md).

## Ce qu'est un album ici

- **Une liste de références, rien d'autre.** Aucune photo n'est copiée, déplacée ni modifiée : les
  fichiers sont seulement lus.
- Elle est enregistrée dans `albums.json`, dans votre dossier de rapports (`/reports`), **pas**
  dans le cache : supprimer le cache garde vos albums.
- Une photo déplacée depuis par [`sort`](commands/sort.md) ou [`undo`](commands/undo.md), ou dans
  un dossier que vous avez renommé (une fois qu'un audit l'a vu), est retrouvée par son contenu ;
  une photo introuvable (supprimée, ou en quarantaine) reste dans la liste, comme *manquante*,
  jusqu'à son retour.

## Remplir un album

Dans [`search`](commands/search.md#mettre-des-photos-dans-un-album) ou
[les dossiers de `search`](commands/search.md#parcourir-vos-dossiers), choisissez les photos, tapez le nom de l'album dans **Album** (les
albums déjà faits sont proposés ; un nouveau nom le crée), puis **➕ Ajouter à l'album**. La page
dit ce qu'elle a enregistré, relu depuis le disque.

## La page des albums

`mh` l'ouvre à `/albums` (l'espace *Partager* de la page d'accueil, *Vos albums*). Elle montre
chaque album avec sa couverture, ses dates et son lieu ; un clic ouvre un album, ses photos par
jour, et une photo s'ouvre en plein écran.

Depuis la page, sur le PC (un téléphone regarde seulement : les albums changent sur le PC), vous pouvez :

- **➖ Retirer de l'album** une photo : elle sort de la liste, le fichier reste où il est ;
- **➕ Ajouter à un album** une photo, à un autre album : choisissez-le dans la liste de vos
  albums (le plus récent en premier), ou tapez un nouveau nom en dessous pour en créer un ; un nom
  tapé avec d'autres majuscules est le même album ;
- **🖼 Utiliser comme couverture** une photo : la liste des albums la montre désormais, après un
  redémarrage aussi. La couverture suit sa photo quand le fichier est déplacé ; retirée de
  l'album, la couverture redevient celle que `mh` choisit (la photo la plus nette du premier jour).

Seul `albums.json` change. Rien d'autre n'est possible ici : aucun fichier n'est supprimé, déplacé
ni envoyé.

### Sur un téléphone

Avec `mh --lan`, un téléphone jumelé par son code sur le Wi-Fi de la maison ouvre la même page,
tant que `mh` tourne sur le PC. Il ne voit que les images des albums, à la taille d'un téléphone,
jamais une autre photo de la bibliothèque ni un original. Il ne change rien : ni *➖*, ni *➕*, ni *🖼*.

## Les albums et les dossiers de liens

[L'étape 12 du guide du tri](sort/12-albums.md) et [`album`](commands/album.md) transforment un
album en **dossier de liens physiques** sur le disque, à ouvrir dans l'Explorateur. La liste est la
même : le dossier est une façon de plus de s'en servir, et `undo` le supprime. La page des albums
ne fabrique jamais ce dossier.

## Pour aller plus loin

- [`search` : mettre des photos dans un album](commands/search.md#mettre-des-photos-dans-un-album)
- [`slideshow`](commands/slideshow.md), [`share`](commands/share.md), [`album`](commands/album.md)

---

← [Documentation](README.md)
