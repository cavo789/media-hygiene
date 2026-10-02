# 2. Garder le cache

[Documentation](../README.md) › Pour commencer, étape 2 sur 3 · 🇬🇧 [English](../../en/start/02-keep-the-cache.md)

Votre premier audit a lu chaque photo, certaines entièrement. Sur une grosse bibliothèque, et
plus encore via Docker sous Windows, cela prend des minutes, parfois bien plus. Sans cache,
**chaque** audit repart de zéro.

Le cache retient ce que l'outil a appris sur chaque fichier : son empreinte, s'il est lisible,
à quoi il ressemble. Les audits suivants ne lisent que les fichiers nouveaux ou modifiés.

## Ajouter le cache

Ajoutez un `-v` à la commande de l'étape 1 :

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  cavo789/media-hygiene --locale fr audit
```

Dans PowerShell, la backtick `` ` `` en fin de ligne continue la commande sur la ligne suivante
(rien ne doit la suivre, pas même un espace). C'est la même commande que sur une seule ligne.

`media-hygiene-cache` n'est pas un de vos dossiers : c'est un *volume*, un espace de stockage que
Docker gère lui-même. Rien à créer : Docker le crée la première fois et le garde d'un lancement à
l'autre.

## Ce qui change

- Le premier audit avec le cache dure autant qu'avant : il remplit le cache.
- Les suivants ne lisent que les fichiers nouveaux ou modifiés : la ligne *Durée* du résumé
  montre la différence. Une étape qui n'a plus rien à faire est sautée.
- L'astuce *« Ajoutez -v media-hygiene-cache:/cache : les prochains audits seront bien plus
  rapides. »* ne s'affiche plus.

Un fichier est reconnu à son chemin, sa taille et sa date de modification : changez l'un des
trois et il est relu. Les résultats sont les mêmes, avec ou sans cache.

Le cache garde aussi ce que chaque fichier dit de lui-même, lu pendant sa vérification : la date
de prise de vue, la position GPS, l'appareil, les étoiles données dans Windows, la durée d'une
vidéo… Rien de plus n'est lu pour cela. `inventory` exporte tout cela vers un classeur Excel,
sans relire vos photos ([le classeur d'inventaire](../reference-inventory.md)).

## Bon à savoir

- **Gardez ce `-v` dans chaque commande** à partir de maintenant : `audit`, puis plus tard
  `clean`, `review`… utilisent tous le même cache.
- **Repartir de zéro** : `docker volume rm media-hygiene-cache`. Rien n'est perdu : l'audit suivant
  relit simplement tout.
- **Après une mise à jour** de l'outil, le premier audit peut relire vos photos une fois de plus,
  quand la nouvelle version apprend quelque chose de nouveau sur elles. Quand il ne lui faut que
  ce qu'une photo dit d'elle-même, il lit son en-tête, pas toute l'image : quelques minutes pour
  des dizaines de milliers de photos, avec une barre de progression à part.
- **Le cache oublie les fichiers disparus** : supprimés par `clean`, déplacés en quarantaine, ou
  déplacés et supprimés à la main. Il n'oublie que là où l'audit a pu regarder : un disque non
  monté cette fois, un dossier illisible, un dossier exclu, ou d'autres types de fichiers que ceux
  de `--ext` gardent leur place dans le cache.

---

← [1. Votre premier audit](01-first-audit.md) · [Documentation](../README.md) · Suivant : **[3. Plusieurs dossiers et disques](03-several-folders.md)** →
