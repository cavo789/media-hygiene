# `people` : trouver les visages et regrouper ceux qui se ressemblent

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `people` · 🇬🇧 [English](../../en/commands/people.md)

`people` trouve les **visages** de vos photos, regroupe ceux qui se ressemblent (sans doute une
personne par groupe), et montre les groupes dans votre navigateur, les plus grands d'abord. Tout
tourne sur votre ordinateur : les visages restent dans le cache, jamais envoyés nulle part. Cette
première version trouve et regroupe ; nommer les groupes viendra ensuite.

## En bref

| | |
|---|---|
| Vos photos | 🔒 Jamais modifiées : montez-les en `:ro`. |
| Il faut | Vos dossiers, `/cache` (en écriture : les visages y sont gardés), et `-p 127.0.0.1:8088:8088`. |
| Écrit | Les visages et les deux modèles de visages (39 Mo, une fois), dans le cache. |
| Annuler | `people --forget` supprime tous les visages du cache. |
| Avec `mh` | `mh people` : le port est publié pour vous. |

## Lancer

```powershell
docker run --rm -it -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  cavo789/media-hygiene --locale fr people
```

La première exécution télécharge les deux modèles de visages dans le cache, une fois. Chaque photo
est analysée une fois ; les exécutions suivantes n'analysent que les nouvelles. Il affiche ensuite
les groupes trouvés et l'adresse de la page : un clic sur un visage ouvre sa photo. Ctrl+C l'arrête.

## Options

| Option | Rôle |
|---|---|
| `--path CHEMIN` | Seulement les photos sous ce dossier (chemin de l'hôte, tel que vous l'avez monté) ; à répéter pour plusieurs. |
| `--sample N` | Analyser N photos prises au hasard, afficher le temps par photo et l'estimation d'une exécution complète, puis s'arrêter. |
| `--forget` | Supprimer tous les visages du cache, puis montrer qu'il n'en reste aucun. |
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
- Les vidéos ne sont pas encore analysées.
- Sans réseau, l'erreur nomme les deux fichiers de modèle à enregistrer à la main dans le dossier
  `models` du cache.

## Pour aller plus loin

- [Les personnes](../reference-people.md) : comment ça marche, les réglages, ce qui vient ensuite.

## L'aide intégrée

<details>
<summary><code>people --help</code></summary>

<!-- capture: help-people.txt -->
```text
 Utilisation : media-hygiene people [OPTIONS]

 🔒 Lecture seule : ne modifie jamais vos photos. Trouver les visages des
 photos et regrouper ceux qui se ressemblent, à voir dans votre navigateur.
 Gardés dans le cache, jamais envoyés nulle part.

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
│                                       puis montrer qu'il n'en reste aucun.   │
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
