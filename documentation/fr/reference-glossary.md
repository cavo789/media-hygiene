# Les mots de ce guide

[Documentation](README.md) › Référence · 🇬🇧 [English](../en/reference-glossary.md)

Les mots que vous rencontrez dans les guides et à l'écran, en langage courant, de A à Z. Chacun
renvoie à la page qui le montre à l'œuvre.

### Audit

L'outil lit vos dossiers et liste ce qu'il trouve : doublons, fichiers cassés, photos prises en
rafale. Il ne change rien : comme un bilan chez le médecin avant tout traitement.
[Premier audit](start/01-first-audit.md)

### Cache

Un petit fichier où l'outil note ce qu'il a déjà lu de chaque photo, pour que l'audit suivant
prenne quelques secondes au lieu de quelques heures, comme un marque-page.
[Garder le cache](start/02-keep-the-cache.md)

### Classeur

`classify.xlsx` : le fichier Excel (ou LibreOffice) où vous corrigez la proposition de `classify`
avant que `sort` ne déplace quoi que ce soit.
[Étape 5 du tri](sort/05-review-the-proposal.md#le-classeur--modifier-les-cellules-jaunes)

### Conteneur

L'outil qui tourne le temps d'une commande, dans Docker, puis disparaît. Ce qu'il écrit en dehors
des dossiers que vous montez disparaît avec lui.
[Installer Docker](start/00-install-docker.md)

### Copie gardée

De plusieurs fichiers identiques, celui qui reste en place. Les autres sont les copies en trop,
mises de côté par `clean`.
[Étape 5 du nettoyage](clean/05-choose-the-kept-copy.md)

### Dossier de sauvegarde

Une sauvegarde ou un ancien disque que l'outil lit et compare, sans jamais le modifier
(`--backup`). L'audit dit lesquelles de vos photos lui manquent, et lesquels de ses fichiers ne
sont nulle part ailleurs : ceux à copier avant d'effacer ce disque. Ses copies ne sont jamais la
raison du départ d'un fichier de vos photos.
[Étape 5 du nettoyage](clean/05-choose-the-kept-copy.md#comparer-une-sauvegarde-ou-un-ancien-disque)

### Dossier exclu

Un dossier que l'outil ne lit jamais (`--exclude`). Une sauvegarde à vérifier est plutôt un
[dossier de sauvegarde](#dossier-de-sauvegarde).
[Étape 5 du nettoyage](clean/05-choose-the-kept-copy.md#exclure-un-dossier)

### Dossier protégé

Un dossier jamais modifié, dont les fichiers sont toujours les copies gardées, par exemple votre
photothèque de référence (`--protect`).
[Étape 5 du nettoyage](clean/05-choose-the-kept-copy.md#protéger-un-dossier)

### Empreinte (SHA-256)

Un long code calculé à partir de chaque octet d'un fichier. Deux fichiers à la même empreinte
sont identiques, octet par octet : c'est ainsi que l'outil prouve qu'une copie est une copie.
[Qu'est-ce qu'un doublon ?](reference-safety.md#quest-ce-quun-doublon-)

### Événement

Un moment de votre vie vu par vos photos (une kermesse, un week-end à la mer, un Noël) :
`classify` réunit les photos et vidéos prises sans pause de plus de 6 heures, d'un dossier ou d'un
téléphone à l'autre. Le nom que vous lui donnez devient son dossier quand `sort` range la
collection.
[`review-sort` : à quoi ça sert](commands/review-sort.md#à-quoi-ça-sert)

### Exécution

Un lancement d'une commande, nommé par sa date et son heure (`20261011-204239`). `history` les
liste ; `undo` en annule une.
[Étape 9 du nettoyage](clean/09-undo-history-purge.md#voir-ce-qui-a-été-fait--history)

### Fichier compagnon

Un petit fichier à côté d'une photo, qui garde ses retouches ou ses métadonnées : `.xmp`
(Lightroom), `.aae` (iPhone), `.thm`. Il suit sa photo.
[Fichiers compagnons](reference-sidecars.md)

### Fichier compagnon orphelin

Un [fichier compagnon](#fichier-compagnon) dont la photo a disparu : un `IMG_1.xmp` sans
`IMG_1.jpg` à côté. `clean` le déplace en quarantaine.
[Fichiers compagnons](reference-sidecars.md)

### Fichier des décisions

`decisions.json` : les choix que vous faites dans le navigateur (quelles photos de rafale mettre
de côté, que faire des quasi-doublons), enregistrés au fur et à mesure. `clean --decisions` les
applique.
[Étape 10 du nettoyage](clean/10-review-bursts.md#étape-7--appliquer-vos-choix)

### Groupe GPS

Des photos prises à environ 200 mètres les unes des autres, montrées en un seul cercle sur la
carte de `places`, pour nommer le lieu une fois : « Chez mamie ».
[Étape 9 du tri](sort/09-places-from-gps.md#nommer-vos-lieux-sur-une-carte)

### Image Docker

L'outil emballé avec tout ce dont il a besoin, téléchargé une fois (`cavo789/media-hygiene`).
Chaque `docker run` en démarre un [conteneur](#conteneur).
[Installer Docker](start/00-install-docker.md)

### Journal

La trace écrite de chaque fichier qu'un `clean` ou un `sort` a déplacé, ligne par ligne. C'est
lui qui rend `undo` possible : ces commandes refusent donc de tourner sans lui.
[Étape 8 du nettoyage](clean/08-clean.md#deux-dossiers-de-plus--le-journal-et-la-quarantaine)

### Lecture seule (`:ro`)

Ajouté à la fin d'un `-v`, il demande au système lui-même d'interdire toute modification de ce
dossier : la garantie la plus forte pour les commandes qui ne font que lire.
[Comment vos photos restent en sécurité](reference-safety.md#notre-promesse--ces-commandes-ne-modifient-jamais-vos-photos)

### Lien physique

Un second nom pour le même fichier, dans un autre dossier, sans place en plus. Les albums sont
faits de liens physiques : la photo est dans « Noël » et dans le dossier de son année, stockée une
seule fois.
[Étape 12 du tri](sort/12-albums.md#ce-quest-un-lien-physique-dans-windows)

### Modèle de vision

Un programme qui regarde une photo et la décrit (« une plage, deux enfants »), sur votre propre
ordinateur avec Ollama : rien n'est envoyé en ligne.
[Étape 8 du tri](sort/08-subjects-from-a-local-model.md)

### Montage, point de montage

Prêter un dossier de votre ordinateur à l'outil : `-v "C:\Photos:/data/c/Photos"`. À gauche
votre dossier, à droite (le point de montage) l'endroit où l'outil le voit. L'outil ne voit rien
d'autre.
[Points de montage](reference-mount-points.md)

### Niveau (`--tier`)

Jusqu'où va `clean` : `exact` (les copies octet par octet, par défaut), `near` (aussi les
quasi-doublons sûrs), `near-all` (tous les quasi-doublons).
[Étape 11 du nettoyage](clean/11-near-duplicates.md#les-déplacer--clean---tier-near-ou---tier-near-all)

### Plan

Ce que l'outil propose avant d'agir : quelle copie reste, lesquelles partent (le `plan.csv` d'un
rapport), ou où chaque photo serait rangée (le `plan.json` de `classify`).
[Étape 4 du nettoyage](clean/04-html-report.md)

### Port

Un numéro de porte qu'utilisent les pages du navigateur, `8088` : `http://127.0.0.1:8088/` ouvre
la page de `review`, `places` ou `people` sur votre ordinateur seulement.
[Étape 10 du nettoyage](clean/10-review-bursts.md#étape-2--ouvrir-la-page)

### Quarantaine

Un dossier où `clean` *déplace* les copies en trop au lieu de les supprimer, comme une corbeille
que vous contrôlez. `undo` les remet en place ; `purge` la vide pour de bon.
[Étape 8 du nettoyage](clean/08-clean.md#deux-dossiers-de-plus--le-journal-et-la-quarantaine)

### Quasi-doublon

La même photo enregistrée à nouveau, mais pas octet par octet : réduite pour WhatsApp,
recompressée pour un e-mail. Laissée en place sauf si vous le demandez (`--tier near`).
[Étape 11 du nettoyage](clean/11-near-duplicates.md)

### Rafale

Des photos prises à une seconde d'intervalle, par exemple dix photos du même saut. Ce ne sont pas
des doublons : l'outil les liste et ne met de côté que les photos que **vous** choisissez.
[Étape 10 du nettoyage](clean/10-review-bursts.md#quest-ce-quune-rafale-)

### Vidéo réencodée

La même vidéo enregistrée à nouveau par un téléphone ou une application : même durée, mêmes
images, un autre fichier. Une sorte de [quasi-doublon](#quasi-doublon).
[Étape 11 du nettoyage](clean/11-near-duplicates.md#les-vidéos-aussi--les-copies-réencodées)

### Volume

Un espace de stockage que Docker garde pour vous, par un nom plutôt que par un dossier : le
cache vit dans le volume `media-hygiene-cache`.
[Garder le cache](start/02-keep-the-cache.md)

---

← [Documentation](README.md)
