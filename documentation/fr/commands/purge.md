# `purge` : vider la quarantaine pour de bon

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `purge` · 🇬🇧 [English](../../en/commands/purge.md)

## En bref

**Récupérer la place pour de bon, une fois que vous avez vérifié ce que contient la
quarantaine.**

`clean` n'efface jamais : il déplace les copies en trop en quarantaine. `purge` supprime **pour
de bon** la quarantaine d'une exécution, ou de toutes. C'est la seule commande qui efface du
contenu (avec `clean --delete`, si vous l'utilisez), et elle le dit avant de demander.

**Quand** : une fois le dossier de la quarantaine ouvert dans l'Explorateur et vérifié, quand
vous avez besoin de la place ; [`status`](status.md) vous rappelle une quarantaine de plus de 30
jours.

**Essayer** :

```powershell
docker run --rm -it -v "$HOME\media-hygiene\quarantine:/quarantine" cavo789/media-hygiene --locale fr purge
```

## D'un coup d'œil

| | |
|---|---|
| Vos photos | ⚠️ Efface les fichiers de la quarantaine ; vos dossiers eux-mêmes ne sont pas touchés. |
| Il faut | `/quarantine`, en écriture. |
| Conseillé | Les mêmes options `-v` que votre `clean` (ou `mh purge`). |
| Écrit | Rien : il supprime les dossiers de quarantaine. |
| Annuler | **Impossible** : après une purge, `undo` ne peut plus ramener ces fichiers. |
| Avec `mh` | `mh purge`, `mh purge <exécution>`. |

## Lancer

```powershell
docker run --rm -it `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene --locale fr purge
```

Il prévient que les fichiers ne pourront pas revenir, donne combien de fichiers et quelle place,
puis demande : *Effacer la quarantaine de 20261011-100826 (41 fichiers, 16,3 Mo) ? [o/N]*.
Avec `o` : *✅ Quarantaine vidée : 16,3 Mo libérés.*

## Options

| Option | Rôle |
|---|---|
| `EXÉCUTION` | Seulement la quarantaine de cette exécution (voir [`history`](history.md)) ; toutes par défaut. |
| `--yes`, `-y` | Ne pas demander. |

## Bon à savoir

- Une quarantaine vide dit *La quarantaine est vide* et ne fait rien.
- Un nom d'exécution sans quarantaine est refusé : *L'exécution … n'a pas de quarantaine*.
- La quarantaine contient ce que `clean` a déplacé (copies en trop, fichiers illisibles, fichiers
  compagnons orphelins, quasi-doublons et photos de rafale que vous avez écartés) et ce que `sort`
  a mis de côté (`Thumbs.db` et consorts). Les photos de rafale et les quasi-doublons ne sont
  **pas** des copies : une fois purgés, rien ne peut les reconstruire.

## Pour aller plus loin

- [9. Annuler, historique, purge](../clean/09-undo-history-purge.md#vider-la-quarantaine--purge)
- [Comment vos photos restent en sécurité](../reference-safety.md#rien-nest-effacé-tant-que-vous-ne-lancez-pas-purge)

## L'aide intégrée

<details>
<summary><code>purge --help</code></summary>

<!-- capture: help-purge.txt -->
```text
 Utilisation : media-hygiene purge [OPTIONS] [run_id]

 Effacer pour de bon la quarantaine d'une exécution : avec 'clean --delete', la
 seule façon dont l'outil supprime du contenu.

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│   run_id      <str>  Exécution dont la quarantaine est effacée ; toutes par  │
│                      défaut.                                                 │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --yes   -y        Ne pas demander de confirmation (remplace clean.confirm).  │
│ --help  -h        Affiche ce message et quitte.                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
