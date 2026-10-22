# `album` : un album en dossier sur le disque, sans copie

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `album` · 🇬🇧 [English](../../en/commands/album.md)

## En bref

**Donner à un album son propre dossier dans l'Explorateur (« Crète 2023 », « Mes plus belles
photos ») sans copier une photo : aucune place en plus.**

Un **album** est la liste nommée de photos que vous faites dans
[`search`](search.md#mettre-des-photos-dans-un-album), [`browse`](browse.md) ou la revue des
rafales, enregistrée dans `albums.json`. Il a plusieurs usages, tous sous *Partager* dans la page
d'accueil et `mh menu` :

| Usage | Commande |
|---|---|
| Sur la télé | [`slideshow --album "Crète 2023"`](slideshow.md) |
| Sur votre téléphone, à la maison | [la page des albums](home.md#vos-albums-sur-le-téléphone) |
| Prêt à envoyer par mail | [`share --album "Crète 2023"`](share.md) |
| Un dossier de liens sur le disque | `album "Crète 2023"`, cette page |

`album` crée ce dossier de **liens physiques** : un deuxième nom pour le même fichier, ni copié ni
déplacé, dans un seul dossier quels que soient les dossiers d'où viennent les photos. Sans
`--apply`, il montre seulement ce qu'il ferait.

**Quand** : une fois l'album fait, après un [`audit`](audit.md) (une photo de l'album déplacée
depuis est retrouvée par son contenu).

**Essayer** :

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene --locale fr album "Crète 2023"
```

## D'un coup d'œil

| | |
|---|---|
| Vos photos | ✋ Agit avec `--apply` seulement : ajoute des deuxièmes noms (liens physiques) ; aucune photo n'est copiée, déplacée ni supprimée. |
| Il faut | `/reports` (les albums, `albums.json`) ; avec `--apply`, vos dossiers **sans** `:ro` et `/journal`. |
| Conseillé | `/cache` (pour retrouver une photo déplacée depuis ; indispensable pour `--rating`), `/config` (le dossier de `[album]`). |
| Écrit | Le dossier de l'album, ses liens et un fichier `.media-hygiene-album` ; le journal. `albums.json` est seulement lu. |
| Annuler | [`undo <exécution>`](undo.md) retire les liens et les dossiers qu'il a créés ; les originaux restent. |
| Avec `mh` | `mh album "Crète 2023"`. |

## Lancer

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene --locale fr album "Crète 2023"
```

Il montre le dossier de l'album, les fichiers de l'album, les liens à créer, ceux déjà dans le
dossier, et ceux qu'il ne peut pas lier (*Introuvables* : déplacés ou supprimés depuis leur ajout,
*Sur un autre disque ou montage*), puis *💡 Rien n'a été modifié : ajoutez --apply pour créer les
liens*. Ajoutez `--apply` pour les créer. Le nom est celui de l'album, quelle que soit sa casse :
`album "crète 2023"` crée le dossier `Crète 2023`.

## Sans album : une sélection du plan de classify

Après [`classify`](classify.md), `album` peut aussi rassembler une sélection de son plan, sans
album enregistré d'abord : `album "Noël" --category Noël`. Chaque option ci-dessous choisit dans
le plan **au lieu de** `albums.json` ; données ensemble, toutes les options doivent correspondre :
`--category Noël --rating 4` rassemble les plus belles photos de Noël. La casse ne compte pas.
Plus : [Trier, étape 12](../sort/12-albums.md#choisir-ce-que-lalbum-rassemble).

## Options

| Option | Rôle |
|---|---|
| `NOM` | Le nom de l'album, tel que `search` et `browse` l'ont enregistré : le dossier qui contient ses liens (obligatoire). |
| `--category NOM` | Au lieu d'un album enregistré : les fichiers de cette catégorie, d'après le classeur de `classify` modifié. |
| `--event ÉVÉNEMENT` | Les fichiers de cet événement : son identifiant (feuille Événements) ou son nom. |
| `--rule NOM` | Les fichiers que l'entrée `[[classify.rules]]` de ce nom a décidés. |
| `--rating N` | Les fichiers qui ont au moins N étoiles (1 à 5) dans Windows, telles que l'audit les a lues. |
| `--workbook CHEMIN` | Le classeur de `classify` à lire ; celui du dernier `classify` par défaut. |
| `--apply` | Créer les liens ; sans cette option, montrer seulement ce que l'album rassemble. |

## Bon à savoir

- **Où vont les albums** : `root` dans la section `[album]` de `config.toml` ; vide, un dossier
  `Albums` dans la `target` de `[classify]`.
- **Un lien physique ne quitte jamais son disque, ni son `-v`** : montez le dossier qui contient à
  la fois les photos et les albums (`C:\Photos` pour `C:\Photos\Albums`).
- **Relancez-le** plus tard, après avoir ajouté des photos à l'album : seules les nouvelles photos
  sont ajoutées ; une photo n'est jamais liée deux fois. Une photo retirée de l'album reste dans
  son dossier : annulez l'exécution (`undo`), ou supprimez le lien.
- **Jamais vu comme des doublons** : `audit`, `clean`, `classify` et `sort` ignorent tout dossier
  qui contient `.media-hygiene-album`. Gardez ce fichier.
- Une photo retouchée dans l'album l'est aussi dans son dossier trié : c'est le même fichier.
- Un disque qui refuse les liens physiques (FAT, exFAT, certains partages réseau) arrête `album` au
  premier refus, avec la raison.

## Pour aller plus loin

- [`search` : mettre des photos dans un album](search.md#mettre-des-photos-dans-un-album)
- [`share` : l'album prêt à envoyer](share.md)
- [Trier, étape 12 : les albums](../sort/12-albums.md)

## L'aide intégrée

<details>
<summary><code>album --help</code></summary>

<!-- capture: help-album.txt -->
```text
 Utilisation : media-hygiene album [OPTIONS] {name}

 Rassemble une sélection du plan de classify dans un dossier de liens physiques
 : rien n'est copié ni déplacé (journalisé, annulable).

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│ *    name      <str>  Le nom de l'album : le dossier qui contient ses liens. │
│                       [required]                                             │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --category          <str>  Les fichiers de cette catégorie, d'après le       │
│                            classeur modifié.                                 │
│ --event             <str>  Les fichiers de cet événement : son identifiant   │
│                            ou son nom.                                       │
│ --apply                    Crée les liens ; sans cette option, montre        │
│                            seulement ce que l'album rassemble.               │
│ --help      -h             Affiche ce message et quitte.                     │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options avancées ───────────────────────────────────────────────────────────╮
│ --rule            <str>                  Les fichiers que la règle de        │
│                                          classify de ce nom a décidés.       │
│ --rating          <int range> [1<=x<=5]  Les fichiers qui ont au moins ces   │
│                                          étoiles dans Windows (1 à 5).       │
│ --workbook        <str>                  Le classeur de classify à lire ;    │
│                                          celui du dernier classify par       │
│                                          défaut.                             │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Avancé : dossiers (remplacent folders.* de config.toml) ────────────────────╮
│ --backup        <str>  Une sauvegarde ou un ancien disque, monté en lecture  │
│                        seule : jamais modifié, et jamais refusé pour cela    │
│                        (mh passe vos sauvegardes). Répétable.                │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
