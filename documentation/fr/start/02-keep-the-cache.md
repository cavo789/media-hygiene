# 2. Garder le cache

[Documentation](../README.md) › Pour commencer, étape 2 sur 3 · 🇬🇧 [English](../../en/start/02-keep-the-cache.md)

Votre premier audit a lu chaque photo, certaines entièrement. Sur une grosse bibliothèque, et
plus encore via Docker sous Windows, cela prend des minutes, parfois bien plus.

Le cache retient ce que l'outil a appris sur chaque fichier : son empreinte, s'il est lisible,
à quoi il ressemble. Les audits suivants ne lisent que les fichiers nouveaux ou modifiés.
**`mh` le garde pour vous** : chaque commande `mh` utilise le même cache, un volume Docker nommé
`media-hygiene-cache`. Rien à régler.

## Auditer à nouveau

```powershell
mh audit
```

<!-- capture: audit-mh-again.txt|re:^─+ Audit|Rien de nouveau -->
```text
──────────────────────────────────── Audit ─────────────────────────────────────
16 dossiers inchangés repris de l'index, 0 relus.
💡 Une photo modifiée sur place par un autre programme ? 'audit --full' relit
tous les dossiers (c'est fait de toute façon pour ceux listés il y a 7 jours).

♻️  Rien de nouveau ni de modifié depuis le dernier audit : 61 fichiers repris
du cache.
```

## Ce qui change

- Le premier audit remplit le cache. Sa ligne ⏳ dit que vous pouvez arrêter à tout moment
  (Ctrl+C) sans perdre ce qui est vérifié, et après le résumé : *« ⚡ Prochain audit : quelques
  secondes, les fichiers vérifiés sont repris du cache. »*
- Les suivants ne lisent que les fichiers nouveaux ou modifiés : la ligne *Durée* du résumé
  montre la différence. Une étape qui n'a plus rien à faire est sautée. Quand aucun fichier
  n'est nouveau ni modifié, l'audit le dit, comme ci-dessus.

Un fichier est reconnu à son chemin, sa taille et sa date de modification : changez l'un des
trois et il est relu. Les résultats sont les mêmes, avec ou sans cache.

Même le parcours de vos dossiers raccourcit : un dossier où aucun fichier n'a été ajouté,
supprimé ou renommé depuis le dernier audit est repris du cache, sans regarder chacun de ses
fichiers. L'audit le dit en une ligne : *« 851 dossiers inchangés repris de l'index, 6 relus. »*
Un dossier où des photos ont été ajoutées est relu, mais seules ses nouvelles photos sont
examinées une à une. Une photo modifiée **sur place** par un autre programme (même nom) ne
change pas son dossier : elle est vue au plus tard après `full_check_days` (7 jours) dans
`[scan]`, quand chaque dossier est relu en entier, ou tout de suite avec `audit --full`.

Renommer ou déplacer des dossiers dans l'Explorateur garde ce que le cache sait : un fichier
retrouvé ailleurs avec la même taille, la même date de modification et les mêmes 64 premiers et
derniers Ko est le même fichier. L'audit le dit : *« 1 234 fichiers déplacés ou renommés depuis
le dernier audit : ce que le cache en savait les suit. »* Ses vérifications, ses visages et ce
qu'un modèle local en a dit ne sont pas refaits ; un fichier modifié (nouvelle date) est revérifié.
De même pour les fichiers qu'`undo` ramène de la quarantaine ; `purge` oublie ce que le cache
savait des fichiers qu'il efface.

Le cache garde aussi ce que chaque fichier dit de lui-même, lu pendant sa vérification : la date
de prise de vue, la position GPS, l'appareil, les étoiles données dans Windows, la durée d'une
vidéo… Rien de plus n'est lu pour cela. `inventory` exporte tout cela vers un classeur Excel,
sans relire vos photos ([le classeur d'inventaire](../reference-inventory.md)).

Pour les photos et vidéos trouvées semblables, il garde aussi à quel point chacune est colorée
(une retouche en noir et blanc n'est pas une copie) et, pour les vidéos réencodées, une empreinte
de leur image et de leur son : les audits suivants, `review --near` et `clean` ne mesurent que ce
qui est nouveau ou modifié.

Il garde aussi les aperçus de vos photos, un par taille : les petits des rapports HTML, les
grands des pages de revue, la grille de `search`. Une photo est décodée une fois ; les rapports
et pages suivants relisent son aperçu. Les aperçus prennent au plus 2 Go : au-delà, ceux qui
n'ont plus été affichés depuis le plus longtemps sont supprimés, et refaits s'il le faut. Pour
changer cette limite, réglez `previews_max_gb` dans la table `[cache]` de `config.toml`
(`config --upgrade` l'ajoute à un fichier plus ancien).

## Bon à savoir

- **Un audit arrêté en cours de route** (Ctrl+C, `docker stop`, le PC éteint) garde ce qu'il a
  déjà vérifié : le cache enregistre son travail toutes les quelques secondes, et l'audit suivant
  reprend de là.
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


??? note "Sans `mh` : ajouter le cache vous-même"

    Ajoutez un `-v` au `docker run` de l'étape 1 :

    ```powershell
    docker run --rm -it `
      -v "C:\Photos:/data/c/Photos:ro" `
      -v media-hygiene-cache:/cache `
      cavo789/media-hygiene --locale fr audit
    ```

    Dans PowerShell, la backtick `` ` `` en fin de ligne continue la commande sur la ligne
    suivante (rien ne doit la suivre, pas même un espace). `media-hygiene-cache` n'est pas un de
    vos dossiers : c'est un *volume*, un espace de stockage que Docker gère lui-même, créé la
    première fois et gardé d'un lancement à l'autre. **Gardez ce `-v` dans chaque commande** dès
    lors : `audit`, puis plus tard `clean`, `review`… utilisent tous le même cache. Tant qu'il
    n'y est pas, la ligne ⚙️ *À régler une fois* de chaque audit le propose.

---

← [1. Votre premier audit](01-first-audit.md) · [Documentation](../README.md) · Suivant : **[3. Plusieurs dossiers et disques](03-several-folders.md)** →
