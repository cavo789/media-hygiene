# `album` : une photo dans plusieurs dossiers, sans copie

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `album` · 🇬🇧 [English](../../en/commands/album.md)

## En bref

**Mettre une même photo dans plusieurs albums (« Noël », « Mes plus belles photos ») sans la
copier : aucune place en plus.**

Une arborescence donne à chaque photo **une** place. `album` rassemble une sélection dans un
dossier de **liens physiques** : un deuxième nom pour le même fichier, ni copié ni déplacé. Sans
`--apply`, il montre seulement ce qu'il ferait.

**Quand** : après [`classify`](classify.md), chaque fois que vous voulez une sélection : une
catégorie, un événement, les photos notées d'étoiles dans Windows.

**Essayer** :

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene --locale fr album "Noël" --category Noël
```

## D'un coup d'œil

| | |
|---|---|
| Vos photos | ✋ Agit avec `--apply` seulement : ajoute des deuxièmes noms (liens physiques) ; aucune photo n'est copiée, déplacée ni supprimée. |
| Il faut | `/reports` (l'exécution de `classify`) ; avec `--apply`, vos dossiers **sans** `:ro` et `/journal`. |
| Conseillé | `/cache` (indispensable pour `--rating`), `/config` (le dossier de `[album]`). |
| Écrit | Le dossier de l'album, ses liens et un fichier `.media-hygiene-album` ; le journal. |
| Annuler | [`undo <exécution>`](undo.md) retire les liens et les dossiers qu'il a créés ; les originaux restent. |
| Avec `mh` | `mh album "Noël" --category Noël`. |

## Lancer

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene --locale fr album "Noël" --category Noël
```

Il montre le dossier de l'album, les fichiers choisis, les liens à créer, ceux déjà dans l'album,
et ceux qu'il ne peut pas lier (*Introuvables*, *Sur un autre disque ou montage*), puis *💡 Rien
n'a été modifié : ajoutez --apply pour créer les liens*. Ajoutez `--apply` pour les créer.

## Options

| Option | Rôle |
|---|---|
| `NOM` | Le nom de l'album : le dossier qui contient ses liens (obligatoire). |
| `--category NOM` | Les fichiers de cette catégorie, d'après le classeur modifié. |
| `--event ÉVÉNEMENT` | Les fichiers de cet événement : son identifiant (feuille Événements) ou son nom. |
| `--rule NOM` | Les fichiers que l'entrée `[[classify.rules]]` de ce nom a décidés. |
| `--rating N` | Les fichiers qui ont au moins N étoiles (1 à 5) dans Windows, telles que l'audit les a lues. |
| `--workbook CHEMIN` | Le classeur de `classify` à lire ; celui du dernier `classify` par défaut. |
| `--apply` | Créer les liens ; sans cette option, montrer seulement ce que l'album rassemble. |

Données ensemble, toutes les options doivent correspondre : `--category Noël --rating 4`
rassemble les plus belles photos de Noël. La casse ne compte pas.

## Bon à savoir

- **Où vont les albums** : `root` dans la section `[album]` de `config.toml` ; vide, un dossier
  `Albums` dans la `target` de `[classify]`.
- **Un lien physique ne quitte jamais son disque, ni son `-v`** : montez le dossier qui contient à
  la fois les photos et les albums (`C:\Photos` pour `C:\Photos\Albums`).
- **Relancez-le** plus tard : seules les nouvelles photos sont ajoutées ; une photo n'est jamais
  liée deux fois.
- **Jamais vu comme des doublons** : `audit`, `clean`, `classify` et `sort` ignorent tout dossier
  qui contient `.media-hygiene-album`. Gardez ce fichier.
- Une photo retouchée dans l'album l'est aussi dans son dossier trié : c'est le même fichier.
- Un disque qui refuse les liens physiques (FAT, exFAT, certains partages réseau) arrête `album` au
  premier refus, avec la raison.

## Pour aller plus loin

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
