# 9. Annuler, historique, purge

[Documentation](README.md) › Étape 9 sur 13 · 🇬🇧 [English](../en/09-undo-history-purge.md)

Un nettoyage n'est pas définitif. Le journal retient chaque action : vous pouvez tout remettre en
place, voir ce que chaque nettoyage a fait et, une fois sûr·e, vider la quarantaine pour de bon.

Pour les trois commandes ci-dessous, gardez les mêmes options `-v` que votre `clean` (étape 8) ;
seul le dernier mot change.

## Annuler un nettoyage : `undo`

Vous changez d'avis ? Lancez la même commande avec `undo` au lieu de `clean` :

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v "D:\Ancien disque:/data/d/Ancien disque" `
  -v media-dedup-cache:/cache `
  -v "$HOME\media-dedup\reports:/reports" `
  -v "$HOME\media-dedup\config:/config" `
  -v "$HOME\media-dedup\journal:/journal" `
  -v "$HOME\media-dedup\quarantine:/quarantine" `
  cavo789/media-dedup --locale fr undo
```

<!-- capture: undo.txt -->
```text
────────────────────────── Annulation 20260927-064355 ──────────────────────────
Annulation 20260927-064355
┌───────────────────────────┬─────────┐
│ Fichiers traités          │      36 │
│ Taille                    │ 15,5 Mo │
│ Ignorés (laissés intacts) │       0 │
│ En échec                  │       0 │
│ Durée                     │     0 s │
└───────────────────────────┴─────────┘
```

- Chaque copie supprimée est **reconstruite à partir de la copie gardée**, date comprise, même
  d'un disque à l'autre : c'est pour cela qu'un nettoyage peut vraiment supprimer.
- Chaque fichier mis en quarantaine est remis à sa place.
- Sans nom, `undo` restaure le dernier nettoyage ; `undo <exécution>` restaure celui-là. Les
  noms des exécutions viennent d'`history`, ci-dessous, et des dernières lignes de chaque
  nettoyage.

## Voir ce qui a été fait : `history`

```powershell
cavo789/media-dedup --locale fr history
```

<!-- capture: history.txt -->
```text
Nettoyages (du plus récent au plus ancien)
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Exécution       ┃ Supprimés ┃  Libéré ┃ En quarantaine ┃ Restaurés ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ 20260927-064358 │        33 │ 16,2 Mo │              7 │         0 │
│ 20260927-064355 │        33 │ 15,5 Mo │              3 │        36 │
└─────────────────┴───────────┴─────────┴────────────────┴───────────┘
💡 'media-dedup undo <run>' restaure les fichiers d'une exécution.
```

Une ligne par nettoyage, le plus récent d'abord : combien de fichiers il a supprimés, l'espace
libéré, combien de fichiers il a mis en quarantaine, et combien ont été restaurés depuis. Ici le
premier nettoyage a été entièrement annulé (36 fichiers restaurés), puis refait.

## Vider la quarantaine : `purge`

La quarantaine garde ce que `clean` a déplacé : fichiers illisibles, fichiers compagnons
orphelins et, si vous l'avez demandé, quasi-doublons et photos de rafale. Une fois que vous les
avez vérifiés (ouvrez le dossier de quarantaine dans l'Explorateur), `purge` les supprime **pour
de bon** :

```powershell
cavo789/media-dedup --locale fr purge
```

<!-- capture: purge.txt -->
```text
❓ Supprimer définitivement la quarantaine de 20260927-064358, 20260927-064355
(2,2 Mo) ? [o/N] o
✅ Quarantaine vidée : 2,2 Mo libérés.
💡 'undo' ne pourra plus restaurer ces fichiers cassés.
```

- Sans nom, `purge` vide la quarantaine de tous les nettoyages ; `purge <exécution>` seulement
  celle-là.
- Il demande d'abord, comme `clean` ; `--yes` saute la question.
- Après une purge, `undo` ne peut plus ramener ces fichiers.

## Gardez le dossier du journal

Le journal est léger, et c'est lui qui rend `undo` possible. Ne le supprimez jamais tant que vous
pourriez encore vouloir restaurer un nettoyage.

---

← [8. Nettoyer](08-clean.md) · [Documentation](README.md) · Suivant : **[10. Trier les rafales dans le navigateur](10-review-bursts.md)** →
