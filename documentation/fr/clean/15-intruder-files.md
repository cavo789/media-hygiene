# 15. Les fichiers intrus

[Documentation](../README.md) › Nettoyer, étape 15 sur 15 · 🇬🇧 [English](../../en/clean/15-intruder-files.md)

Un zip, un document Word ou un PDF copié parmi les photos de famille prend de la place et n'est
jamais comparé. L'audit les compte et le dit à la fin :

```text
🧹 3 fichiers qui ne sont ni des photos ni des vidéos (zip, pdf) occupent 12 Mo dans vos
dossiers photos : voir « Fichiers intrus » dans le rapport ; 'review --intruders' choisit ceux à
mettre de côté.
```

Les compagnons ne sont jamais des intrus : fichiers annexes (`.xmp`, `.aae`), `.json` de
Takeout, `Thumbs.db`, `desktop.ini`… (`[scan] companions` dans `config.toml`). Les dossiers
protégés et de sauvegarde sont laissés de côté : ils ne sont jamais modifiés. Un `.mpo` (le JPEG
3D ou multi-images de certains appareils) est une photo, pas un intrus.

Trois chemins mènent à la page : la commande ci-dessous, la section *Fichiers intrus* du rapport
(sa commande à copier, ou son bouton quand la page d'accueil sert le rapport), et la tuile
**Fichiers intrus** de *Où vous en êtes* sur la page d'accueil, qui montre leur poids au dernier
audit : un clic ouvre la page (sans intrus, il ouvre l'espace Nettoyer).

Depuis la page d'accueil, la page a *Retour à l'accueil* et sa barre latérale. Tapée dans la
console, aucune page d'accueil n'attend derrière : sa barre du haut le dit (`Ctrl+C` dans la console
ferme la page, puis `mh` ouvre la page d'accueil) et aucune entrée de barre latérale n'est dessinée.

## Étape 1 : les cocher

```powershell
mh review --intruders
```

La page liste les fichiers intrus deux fois, **par extension** et **par dossier**, avec le
nombre de fichiers et la place de chacun. Cochez des extensions, des dossiers, ou les deux. La
barre en haut de la page, toujours visible, dit en une phrase quels fichiers vos coches prennent,
avec leur nombre et leur taille, et son bouton rouge porte ce nombre (**Mettre ces 12 fichiers de
côté**) :

- une extension seule : tous les fichiers de ce type, où qu'ils soient ;
- un dossier seul : tous les fichiers intrus de ce dossier et de ses sous-dossiers ;
- les deux : les fichiers d'une extension cochée rangés dans un dossier coché.

Tant qu'une extension est cochée, le tableau des dossiers ne liste que ceux qui en contiennent,
chacun avec le nombre et la taille de cette extension : vous voyez où ils sont. Un dossier coché
fait de même sur le tableau des extensions. Décochez tout pour revoir toutes les lignes.

À côté de certaines extensions, un indice discret : *un cache, recréé par l'appareil ou
l'application* (`.ithmb`, les miniatures qu'écrit la synchronisation d'un iPod ou d'un iPhone :
iTunes les réécrit à la synchronisation suivante), ou *à garder, sauf si vous l'avez ailleurs*
(archives comme `.zip` ou `.7z`, documents, audio, projets de logiciels d'image). Toute autre
extension n'en a pas. C'est un indice, jamais un verdict, et jamais « supprimer » : vous seul
savez si un zip a été extrait ou si un document est le seul exemplaire, et ce que vous
choisissez va en quarantaine, où `undo` le retrouve.

**Rien ne bouge ici.** Un docx peut compter : rien n'est mis de côté sans vous. Chaque choix est
enregistré aussitôt dans `decisions.json` du dossier des rapports ; la liste sous les tableaux
est ce fichier, relu sur le disque. **Remettre tous les fichiers intrus** le vide à nouveau.

## Étape 2 : appliquer

Ouverte depuis la page d'accueil, la barre montre **Appliquer maintenant** dès qu'un fichier est
mis de côté : `mh` lance l'étape qui les déplace, avec sa question habituelle. Ouverte par sa
commande, arrêtez la page avec Ctrl+C, puis lancez `clean` avec le fichier de décisions :

```powershell
mh clean --decisions decisions.json
```

Les fichiers mis de côté vont dans la quarantaine de leur disque, journalisés : `undo` les
ramène. Un fichier modifié ou déplacé depuis que vous l'avez coché reste où il est.

---

← [14. Les photos indésirables](14-unwanted-photos.md) · [Documentation](../README.md)
