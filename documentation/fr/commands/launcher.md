# `launcher` : écrire vos dossiers une fois, puis taper `mh`

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `launcher` · 🇬🇧 [English](../../en/commands/launcher.md)

## En bref

**Taper `mh audit` au lieu d'un long `docker run` : vos dossiers sont écrits une fois, avec les
bons montages pour chaque commande.**

Les commandes `docker run` s'allongent à chaque dossier, et chaque commande demande des montages
un peu différents (`:ro` ou non, le [journal](../reference-glossary.md#journal), un port pour le navigateur). `launcher` affiche un
court script qui définit `mh`, une commande qui retient les dossiers montés au moment où vous
l'avez créée. Ensuite, `mh audit`, `mh clean`, `mh review`… suffisent.

**Quand** : une fois que vous savez sur quels dossiers vous travaillez ; à nouveau quand vous en
ajoutez un.

**Essayer** :

```powershell
mkdir -Force "$HOME\media-hygiene"
docker run --rm -v "C:\Photos:/data/c/Photos" cavo789/media-hygiene --locale fr launcher > "$HOME\media-hygiene\mh.ps1"
. "$HOME\media-hygiene\mh.ps1"
mh audit
```

## D'un coup d'œil

| | |
|---|---|
| Vos photos | 🔒 Jamais modifiées : il affiche seulement un script. |
| Il faut | Vos dossiers, un `-v` chacun, tels que vous voulez que `mh` les monte. |
| Conseillé | Vos propres dossiers de l'outil, s'ils ne sont pas ceux de `$HOME\media-hygiene`. |
| Écrit | Rien lui-même : vous redirigez ce qu'il affiche vers un fichier. |
| Annuler | Supprimez le fichier. |

## Lancer

**Sans `-it`**, et avec `>` pour enregistrer ce qu'il affiche :

```powershell
mkdir -Force "$HOME\media-hygiene"
docker run --rm `
  -e TZ=Europe/Brussels `
  -v "C:\Photos:/data/c/Photos" `
  -v "D:\Ancien disque:/data/d/Ancien disque" `
  cavo789/media-hygiene --locale fr launcher > "$HOME\media-hygiene\mh.ps1"
. "$HOME\media-hygiene\mh.ps1"
mh audit
```

Depuis WSL :

```bash
mkdir -p ~/media-hygiene
docker run --rm \
  -e TZ=Europe/Brussels \
  -v "/mnt/c/Photos:/data/c/Photos" \
  cavo789/media-hygiene --locale fr launcher --shell bash > ~/media-hygiene/mh.sh
source ~/media-hygiene/mh.sh
mh audit
```

## Ce que `mh` fait pour chaque commande

- **Vos dossiers en lecture seule** (`:ro`) pour chaque commande qui ne les modifie jamais, en
  écriture seulement pour `clean`, `sort`, `album`, `undo`, `purge` et `xmp`.
- **Le cache** (le volume `media-hygiene-cache`) et les dossiers `reports`, `config`, `journal`
  et `quarantine` de `$HOME\media-hygiene`, créés s'ils manquent ; un dossier de l'outil que vous
  avez monté vous-même en lançant `launcher` est gardé à la place.
- **Le port de la page du navigateur** (`-p 127.0.0.1:8088:8088`) pour `review`, `review-sort`,
  `places`, `search` et `people`.
- **Les commandes que l'outil propose** à la fin d'une exécution s'écrivent `mh …` elles aussi.
- **Votre langue et votre fuseau horaire** : un `--locale fr` donné à `launcher` et le `-e TZ=…`
  de son exécution sont écrits dans le script : `mh` parle français et date ses rapports à votre
  heure. Une langue réglée dans `config.toml` est laissée au fichier (une modification de celui-ci
  compte toujours). `launcher` finit par une ligne qui dit ce que `mh` retient : dossiers, langue,
  fuseau horaire.

## Options

| Option | Rôle |
|---|---|
| `--shell powershell` | Un script PowerShell (`mh.ps1`), pour Windows. |
| `--shell bash` | Un script bash (`mh.sh`), pour WSL, Linux, macOS. |

Par défaut, le shell est deviné d'après les dossiers montés : un dossier Windows (`C:\…`) donne
PowerShell.

## Bon à savoir

- **Dans un nouveau terminal**, rechargez-le : `. "$HOME\media-hygiene\mh.ps1"` ; ajoutez cette
  ligne à votre profil (`notepad $PROFILE`) pour avoir `mh` partout. En bash, ajoutez la ligne
  `source` à `~/.bashrc`.
- **Un autre dossier ?** Relancez `launcher` avec un `-v` de plus, vers le même fichier.
- **Pas à Bruxelles ?** Remplacez `Europe/Brussels` par votre fuseau (`Europe/Paris`,
  `America/Montreal`…). Sans `-e TZ=…`, `mh` tourne en UTC : les dossiers et heures des rapports
  sont décalés d'une ou deux heures.
- **Avec `-it`**, Docker envoie aussi les messages dans le fichier : `launcher` n'écrit pas de
  lanceur, et le chargement du fichier s'arrête sur la bonne commande (sans `-it`).
- PowerShell refuse de charger le fichier (*l'exécution de scripts est désactivée*) ? Une fois :
  `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

## Pour aller plus loin

- [3. Plusieurs dossiers et disques : `mh`](../start/03-several-folders.md#écrire-vos-dossiers-une-fois--mh)
- [Points de montage](../reference-mount-points.md)

## L'aide intégrée

<details>
<summary><code>launcher --help</code></summary>

<!-- capture: help-launcher.txt -->
```text
 Utilisation : media-hygiene launcher [OPTIONS]

 🔒 Lecture seule : ne modifie jamais vos photos. Écrit 'mh', une commande
 courte qui retient vos dossiers : mh audit, mh clean.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --shell          <powershell|bash>  Le shell du script : 'powershell'        │
│                                     (Windows) ou 'bash' (WSL, Linux, macOS). │
│                                     Par défaut : deviné d'après les dossiers │
│                                     montés.                                  │
│ --help   -h                         Affiche ce message et quitte.            │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
