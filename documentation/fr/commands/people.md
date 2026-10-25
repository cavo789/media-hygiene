# `people` : trouver les visages, regrouper ceux qui se ressemblent, les nommer

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `people` · 🇬🇧 [English](../../en/commands/people.md)

## En bref

**Retrouver les photos de quelqu'un par son nom, et les ranger selon qui y figure, sans qu'aucun
visage ne quitte votre ordinateur.**

`people` trouve les **visages** de vos photos, regroupe ceux qui se ressemblent (sans doute une
personne par groupe), et montre les groupes dans votre navigateur, les plus grands d'abord, où
vous les **nommez**. Ensuite, `search Chloé` trouve les photos de Chloé, et une règle `person`
de [`classify`](classify.md) les range. Les visages restent dans le [cache](../reference-glossary.md#cache), jamais envoyés nulle
part ; les noms vont dans votre `config.toml`.

**Quand** : après un audit lancé avec le cache, ou dans la foulée avec `audit --people` ; à
nouveau après de nouvelles photos : seules celles-là sont analysées.

**Essayer** :

```powershell
docker run --rm -it `
  -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene --locale fr people
```

## D'un coup d'œil

| | |
|---|---|
| Vos photos | 🔒 Jamais modifiées : montez-les en `:ro`. |
| Il faut | Vos dossiers, `/cache` (en écriture : les visages y sont gardés), `/config` (en écriture, pour enregistrer les noms) et `-p 127.0.0.1:8088:8088`. |
| Écrit | Les visages et les deux modèles de visages (39 Mo, une fois), dans le cache ; les noms, dans `config.toml` ; les photos mises de côté, dans `decisions.json` de `/reports`. |
| Annuler | `people --forget` supprime tous les visages du cache, puis demande si les noms partent aussi. |
| Avec `mh` | `mh people` : le port est publié pour vous. |

## Lancer

```powershell
docker run --rm -it -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene --locale fr people
```

Avec WSL ou Linux :

```bash
docker run --rm -it -p 127.0.0.1:8088:8088 \
  -v "/mnt/c/Photos:/data/c/Photos:ro" \
  -v media-hygiene-cache:/cache \
  -v "$HOME/media-hygiene/config:/config" \
  cavo789/media-hygiene --locale fr people
```

La première exécution télécharge les deux modèles de visages dans le cache, une fois. Chaque photo
est analysée une fois ; les exécutions suivantes n'analysent que les nouvelles. Il affiche ensuite
les groupes trouvés, les personnes déjà nommées et l'adresse de la page : un clic sur un visage
ouvre sa photo. Ctrl+C, ou fermer son onglet, l'arrête.

<!-- capture: people.txt|re:^✅| -->
```text
✅ 37 photos analysées : 12 visages, 0,04 s par photo.
✅ 17 visages dans 47 photos : 3 groupes de visages semblables, les plus grands
7, 5, 4 ; 1 vus une seule fois.
✅ Visages prêts, ouvrez http://127.0.0.1:8088/ dans votre navigateur pour les
nommer ; chaque nom est enregistré aussitôt dans config.toml. Ctrl+C l'arrête ;
les photos ne sont pas modifiées.
💡 La page ne s'ouvre pas ? docker run doit publier le même port des deux côtés,
avec -p 127.0.0.1:8088:8088.

✅ Page arrêtée ; rien n'a été modifié.
```

## Nommer les groupes

Dans la page, tapez un nom sur un groupe et appuyez sur Entrée : le nom est enregistré dans
`config.toml`, relu et affiché. `x` choisit plusieurs groupes à nommer d'un coup, × retire un
visage erroné, `i` ignore un groupe d'inconnus, Chaque personne s'affiche ensuite deux fois au plus : **Chloé ✓ vérifié**, les visages que
vous avez confirmés, et **Chloé attribué**, les visages qui lui sont donnés parce qu'ils leur
ressemblent ; `y` confirme les visages attribués affichés, qui passent dans vérifié. Les
exécutions suivantes gardent tous les noms, et [`search`](search.md) retrouve les personnes par
leur nom : `search Chloé montagne`, `search person:chloe`. Les noms suivent les photos que
[`sort`](sort.md) déplace (et qu'`undo` remet en place) ; `config.toml` est mis à jour la
prochaine fois que la page enregistre un nom. Chaque nom est une entrée
`[[people.person]]` de `config.toml`. Détails :
[Les personnes](../reference-people.md#nommer-les-groupes).

Chaque titre replie ou déplie sa section (cliquez-le, ou `o`). Les sections **vérifiées**, déjà
faites, arrivent repliées : une ligne avec le nom, ✓, les nombres et une bande de quelques
visages, pour que le travail restant vienne en premier ; leurs visages ne sont chargés que quand
vous les ouvrez. La page retient dans ce navigateur ce que vous avez replié, personne par
personne ; Entrée sur une section repliée l'ouvre, puis va à son champ de nom.

## Retirer toutes les photos de quelqu'un

Pour oublier quelqu'un (un ex, par exemple), retirez les photos où il apparaît depuis le groupe
lui-même :

1. Cliquez sur **et N visages de plus** : la page montre tous les visages du groupe, pas
   seulement les quelques dizaines de l'échantillon. Retirez avec × chaque visage d'une autre
   personne : sa photo reste.
2. Cliquez sur **Mettre de côté ses N photos**. Le bouton attend que tous les visages soient
   affichés. Chaque photo où cette personne apparaît part, avec d'autres ou non. Rien n'est
   supprimé depuis la page : le choix est enregistré aussitôt dans `decisions.json` de vos
   rapports (`/reports`, monté par `mh`), relu sur le disque et affiché avec son nombre et sa
   taille. Les photos mises de côté quittent alors la page : ni affichées, ni comptées, jamais
   confirmées avec les autres. Leur section dit *N photos mises de côté, masquées* :
   **Afficher** les remontre, estompées, chacune avec ↺ pour reprendre celle-là ; **Retirer de
   la mise de côté** les reprend toutes. Il en va de même des photos mises de côté depuis une
   autre page ([`search`](search.md), [`browse`](browse.md)), jusqu'à ce que `clean --decisions`
   les déplace.
3. Ouverte depuis la page d'accueil (`mh`), **Appliquer maintenant** ferme la page et lance
   [`clean --decisions`](clean.md), qui demande d'abord. Sinon, la commande le propose quand vous
   arrêtez la page. Il déplace les photos en quarantaine, journalisé ; [`undo`](undo.md) les
   remet, [`purge`](purge.md) libère la place.

**La page se souvient de la personne.** Mettre de côté les photos d'un groupe garde leurs
visages dans le cache, sans nom et sans les photos (rien ne va dans `config.toml`). À chaque
ouverture de la page, les photos qui ressemblent à cette personne viennent en premier, dans une
section à part : *N autres photos ressemblent à la personne mise de côté le <date>*, y compris
les visages d'aucun groupe (trop petits, trop flous, vus une seule fois). Elles sont montrées
pour que vous vérifiiez, jamais mises de côté toutes seules : retirez avec × les visages de
quelqu'un d'autre, puis **Mettre aussi ces N photos de côté**. Une photo ajoutée plus tard y
apparaît à l'ouverture suivante. Les visages restent après `clean` et `purge` ; reprendre les
photos (↺, **Retirer de la mise de côté**, ou `undo`) les oublie, et `people --forget` les
oublie avec tous les autres visages.

**Une photo à la fois.** Un visage que l'outil ne voit pas (de profil, flou, une photo penchée)
laisse sa photo dans la section de quelqu'un d'autre. Cliquez sur le visage : la grande vue
montre la photo avec **Mettre cette photo de côté** (ou la touche Suppr) ; Retour arrière la
reprend.

Le même `decisions.json` garde ce que [`search`](search.md#mettre-des-photos-de-côté) et
[`review`](review.md) ont mis de côté : un seul `clean --decisions` applique tout. Une photo
modifiée depuis votre choix reste en place.

## Depuis n'importe quelle page : mettre une personne de côté

Une photo montre quelqu'un que vous ne voulez plus voir, sur n'importe quelle page (`review`,
`browse`, `search`) : **👤 cette personne** sous une photo de `review`, ou **👤 Mettre une
personne de côté** dans la grande vue de `browse` et `search`, ouvre la page *Mettre une
personne de côté* dans un nouvel onglet, sur cette photo. Vous pouvez aussi l'ouvrir vous-même à
`/person` sur l'adresse de l'une de ces pages et y coller le chemin d'une photo
(`C:\Photos\…\IMG_1234.jpg`).

1. La page montre les visages trouvés sur cette photo par `audit --people` ; cliquez sur le bon
   (un visage seul est pris d'office).
2. À droite, les photos de cette personne, les plus ressemblantes d'abord, en grille à choisir
   comme dans [`browse`](browse.md) : clic, Ctrl, Maj, rectangle, Ctrl+A, I, Suppr, la grande vue
   et ses touches. Si elles ressemblent à quelqu'un mis de côté avant, la barre le dit (*la
   personne mise de côté le <date>*) : ce que vous mettez de côté maintenant rejoint cette
   personne.
3. Suppr (ou **Mettre de côté les fichiers choisis**) les enregistre aussitôt dans
   `decisions.json`, relu et affiché, et retient le visage, comme
   [plus haut](#retirer-toutes-les-photos-de-quelquun) : la page people montrera les photos qui
   lui ressemblent. Si la page qui la sert a été ouverte par `mh` depuis l'accueil,
   **Appliquer maintenant** dans la barre lance `clean --decisions` comme sur cette page.
4. Une photo de la grille montre la personne sous un autre angle ? Son **👤** (à côté de son nom,
   ou dans sa grande vue) rouvre la page sur cette photo, dans un nouvel onglet.

**Pas de visage sur la photo ?** Un visage penché, couché ou flou échappe souvent à l'audit, qui
regarde chaque photo droite. **Regarder encore, plus lentement** regarde cette seule photo
tournée (jusqu'à 90° de chaque côté) et moins exigeante ; ce qu'elle trouve est montré pour
choisir, jamais enregistré. Mesuré sur 9 vraies photos d'une même personne manquées par
l'audit : 6 retrouvées, 1 tout juste à la limite, 2 non (très floues). Quand rien n'est trouvé,
mettez la photo de côté toute seule (Suppr dans sa grande vue).

## Options

| Option | Rôle |
|---|---|
| `--path CHEMIN` | Seulement les photos sous ce dossier (chemin de l'hôte, tel que vous l'avez monté) ; à répéter pour plusieurs. |
| `--sample N` | Analyser N photos prises au hasard, afficher le temps par photo et l'estimation d'une exécution complète, puis s'arrêter. |
| `--forget` | Supprimer tous les visages du cache, puis montrer qu'il n'en reste aucun ; demande avant de supprimer aussi les noms de `config.toml`. |
| `--port PORT` | Port de la page, 8088 par défaut ; publiez le même. |

## Votre vie privée

Les nombres qui décrivent un visage sont des **données biométriques**. Ils restent dans le cache,
jamais dans vos photos ni dans les rapports ; la page est servie sur `127.0.0.1` seulement et
découpe les visages dans les photos à la demande, sans jamais les enregistrer. Le seul accès au
réseau est le téléchargement, une fois, des deux modèles depuis OpenCV Zoo, vérifiés par leur
SHA-256 : il n'envoie rien sur vos photos.

## Bon à savoir

- Les réglages `[people]` (`similarity`, `min_face`, `min_sharpness`) changent le regroupement,
  et les visages trop petits ou trop flous pour la page ne sont nommés nulle part (`search`,
  `classify`, XMP), sauf si vous les avez confirmés : rien n'est analysé à nouveau.
- `audit --people` cherche les visages juste après un audit, une fois que vous avez accepté le
  temps que ça prend ; `with_audit = true` dans `[people]` le fait à chaque audit.
- Les vidéos ne sont pas encore analysées.
- Sans réseau, l'erreur nomme les deux fichiers de modèle à enregistrer à la main dans le dossier
  `models` du cache.

## Pour aller plus loin

- [Retrouver en bref](../find/quick-guide.md)
- [Les personnes](../reference-people.md) : comment ça marche, nommer, les réglages, ce qui vient
  ensuite.
- [Trier, étape 10 : trier par personne](../sort/10-sort-by-person.md) : des groupes nommés aux
  dossiers triés.

## L'aide intégrée

<details>
<summary><code>people --help</code></summary>

<!-- capture: help-people.txt -->
```text
 Utilisation : media-hygiene people [OPTIONS]

 🔒 Lecture seule : ne modifie jamais vos photos. Trouver les visages des
 photos, regrouper ceux qui se ressemblent et les nommer dans votre navigateur.
 Visages gardés dans le cache, jamais envoyés nulle part.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --path            <str>               Seulement les photos sous ce dossier   │
│                                       (chemin de l'hôte, tel que vous l'avez │
│                                       monté) ; à répéter pour plusieurs. Par │
│                                       défaut : toutes les photos de l'index. │
│ --sample          <int range> [x>=0]  Analyser ce nombre de photos prises au │
│                                       hasard, afficher le temps par photo et │
│                                       l'estimation d'une exécution complète, │
│                                       puis s'arrêter.                        │
│ --forget                              Supprimer tous les visages du cache,   │
│                                       puis montrer qu'il n'en reste aucun ;  │
│                                       demande aussi avant d'effacer les noms │
│                                       de config.toml.                        │
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
