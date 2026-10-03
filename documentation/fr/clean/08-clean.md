# 8. Nettoyer

[Documentation](../README.md) › Nettoyer, étape 8 sur 13 · 🇬🇧 [English](../../en/clean/08-clean.md)

Vous avez fait l'audit, lu les paires de dossiers, peut-être choisi quels dossiers restent. Place
au ménage. `clean` déplace les copies en trop en quarantaine — rien n'est effacé — et garde une
trace écrite de tout, pour que vous puissiez changer d'avis. Une fois que vous avez vérifié,
`purge` libère la place ([étape 9](09-undo-history-purge.md)).

## Avant le premier nettoyage

- **Commencez petit** : nettoyez d'abord un sous-dossier, vérifiez le résultat, puis élargissez.
- **Mettez en pause la synchronisation cloud** (OneDrive, Google Drive, Dropbox, iCloud) pendant
  le nettoyage. Sinon, chaque changement est recopié dans le cloud et sur vos autres appareils.
- **Refaites un audit juste avant**, avec les mêmes options, et lisez les paires de dossiers.
- Si vous le pouvez, une sauvegarde sur un disque externe est le filet de plus contre ce
  qu'aucun logiciel ne peut empêcher (un disque qui lâche, une erreur en dehors de l'outil).
  Bienvenue, pas obligatoire : [comment vos photos restent en sécurité](../reference-safety.md).

## Deux dossiers de plus : le journal et la quarantaine

`clean` a besoin de deux de vos dossiers :

- **le journal** (`/journal`) : un fichier par nettoyage, qui liste chaque action. Sans lui, pas
  d'`undo` : `clean` refuse donc de s'exécuter.
- **la quarantaine** (`/quarantine`) : là où les fichiers sont *déplacés* au lieu d'être
  supprimés : les copies en trop, les fichiers illisibles, les fichiers compagnons orphelins, et
  plus tard quasi-doublons et photos de rafale. Sans elle, `clean` refuse de s'exécuter (sauf
  avec `--delete`, plus bas).

```powershell
mkdir "$HOME\media-hygiene\journal", "$HOME\media-hygiene\quarantine"
```

## Lancer le nettoyage

La même commande que votre audit, avec trois changements : **pas de `:ro`** sur vos dossiers
(l'outil doit avoir le droit de déplacer des fichiers), le journal et la quarantaine, et `clean` au lieu
d'`audit` :

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v "D:\Ancien disque:/data/d/Ancien disque" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene --locale fr clean
```

`clean` refait l'audit (rapidement, grâce au cache), affiche le même résumé et les mêmes paires
de dossiers, puis **demande avant de faire quoi que ce soit** :

<!-- capture: clean.txt|re:^🛟|❓ -->
```text
🛟 Rien n'est effacé : chaque copie est comparée octet par octet avec celle gardée, puis
déplacée en quarantaine. 'purge' l'efface une fois que vous avez vérifié.
1 fichier compagnon orphelin (.xmp, .aae, .thm) sera déplacé en quarantaine.
❓ Déplacer 32 copies en double (13,9 Mo) en quarantaine et traiter 3 fichiers cassés ? [o/N] o
```

Toute autre réponse que `o` arrête tout ici, et rien ne change. Avec `o` :

<!-- capture: clean.txt|re:^─+ Nettoyage| -->
```text
────────────────────────────────── Nettoyage ───────────────────────────────────
Nettoyage 20261002-152727
┌───────────────────────────┬─────────┐
│ Fichiers traités          │      36 │
│ Taille                    │ 15,5 Mo │
│ Déplacés en quarantaine   │      35 │
│ Ignorés (laissés intacts) │       0 │
│ En échec                  │       0 │
│ Durée                     │     0 s │
└───────────────────────────┴─────────┘
✅ Rapport HTML : /reports/20261002-152727-clean/report.html
💡 Ouvrez index.html dans le dossier monté sur /reports : il liste tous les
rapports.
💡 Vous changez d'avis ? 'media-hygiene undo 20261002-152727' restaure tout.
💡 L'espace est libéré par 'purge', une fois que vous avez vérifié : media-hygiene
purge 20261002-152727
```

| Ligne | Ce qu'elle veut dire |
|---|---|
| Fichiers traités | Chaque fichier sur lequel l'outil a agi : ici 32 copies en trop et 3 autres fichiers déplacés, 1 fichier vide supprimé. |
| Taille | Leur taille totale. |
| Déplacés en quarantaine | Les copies en trop, les fichiers illisibles et les fichiers compagnons orphelins : mis de côté, pas supprimés. |
| Ignorés (laissés intacts) | Fichiers refusés par la dernière vérification (voir ci-dessous). Rien n'est forcé. |
| En échec | Fichiers que le système n'a pas laissé l'outil traiter. Le rapport les liste. |

## Ce qui est arrivé à chaque fichier

| Fichier | Ce que `clean` a fait |
|---|---|
| Copie en trop d'une photo ou d'une vidéo | **Déplacée** en quarantaine, juste après une nouvelle comparaison octet par octet avec la copie gardée. La moindre différence ? Ignorée. |
| Fichier vide (0 octet) | Supprimé : il ne contient rien (`undo` le recrée). |
| Fichier illisible (tronqué, abîmé) | **Déplacé** en quarantaine. |
| [Fichier compagnon](../reference-sidecars.md) orphelin | Déplacé en quarantaine. |
| Quasi-doublons, photos de rafale | **Pas touchés** : seulement si vous le demandez ([étape 10](10-review-bursts.md), [étape 11](11-near-duplicates.md)). |
| Fichiers d'un dossier protégé | Pas touchés, jamais. |

La quarantaine contient un dossier par nettoyage, au nom de l'exécution (sa date et son heure),
et garde en dessous les chemins d'origine :
`quarantine\<exécution>\d\Ancien disque\2020\IMG_1203.jpg`.

## Le rapport de nettoyage

Chaque nettoyage écrit son propre rapport, listé dans `index.html` à côté des audits : ce qui a
été libéré, les paires de dossiers telles qu'elles ont été nettoyées, et les fichiers laissés
intacts, s'il y en a.

![Le haut d'un rapport de nettoyage : 83 fichiers média analysés, 32 copies en double dans 20 groupes, 16,2 Mo retirés de vos dossiers, 3 fichiers cassés, puis les paires de dossiers nettoyées](../images/clean-report.webp)

## Besoin de la place tout de suite ? `--delete`

`clean --delete` supprime pour de bon les copies en trop au lieu de les déplacer, après la même
comparaison octet par octet avec la copie gardée. La copie gardée reste : `undo` reconstruit
chaque copie supprimée à partir d'elle. C'est, avec `purge`, la seule façon dont l'outil supprime
du contenu, et il le dit avant de demander. Les copies d'autres fichiers que des médias (`--ext`)
vont toujours en quarantaine.

## Bon à savoir

- **Sans question** : ajoutez `--yes` (`clean --yes`), ou mettez `confirm = false` dans la section
  `[clean]` de `config.toml`. Sans `-it`, `clean` ne peut pas demander et s'arrête : utilisez
  alors `--yes`.
- **Interrompu ?** Ctrl+C, une coupure de courant : chaque action est écrite dans le journal
  *avant* et *après* avoir eu lieu, `undo` restaure donc ce qui a été fait.
- **Des refus qui vous protègent** : `clean` s'arrête avant l'analyse sans `/journal` ni
  `/quarantine`, avec un dossier en `:ro`, avec un dossier où il ne peut pas écrire, ou avec un
  dossier de l'outil (quarantaine, journal, cache, rapports) placé dans un dossier de photos. Le
  message dit lequel.

---

← [7. Le fichier de configuration](07-configuration-file.md) · [Documentation](../README.md) · Suivant : **[9. Annuler, historique, purge](09-undo-history-purge.md)** →
