# 4. Proposer une arborescence rangée : `classify`

[Documentation](../README.md) › Trier, étape 4 · 🇬🇧 [English](../../en/sort/04-classify.md)

Les étapes 1 à 3 ont montré ce que contiennent vos dossiers. `classify` va un pas plus loin :
pour chaque photo et chaque vidéo, il propose une place dans une arborescence rangée,
`année/catégorie` par défaut. Il **ne fait que proposer** : rien ne bouge, et les dossiers montés
en `:ro` conviennent.

> 💡 Nettoyez d'abord les doublons ([le guide Nettoyer](../README.md#nettoyer-les-doublons)) :
> sinon les deux copies d'une photo sont triées, et l'une d'elles est renommée.

## Le lancer

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene --locale fr classify
```

Après un audit avec [le cache](../start/02-keep-the-cache.md), rien n'est relu : les dates, les
appareils et les lieux viennent du cache, et les empreintes de l'audit disent quels doublons sont
encore là. Le dossier de rapports reçoit le classeur où vous corrigez la proposition
([étape 5](05-review-the-proposal.md)).

<!-- capture: classify.txt -->
```text
─────────────────────────────────── Classer ────────────────────────────────────
Déjà à leur place : 43 sur 80 (54 %).
Proposition
┏━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Bande     ┃ Fichiers ┃ À déplacer ┃
┡━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━┩
│ Sûrs      │       74 │         31 │
│ À trier   │        3 │          3 │
│ Sans date │        3 │          3 │
└───────────┴──────────┴────────────┘

Pourquoi
┌─────────────────────┬────┐
│ Dossiers existants  │ 74 │
│ no-signal           │  3 │
│ undated             │  3 │
│   Vacances à la mer │ 13 │
│   Photos 2019       │ 12 │
│   Randonnée         │ 10 │
│   Anniversaire      │  8 │
│   Ancien téléphone  │  8 │
│   Noël              │  6 │
│   Lac               │  6 │
│   Téléphone         │  6 │
│   Noël 2020         │  4 │
│   WhatsApp          │  1 │
└─────────────────────┴────┘

⚠️  Règles qui n'ont rien décidé : Films et séries, Captures d'écran et
documents, Voisins d'événement, Noël, Nouvel An, Saint-Nicolas.
💡 Vérifiez leurs dates, leurs expressions et leur ordre dans config.toml.
À vérifier ou à trier : 3 fichiers dans 1 événement.
💡 32 doublons exacts sont encore là : lancez d'abord 'clean', sinon les deux
copies sont triées.
💡 Rien n'a été modifié : 'classify' ne fait que proposer.
✅ Classeur à modifier : /reports/20260930-191220-classify/classify.xlsx
✅ Rapport avec les photos : /reports/20260930-191220-classify/report.html
💡 Modifiez les cellules jaunes et enregistrez : rien ne bouge avant 'sort'.
```

## Lire le résultat

*Déjà à leur place* compte les fichiers qui sont déjà là où la proposition les veut. Après
quelques tris, c'est l'avancement de votre collection.

*Proposition* donne les fichiers de chaque bande, et combien seraient déplacés :

- **Sûrs** : un nom de dossier que vous avez choisi (`2019/Vacances à la mer` reste
  `2019/Vacances à la mer`), ou une date fiable quand le modèle n'a pas besoin de catégorie. Ils
  vont dans `année/catégorie`.
- **À vérifier** : une supposition dont l'outil n'est pas sûr, par exemple une photo dont la date
  contredit son dossier. Elles sont regroupées dans `année/À vérifier/catégorie` : regardez-les
  dans le rapport, et confirmez-les dans le classeur ([étape 5](05-review-the-proposal.md)).
- **À trier** : rien ne dit où elles vont. Elles sont regroupées dans `année/À trier/<événement>`,
  un dossier par événement (des photos prises à peu d'intervalle, d'un dossier ou d'un téléphone
  à l'autre), pour que vous nommiez un événement une seule fois : dans le classeur, nommez
  l'événement `2016-07-14` `Kermesse`, et ses fichiers vont dans `2016/Kermesse`.
- **Sans date** : seule la date du fichier sur le disque est connue, qui dit quand il a été copié,
  pas quand la photo a été prise. Ils vont dans `À trier/Sans date`, ou dans
  `À trier/Reçues et téléchargées` quand aucun appareil ne les a prises (des images reçues dans
  une messagerie).
- **Laissés tels quels** : vos dossiers protégés et ceux que vous avez demandé de ne pas trier.

*Pourquoi* donne la règle (ou la raison) de chaque proposition, puis les catégories les plus trouvées.

## D'où viennent les dates

La première source fiable l'emporte : la date écrite par l'appareil (EXIF), les balises d'une
vidéo (son heure UTC ramenée à votre heure locale : une vidéo du réveillon reste dans son année),
le nom du fichier (`IMG_20210712_…`, les noms WhatsApp), le dossier (`2016`, `Juillet 2016`), et
en dernier la date sur le disque. Un appareil dont l'horloge n'a jamais été réglée est repéré :
les dates de ses dossiers l'emportent.

Un événement garde l'année de son début, et un dossier que vous avez nommé garde l'année de sa
photo la plus ancienne : une fête du Nouvel An n'est pas coupée en deux.

## Votre propre structure

Tout est dans la section `[classify]` de `config.toml`
([étape 7](../clean/07-configuration-file.md)), et chaque valeur y est un exemple à remplacer :

- `--layout "{year}/{month}"` : trier par mois, sans aucune catégorie.
- `--target 'D:\Photos triées'` : construire l'arborescence ailleurs (le dossier doit être
  monté) ; par défaut, chaque dossier monté est réorganisé sur place.
- `--year 2016`, ou `--year 2015-2017` : une année à la fois, une soirée à la fois.
- `--leave 'C:\Photos\Albums'` : un dossier jamais trié, toujours analysé et nettoyé.

Les modèles acceptent `{year}`, `{quarter}`, `{month}`, `{month_name}`, `{day}`, `{category}`,
`{event}` et `{event_start}`. Un modèle vide laisse les fichiers où ils sont.

Les catégories viennent de règles que vous ordonnez et complétez : vos dossiers, vos voyages, vos
anniversaires, Noël, les captures d'écran ([étape 6](06-write-down-what-you-know.md)).

---

← [3. Plusieurs dossiers et disques](../start/03-several-folders.md) · [Documentation](../README.md) · Suivant : **[5. Revoir la proposition](05-review-the-proposal.md)** →
