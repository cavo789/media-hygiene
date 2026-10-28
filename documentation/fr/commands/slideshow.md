# `slideshow` : vos photos sur la télé, le téléphone comme télécommande

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `slideshow` · 🇬🇧 [English](../../en/commands/slideshow.md)

## En bref

**Les photos des vacances sur la télé du salon, la famille dans le canapé, la photo suivante
choisie depuis le téléphone.**

`slideshow` sert deux pages depuis votre PC. L'**écran**, ouvert une fois dans le navigateur de la
télé (ou d'un Chromecast branché dessus) : noir, une photo à la fois, ajustée à l'écran, jamais un
nom de fichier. La **télécommande**, sur votre téléphone : les vignettes de la sélection, ◀ et ▶,
lecture et pause avec le temps que reste chaque photo, **Ne pas montrer** pour en passer une ce
soir, et une vignette touchée montre cette photo sur la télé. Les vidéos de la sélection passent
aussi, telles quelles. Le PC tient le diaporama : une télé rechargée ou un téléphone mis en veille
ne perd rien.

**Où le lancer** : dans la page d'accueil, l'espace **Partager** (hors du cycle, dans le menu de
gauche), ou `mh menu`, sous *Partager*.

**Quand** : après un [`audit`](audit.md) : il montre ce que l'audit a lu. Une recherche demande
d'abord [`tags`](tags.md).

**Essayer** (sur le PC seulement ; pour la télé, voyez [Lancer](#lancer)) :

```powershell
docker run --rm -it `
  -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/[cache](../reference-glossary.md#cache) `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene slideshow --folder "C:\Photos\Vacances 2026"
```

## D'un coup d'œil

| | |
|---|---|
| Vos photos | 🔒 Jamais modifiées : montez-les en `:ro`. |
| Demande | `/cache` (les fichiers du dernier audit), vos dossiers (pour montrer les photos), le port de la page ; `/reports` pour `--album`. |
| Écrit | Les images de la télé et les vignettes du téléphone, dans le cache. Rien d'autre : le diaporama vit en mémoire. |
| Atteint | Le PC seulement ; avec `--lan`, la télé et les téléphones de votre réseau de la maison, jamais Internet. |
| Avec `mh` | `mh slideshow --folder "C:\Photos\Vacances 2026" --lan`. |

## Lancer

Dans Windows PowerShell, sur le PC :

```powershell
mh slideshow --folder "C:\Photos\Vacances 2026" --lan
```

`--lan` ouvre le diaporama à votre réseau de la maison pour ce lancement seulement, comme
[`mh --lan`](home.md#depuis-un-téléphone-du-wi-fi-de-la-maison--mh---lan) le fait pour la page d'accueil : la fenêtre donne l'adresse de l'écran, et
l'adresse et le code du téléphone ; le navigateur du PC ouvre la télécommande avec les mêmes
lignes et un QR code. Windows peut demander si Docker Desktop peut accepter des connexions :
autorisez-le sur les réseaux **privés** seulement. Sans `--lan`, seul le PC peut ouvrir le
diaporama (utile pour l'essayer, ou pour le plan B ci-dessous).

Au lieu d'un dossier : `--search "noel 2025"` (les photos que trouve une [`search`](search.md)) ou
`--album "Crète 2023"` (un [album](search.md#mettre-des-photos-dans-un-album) fait dans `search`,
[`browse`](browse.md) ou le tri des rafales [`review`](review.md) : des photos de plusieurs
dossiers ; son bouton **📺 Partager sur la télé** donne cette commande, copiée). `--chosen` n'existe
plus : il montrait les fichiers mis de côté, promis à la quarantaine ; donné, il dit d'utiliser
`--album`. Depuis la
[page d'accueil](home.md) ouverte par `mh --lan`, l'étape *Montrer vos photos sur la télé* demande
le dossier et ouvre le diaporama de la même façon ; *Montrer un album sur la télé* demande le nom de
l'album et ouvre le diaporama **dans le serveur même de la page d'accueil** : la page d'accueil
continue, la télécommande s'ouvre aussitôt (`/slideshow/`). Un téléphone appairé le lance aussi,
depuis le canapé : sur la page d'accueil du téléphone, **Montrer un album sur la télé** liste les
albums enregistrés sur le PC ; un appui ouvre aussitôt la télécommande (sans code). La télé, à son
favori, attend un diaporama tant qu'aucun ne tourne et l'affiche d'elle-même ; elle est appairée
une fois (son code tapé sur la télécommande) et **le reste tant que `mh` tourne** : un autre album
lui arrive sans nouveau code. Aucun album enregistré : le téléphone dit d'en faire un sur le PC.

### Sur la télé, une fois

1. **Un Chromecast avec Google TV** (conseillé : plus rapide que le navigateur d'une télé de
   2012) : installez-y une application de navigateur web, ouvrez-la.
   **Le navigateur de la télé** (sur une Samsung *Smart Hub* : l'application **Internet**)
   fonctionne aussi, plus lentement, et ne montre que les photos : les vidéos demandent le
   navigateur du Chromecast.
2. Tapez l'adresse que donne la fenêtre, par exemple `http://192.168.1.20:8089/screen` (port **8089** :
   la télécommande du téléphone est sur 8088, en `https`). C'est du `http` simple, sur votre
   réseau de la maison : une télé ne peut pas installer le certificat du PC, et rien ne part sur
   Internet. Cette adresse ne sert que les pages de la télé, jamais la télécommande.
3. **Mettez-la en favori** : la fois suivante, le favori suffit (voyez
   [Une adresse stable](#une-adresse-stable)).
4. La télé affiche un code de six chiffres. Sur la télécommande du téléphone, tapez-le dans
   **Le code qu'affiche la télé**, puis **Appairer la télé** : la première photo apparaît. La
   télé reste appairée jusqu'à l'arrêt du diaporama ; quand le diaporama tourne dans la page
   d'accueil (un album lancé depuis elle), jusqu'à l'arrêt de `mh`.
5. Appuyez sur **OK** sur la télécommande de la télé (ou cliquez) pour le plein écran.

Taper un code avec la télécommande d'une télé est pénible : ici la télé en affiche seulement un,
le téléphone le tape.

### Sur le téléphone

Ouvrez l'adresse que donne la fenêtre, en `https`, par exemple `https://192.168.1.20:8088/` (ou
scannez le QR code de la page du PC) et tapez le code de huit chiffres : la télécommande s'ouvre,
et le téléphone est appairé pour de bon, comme sur la page d'accueil.
Un téléphone déjà appairé sur la [page d'accueil](home.md#depuis-un-téléphone-du-wi-fi-de-la-maison--mh---lan)
l'ouvre sans code, depuis son navigateur ou l'application installée. Un téléphone qui dit que la
connexion n'est pas privée installe d'abord le certificat du PC, une fois : la fenêtre dit où
(`http://192.168.1.20:8089/phone`), les étapes sont celles de la
[page d'accueil](home.md#une-fois-par-téléphone--installer-le-certificat). Ensuite :

- **◀** et **▶** : les photos précédente et suivante ; **▶ Lecture** / **❚❚ Pause**, et
  **Chaque photo** : combien de temps une photo reste pendant la lecture.
- Une vignette touchée montre cette photo sur la télé.
- **Ne pas montrer** retire du diaporama la photo sur la télé (la télé passe à la suivante) ; le
  bouton d'une vignette fait de même pour n'importe quelle photo, et **Remontrer** la remet.
- La vignette d'une vidéo est marquée **▶**. Sur la télé, elle passe jusqu'au bout, puis le
  diaporama continue ; **❚❚ Pause** la met en pause aussi. Une vidéo que la télé ne sait pas lire
  est signalée sous sa vignette (*Pas sur la télé : son format (hevc) n'y est pas lu.*) et passée.
- **Le nom de l'événement** : à chaque nouvel événement (un nouveau dossier, dans l'ordre du
  diaporama), la télé montre un carton titre pendant 3 secondes (une de ses photos floutée, le
  nom en grand, le mois et le lieu dessous), puis un bandeau sur sa première photo quelques
  secondes. Le nom est celui du dossier (`2026\2026-10\Promenade à Valkenburg` → *Promenade à
  Valkenburg* : années, mois, dates et dossiers d'appareil sont sautés) ; le mois vient de la
  date de prise de vue ; le lieu est l'un des vôtres (`places`), sinon la ville la plus proche
  de leur GPS, trouvée hors ligne (avec son pays s'il n'est pas le vôtre, p. ex. *Valkenburg,
  Pays-Bas* : le pays du lieu marqué `home`, sinon de votre premier lieu, sinon celui où la
  plupart des photos ont été prises). Une touche choisit où il est annoncé : **TV et téléphone**
  (par défaut), **Téléphone seul** (sous les commandes ; les notes du conteur s'ouvrent alors d'elles-mêmes),
  **Nulle part**.
- **Les notes du conteur** (à déplier sous les commandes) : pendant que la famille regarde la
  télé, le téléphone montre en plus grand la photo affichée, son jour et son heure, l'événement
  et son lieu, sa description et ses mots (quand `describe` en a donné), la photo suivante, et
  un petit dessin des endroits où les photos de l'événement ont été prises (le point rouge :
  celle-ci), sur les noms des villes et villages proches (lus dans les villes intégrées à
  l'outil : rien ne part sur internet). Si vous réglez `[places] tiles` dans `config.toml` (la
  carte de [`places`](places.md)), de vraies tuiles de carte sont dessinées sous les points à la
  place : le navigateur du téléphone les télécharge, le serveur de tuiles voit donc la zone
  regardée (jamais une photo). Trois boutons : **Pause,
  je raconte**, **Retour au début de cet événement**, **Événement suivant**. Ils ne font que
  déplacer le diaporama : rien n'est modifié sur le PC.

La télé charge la photo suivante à l'avance, derrière celle affichée, et les échange une fois
décodée : vous ne voyez jamais une photo dessinée par bandes.

Ctrl+C dans la fenêtre PowerShell arrête le diaporama ; la télé garde sa dernière photo.

## Une adresse stable

Le favori de la télé nomme l'adresse du PC sur votre réseau de la maison et le port. Le port est
fixe (`[review] port`, 8088 ; celui de la télé, 8089). L'adresse est donnée par votre box, et peut changer avec le temps :
dans la page de la box, **réservez** l'adresse du PC (souvent *DHCP › Bail statique* ou
*Réservation d'adresse*, par l'adresse MAC du PC). L'outil ne le fait pas pour vous.

## Plan B : caster un onglet

Si ni le navigateur du Chromecast ni celui de la télé n'ouvrent l'écran : lancez sans `--lan`,
ouvrez `http://127.0.0.1:8088/screen` dans Chrome ou Edge sur le PC, puis **Caster** cet onglet
vers le Chromecast depuis le menu du navigateur. La télécommande fonctionne alors sur le PC
lui-même, à `http://127.0.0.1:8088/`.

## Réglages

Dans `config.toml`, `[slideshow]` :

| Clé | Par défaut | Ce qu'elle fait |
|---|---|---|
| `screen_px` | `1920` | La largeur des images de la télé : chaque photo est ajustée à `screen_px` × 9/16 de cela (1920 × 1080). `3840` pour une télé 4K ; plus petit se charge plus vite sur une vieille télé. |
| `interval_seconds` | `8` | Combien de temps une photo reste pendant la lecture (2 à 600) ; le téléphone le change pour la soirée. |

Le port est `[review] port`, celui de toutes les pages.

## Options

| Option | Ce qu'elle fait |
|---|---|
| `--folder "C:\…"` | Les photos de ce dossier et de ses sous-dossiers, tel que l'Explorateur le montre. |
| `--search "mots"` | Les photos que trouve une recherche, tapée comme dans [`search`](search.md). |
| `--album "Crète 2023"` | Un album fait dans `search`, `browse` ou le tri des rafales ; ses fichiers manquants (supprimés, en quarantaine) sont comptés, pas montrés. |
| `--port PORT` | Port de la page, 8088 par défaut ; publiez le même. |
| `--lan` (`mh` seulement) | Ouvre le diaporama à la télé et aux téléphones de votre réseau de la maison, pour ce lancement (Windows PowerShell). |

## Bon à savoir

- Les vidéos passent telles quelles, jamais converties : H.264 (la plupart des vidéos de
  téléphone), VP8 et VP9, en `.mp4`, `.m4v`, `.mov` ou `.webm`. Les autres (HEVC, un `.avi`…) sont
  passées : les convertir prendrait des minutes par vidéo pour une poignée de fichiers (4 sur
  environ 1 200 dans une collection mesurée). Le codec est celui que le dernier audit a lu ; le
  navigateur d'une télé de 2012 ne montre que les photos.
- Les plus anciennes d'abord, par date de prise de vue de la photo ou de la vidéo ; celles sans date
  à la fin. Au plus 3 000 fichiers : les premiers par date.
- La télé reçoit chaque photo redressée, à la taille de son écran (300 à 500 Ko, estimé), faite
  une fois et gardée dans le cache avec les autres aperçus.
- Seuls les fichiers du diaporama sont servis : une télé ou un téléphone n'atteint jamais un autre
  fichier de votre photothèque, ni l'original d'une photo (une vidéo est envoyée telle quelle).
- Un téléphone appairé par le code peut piloter le diaporama ; une télé appairée par son code peut
  seulement le montrer. Trop de codes erronés ferment l'appairage jusqu'au prochain lancement.

## Aller plus loin

- [`home` : la page d'accueil, et `mh --lan`](home.md)
- [Retrouver en bref](../find/quick-guide.md)
- [`share` : l'album prêt à envoyer par mail](share.md)

## L'aide intégrée

<details>
<summary><code>slideshow --help</code></summary>

<!-- capture: help-slideshow.txt -->
```text
 Utilisation : media-hygiene slideshow [OPTIONS]

 🔒 Lecture seule : ne modifie jamais vos photos. Montrer des photos sur la
 télé, le téléphone choisissant la suivante : un dossier, une recherche ou un
 album.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --folder          <str>               Montrer les photos de ce dossier et de │
│                                       ses sous-dossiers, tel que             │
│                                       l'Explorateur le montre :              │
│                                       "C:\Photos\Vacances 2026".             │
│ --search          <str>               Montrer les photos que trouve une      │
│                                       recherche, tapée comme dans search :   │
│                                       "noel 2025".                           │
│ --album           <str>               Montrer un album, fait dans search,    │
│                                       browse ou le tri des rafales : "Crète  │
│                                       2023".                                 │
│ --port            <int range> [x>=1]  Port de la page. docker run le publie  │
│                                       sous le même numéro sur votre          │
│                                       ordinateur, par exemple -p             │
│                                       127.0.0.1:9000:9000 pour --port 9000.  │
│                                       Par défaut :  port dans config.toml,   │
│                                       8088.                                  │
│ --help    -h                          Affiche ce message et quitte.          │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
