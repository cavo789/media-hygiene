# 2. Garder le cache

[Documentation](README.md) › Étape 2 sur 13 · 🇬🇧 [English](../en/02-keep-the-cache.md)

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

## Bon à savoir

- **Gardez ce `-v` dans chaque commande** à partir de maintenant : `audit`, puis plus tard
  `clean`, `review`… utilisent tous le même cache.
- **Repartir de zéro** : `docker volume rm media-hygiene-cache`. Rien n'est perdu : l'audit suivant
  relit simplement tout.
- **Après une mise à jour** de l'outil, le premier audit peut relire vos photos une fois de plus,
  quand la nouvelle version apprend quelque chose de nouveau sur elles.

---

← [1. Votre premier audit](01-first-audit.md) · [Documentation](README.md) · Suivant : **[3. Plusieurs dossiers et disques](03-several-folders.md)** →
