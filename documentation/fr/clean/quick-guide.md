# Nettoyer en bref : le parcours complet

[Documentation](../README.md) › Nettoyer en bref · 🇬🇧 [English](../../en/clean/quick-guide.md)

Libérez la place que prennent vos photos et vidéos en double, sans risque : une commande par
étape, à coller dans **PowerShell**. Rien n'est effacé avant la dernière étape, et jusque-là tout
peut être annulé. Aucune IA nécessaire : Docker suffit.

<div class="mh-path" markdown>

**Le strict minimum**, pour un premier nettoyage : cinq étapes. Les autres sont facultatives.

- [0 · Écrire `mh`](#0-une-seule-fois--écrire-la-commande-mh)
- [1 · Auditer](#1-auditer)
- [2 · Lire le rapport](#2-lire-le-rapport)
- [7 · Mettre de côté](#7-mettre-les-doublons-exacts-de-côté)
- [11 · Libérer l'espace](#11-libérer-lespace-pour-de-bon)

</div>

Chaque étape dit ce qu'elle risque : <span class="mh-badge mh-safe">🔒 Photos intactes</span>
<span class="mh-badge mh-undo">↩️ Annulable</span> <span class="mh-badge mh-final">⚠️ Pour de
bon</span>. De retour après quelques jours ? `mh status` dit où vous en êtes et ce qui vient
ensuite.

## 0. Une seule fois : écrire la commande `mh`

<span class="mh-badge mh-once">⏱ Une fois</span>

Pas encore de Docker ? [Installez Docker](../start/00-install-docker.md) d'abord : quelques
minutes, une fois.

**D'abord**, laissez PowerShell exécuter les scripts écrits sur votre ordinateur, `mh` compris :
Windows l'interdit par défaut (*l'exécution de scripts est désactivée sur ce système*). Pour votre
compte seulement ; les scripts téléchargés sur Internet doivent toujours être signés :

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned -Force
```

**Ensuite**, écrivez `mh`, avec votre dossier à la place de `C:\Photos` :

```powershell
mkdir -Force "$HOME\media-hygiene"
docker run --rm -e MEDIA_HYGIENE_GENERAL__LOCALE=fr `
  -e TZ=Europe/Brussels `
  -v "C:\Photos:/data/c/Photos" `
  cavo789/media-hygiene launcher > "$HOME\media-hygiene\mh.ps1"
. "$HOME\media-hygiene\mh.ps1"
```

Dans un nouveau terminal, rechargez `mh` avec la dernière ligne.

??? question "Vos photos ne sont pas dans `C:\Photos` ?"

    Changez **les deux côtés** de `-v` : le dossier Windows à gauche, le même chemin à droite
    après `/data/`, la lettre du disque en minuscule et des `/` au lieu des `\`.
    `D:\Images\Famille` s'écrit :

    ```powershell
    -v "D:\Images\Famille:/data/d/Images/Famille"
    ```

    Avec seulement la gauche changée, les rapports montreraient `C:\Photos` et `--prefer
    "D:\Images\…"` ne désignerait rien. Deux dossiers ? Deux `-v` : [plusieurs dossiers et
    disques](../start/03-several-folders.md). Un dossier de plus plus tard ? Relancez la commande
    avec un `-v` de plus.

??? info "Ce que fait cette commande"

    C'est la seule commande longue : elle écrit `mh`, une commande courte qui retient vos
    dossiers et monte, à chaque étape, exactement ce qu'il faut (en français, grâce au
    `-e …LOCALE=fr`, et à votre heure grâce au `-e TZ=…` : mettez votre fuseau s'il n'est pas
    `Europe/Brussels`). Ses dossiers, dans `$HOME\media-hygiene`, sont créés par `mh` lui-même la
    première fois :

    | Dossier | Ce qu'il reçoit |
    |---|---|
    | `reports` | Les rapports HTML, à ouvrir dans votre navigateur. |
    | `config` | `config.toml`, vos réglages. |
    | `journal` | Le journal de chaque nettoyage : ce qui permet `undo`. |
    | `quarantine` | Les fichiers mis de côté, jusqu'à ce que vous les effaciez. |

??? tip "`mh` dans chaque terminal"

    Écrivez la ligne de chargement dans votre profil PowerShell, une fois :

    ```powershell
    New-Item -ItemType Directory -Force (Split-Path $PROFILE) | Out-Null
    Add-Content $PROFILE '. "$HOME\media-hygiene\mh.ps1"'
    ```

**Perdu ?** Tapez `mh` seul : chaque étape des guides avec sa commande, la prochaine proposée ;
Entrée la lance. Plus : [`menu`](../commands/menu.md).

## 1. Auditer

<span class="mh-badge mh-safe">🔒 Photos intactes</span>

Trouvez les copies en double et les fichiers cassés :

```powershell
mh audit
```

![Un audit dans le terminal : 83 fichiers média analysés, 20 groupes de fichiers identiques, 32 copies en trop, 14,0 Mo à libérer, puis les dossiers partageant des fichiers identiques, chaque paire disant quel dossier garde ses copies](../images/terminal-audit.webp)

??? info "Détails"

    Rien n'est modifié : `mh` monte vos dossiers en lecture seule (`:ro`) pour toute commande qui
    ne les change pas. Le premier audit lit tout ; grâce au cache, les suivants prennent quelques
    secondes. La console résume ce qu'il a trouvé : copies en double, place qu'elles prennent,
    fichiers cassés. Plus : [votre premier audit](../start/01-first-audit.md), [garder le
    cache](../start/02-keep-the-cache.md).

## 2. Lire le rapport

<span class="mh-badge mh-safe">🔒 Photos intactes</span>

À la fin de l'audit, Ctrl+clic sur le chemin de `report.html` :

![Le haut d'un rapport d'audit : 85 fichiers média analysés, 32 copies en double dans 20 groupes, 14,0 Mo libérables, 3 fichiers cassés, puis Ce que vous pouvez faire (copies identiques, quasi-doublons, rafales, chacune avec Copier la commande), la ligne d'inventaire, le sommaire et comment on sait que ce sont des doublons](../images/report-top.webp)

Lisez-le dans cet ordre :

1. **Les paires de dossiers** : pour chacune, quel dossier garde ses copies. C'est la
   vérification la plus rapide.
2. **Les groupes de fichiers identiques** : chaque copie, et pourquoi celle-là est gardée.
3. **Les fichiers cassés et les fichiers compagnons orphelins** : une photo illisible, un `.xmp`
   ou un `.aae` dont la photo a disparu ([fichiers compagnons](../reference-sidecars.md)) ;
   `clean` les met aussi de côté.
4. **Les quasi-doublons et les rafales** : rien n'en est fait pour l'instant, ils viennent aux
   étapes 9 et 10.

??? info "Détails"

    Le rapport est fermé ? Ouvrez `index.html` dans `$HOME\media-hygiene\reports` : il liste tous
    les rapports. Chaque fichier, avec ce qui lui arrivera, est aussi dans `plan.csv`, à côté du
    rapport, à ouvrir dans Excel. Plus : [le rapport HTML](04-html-report.md).

## 3. Choisir la copie gardée

<span class="mh-badge mh-optional">Facultatif</span> <span class="mh-badge mh-safe">🔒 Photos intactes</span>

L'outil choisit seul la copie gardée de chaque groupe (un dossier choisi par vous plutôt qu'un
`DCIM`, l'original plutôt que `IMG_0001 (1).jpg`, la plus ancienne…). Pas d'accord pour **tout un
dossier** ? Dites-le, puis relisez le rapport :

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
fois pour toutes (étape 5).

??? question "Pas d'accord avec une seule paire ?"

    Dans le rapport, la liste *Votre décision* de cette paire propose *Inverser les dossiers* ou
    *Ne pas toucher*. Cliquez ensuite sur **Télécharger decisions.json** et enregistrez le
    fichier dans `$HOME\media-hygiene\reports`, à côté d'`index.html` : `mh clean --decisions`
    l'appliquera à l'étape 7.

    ![Le tableau des paires de dossiers : vignettes d'exemple, le dossier gardé avec la raison, le dossier qui perd ses copies avec un badge quand c'est entièrement une copie, le nombre de fichiers, la taille, et une liste Votre décision](../images/report-pairs.webp)

    Plus : [choisir la copie gardée](05-choose-the-kept-copy.md), [décider paire par
    paire](12-decide-pair-by-pair.md).

## 4. Seulement certains types de fichiers (facultatif)

<span class="mh-badge mh-optional">Facultatif</span> <span class="mh-badge mh-safe">🔒 Photos intactes</span>

Par défaut, l'audit regarde les photos, les images RAW et les vidéos. `--ext` restreint l'analyse
à quelques types, ou l'élargit à d'autres fichiers :

```powershell
mh audit --ext heic,video
```

??? info "Détails"

    `--ext video` ne regarde que les vidéos ; `--ext pdf` cherche aussi les PDF en double. Vos
    propres listes de types se nomment dans `[scan.categories]` de `config.toml`. Plus :
    [seulement certains types de fichiers](06-file-types.md).

## 5. Écrire vos choix une fois (facultatif)

<span class="mh-badge mh-optional">Facultatif</span> <span class="mh-badge mh-safe">🔒 Photos intactes</span>

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

??? info "Détails"

    Chaque réglage est expliqué dans le fichier lui-même. Relancez `mh config` : il affiche
    chaque réglage, d'où il vient (le fichier, une variable d'environnement, la ligne de
    commande, qui l'emporte) et l'état de chaque dossier monté. Plus : [le fichier de
    configuration](07-configuration-file.md).

## 6. Un second avis, avant de nettoyer (facultatif)

<span class="mh-badge mh-optional">Facultatif</span> <span class="mh-badge mh-safe">🔒 Photos intactes</span>

Avant de mettre de côté des photos de famille, vous voulez une preuve indépendante ? Czkawka, un
autre détecteur de doublons open source, vérifie les mêmes dossiers :

```powershell
mh crosscheck
```

??? info "Détails"

    Czkawka est livré dans l'image : `crosscheck` le lance sur vos dossiers (quelques minutes sur
    une grande collection la première fois), puis compare les deux résultats groupe par groupe et
    dit où ils diffèrent. Plus : [un second avis](13-second-opinion.md).

## 7. Mettre les doublons exacts de côté

<span class="mh-badge mh-undo">↩️ Annulable</span>

Déplacez les copies en trop, les fichiers illisibles et les fichiers compagnons orphelins en
quarantaine :

```powershell
mh clean
```

`clean` dit ce qu'il va faire et demande confirmation : répondez `o`. Un rapport de nettoyage dit
ensuite ce qui est arrivé à chaque fichier :

![Le haut d'un rapport de nettoyage : 85 fichiers média analysés, 32 copies en double dans 20 groupes, 16,4 Mo retirés de vos dossiers, 3 fichiers cassés, puis les paires de dossiers nettoyées](../images/clean-report.webp)

- Vous avez téléchargé `decisions.json` à l'étape 3 ? `mh clean --decisions`.
- Besoin de la place tout de suite ? `mh clean --delete` supprime les copies au lieu de les
  déplacer ; `undo` sait encore les reconstruire à partir de la copie gardée. Gardez-le pour
  quand vous aurez confiance.

??? info "Détails"

    Pour `clean`, `mh` monte vos dossiers en écriture (`clean` déplace des fichiers) et ajoute le
    journal et la quarantaine. `clean` refait l'audit avant d'agir. Rien ne va par-dessus un autre
    fichier, et chaque copie est d'abord comparée octet par octet à celle qui reste. Plus :
    [nettoyer](08-clean.md), [comment vos photos restent en sécurité](../reference-safety.md).

## 8. Vérifier, voir ce qui a été fait, annuler

<span class="mh-badge mh-safe">🔒 Photos intactes</span> <span class="mh-badge mh-undo">↩️ undo remet en place</span>

```powershell
explorer "$HOME\media-hygiene\quarantine"
mh history
```

La quarantaine reproduit vos dossiers, sous un dossier par nettoyage. Vous changez d'avis ?

```powershell
mh undo
```

Tout revient à sa place.

??? info "Détails"

    `history` liste chaque exécution : sa commande, les fichiers mis de côté ou supprimés, la
    place libérée, ce qui a été restauré. `mh undo <exécution>` annule une exécution plus
    ancienne, par le nom qu'en donne `history`. Plus : [annuler, historique,
    purge](09-undo-history-purge.md).

## 9. Les quasi-doublons (facultatif)

<span class="mh-badge mh-optional">Facultatif</span> <span class="mh-badge mh-undo">↩️ Annulable</span>

Les copies réduites ou recompressées (WhatsApp, e-mail…) et les vidéos réencodées : pas
identiques à l'original, elles attendent votre accord. Regardez-les dans le rapport de l'étape 2
(*Quasi-doublons*, *Vidéos réencodées*), puis déplacez les sûres :

```powershell
mh clean --tier near
```

Les autres, décidez-les une à une dans le navigateur, puis appliquez vos choix :

```powershell
mh review --near
mh clean --tier near --decisions
```

![La page de review --near : Groupe 1 sur 4, à vérifier et non décidé ; la photo de plage IMG_0104.jpg gardée en 1500 × 1000, encadrée en vert, sa copie WhatsApp de 800 × 533 en pointillés rouges ; au-dessus la ligne 💬 ; à gauche l'ordre (à vérifier d'abord), l'aide-mémoire du clavier et les trois paires de dossiers, Vacances à la mer → WhatsApp avec 2 groupes, chacune avec son bouton ✔ comme prévu](../images/review-near.webp)

??? info "Détails"

    *Sûr* veut dire : même image et même son, empreintes identiques, copie plus petite dans un
    dossier de messagerie ; `--tier near` dit combien de groupes à vérifier restent en place.
    `--tier near-all` les déplace tous sans demander. La plus haute résolution reste, tout part
    en quarantaine : `undo` si un groupe ne vous plaît pas. Plus : [les
    quasi-doublons](11-near-duplicates.md).

## 10. Les rafales (facultatif)

<span class="mh-badge mh-optional">Facultatif</span> <span class="mh-badge mh-undo">↩️ Annulable</span>

Les séries de photos prises à quelques secondes d'intervalle : choisissez lesquelles garder, dans
votre navigateur, au clavier.

```powershell
mh review
```

Ouvrez `http://127.0.0.1:8088/` (Ctrl+clic) :

![La page de tri : en-tête « Tri des rafales, Série 2 sur 3 », cinq photos d'anniversaire, quatre côte à côte et la cinquième en dessous, numérotées de 1 à 5 ; la première marquée la plus nette et encadrée en vert, la dernière floue avec une netteté de 30, encadrée en pointillés rouges et proposée à l'écart ; à gauche le sommaire et l'aide-mémoire du clavier](../images/review.webp)

**Ctrl+C** dans le terminal quand vous avez fini, puis mettez les photos écartées en quarantaine :

```powershell
mh clean --decisions
```

??? info "Détails"

    Les séries évidentes s'acceptent toutes d'un clic. Chaque choix est enregistré aussitôt dans
    `decisions.json`, dans votre dossier de rapports ; le `review` suivant reprend où vous en
    étiez. Le même `decisions.json` garde aussi vos paires de dossiers (étape 3) et vos
    quasi-doublons (étape 9) : un seul `mh clean --tier near --decisions` applique les trois.
    Plus : [trier les rafales dans le navigateur](10-review-bursts.md).

## 11. Libérer l'espace, pour de bon

<span class="mh-badge mh-final">⚠️ Pour de bon</span>

Jusqu'ici, rien n'est effacé : la quarantaine occupe toujours la place. Une fois que vous avez
vérifié :

```powershell
mh purge
```

Elle demande confirmation. Après `purge`, `undo` ne peut plus ramener ces fichiers.
`mh purge <exécution>` ne vide que la quarantaine de cette exécution.

## 12. Contrôler, et revenir plus tard

<span class="mh-badge mh-safe">🔒 Photos intactes</span>

`mh audit` à nouveau : il doit dire *Rien à nettoyer*. Ses quasi-doublons et rafales restants
sont ceux que vous avez choisi de garder. Les semaines suivantes :

- **Où en suis-je ?** `mh status` : le dernier audit, ce qui est en quarantaine et depuis quand,
  ce que `undo` peut encore restaurer, les décisions pas encore appliquées, puis la prochaine
  étape en commande complète.
- **De nouvelles photos ?** Reprenez à l'étape 1 : grâce au cache, seules les nouvelles sont lues.
- **Trop de rapports ?** `mh reports --prune 10` garde les dix plus récents et refait
  `index.html`.

Plus : [où en suis-je ?](09-undo-history-purge.md#où-en-suis-je--status), [lister et ranger
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
| [`menu`](../commands/menu.md) | 12 | Liste chaque étape avec sa commande ; Entrée lance la prochaine. |
| [`reports`](../commands/reports.md) | 12 | Liste les rapports, supprime les anciens. |

Les autres commandes ont leur propre parcours : pour donner à vos photos une arborescence bien
rangée, par année, événement, lieu ou personne (`classify`, `sort`, `album`) : **[trier en
bref](../sort/quick-guide.md)** ; pour retrouver une photo par un mot (« Chloé à la montagne » :
`people`, `tags`, `search`, `xmp`, `inventory`) : **[retrouver en bref](../find/quick-guide.md)**. Un mot vous échappe ? [Les mots de ce
guide](../reference-glossary.md). Un message d'erreur ? [Dépannage](../reference-troubleshooting.md).

??? note "Sans `mh` : les commandes complètes"

    Chaque commande `mh` est un `docker run` avec les mêmes dossiers. Pour celles qui ne
    modifient rien (`audit`, `config`, `crosscheck`, `history`, `status`, `reports`), en lecture
    seule :

    ```powershell
    docker run --rm -it `
      -v "C:\Photos:/data/c/Photos:ro" `
      -v media-hygiene-cache:/cache `
      -v "$HOME\media-hygiene\reports:/reports" `
      -v "$HOME\media-hygiene\config:/config" `
      cavo789/media-hygiene --locale fr audit
    ```

    Pour `clean`, `undo` et `purge` : `:ro` est retiré, `/journal` et `/quarantine` sont
    ajoutés ; remplacez `clean` par la commande de l'étape :

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
    quatre dossiers avant le premier lancement (`mkdir -Force "$HOME\media-hygiene\reports", …`) :
    un dossier que Docker crée lui-même appartient à l'administrateur, et l'outil ne pourrait pas
    y écrire.

---

[Documentation](../README.md) · Pas à pas : **[4. Le rapport HTML](04-html-report.md)** →
