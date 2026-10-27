# `backup` : l'index et les réglages, gardés hors de Docker

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `backup` · 🇬🇧 [English](../../en/commands/backup.md)

## En bref

**Ce que les audits et `mh tags` ont appris, à l'abri d'une remise à zéro de Docker.**

Le [cache](../reference-glossary.md#cache) (`/cache`) est un volume Docker, `media-hygiene-cache` :
un `docker volume prune`, une réinitialisation de Docker Desktop ou un nouveau WSL l'effacent. Il
contient l'index : l'empreinte de chaque fichier, ce que les audits ont lu, les mots de `tags`, les
descriptions, les visages — des heures de travail à refaire. `backup` écrit l'index et vos réglages
(`config.toml`, `people\*.toml`) dans un seul zip, `mh-backup-AAAAMMJJ-HHMMSS.zip`, dans
`$HOME\media-hygiene\backups` ; [`restore`](restore.md) le remet en place.

À ne pas confondre avec `--backup` (un dossier
[comparé](../clean/05-choose-the-kept-copy.md#comparer-une-sauvegarde-ou-un-ancien-disque)) ni avec
[`push`](push.md) (vos photos copiées sur le NAS) : `backup` garde la mémoire de l'outil, jamais une
photo.

**Quand** : après un long `mh tags` ou `mh people`, avant une mise à jour ou une réinitialisation de
Docker Desktop.

## D'un coup d'œil

| | |
|---|---|
| Vos photos | 🔒 Ni lues ni modifiées. |
| Besoins | `/cache` (l'index), `/config`, `/backups` (où va l'archive). |
| Écrit | Dans `/backups` seulement : l'archive ; les 3 plus récentes sont gardées, les plus anciennes supprimées. |
| Avec `mh` | `mh backup` : `mh` monte `$HOME\media-hygiene\backups` pour `backup` et `restore` seulement. |

## Lancer

Dans Windows PowerShell :

```powershell
mh backup
```

L'index est copié par la sauvegarde propre à SQLite (cohérente même si une autre fenêtre le lit),
puis l'archive est **relue sur le disque** : chaque fichier comparé à son SHA-256 de
`manifest.json`, l'index vérifié en entier (`PRAGMA integrity_check`). La fenêtre montre alors
l'archive, sa taille et les lignes de chaque table relues (`files`, `tags`, `descriptions`,
`meanings`, `faces`).

L'archive est sur `C:`, comme le disque de Docker : elle protège d'une fausse manœuvre, pas d'une
panne du disque. Copiez-la aussi sur une clé USB ou le NAS.

Avec `docker run`, montez vous-même le dossier des archives :

```powershell
docker run --rm -it `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\config:/config" `
  -v "$HOME\media-hygiene\backups:/backups" `
  cavo789/media-hygiene backup
```

## Bon à savoir

- Pas dans l'archive : les aperçus (refaits par les rapports), les modèles (téléchargés à nouveau),
  le journal (déjà hors du volume, dans `$HOME\media-hygiene\journal`), les mots de passe du NAS
  (lisibles par votre compte Windows sur ce PC seulement).
- Les 3 archives les plus récentes sont gardées dans `$HOME\media-hygiene\backups` ; une quatrième
  supprime la plus ancienne, dit en une ligne.

## Pour aller plus loin

- [`restore` : remettre une sauvegarde](restore.md)

## L'aide intégrée

<details>
<summary><code>backup --help</code></summary>

<!-- capture: help-backup.txt -->
```text
 Usage: media-hygiene backup [OPTIONS]

 🔒 Read-only: never changes your photos. Back up the index and the settings
 into one archive outside Docker's cache volume, read back.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help  -h        Show this message and exit.                                │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
