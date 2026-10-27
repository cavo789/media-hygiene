# `push` : copier vos photos sur le NAS, seulement ce qui lui manque

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `push` · 🇬🇧 [English](../../en/commands/push.md)

> À ne pas confondre avec `--backup` (un dossier comparé à vos photos, jamais modifié) ni avec `mh backup` (la sauvegarde de l'index et des réglages, TODO 0352).

> **Windows seulement.** Tapez-la dans **Windows PowerShell** : `mh push --to \\<NAS>\backup_photos`.
> Windows écrit sur le NAS environ 7 fois plus vite qu'une copie par Docker (86 à 105,8 Mo/s
> contre 15,1 Mo/s, mesuré sur un Synology en Ethernet) ; le `mh` de WSL ou de Linux la refuse
> et donne cette même commande.

## En bref

**Copier chaque dossier de photos que `mh` connaît dans un dossier rien qu'à eux sur le NAS :
seulement ce qui lui manque ; une photo déplacée sur le PC y est renommée, jamais renvoyée ; une
photo supprimée par erreur n'est jamais supprimée du NAS.**

Le conteneur décide (il connaît vos audits, ce que vous avez déplacé, mis de côté ou purgé),
Windows copie : renommages par `Move-Item`, copies par `robocopy`. Vos photos sont seulement lues.

**Quand** : après un import, un nettoyage ou un tri ; aussi souvent que vous voulez, un passage
sans rien de nouveau ne fait que lister les deux côtés.

**Essayez** (la première fois, puis `mh push` seul) :

```powershell
mh push --to \\NAS\backup_photos
```

## D'un coup d'œil

| | |
|---|---|
| Vos photos | 🔒 Seulement lues (montées `:ro`). |
| Le dossier de sauvegarde | ✋ Écrit par Windows : nouveaux fichiers copiés, fichiers renommés renommés, fichiers mis de côté dans `.removed`. Jamais `robocopy /MIR` ni `/PURGE`. |
| Besoin | Windows PowerShell ; un dossier partagé rien qu'à lui sur le NAS (dans DSM : *Panneau de configuration → Dossier partagé → Créer*, p. ex. `backup_photos`) ; `/journal` ; `/cache`. |
| Annuler | `mh push --undo <passage>` remet ce qu'un passage a renommé ou mis de côté (les copies restent). |
| Avec `mh` | `mh push --to <dossier>` une fois, puis `mh push` ; `--anyway` ; `--undo <passage>`. |

## Le dossier de sauvegarde

Un dossier **rien qu'à lui** : jamais le partage `Photos` de votre NAS (une [sauvegarde que vous comparez](../clean/05-choose-the-kept-copy.md#comparer-une-sauvegarde-ou-un-ancien-disque),
qu'aucune commande ne modifie), jamais un dossier de photos, jamais à l'intérieur d'un : `mh`
refuse un tel dossier et nomme les deux. Chaque dossier de photos va dessous par son propre
chemin, le lecteur comme dossier : `C:\Photos` dans `\\NAS\backup_photos\C\Photos`, pour que
deux dossiers du même nom ne se rencontrent jamais. Le dossier donné avec `--to` est retenu
(`%USERPROFILE%\media-hygiene\push-target.txt`), relu et affiché ; le mot de passe du NAS est
celui que `mh folders add --backup` a gardé, sinon demandé une fois. Si Windows ne peut pas
encore ouvrir le partage, il reçoit une lettre de lecteur libre (`Z:` d'abord) le temps du
passage, retirée ensuite.

## Ce que fait un passage

1. **Liste** vos dossiers de photos et la sauvegarde (taille, date) : tous les fichiers, pas
   seulement les photos (un PDF dans `C:\Photos` est sauvegardé aussi), sauf les dossiers
   système (`#recycle`, `@eaDir`…), les dossiers exclus et la quarantaine.
2. **Planifie**, et le dit : ce qui est déjà là, ce qui est nouveau, ce qui a été déplacé (même
   taille, date, premiers et derniers 64 Ko : renommé sur le NAS, rien n'est envoyé), ce qui a
   été modifié (la copie du NAS mise de côté d'abord), ce qui a disparu du PC.
3. **Demande une fois**, journalise chaque renommage, puis Windows renomme et lance `robocopy`
   par dossier : seuls les fichiers nouveaux ou changés de taille ou de date sont copiés, un
   passage interrompu reprend au suivant.
4. **Prouve** : la sauvegarde est listée à nouveau, chaque copie retrouvée avec sa taille et sa
   date (un fichier que robocopy n'a pas copié est nommé), le passage noté dans
   [`history`](history.md).

Un dossier non branché (un disque USB) ou non lu en entier laisse sa partie de la sauvegarde
telle quelle.

## Ce qui quitte la sauvegarde

Un fichier que le PC n'a plus est **mis de côté** dans `\\NAS\backup_photos\.removed\<passage>\…`,
et seulement si vous l'avez retiré exprès : **purgé** de la quarantaine (ou supprimé par `clean`
comme copie exacte), ou **confirmé** supprimé dans [`review --gone`](review.md). Un fichier
encore en quarantaine, une suppression pas encore confirmée, ou un fichier dont l'outil ne sait
rien (une suppression par erreur ?) **reste**, compté par raison. La copie précédente d'un
fichier modifié va aussi dans `.removed`. `.removed` est vidé après `keep_removed_days` (90
jours).

Un fichier que l'[audit](audit.md) a trouvé abîmé ne remplace jamais sa copie dans la
sauvegarde.

**L'arrêt de sécurité** : quand les fichiers mis de côté et remplacés dépassent
`stop_above_percent` (20 %) de la sauvegarde, rien n'est appliqué : un disque absent ? beaucoup
de fichiers changés d'un coup ? Regardez, puis `mh push --anyway`.

## Vitesse

Une première sauvegarde de 240,9 Go : environ 40 minutes aux 100 Mo/s de Windows, contre 4 h 28
par Docker à 15 Mo/s (estimé d'après les lectures mesurées ; la vitesse d'écriture du NAS est
mesurée par l'étape 27 de `mh-measure.ps1`). Les passages suivants listent les deux côtés
(environ 21 s pour 52 094 fichiers, estimé) et ne copient que les nouveaux fichiers ; après un
tri qui déplace toute la photothèque, seulement des renommages.

## Réglages (`config.toml`)

| Réglage | Par défaut | Ce qu'il fait |
|---|---|---|
| `[push] keep_removed_days` | `90` | Jours qu'un fichier attend dans `.removed` avant que `mh push` l'efface. |
| `[push] stop_above_percent` | `20` | L'arrêt de sécurité. |
| `[push] threads` | `8` | Fichiers que robocopy copie à la fois (`/MT`). |

## Options

| Option | Ce qu'elle fait |
|---|---|
| `--to DOSSIER` | Le dossier de sauvegarde (`\\NAS\backup_photos`, ou un dossier d'un disque) ; retenu pour les passages suivants. |
| `--anyway` | Passer outre l'arrêt de sécurité. |
| `--undo PASSAGE` | Remettre ce que ce passage a renommé ou mis de côté (`mh` seulement). |
| `--backup CHEMIN` | Une sauvegarde comparée, que le dossier ne doit pas chevaucher (`mh` passe les vôtres). |

Lancée à la main (`docker run … media-hygiene push --to …`), la commande ne fait que montrer le
plan.

## Aller plus loin

- [Plusieurs dossiers : votre NAS](../start/03-several-folders.md#votre-nas--sauvegardez-y-vos-photos)
- [`import`](import.md) : récupérer ce que seul le NAS contient
- [Le lanceur `mh`](launcher.md)

## L'aide intégrée

<details>
<summary><code>push --help</code></summary>

<!-- capture: help-push.txt -->
```text
 Utilisation : media-hygiene push [OPTIONS]

 Windows seulement, en mh push : copier vos dossiers de photos dans un
 dossier rien qu'à eux sur le NAS, seulement ce qui lui manque ; une photo
 déplacée y est renommée, une suppression par erreur n'y est jamais reportée.
 Lancée ici, elle montre le plan.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ *  --to              <str>  The backup folder, as Windows writes it          │
│                             (\\NAS\backup_photos): a folder of its own,      │
│                             never a photo folder nor a backup compared.      │
│                             [required]                                       │
│    --anyway                 Go on even when more than stop_above_percent     │
│                             (config.toml) of the backup would be set aside   │
│                             or replaced.                                     │
│    --help    -h             Affiche ce message et quitte.                    │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Avancé : dossiers (remplacent folders.* de config.toml) ────────────────────╮
│ --backup        <str>  Une sauvegarde ou un ancien disque, monté en lecture  │
│                        seule : jamais modifié, et jamais refusé pour cela    │
│                        (mh passe vos sauvegardes). Répétable.                │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
