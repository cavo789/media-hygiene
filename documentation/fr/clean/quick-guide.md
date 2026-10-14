# Nettoyer en bref : le parcours complet

[Documentation](../README.md) › Nettoyer en bref · 🇬🇧 [English](../../en/clean/quick-guide.md)

Tout ce que l'outil sait faire pour nettoyer, dans l'ordre, une étape à la fois, prêt à copier
dans **PowerShell**. Chaque étape tient en quelques lignes et renvoie à sa page détaillée, si vous
voulez comprendre. Arrivé en bas, vous avez fait le tour : [la dernière
section](#vous-avez-fait-le-tour) reprend chaque commande et l'étape qui la montre. Remplacez
`C:\Photos` par votre dossier (ou ajoutez-en d'autres : [plusieurs dossiers et
disques](../start/03-several-folders.md)).

Rien ne presse : vous pouvez vous arrêter après n'importe quelle étape, sauter celles marquées
*facultatif*, et tout ce que fait `clean` peut être annulé jusqu'à `purge`. De retour après
quelques jours ? `mh status` dit où vous en êtes et ce qui vient ensuite. Aucune commande de ce parcours ne demande d'IA : Docker
suffit.

## 0. Une seule fois : écrire la commande `mh`

```powershell
mkdir -Force "$HOME\media-hygiene"
docker run --rm -e MEDIA_HYGIENE_GENERAL__LOCALE=fr `
  -e TZ=Europe/Brussels `
  -v "C:\Photos:/data/c/Photos" `
  cavo789/media-hygiene launcher > "$HOME\media-hygiene\mh.ps1"
. "$HOME\media-hygiene\mh.ps1"
```

C'est la seule commande longue : elle écrit `mh`, une commande courte qui retient vos dossiers
et monte, à chaque étape, exactement ce qu'il faut (en français, grâce au `-e …LOCALE=fr`, et
à votre heure grâce au `-e TZ=…` : mettez votre fuseau s'il n'est pas `Europe/Brussels`). Ses
dossiers, dans `$HOME\media-hygiene`, sont créés par `mh` lui-même la première fois :

| Dossier | Ce qu'il reçoit |
|---|---|
| `reports` | Les rapports HTML, à ouvrir dans votre navigateur. |
| `config` | `config.toml`, vos réglages. |
| `journal` | Le journal de chaque nettoyage : ce qui permet `undo`. |
| `quarantine` | Les fichiers mis de côté, jusqu'à ce que vous les effaciez. |

Dans un nouveau terminal, rechargez `mh` avec la dernière ligne ci-dessus. Pour avoir `mh` dans
chaque terminal, écrivez cette ligne dans votre profil PowerShell, une fois :

```powershell
New-Item -ItemType Directory -Force (Split-Path $PROFILE) | Out-Null
Add-Content $PROFILE '. "$HOME\media-hygiene\mh.ps1"'
```

PowerShell refuse de le charger ? Voyez [écrire vos dossiers une
fois](../start/03-several-folders.md#écrire-vos-dossiers-une-fois--mh). Un dossier de plus plus
tard ? Relancez la commande ci-dessus avec un `-v` de plus.

## 1. Auditer

```powershell
mh audit
```

Rien n'est modifié : `mh` monte vos dossiers en lecture seule (`:ro`) pour toute commande qui ne
les change pas. Le premier audit lit tout ; grâce au cache, les suivants prennent quelques
secondes. La console résume ce qu'il a trouvé : copies en double, place qu'elles prennent,
fichiers cassés. Détails : [votre premier audit](../start/01-first-audit.md), [garder le
cache](../start/02-keep-the-cache.md).

## 2. Lire le rapport

À la fin de l'audit, Ctrl+clic sur le chemin de `report.html` (ou ouvrez `index.html` dans
`$HOME\media-hygiene\reports` : il liste tous les rapports). Lisez-le dans cet ordre :

1. **Les paires de dossiers** : pour chacune, quel dossier garde ses copies. C'est la
   vérification la plus rapide.
2. **Les groupes de fichiers identiques** : chaque copie, et pourquoi celle-là est gardée.
3. **Les fichiers cassés et les fichiers compagnons orphelins** : une photo illisible, un `.xmp`
   ou un `.aae` dont la photo a disparu ([fichiers compagnons](../reference-sidecars.md)) ;
   `clean` les met aussi de côté.
4. **Les quasi-doublons et les rafales** : rien n'en est fait pour l'instant, ils viennent aux
   étapes 9 et 10.

Chaque fichier, avec ce qui lui arrivera, est aussi dans `plan.csv`, à côté du rapport, à ouvrir
dans Excel. Détails : [le rapport HTML](04-html-report.md).

## 3. Choisir la copie gardée

L'outil choisit seul la copie gardée de chaque groupe (un dossier choisi par vous plutôt qu'un
`DCIM`, l'original plutôt que `IMG_0001 (1).jpg`, la plus ancienne…). Pas d'accord pour **tout un
dossier** ? Dites-le après `audit`, puis relisez le rapport :

```powershell
mh audit --prefer "C:\Photos\Famille"
```

| Option | Le dossier… |
|---|---|
| `--prefer "C:\Photos\Famille"` | garde ses copies en priorité. |
| `--protect "C:\Photos\Famille"` | n'est **jamais** modifié et garde toujours la copie : les copies identiques ailleurs partent. |
| `--exclude "D:\Sauvegarde"` | n'est pas analysé du tout : une vraie sauvegarde n'est pas un doublon. |
| `--exclude-name "Thumbnails,*.lrdata"` | est ignoré par son nom, sur tous les disques (vignettes, catalogues). |

Chaque option peut être répétée. Donnez les mêmes à `mh clean` (étape 7), ou écrivez-les une
fois pour toutes (étape 5). Détails : [choisir la copie gardée](05-choose-the-kept-copy.md).

Pas d'accord avec **une seule paire** ? Dans le rapport, la liste *Votre décision* de cette paire
propose *Inverser les dossiers* ou *Ne pas toucher*. Cliquez ensuite sur **Télécharger
decisions.json** et enregistrez le fichier dans `$HOME\media-hygiene\reports`, à côté
d'`index.html` : `mh clean --decisions` l'appliquera à l'étape 7. Détails : [décider paire par
paire](12-decide-pair-by-pair.md).

## 4. Seulement certains types de fichiers (facultatif)

Par défaut, l'audit regarde les photos, les images RAW et les vidéos. `--ext` restreint l'analyse
à quelques types, ou l'élargit à d'autres fichiers :

```powershell
mh audit --ext heic,video
```

`--ext video` ne regarde que les vidéos ; `--ext pdf` cherche aussi les PDF en double. Vos
propres listes de types se nomment dans `[scan.categories]` de `config.toml`. Détails :
[seulement certains types de fichiers](06-file-types.md).

## 5. Écrire vos choix une fois (facultatif)

Plutôt que de répéter `--prefer`, `--protect`, `--exclude` à chaque commande, écrivez-les dans
`config.toml`. La première fois, `config` crée un fichier commenté :

```powershell
mh config
notepad "$HOME\media-hygiene\config\config.toml"
```

Les réglages que la plupart des gens changent, chemins Windows entre **apostrophes** :

```toml
[folders]
preferred = ['C:\Photos\Famille']
protected = []
excluded = ['D:\Sauvegarde']
```

Chaque réglage est expliqué dans le fichier lui-même. Relancez `mh config` : il affiche chaque
réglage, d'où il vient (le fichier, une variable d'environnement, la ligne de commande, qui
l'emporte) et l'état de chaque dossier monté. Détails : [le fichier de
configuration](07-configuration-file.md).

## 6. Un second avis, avant de nettoyer (facultatif)

Avant de mettre de côté des photos de famille, vous voulez une preuve indépendante ? Czkawka, un
autre détecteur de doublons open source, peut vérifier les mêmes dossiers :

```powershell
mh crosscheck
```

Czkawka est livré dans l'image : `crosscheck` le lance sur vos dossiers (quelques minutes sur une
grande collection la première fois), puis compare les deux résultats groupe par groupe et dit où
ils diffèrent. Détails : [un second avis](13-second-opinion.md).

## 7. Mettre les doublons exacts de côté

```powershell
mh clean
```

Pour `clean`, `mh` monte vos dossiers en écriture (`clean` déplace des fichiers) et ajoute le
journal et la quarantaine. `clean` refait l'audit, dit ce qu'il va faire et demande
confirmation : répondez `o`. Les copies en trop, les fichiers illisibles et les fichiers
compagnons orphelins partent en quarantaine, jamais par-dessus un autre fichier ; chaque copie
est d'abord comparée octet par octet à celle qui reste. Un rapport de nettoyage dit ce qui est
arrivé à chaque fichier.

- Vous avez téléchargé `decisions.json` à l'étape 3 ? `mh clean --decisions`.
- Besoin de la place tout de suite ? `mh clean --delete` supprime les copies au lieu de les
  déplacer ; `undo` sait encore les reconstruire à partir de la copie gardée. Gardez-le pour
  quand vous aurez confiance.

Détails : [nettoyer](08-clean.md), [comment vos photos restent en
sécurité](../reference-safety.md).

## 8. Vérifier, voir ce qui a été fait, annuler

```powershell
explorer "$HOME\media-hygiene\quarantine"
mh history
```

La quarantaine reproduit vos dossiers, sous un dossier par nettoyage. `history` liste chaque
exécution : sa commande, les fichiers mis de côté ou supprimés, la place libérée, ce qui a été
restauré. Vous changez d'avis ?

```powershell
mh undo
```

Tout revient à sa place. `mh undo <exécution>` annule une exécution plus ancienne, par le nom
qu'en donne `history`. Détails : [annuler, historique, purge](09-undo-history-purge.md).

## 9. Les quasi-doublons (facultatif)

Les copies réduites ou recompressées (WhatsApp, e-mail…) et les vidéos réencodées ne sont pas
identiques à l'original : regardez-les d'abord dans le rapport de l'étape 2, sections
*Quasi-doublons* et *Vidéos réencodées*. Puis :

```powershell
mh clean --tier near
```

`--tier near` ne déplace que les groupes **sûrs** (même image et même son, empreintes
identiques, copie plus petite dans un dossier de messagerie) et dit combien de groupes à vérifier
restent en place : décidez-les un à un dans le navigateur avec `mh review --near`, puis
`mh clean --tier near --decisions` ; ou `--tier near-all` les déplace tous. La plus haute
résolution reste, tout part en quarantaine : `undo` si un groupe ne vous plaît pas. Détails :
[les quasi-doublons](11-near-duplicates.md).

## 10. Les rafales (facultatif)

Les séries de photos prises à quelques secondes d'intervalle : vous choisissez lesquelles garder,
dans votre navigateur.

```powershell
mh review
```

Ouvrez l'adresse affichée, `http://127.0.0.1:8088/`, dans votre navigateur (Ctrl+clic) et triez
au clavier ; les séries évidentes s'acceptent toutes d'un clic. Chaque choix est enregistré
aussitôt dans `decisions.json`, dans votre dossier de rapports ; **Ctrl+C** arrête, le `review`
suivant reprend où vous en étiez. Ensuite, `--decisions` met les photos écartées en quarantaine :

```powershell
mh clean --decisions
```

Le même `decisions.json` garde aussi vos paires de dossiers (étape 3) et vos quasi-doublons
(étape 9) : un seul `mh clean --tier near --decisions` applique les trois. Détails : [trier les
rafales dans le navigateur](10-review-bursts.md).

## 11. Libérer l'espace, pour de bon

Jusqu'ici, rien n'est effacé : la quarantaine occupe toujours la place. Une fois que vous avez
vérifié :

```powershell
mh purge
```

Elle demande confirmation. `mh purge <exécution>` ne vide que la quarantaine de cette exécution.
Après `purge`, `undo` ne peut plus ramener ces fichiers.

## 12. Contrôler, et revenir plus tard

`mh audit` à nouveau : il doit dire *Rien à nettoyer*. Ses quasi-doublons et rafales restants
sont ceux que vous avez choisi de garder.

Les semaines suivantes :

- **Où en suis-je ?** `mh status` dit, en une seconde et sans rien analyser, le dernier audit, ce
  qui est en quarantaine et depuis quand, ce que `undo` peut encore restaurer, les décisions pas
  encore appliquées, puis la prochaine étape en commande complète.
- **De nouvelles photos ?** Reprenez à l'étape 1 : grâce au cache, seules les nouvelles sont lues.
- **Trop de rapports ?** `mh reports --prune 10` garde les dix plus récents et refait
  `index.html`.

Détails : [où en suis-je ?](09-undo-history-purge.md#où-en-suis-je--status), [lister et ranger
les rapports](04-html-report.md#lister-et-ranger-les-rapports).

## Vous avez fait le tour

Chaque commande du nettoyage, et l'étape de cette page qui la montre :

| Commande | Étape | Ce qu'elle fait |
|---|---|---|
| [`launcher`](../commands/launcher.md) | 0 | Écrit `mh`, qui retient vos dossiers. |
| [`audit`](../commands/audit.md) | 1 à 4 | Trouve les doublons et les fichiers cassés, sans rien modifier ; `--prefer`, `--protect`, `--exclude`, `--exclude-name`, `--ext`. |
| [`config`](../commands/config.md) | 5 | Crée `config.toml`, puis montre chaque réglage et son origine. |
| [`crosscheck`](../commands/crosscheck.md) | 6 | Compare l'audit avec Czkawka. |
| [`clean`](../commands/clean.md) | 7, 9, 10 | Met de côté les copies, les fichiers cassés, les compagnons orphelins ; `--decisions`, `--tier near`, `--delete`. |
| [`history`](../commands/history.md) | 8 | Liste ce que chaque exécution a fait. |
| [`undo`](../commands/undo.md) | 8 | Remet chaque fichier d'une exécution à sa place. |
| [`review`](../commands/review.md) | 9, 10 | Décide les rafales et les quasi-doublons dans le navigateur. |
| [`purge`](../commands/purge.md) | 11 | Vide la quarantaine : la place est libérée. |
| [`status`](../commands/status.md) | 12 | Dit où vous en êtes et la prochaine étape. |
| [`reports`](../commands/reports.md) | 12 | Liste les rapports, supprime les anciens. |

Les autres commandes rangent et retrouvent vos photos : par année, événement, lieu ou personne
(`classify`, `sort`, `places`, `people`), par un mot (« Chloé à la montagne » : `tags`, `search`),
dans des albums ou dans Excel (`album`, `xmp`, `inventory`). Elles ont leur propre parcours :
**[trier en bref](../sort/quick-guide.md)**. Un mot vous échappe ? [Les mots de ce
guide](../reference-glossary.md). Un message d'erreur ? [Dépannage](../reference-troubleshooting.md).

<details>
<summary>Sans <code>mh</code> : les commandes complètes</summary>

Chaque commande `mh` est un `docker run` avec les mêmes dossiers. Pour celles qui ne modifient
rien (`audit`, `config`, `crosscheck`, `history`, `status`, `reports`), en lecture seule :

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene --locale fr audit
```

Pour `clean`, `undo` et `purge` : `:ro` est retiré, `/journal` et `/quarantine` sont ajoutés ;
remplacez `clean` par la commande de l'étape :

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene --locale fr clean
```

Pour `review` : la première commande avec `-p 127.0.0.1:8088:8088` après `-it`. Créez les
quatre dossiers avant le premier lancement (`mkdir -Force "$HOME\media-hygiene\reports", …`) : un
dossier que Docker crée lui-même appartient à l'administrateur, et l'outil ne pourrait pas y
écrire.

</details>

---

[Documentation](../README.md) · Pas à pas : **[4. Le rapport HTML](04-html-report.md)** →
