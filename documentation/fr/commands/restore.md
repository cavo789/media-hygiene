# `restore` : une sauvegarde de l'index remise en place

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `restore` · 🇬🇧 [English](../../en/commands/restore.md)

## En bref

**Le cache perdu (Docker réinitialisé, volume supprimé) : l'index de retour en quelques secondes,
sans refaire les audits.**

`restore` remet en place une archive écrite par [`backup`](backup.md) : la plus récente de
`$HOME\media-hygiene\backups`, ou celle que vous nommez. Le `mh audit` suivant ne relit alors que
ce qui a changé depuis la sauvegarde.

## D'un coup d'œil

| | |
|---|---|
| Vos photos | 🔒 Ni lues ni modifiées. |
| Besoins | `/backups` (les archives), `/cache` (l'index remplacé), `/config` avec `--config`. |
| Écrit | L'index dans `/cache` ; avec `--config`, les réglages dans `/config` ; une sauvegarde de l'index remplacé, dans `/backups`. |
| Avec `mh` | `mh restore` : `mh` monte `$HOME\media-hygiene\backups` pour `backup` et `restore` seulement. |

## Lancer

```powershell
mh restore
mh restore mh-backup-20261027-101500.zip
```

Rien n'est écrasé avant que l'archive soit prouvée intacte : chaque fichier comparé à son SHA-256,
l'index vérifié ; une archive faite par une version plus récente est refusée (`mh update` d'abord).
Ensuite l'index en place est **sauvegardé d'abord**, et la fenêtre finit sur la ligne qui le remet :
`mh restore <cette archive>`. Les lignes de chaque table sont montrées, relues dans l'index remis.

## Options

| Option | Ce qu'elle fait |
|---|---|
| `archive` | Le nom de l'archive dans `$HOME\media-hygiene\backups` ; la plus récente par défaut. |
| `--config` | Remet aussi les réglages (`config.toml`, `people\*.toml`) ; l'index seul par défaut, car vous les avez peut-être modifiés depuis. Un fichier écrit depuis la sauvegarde et absent d'elle reste. |

## Bon à savoir

- Un fichier déplacé, renommé ou supprimé depuis la sauvegarde : l'index le connaît par son chemin,
  donc l'audit suivant oublie les chemins disparus et lit les nouveaux ; les mots de `tags` d'un
  fichier déplacé sont recalculés par le `mh tags` suivant.
- Le script `mh` lui-même n'est jamais remis : `mh update` le réécrit.

## Pour aller plus loin

- [`backup` : l'index et les réglages, gardés hors de Docker](backup.md)

## L'aide intégrée

<details>
<summary><code>restore --help</code></summary>

<!-- capture: help-restore.txt -->
```text
 Usage: media-hygiene restore [OPTIONS] [archive]

 Put back a backup of the index (and the settings with --config), after backing
 up the current one.

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│   archive      <str>  The backup to restore, by its name; the most recent by │
│                       default.                                               │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --config            Restore the settings (config.toml, people) too; the      │
│                     index alone by default.                                  │
│ --help    -h        Show this message and exit.                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
