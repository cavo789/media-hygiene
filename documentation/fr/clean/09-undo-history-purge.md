# 9. Annuler, historique, purge

[Documentation](../README.md) › Nettoyer, étape 9 sur 13 · 🇬🇧 [English](../../en/clean/09-undo-history-purge.md)

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
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene --locale fr undo
```

<!-- capture: undo.txt -->
```text
─────────────── Annulation de l'exécution clean 20260930-191245 ────────────────
Annulation de l'exécution clean
20260930-191245
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
- Sans nom, `undo` restaure la dernière exécution ; `undo <exécution>` restaure celle-là. Les
  noms des exécutions viennent d'`history`, ci-dessous, et des dernières lignes de chaque
  nettoyage.
- Un fichier déjà revenu, ou dont la copie a disparu, est laissé tel quel et listé avec la
  raison : `undo` n'écrase jamais rien et ne devine rien.
- Un [tri](../sort/07-sort.md) s'annule de la même façon : les fichiers reviennent, les dossiers
  qu'il a supprimés reviennent, ceux qu'il a créés s'en vont. Un tri arrêté puis relancé avec le
  même classeur s'annule en entier : tous ses passages, le plus récent d'abord, après une seule
  question (`--yes` la saute).

## Voir ce qui a été fait : `history`

```powershell
cavo789/media-hygiene --locale fr history
```

<!-- capture: history.txt -->
```text
Exécutions (les plus récentes d'abord)
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃                 ┃          ┃           ┃         ┃            En ┃           ┃
┃ Exécution       ┃ Commande ┃ Supprimés ┃  Libéré ┃   quarantaine ┃ Restaurés ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ 20260930-191249 │ clean    │        33 │ 16,2 Mo │             7 │         0 │
│ 20260930-191245 │ clean    │        33 │ 15,5 Mo │             3 │        36 │
└─────────────────┴──────────┴───────────┴─────────┴───────────────┴───────────┘
💡 'media-hygiene undo <run>' restaure les fichiers d'une exécution.
```

Une ligne par exécution, la plus récente d'abord : la commande qui l'a faite, combien de fichiers
elle a supprimés, l'espace libéré, combien de fichiers elle a mis en quarantaine, et combien ont
été restaurés depuis. Une colonne *Déplacés* apparaît dès qu'une exécution a déplacé des fichiers
vers un autre de vos dossiers. Ici le premier nettoyage a été entièrement annulé (36 fichiers
restaurés), puis refait.

## Vider la quarantaine : `purge`

La quarantaine garde ce que `clean` a déplacé : fichiers illisibles, fichiers compagnons
orphelins et, si vous l'avez demandé, quasi-doublons et photos de rafale. Une fois que vous les
avez vérifiés (ouvrez le dossier de quarantaine dans l'Explorateur), `purge` les supprime **pour
de bon** :

```powershell
cavo789/media-hygiene --locale fr purge
```

<!-- capture: purge.txt -->
```text
❓ Supprimer définitivement la quarantaine de 20260930-191249, 20260930-191245
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

← [8. Nettoyer](08-clean.md) · [Documentation](../README.md) · Suivant : **[10. Trier les rafales dans le navigateur](10-review-bursts.md)** →
