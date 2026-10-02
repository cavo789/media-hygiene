# Le classeur d'inventaire

[Documentation](README.md) › Référence · 🇬🇧 [English](../en/reference-inventory.md)

Un seul fichier Excel qui liste chaque photo, fichier RAW et vidéo que les audits ont vus, avec
tout ce qu'ils en ont appris : taille, dates, appareil, réglages, lieu, qualité, doublons. Triez-le
et filtrez-le pour répondre à vos propres questions : combien de photos par année ou par appareil,
quelles images sont floues ou minuscules, quel appareil avait son horloge mal réglée.

`inventory` lit le cache ([étape 2](start/02-keep-the-cache.md)) et rien d'autre : **aucun
fichier de vos dossiers n'est ouvert**, cela prend quelques secondes même pour des dizaines de
milliers de photos. Lancez d'abord un `audit`, avec le même cache.

## L'exporter

```powershell
docker run --rm -it `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene --locale fr inventory
```

Aucun dossier de photos n'est monté : aucun n'est nécessaire. Le classeur arrive dans un nouveau
dossier de votre dossier de rapports, `<date>-inventory\inventory.xlsx` ; la console dit où, et
quand chaque dossier a été audité en entier pour la dernière fois :

<!-- capture: inventory.txt -->
```text
✅ Inventaire de 82 fichiers écrit :
/reports/20261002-152703-inventory/inventory.xlsx
Dernier audit complet (UTC)
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┓
┃ Dossier          ┃ Date             ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━┩
│ C:\Photos        │ 2026-10-02 15:27 │
│ D:\Ancien disque │ 2026-10-02 15:27 │
└──────────────────┴──────────────────┘
```

L'inventaire est aussi frais que le dernier audit : une photo ajoutée depuis y manque, une photo
supprimée à la main y figure encore. Relancez un audit, puis exportez à nouveau.

## La feuille Fichiers

Une ligne par fichier, une ligne d'en-tête figée et un filtre sur chaque colonne. Les nombres
sont des nombres et les dates des dates : trier et filtrer fonctionnent quelle que soit la langue
d'Excel.

- **Où** : le fichier tel que vous le connaissez (`C:\Photos\…`), son dossier, son nom, son type
  (photo, RAW, vidéo), sa taille et sa date de modification (UTC).
- **Quand** : la date de prise de vue, lue comme `classify` la lit
  ([trier, étape 4](sort/04-classify.md)), son origine (EXIF ou les balises de la vidéo), son
  année, et le fuseau horaire que le fichier enregistre.
- **Avec quoi** : l'appareil, l'objectif, la focale, le temps d'exposition, l'ouverture, l'ISO,
  si le flash s'est déclenché ; le logiciel qui a écrit le fichier en dernier.
- **À quoi il ressemble** : largeur et hauteur, netteté, format, qualité JPEG estimée,
  luminosité moyenne et parts de pixels noir pur et blanc pur, les étoiles données dans Windows.
- **Où il a été pris** : latitude, longitude, altitude ; pour une vidéo, le lieu que ses balises
  contiennent.
- **Vidéos** : durée, codec, images par seconde, débit binaire.
- **État** : sain, non vérifié, ou pourquoi il ne peut pas être lu, avec le message du décodeur.
- **Doublons** : le SHA-256, le numéro de son groupe de fichiers identiques et le nombre de copies
  de ce groupe. Seuls les fichiers qui ressemblaient à un autre (même taille, mêmes premiers
  octets) ont un SHA-256 : les autres ne peuvent pas avoir de copie identique. Quelle copie
  `clean` garderait dépend de vos réglages : c'est le rôle du `plan.csv` du rapport
  ([étape 4](clean/04-html-report.md)).

Les fichiers RAW n'ont que leur taille, leurs dates et leur empreinte : leur contenu n'est pas
décodé. Les fichiers autres que photos et vidéos (`--ext pdf`, [étape 6](clean/06-file-types.md))
sont laissés de côté.

## La feuille Résumé

D'abord la date du dernier audit complet de chaque dossier, puis le nombre de fichiers par type,
année, appareil, format et état, avec et sans date, avec et sans GPS, et le nombre de fichiers qui
ont une copie identique.

## Étiquettes de qualité et d'exposition

Deux colonnes traduisent des mesures en mots, **au moment de l'export** : *Qualité* (flou, petit)
et *Exposition* (sombre, clair), ou *ok*. Leurs seuils sont dans `config.toml`
([étape 7](clean/07-configuration-file.md)) :

```toml
[inventory]
blurry_below = 100.0   # netteté en dessous : flou
small_below = 1000     # petit côté, en pixels, en dessous : petit
dark_below = 50.0      # luminosité moyenne (0 à 255) en dessous : sombre
bright_above = 205.0   # luminosité moyenne au-dessus : clair
clipped_above = 0.25   # plus que cette part de pixels noir (blanc) pur : sombre (clair)
```

Un ciel de nuit est sombre exprès : changez une valeur et exportez à nouveau, rien n'est relu.

## Un fichier CSV à la place

`inventory --format csv` écrit la feuille Fichiers seule, en `inventory.csv`, comme `plan.csv` :
en français, `;` entre les colonnes et une virgule décimale, pour qu'Excel l'ouvre tel quel.

Un texte qui commence par `=`, `+`, `-` ou `@` (un fichier nommé `-2019 voyage.jpg`) est écrit
précédé d'une apostrophe, `'-2019 voyage.jpg` : sinon Excel le calculerait et afficherait
`#NOM?`. Le classeur (`xlsx`) n'en a pas besoin : il garde ces noms tels quels.

## Le cache lui-même

Le cache est un fichier SQLite, `index.sqlite`, dans le volume `media-hygiene-cache`. Tout
navigateur SQLite l'ouvre, par exemple [DB Browser for SQLite](https://sqlitebrowser.org/) :
copiez-le d'abord hors du volume, et ouvrez la copie **en lecture seule**, pour que rien ne la
modifie par mégarde.

---

[Documentation](README.md) · [Commandes et options](reference-commands.md)
