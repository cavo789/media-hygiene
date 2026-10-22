# `share` : un album prêt à envoyer, un dossier et un zip

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `share` · 🇬🇧 [English](../../en/commands/share.md)

## En bref

**Les photos des vacances à la famille par mail, ou sur un réseau social, sans envoyer des
photos de 8 Mo qui disent où est la maison.**

`share` prend un [album](search.md#mettre-des-photos-dans-un-album) (une liste nommée de photos
de n'importe quels dossiers, faite dans `search`, `browse` ou la `review` des rafales) et fait une
copie de chaque photo, prête à envoyer : redressée, son grand côté ramené à 2048 pixels,
enregistrée en JPEG, et **sans sa position GPS**. La date, l'appareil et la description restent.
Les copies vont dans un dossier au nom de l'album, avec un zip de ce dossier à côté : joignez le
zip à un mail, ou ajoutez les photos du dossier à un album que vous créez sur votre réseau social,
ou copiez le dossier sur une clé USB. Aucun compte, aucun mot de passe : l'outil n'envoie rien
lui-même.

**Où le lancer** : dans la page d'accueil, l'espace **Partager** (hors du cycle, dans le menu de
gauche), l'étape *Préparer un album pour l'envoyer* ; ou le bouton **📨 Préparer pour l'envoi** à
côté de l'album dans `search` ou `browse`, qui donne la commande, copiée ; ou `mh menu`, sous
*Partager*.

**Quand** : une fois l'album fait, après un [`audit`](audit.md) (une photo de l'album déplacée
depuis est retrouvée par ce que l'audit a lu).

**Essayer** :

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/[cache](../reference-glossary.md#cache) `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  -v "$HOME\media-hygiene\Shares:/shares" `
  cavo789/media-hygiene share --album "Crète 2023"
```

## D'un coup d'œil

| | |
|---|---|
| Vos photos | 🔒 Seulement lues, jamais modifiées : montez-les en `:ro`. |
| Demande | `/reports` (les albums, `albums.json`), vos dossiers (pour lire les photos), `/shares` (où vont les copies) ; `/cache` pour retrouver une photo déplacée depuis. |
| Écrit | Dans `/shares` seulement : le dossier de l'album et son zip. Préparé à nouveau, l'album remplace son dossier et son zip. |
| Atteint | Rien hors de votre PC : l'outil n'envoie aucun mail et ne publie rien. |
| Avec `mh` | `mh share --album "Crète 2023"` : `mh` monte `$HOME\media-hygiene\Shares` pour cette commande seulement, puis l'ouvre dans l'Explorateur. |

## Lancer

Dans Windows PowerShell :

```powershell
mh share --album "Crète 2023"
```

La fenêtre dit ce qui est sur le disque une fois fini, relu depuis lui : combien de photos sont
prêtes, leur taille totale, où est le dossier (`C:\Users\<vous>\media-hygiene\Shares\Crète 2023`),
et le zip (`Crète 2023.zip`, à côté) avec sa taille. Puis l'Explorateur s'ouvre sur le dossier
`Shares` : le dossier de l'album et son zip côte à côte.

Ce que l'album contient mais pas le dossier est compté, jamais caché :

- **Les vidéos sont laissées de côté** : *3 vidéos non incluses*. Une vidéo seule peut dépasser ce
  qu'un mail accepte ; partagez une vidéo autrement (une clé USB, un espace partagé).
- Une photo de l'album introuvable (supprimée, ou en quarantaine) est comptée comme manquante.
- Une photo illisible (abîmée) est comptée aussi.

Préparé à nouveau (après avoir ajouté des photos à l'album), l'album **remplace** son dossier et
son zip ; la fenêtre le dit en une ligne. Le dossier est d'abord fait à part : arrêté en route
(Ctrl+C), le dossier précédent reste tel quel.

### La taille du zip

Au-delà de **25 Mo**, la fenêtre vous prévient : certains webmails refusent une pièce jointe
aussi grande. La limite dépend de votre messagerie : vérifiez la sienne. Mesuré ici sur des
photos synthétiques de 12 mégapixels, une copie pèse de 0,3 à 0,8 Mo, soit environ 30 à 80 photos
pour 25 Mo (estimé ; de vraies photos peuvent différer). Au-delà de la limite, envoyez le dossier
autrement, ou faites un album de moins de photos.

## La position GPS

Une photo prise au téléphone contient en général l'endroit où elle a été prise, à quelques mètres
près : partagées telles quelles, les photos du jardin disent où est la maison. `share` **retire la
position** de chaque copie par défaut, et la fenêtre le dit. Vos photos d'origine gardent la leur :
seules les copies la perdent. Pour la garder (des photos de vacances envoyées à la famille, les
lieux étant le sujet) :

```powershell
mh share --album "Crète 2023" --keep-gps
```

Les notes du fabricant (un bloc propre à chaque marque d'appareil, qui peut contenir son numéro de
série) et le bloc XMP ne sont jamais copiés non plus.

## Réglages

Dans `config.toml`, `[share]` :

| Clé | Par défaut | Ce qu'elle fait |
|---|---|---|
| `long_side_px` | `2048` | Le grand côté de chaque copie, en pixels (320 à 8192). Une photo plus petite n'est jamais agrandie. |
| `quality` | `85` | La qualité JPEG des copies (30 à 95). |
| `keep_gps` | `false` | Garder la position GPS dans les copies, à chaque fois ; `--keep-gps` le fait pour une fois. |

## Options

| Option | Ce qu'elle fait |
|---|---|
| `--album "Crète 2023"` | L'album à envoyer, fait dans `search`, `browse` ou la revue des rafales. |
| `--keep-gps` | Garder la position GPS dans les copies, pour cette fois. |

## Bon à savoir

- Les copies portent le nom des photos (`IMG_1234.jpg`) ; deux photos du même nom venant de deux
  dossiers deviennent `IMG_1234.jpg` et `IMG_1234_1.jpg`. Une photo HEIC ou RAW donne un JPEG (un
  fichier RAW, l'aperçu qu'il contient, sans son EXIF).
- Le dossier est toujours `<votre dossier personnel>\media-hygiene\Shares` : aucun dossier à
  taper, et aucun dossier de photos n'est jamais ouvert en écriture. Supprimez ce que vous avez
  envoyé une fois envoyé : l'album lui-même (`albums.json`) reste.
- `albums.json` et la commande [`album`](album.md) sont deux choses : celle-ci fait un dossier de
  seconds noms (liens physiques) depuis le plan de classify.

## Pour aller plus loin

- [`search` : mettre des photos dans un album](search.md#mettre-des-photos-dans-un-album)
- [`slideshow` : l'album sur la télé](slideshow.md)
- [`home` : l'album sur votre téléphone, à la maison](home.md#vos-albums-sur-le-téléphone)

## L'aide intégrée

<details>
<summary><code>share --help</code></summary>

<!-- capture: help-share.txt -->
```text
 Utilisation : media-hygiene share [OPTIONS]

 🔒 Lecture seule : ne modifie jamais vos photos. Préparer un album pour
 l'envoyer : des copies réduites sans la position GPS, un dossier et un zip,
 pour un mail ou un réseau social.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ *  --album             <str>  L'album à envoyer, fait dans search, browse ou │
│                               la revue des rafales : "Crète 2023".           │
│                               [required]                                     │
│    --keep-gps                 Garder la position GPS dans les copies ;       │
│                               retirée par défaut, une photo envoyée ne doit  │
│                               pas dire où est la maison.                     │
│    --help      -h             Affiche ce message et quitte.                  │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
