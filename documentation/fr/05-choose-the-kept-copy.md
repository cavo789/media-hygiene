# 5. Choisir la copie gardée

[Documentation](README.md) › Étape 5 sur 13 · 🇬🇧 [English](../en/05-choose-the-kept-copy.md)

Entre des copies identiques, l'outil en garde une et marque les autres comme en trop. Son choix
est sensé, mais vous connaissez mieux vos dossiers. Trois options permettent de l'orienter, une à
la fois.

## Comment l'outil choisit

Pour chaque groupe de fichiers identiques, la première règle qui fait une différence décide :

1. un dossier **protégé** (voir plus bas) ;
2. un dossier **préféré**, dans l'ordre où vous les avez donnés ;
3. la copie qui a un [fichier compagnon](reference-sidecars.md) (`.xmp`, `.aae`, `.thm`) : elle garde ses retouches ;
4. un nom qui ne ressemble pas à une copie : `IMG_0101.jpg` plutôt que `IMG_0101 (1).jpg` ou `IMG_0101 - Copie.jpg` ;
5. un nom choisi par quelqu'un plutôt que généré par un appareil ou une application : `Marie et Paul.jpg` plutôt que `IMG_1234.jpg` ;
6. un dossier nommé par quelqu'un plutôt qu'un dossier générique : `Vacances 2019` plutôt que `DCIM\100CANON` ;
7. la date la plus ancienne, puis le chemin le plus court, puis l'ordre alphabétique.

Les mêmes dossiers donnent toujours le même choix. Le rapport indique, pour chaque paire et
chaque groupe, la règle qui a décidé (*pourquoi : la date la plus ancienne*).

Le fichier gardé conserve son nom et son dossier ; le nom d'une copie supprimée est perdu.
Regardez donc les paires de dossiers de l'audit : le dossier gardé est-il celui que vous voulez ?

## Préférer un dossier

Dans la bibliothèque de démonstration, `C:\Photos\2019\Vacances à la mer` est gardé plutôt que
`C:\Photos\Ancien téléphone` (ses dates sont plus anciennes). Pour garder plutôt les copies de
`Ancien téléphone`, nommez-le avec `--prefer`, après `audit` :

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v "D:\Ancien disque:/data/d/Ancien disque:ro" `
  -v media-dedup-cache:/cache `
  cavo789/media-dedup --locale fr audit --prefer "C:\Photos\Ancien téléphone"
```

Écrivez le dossier comme Windows l'affiche. Les paires s'inversent :

<!-- capture: audit-prefer.txt|Dossiers partageant|<blank> -->
```text
Dossiers partageant des fichiers identiques
• 3 fichiers sont à la fois dans C:\Photos\Téléphone (gardés) et dans D:\Ancien
  disque\Téléphone (supprimés), gain de 3,0 Mo. D:\Ancien disque\Téléphone ne
  contient rien d'autre : c'est entièrement une copie de C:\Photos\Téléphone.
• 1 fichier est à la fois dans C:\Photos\Vidéos (gardé) et dans D:\Ancien
  disque\Vidéos (supprimé), gain de 2,9 Mo.
• 9 fichiers sont à la fois dans C:\Photos\Ancien téléphone (gardés) et dans
  C:\Photos\2019\Vacances à la mer (supprimés), gain de 2,5 Mo.
• 8 fichiers sont à la fois dans C:\Photos\Ancien téléphone (gardés) et dans
  D:\Ancien disque\Photos 2019 (supprimés), gain de 2,2 Mo.
• 4 fichiers sont à la fois dans C:\Photos\2019\Vacances à la mer (gardés) et
  dans D:\Ancien disque\Photos 2019 (supprimés), gain de 1,3 Mo.
• 4 fichiers sont à la fois dans C:\Photos\2020\Noël (gardés) et dans D:\Ancien
  disque\Noël 2020 (supprimés), gain de 1,2 Mo. D:\Ancien disque\Noël 2020 ne
  contient rien d'autre : c'est entièrement une copie de C:\Photos\2020\Noël.
• 3 fichiers sont à la fois dans C:\Photos\Ancien téléphone (gardés) et dans
  C:\Photos\2019\Nouveau dossier (supprimés), gain de 864,7 Ko.
  C:\Photos\2019\Nouveau dossier ne contient rien d'autre : c'est entièrement
  une copie de C:\Photos\Ancien téléphone.
```

`--prefer` peut être répété : `--prefer "C:\Photos\Famille" --prefer "C:\Photos\Ancien téléphone"`.
Le premier l'emporte quand un fichier est dans les deux.

## Protéger un dossier

`--protect` va plus loin : le dossier n'est **jamais modifié**, et ses fichiers sont toujours les
copies gardées. Pensez à une bibliothèque de référence :

```powershell
cavo789/media-dedup --locale fr audit --protect "C:\Photos\Famille"
```

(la partie `docker run … -v …` ne change pas ; seule la fin de la commande change)

Mesurez bien ce que cela veut dire : les fichiers identiques *ailleurs* sont supprimés, puisque
la copie protégée est celle qui est gardée. Les fichiers cassés et les fichiers compagnons
orphelins d'un dossier protégé restent aussi en place.

## Exclure un dossier

`--exclude` retire un dossier de l'analyse : ses fichiers ne sont ni lus ni comparés. Utilisez-le
pour une vraie sauvegarde qui doit rester une seconde copie :

```powershell
cavo789/media-dedup --locale fr audit --exclude "D:\Ancien disque"
```

Il ne reste que les doublons de `C:\Photos` :

<!-- capture: audit-exclude.txt|Dossiers partageant|<blank> -->
```text
Dossiers partageant des fichiers identiques
• 8 fichiers sont à la fois dans C:\Photos\2019\Vacances à la mer (gardés) et
  dans C:\Photos\Ancien téléphone (supprimés), gain de 2,2 Mo. C:\Photos\Ancien
  téléphone ne contient rien d'autre : c'est entièrement une copie de
  C:\Photos\2019\Vacances à la mer.
• 3 fichiers sont à la fois dans C:\Photos\2019\Vacances à la mer (gardés) et
  dans C:\Photos\2019\Nouveau dossier (supprimés), gain de 864,7 Ko.
  C:\Photos\2019\Nouveau dossier ne contient rien d'autre : c'est entièrement
  une copie de C:\Photos\2019\Vacances à la mer.
• 1 fichier est présent plusieurs fois dans C:\Photos\2019\Vacances à la mer :
  un exemplaire est gardé (gain de 287,5 Ko).
```

## Les options viennent après la commande

`--prefer`, `--protect` et `--exclude` se placent **après** `audit` (et plus tard après `clean`
ou `review`). `--locale` est différent : il concerne tout l'outil, il se place donc **avant** la
commande : `cavo789/media-dedup --locale fr audit --prefer "C:\Photos\Ancien téléphone"`.

Vous tapez les mêmes options à chaque fois ? L'[étape 7](07-configuration-file.md) les écrit une
fois pour toutes dans un fichier.

---

← [4. Le rapport HTML](04-html-report.md) · [Documentation](README.md) · Suivant : **[6. Seulement certains types de fichiers](06-file-types.md)** →
