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
| Écrit | Les visages et les deux modèles de visages (39 Mo, une fois), dans le cache ; les noms, dans `config.toml`. |
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
✅ 37 photos analysées : 15 visages, 0,04 s par photo.
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
visage erroné, `i` ignore un groupe d'inconnus, `y` confirme une suggestion (« Chloé ? »). Les
exécutions suivantes gardent tous les noms, et [`search`](search.md) retrouve les personnes par
leur nom : `search Chloé montagne`, `search person:chloe`. Les noms suivent les photos que
[`sort`](sort.md) déplace (et qu'`undo` remet en place) ; `config.toml` est mis à jour la
prochaine fois que la page enregistre un nom. Chaque nom est une entrée
`[[people.person]]` de `config.toml`. Détails :
[Les personnes](../reference-people.md#nommer-les-groupes).

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

- Les réglages `[people]` (`similarity`, `min_face`, `min_sharpness`) ne changent que le
  regroupement : rien n'est analysé à nouveau.
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
│                                       Par défaut : 8088.                     │
│ --help    -h                          Affiche ce message et quitte.          │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
