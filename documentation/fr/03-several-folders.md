# 3. Plusieurs dossiers et disques

[Documentation](README.md) › Étape 3 sur 13 · 🇬🇧 [English](../en/03-several-folders.md)

Les doublons restent rarement dans un seul dossier : un ancien disque, la sauvegarde d'un
téléphone, une copie sur `D:`. Donnez à l'outil tous les dossiers à comparer, et il trouve les
copies entre eux en une seule fois.

## Un `-v` par dossier

Chaque dossier a son propre `-v`. La règle : **`X:\chemin` devient `/data/x/chemin`**, la lettre
du lecteur en minuscule.

| Sur votre ordinateur | Dans la commande |
|---|---|
| `C:\Photos` | `-v "C:\Photos:/data/c/Photos:ro"` |
| `D:\Ancien disque` | `-v "D:\Ancien disque:/data/d/Ancien disque:ro"` |

Grâce aux guillemets, les chemins avec des espaces fonctionnent. Voici les deux dossiers, avec le
cache de l'étape 2 :

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v "D:\Ancien disque:/data/d/Ancien disque:ro" `
  -v media-dedup-cache:/cache `
  cavo789/media-dedup --locale fr audit
```

Le résultat compare maintenant les deux disques :

<!-- capture: audit.txt|Résumé de l'audit|└ -->
```text
Résumé de l'audit
┌─────────────────────────────────────────────────────────────┬─────────┐
│ Fichiers média analysés                                     │      83 │
│ Groupes de fichiers identiques                              │      20 │
│ Copies en trop, supprimables                                │      32 │
│ Espace libérable                                            │ 13,9 Mo │
│ Fichiers cassés (vides ou illisibles)                       │       3 │
│ Fichiers compagnons orphelins (.xmp, .aae, .thm) à déplacer │       1 │
│ Quasi-doublons (déplacés seulement avec --tier near)        │       2 │
│ Rafales (déplacées seulement si écartées avec 'review')     │       3 │
│ Durée                                                       │     1 s │
└─────────────────────────────────────────────────────────────┴─────────┘
```

<!-- capture: audit.txt|Dossiers partageant|<blank> -->
```text
Dossiers partageant des fichiers identiques
• 12 fichiers sont à la fois dans C:\Photos\2019\Vacances à la mer (gardés) et
  dans D:\Ancien disque\Photos 2019 (supprimés), gain de 3,5 Mo. D:\Ancien
  disque\Photos 2019 ne contient rien d'autre : c'est entièrement une copie de
  C:\Photos\2019\Vacances à la mer.
• 3 fichiers sont à la fois dans C:\Photos\Téléphone (gardés) et dans D:\Ancien
  disque\Téléphone (supprimés), gain de 3,0 Mo. D:\Ancien disque\Téléphone ne
  contient rien d'autre : c'est entièrement une copie de C:\Photos\Téléphone.
• 1 fichier est à la fois dans C:\Photos\Vidéos (gardé) et dans D:\Ancien
  disque\Vidéos (supprimé), gain de 2,9 Mo.
• 8 fichiers sont à la fois dans C:\Photos\2019\Vacances à la mer (gardés) et
  dans C:\Photos\Ancien téléphone (supprimés), gain de 2,2 Mo. C:\Photos\Ancien
  téléphone ne contient rien d'autre : c'est entièrement une copie de
  C:\Photos\2019\Vacances à la mer.
• 4 fichiers sont à la fois dans C:\Photos\2020\Noël (gardés) et dans D:\Ancien
  disque\Noël 2020 (supprimés), gain de 1,2 Mo. D:\Ancien disque\Noël 2020 ne
  contient rien d'autre : c'est entièrement une copie de C:\Photos\2020\Noël.
• 3 fichiers sont à la fois dans C:\Photos\2019\Vacances à la mer (gardés) et
  dans C:\Photos\2019\Nouveau dossier (supprimés), gain de 864,7 Ko.
  C:\Photos\2019\Nouveau dossier ne contient rien d'autre : c'est entièrement
  une copie de C:\Photos\2019\Vacances à la mer.
• 1 fichier est présent plusieurs fois dans C:\Photos\2019\Vacances à la mer :
  un exemplaire est gardé (gain de 287,5 Ko).
```

Chaque chemin est affiché comme Windows l'écrit : `/data/d/Ancien disque` s'affiche
`D:\Ancien disque`.

## Montez chaque dossier une seule fois

Un dossier inclut déjà ses sous-dossiers : `C:\Photos` suffit pour `C:\Photos\2019`. Monter les
deux montrerait chaque photo deux fois, et l'outil le **refuse** plutôt que de prendre une photo
pour un doublon d'elle-même. Attention à la casse : Windows voit `C:\Photos` et `C:\photos\2019`
comme le même dossier, Docker non.

## Une vraie sauvegarde ? Laissez-la de côté

Si `D:\sauvegarde` doit rester une seconde copie de vos photos, ne la montez pas, ou
[excluez-la](05-choose-the-kept-copy.md#exclure-un-dossier). Sinon l'outil voit ses fichiers comme
des doublons, ce qui est exact.

## Le dossier courant

Dans PowerShell, placez-vous dans un dossier avec `cd`, puis utilisez `${PWD}` (le dossier
courant) comme source :

```powershell
docker run --rm -it -v "${PWD}:/data/current:ro" cavo789/media-dedup --locale fr audit
```

L'outil affiche quand même le vrai chemin Windows. Dans l'ancienne console `cmd.exe`, écrivez
`%cd%` au lieu de `${PWD}`.

## Depuis WSL

Dans un terminal WSL (ou Linux), écrivez les chemins Linux, `\` continue une ligne, et ajoutez
`--user "$(id -u):$(id -g)"` pour que les fichiers que l'outil créera ensuite vous appartiennent :

```bash
docker run --rm -it --user "$(id -u):$(id -g)" \
  -v "/mnt/c/Photos:/data/c/Photos:ro" \
  -v "/mnt/d/Ancien disque:/data/d/Ancien disque:ro" \
  -v media-dedup-cache:/cache \
  cavo789/media-dedup --locale fr audit
```

La suite de ce guide montre les commandes PowerShell ; la version WSL suit le même modèle.

---

← [2. Garder le cache](02-keep-the-cache.md) · [Documentation](README.md) · Suivant : **[4. Le rapport HTML](04-html-report.md)** →
