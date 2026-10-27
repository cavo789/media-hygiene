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
protégés et de sauvegarde sont laissés de côté : ils ne sont jamais modifiés.

## Étape 1 : les cocher

```powershell
mh review --intruders
```

La page liste les fichiers intrus deux fois, **par extension** et **par dossier**, avec le
nombre de fichiers et la place de chacun. Cochez des extensions, des dossiers, ou les deux, puis
**Mettre de côté les fichiers cochés** :

- une extension seule : tous les fichiers de ce type, où qu'ils soient ;
- un dossier seul : tous les fichiers intrus de ce dossier et de ses sous-dossiers ;
- les deux : les fichiers d'une extension cochée rangés dans un dossier coché.

**Rien ne bouge ici.** Un docx peut compter : rien n'est mis de côté sans vous. Chaque choix est
enregistré aussitôt dans `decisions.json` du dossier des rapports ; la liste sous les tableaux
est ce fichier, relu sur le disque. **Remettre tous les fichiers intrus** le vide à nouveau.

## Étape 2 : appliquer

Arrêtez la page avec Ctrl+C, puis lancez `clean` avec le fichier de décisions :

```powershell
mh clean --decisions decisions.json
```

Les fichiers mis de côté vont dans la quarantaine de leur disque, journalisés : `undo` les
ramène. Un fichier modifié ou déplacé depuis que vous l'avez coché reste où il est.

---

← [14. Les photos indésirables](14-unwanted-photos.md) · [Documentation](../README.md)
