# Trier en bref : le parcours complet

[Documentation](../README.md) › Trier en bref · 🇬🇧 [English](../../en/sort/quick-guide.md)

Toutes les commandes du tri, dans l'ordre, prêtes à copier dans **PowerShell**. Chaque étape
renvoie à sa page détaillée, si vous voulez comprendre. Remplacez `C:\Photos` par votre dossier.

Le principe : `classify` **propose** une place pour chaque photo et vidéo (`année/catégorie` par
défaut), vous corrigez la proposition dans un classeur, et seul `sort` déplace les fichiers. Rien
ne bouge avant, et `sort` peut être annulé.

## 0. Avant de commencer

**Nettoyez d'abord les doublons** ([nettoyer en bref](../clean/quick-guide.md)) : sinon les deux
copies d'une photo sont triées. La commande `mh` écrite pour le nettoyage sert aussi ici ; sinon,
écrivez-la une fois : [nettoyer en bref, étape 0](../clean/quick-guide.md#0-une-seule-fois--écrire-la-commande-mh).
Dans un nouveau terminal, rechargez-la :

```powershell
. "$HOME\media-hygiene\mh.ps1"
```

## 1. Demander une proposition

```powershell
mh classify
```

Rien n'est modifié : `mh` monte vos dossiers en lecture seule (`:ro`). À la fin, deux fichiers
dans un nouveau dossier `<date>-classify` de vos rapports :

- `classify.xlsx`, le classeur, à ouvrir dans Excel ou LibreOffice : c'est là que vous
  **modifiez** ;
- `report.html`, le rapport, à ouvrir dans votre navigateur : c'est là que vous **regardez** les
  photos.

Détails : [proposer une arborescence](04-classify.md).

## 2. Corriger la proposition

Ouvrez les deux côte à côte. Seules les cellules **jaunes** du classeur se modifient.

1. **Commencez par la feuille Événements** : les plus grands d'abord. Tapez un **Nom**
   (`Italie 2023`) : il devient le dossier de l'événement. Nommer les dix premières lignes règle
   souvent l'essentiel de la collection.
2. Pour comprendre un événement, cherchez son identifiant dans le rapport : ses dates, ses
   aperçus, d'où viennent ses photos.
3. Un fichier mal placé ? Feuille Fichiers, colonne **Dossier final** (`2016/Kermesse`).
4. **Enregistrez et fermez** le classeur.

Plutôt dans le navigateur, une photo à l'écran ? [Nommer les événements dans le
navigateur](10-name-events-in-the-browser.md) fait la même chose au clavier. Détails : [revoir la
proposition](05-review-the-proposal.md).

## 3. Écrire ce que vous savez (facultatif)

Vos voyages, vos fêtes, vos dossiers existants : écrits une fois comme règles dans
`$HOME\media-hygiene\config\config.toml`, ils servent à chaque `classify`. Par exemple :

```toml
[[classify.rules]]
name = "Italie 2023"
match = "date_range"
dates = "2023-07-01..2023-07-15"
category = "Vacances et sorties/Italie 2023"
```

Relancez ensuite l'étape 1 : les modifications déjà faites dans l'ancien classeur sont reprises
dans le nouveau. Détails : [écrire ce que vous savez](06-write-down-what-you-know.md).

## 4. Trier

```powershell
mh sort
```

Pour `sort`, `mh` monte vos dossiers en écriture (`sort` déplace des fichiers) et ajoute le
journal et la quarantaine. `sort` prend le classeur du dernier `classify`, le vérifie, dit combien de
modifications il a lues (pas assez ? le classeur n'était pas enregistré) et demande
confirmation : répondez `o`. Il finit en prouvant que rien n'est perdu : autant de fichiers,
de la même taille, avant et après. Détails : [trier](07-sort.md).

## 5. Vérifier, ou annuler

```powershell
explorer "C:\Photos"
```

Vous changez d'avis ? `mh undo` : chaque fichier revient où il était.

## Aller plus loin (facultatif)

- [Lieux et voyages grâce au GPS](09-places-from-gps.md) : nommer vos lieux sur une carte, et
  laisser le GPS trier maison, famille et voyages.
- [Nommer les sujets avec un modèle local](08-subjects-from-a-local-model.md) : ce que montrent
  les photos isolées, sans rien envoyer sur Internet.
- [Albums](11-albums.md) : une photo dans plusieurs dossiers, sans copie ni place prise.

<details>
<summary>Sans <code>mh</code> : les commandes complètes</summary>

Étape 1, en lecture seule :

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene --locale fr classify
```

Étapes 4 et 5 : `:ro` est retiré, `/journal` et `/quarantine` sont ajoutés ; `undo` à la place de
`sort` pour annuler :

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene --locale fr sort
```

</details>

---

[Documentation](../README.md) · Pas à pas : **[4. Proposer une arborescence](04-classify.md)** →
