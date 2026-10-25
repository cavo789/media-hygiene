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
mh classify
```

<details>
<summary>Sans <code>mh</code> : la commande complète</summary>

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene --locale fr classify
```

</details>

Après un audit avec [le cache](../start/02-keep-the-cache.md), rien n'est relu : les dates, les
appareils et les lieux viennent du cache, et les empreintes de l'audit disent quels doublons sont
encore là. Le dossier de rapports reçoit le classeur où vous corrigez la proposition
([étape 5](05-review-the-proposal.md)).

<!-- capture: classify.txt -->
```text
🔒 Lecture seule : vos photos et vidéos ne sont pas touchées.
─────────────────────────────────── Classer ────────────────────────────────────
24 dossiers inchangés repris de l'index, 0 relus.
💡 Une photo modifiée sur place par un autre programme ? 'audit --full' relit
tous les dossiers (c'est fait de toute façon pour ceux listés il y a 7 jours).

Déjà à leur place : 43 sur 86 (50 %).
Proposition
┏━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Bande     ┃ Fichiers ┃ À déplacer ┃
┡━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━┩
│ Sûrs      │       77 │         34 │
│ À trier   │        5 │          5 │
│ Sans date │        4 │          4 │
└───────────┴──────────┴────────────┘

Pourquoi
┌───────────────────────────────┬────┐
│ Dossiers existants            │ 76 │
│ Aucun indice                  │  5 │
│ Sans date                     │  4 │
│ Captures d'écran et documents │  1 │
└───────────────────────────────┴────┘

Catégories les plus remplies
┌─────────────────────┬────┐
│ Vacances à la mer   │ 13 │
│ Photos 2019         │ 12 │
│ Randonnée           │ 10 │
│ Anniversaire        │  8 │
│ Ancien téléphone    │  8 │
│ Noël                │  6 │
│ Lac                 │  6 │
│ Téléphone           │  6 │
│ Noël 2020           │  4 │
│ WhatsApp            │  3 │
└─────────────────────┴────┘

⚠️  Règles qui n'ont rien décidé : Films et séries, Voisins d'événement, Noël,
Nouvel An, Saint-Nicolas.
💡 Vérifiez leurs dates, leurs expressions et leur ordre dans config.toml.
À vérifier ou à trier : 5 fichiers dans 1 événement.
💡 Rien n'a été modifié : 'classify' ne fait que proposer.
✅ Classeur à modifier :
C:\Users\you\media-hygiene\reports\20261025-084855-classify\classify.xlsx
✅ Rapport avec les photos :
C:\Users\you\media-hygiene\reports\20261025-084855-classify\report.html
👉 Et maintenant : modifiez les cellules jaunes et enregistrez ; rien ne bouge
avant 'sort'.
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v "D:\Ancien disque:/data/d/Ancien disque" `
  -v "$HOME\media-hygiene\config:/config" `
  -v "media-hygiene-cache:/cache" `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene --locale fr sort
💡 32 doublons exacts sont encore là : lancez d'abord 'clean', sinon les deux
copies sont triées.
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

**Une photo gardée dans un dossier générique après un nettoyage.** Quand
[`clean`](../clean/08-clean.md) a retiré une copie, la photo gardée se souvient du dossier de
cette copie. Une photo dont les dossiers ne disent rien (`DCIM`, `Camera`) lit ce dossier comme
si elle s'y trouvait : sa copie dans `Mariage Julie 2015` la range dans `Mariage Julie 2015`,
une copie dans `2017/Durbuy` nomme la ville. Ses propres dossiers passent toujours d'abord. Deux
copies retirées dans des dossiers qui ne s'accordent pas (`Mariage Julie`, `Noël`) : aucun
n'est utilisé, et la photo vous attend dans *À trier*. Le *pourquoi* du classeur dit d'où vient
l'indice : `(le dossier d'une copie retirée : D:\Backup\Mariage Julie 2015)`.

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
([étape 7 du nettoyage](../clean/07-configuration-file.md)), et chaque valeur y est un exemple à remplacer :

- `--layout "{year}/{month}"` : trier par mois, sans aucune catégorie.
- `--target 'D:\Photos triées'` : construire l'arborescence ailleurs (le dossier doit être
  monté) ; par défaut, chaque dossier monté est réorganisé sur place.
- `--year 2016`, ou `--year 2015-2017` : une année à la fois, une soirée à la fois. Les
  fichiers datés seulement par le disque attendent un classify sans `--year` : ils vont dans
  `À trier/Sans date` quelle que soit leur année.
- `--leave 'C:\Photos\Albums'` : un dossier jamais trié, toujours analysé et nettoyé.

Les modèles acceptent `{year}`, `{quarter}`, `{month}`, `{month_name}`, `{day}`, `{category}`,
`{event}` et `{event_start}`. Un modèle vide laisse les fichiers où ils sont.

Les catégories viennent de règles que vous ordonnez et complétez : vos dossiers, vos voyages, vos
anniversaires, Noël, les captures d'écran ([étape 6](06-write-down-what-you-know.md)).

---

← [3. Plusieurs dossiers et disques](../start/03-several-folders.md) · [Documentation](../README.md) · Suivant : **[5. Revoir la proposition](05-review-the-proposal.md)** →
