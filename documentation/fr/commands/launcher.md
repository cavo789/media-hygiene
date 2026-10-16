# `launcher` : écrire vos dossiers une fois, puis taper `mh`

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `launcher` · 🇬🇧 [English](../../en/commands/launcher.md)

## En bref

**Taper `mh audit` au lieu d'un long `docker run` : vos dossiers sont écrits une fois, avec les
bons montages pour chaque commande.**

Les commandes `docker run` s'allongent à chaque dossier, et chaque commande demande des montages
un peu différents (`:ro` ou non, le [journal](../reference-glossary.md#journal), un port pour le navigateur). `launcher` affiche un
court script qui définit `mh`, une commande qui retient vos dossiers, donnés tels que
l'Explorateur les montre : aucun `-v` à écrire. Ensuite, `mh audit`, `mh clean`, `mh review`…
suffisent.

**Quand** : une fois que vous savez sur quels dossiers vous travaillez ; à nouveau quand vous en
ajoutez un.

**Essayer** :

```powershell
mkdir -Force "$HOME\media-hygiene"
docker run --rm cavo789/media-hygiene --locale fr launcher --photos "C:\Photos" > "$HOME\media-hygiene\mh.ps1"
. "$HOME\media-hygiene\mh.ps1"
mh audit
```

## D'un coup d'œil

| | |
|---|---|
| Vos photos | 🔒 Jamais modifiées : il affiche seulement un script. |
| Il faut | Vos dossiers, un `--photos` chacun. |
| Conseillé | `--quarantine` sur le disque des photos, s'il n'est pas `C:`. |
| Écrit | Rien lui-même : vous redirigez ce qu'il affiche vers un fichier. |
| Annuler | Supprimez le fichier. |

## Lancer

**Sans `-it`**, et avec `>` pour enregistrer ce qu'il affiche :

```powershell
mkdir -Force "$HOME\media-hygiene"
docker run --rm cavo789/media-hygiene --locale fr launcher `
  --photos "C:\Photos" `
  --photos "D:\Ancien disque" `
  --quarantine "D:\quarantaine" `
  > "$HOME\media-hygiene\mh.ps1"
. "$HOME\media-hygiene\mh.ps1"
mh audit
```

Depuis WSL :

```bash
mkdir -p ~/media-hygiene
docker run --rm cavo789/media-hygiene --locale fr launcher --photos /mnt/c/Photos > ~/media-hygiene/mh.sh
source ~/media-hygiene/mh.sh
mh audit
```

## Ce que `mh` fait pour chaque commande

- **Il vérifie d'abord vos dossiers** : un disque pas branché est signalé, et rien n'est lancé
  (Docker monterait un dossier vide à sa place).
- **Vos dossiers en lecture seule** (`:ro`) pour chaque commande qui ne les modifie jamais, en
  écriture seulement pour `clean`, `sort`, `album`, `undo`, `purge` et `xmp`.
- **Le cache** (le volume `media-hygiene-cache`) et les dossiers `reports`, `config`, `journal`
  et `quarantine` de `$HOME\media-hygiene`, créés s'ils manquent ; le dossier de `--quarantine`,
  ou un dossier de l'outil que vous avez monté vous-même avec `-v` en lançant `launcher`, est gardé
  à la place.
- **Le port de la page du navigateur** (`-p 127.0.0.1:8088:8088`) pour `review`, `review-sort`,
  `places`, `search` et `people`, et **votre navigateur s'ouvre sur cette page** dès qu'elle
  répond : aucune adresse à copier. Ctrl+C dans la fenêtre l'arrête toujours.
- **Votre ordinateur reste éveillé pendant les commandes longues** (`audit`, `clean`,
  `inventory`, `classify`, `sort`, `tags`, `people`, `undo`) : Windows ne se met pas en veille
  avant leur fin, et peut à nouveau après (l'écran peut toujours s'éteindre). Sous Linux, `mh.sh`
  utilise `systemd-inhibit`, sous macOS `caffeinate` ; sous WSL, Windows décide.
- **Le titre de la fenêtre dit quand une commande longue se termine** : `mh audit...` pendant
  qu'elle tourne, puis `mh audit : terminé` (ou `échec`) avec un son : une fenêtre réduite le
  montre dans la barre des tâches. Votre propre titre revient au `mh` suivant.
- **Accents et emojis lisibles** dans chaque console, l'ancienne de Windows PowerShell 5.1
  aussi : `mh.ps1` lit la sortie de l'outil en UTF-8, puis rend à la console son propre encodage.
- **Les commandes que l'outil propose** à la fin d'une exécution s'écrivent `mh …` elles aussi.
- **Votre fuseau horaire, demandé à chaque lancement** : `mh.ps1` le demande à Windows
  (`Get-TimeZone`), `mh.sh` au système (`/etc/localtime`) : les rapports sont datés à votre heure,
  à l'étranger aussi. Un `[general] timezone` dans `config.toml`, ou un `-e TZ=…` donné à
  `launcher`, l'emporte.
- **Votre langue** : un `--locale fr` donné à `launcher` est écrit dans le script : `mh` parle
  français. Une langue réglée dans `config.toml` est laissée au fichier (une modification de celui-ci
  compte toujours). `launcher` finit par une ligne qui dit ce que `mh` retient : dossiers, langue,
  fuseau horaire.

## Options

| Option | Rôle |
|---|---|
| `--photos "C:\Photos"` | Un dossier de photos et vidéos, tel que l'Explorateur le montre (`/mnt/c/Photos` depuis WSL). Répétez-la pour plusieurs dossiers ; pas un dossier à l'intérieur d'un autre. |
| `--quarantine "D:\quarantaine"` | Où vont les copies mises de côté. Par défaut : `$HOME\media-hygiene\quarantine`. |
| `--shell powershell` | Un script PowerShell (`mh.ps1`), pour Windows. |
| `--shell bash` | Un script bash (`mh.sh`), pour WSL, Linux, macOS. |

Par défaut, le shell est deviné d'après les dossiers : un dossier Windows (`C:\…`) donne
PowerShell. Les `-v` des guides précédents fonctionnent toujours, à côté de `--photos`.

## Bon à savoir

- **Dans un nouveau terminal**, rechargez-le : `. "$HOME\media-hygiene\mh.ps1"`. Pour avoir `mh`
  dans chaque terminal, écrivez cette ligne dans votre profil PowerShell, une fois (le profil et
  son dossier sont créés s'ils manquent ; `notepad $PROFILE` montre ensuite la ligne) :

  ```powershell
  New-Item -ItemType Directory -Force (Split-Path $PROFILE) | Out-Null
  Add-Content $PROFILE '. "$HOME\media-hygiene\mh.ps1"'
  ```

  En bash, ajoutez la ligne `source` à `~/.bashrc`.
- **Un autre dossier ?** Relancez `launcher` avec un `--photos` de plus, vers le même fichier.
  Pour une seule commande : `mh --photos "E:\Clé USB" audit` l'ajoute à vos dossiers.
- **Un dossier réseau** (`\\NAS\photos`) est refusé par `--photos` : copiez les photos sur un
  disque local, ou montez-le vous-même avec `-v`.
- **Un dossier refusé** (dans un autre, réseau, relatif) : `launcher` dit pourquoi à l'écran, et
  le chargement du fichier s'arrête sur la même phrase.
- **Avec `-it`**, Docker envoie aussi les messages dans le fichier : `launcher` n'écrit pas de
  lanceur, et le chargement du fichier s'arrête sur la bonne commande (sans `-it`).
- PowerShell refuse de charger le fichier (*l'exécution de scripts est désactivée*) ? Une fois :
  `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
- **Les dossiers accentués** (`C:\Photos\Vidéos`) ne craignent rien : `mh.ps1` ne contient que
  des caractères ASCII, que `>` ne peut pas abîmer, quelle que soit la page de codes de la
  console. Un `é` de dossier y est écrit `$([char]0x00E9)`, que PowerShell retransforme en `é` ;
  les commentaires perdent leurs accents.

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
