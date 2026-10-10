# Nettoyer en bref : le parcours complet

[Documentation](../README.md) › Nettoyer en bref · 🇬🇧 [English](../../en/clean/quick-guide.md)

Toutes les commandes du nettoyage, dans l'ordre, prêtes à copier dans **PowerShell**. Chaque étape
renvoie à sa page détaillée, si vous voulez comprendre. Remplacez `C:\Photos` par votre dossier
(ou ajoutez-en d'autres : [plusieurs dossiers et disques](../start/03-several-folders.md)).

Rien ne presse : vous pouvez vous arrêter après n'importe quelle étape, et tout ce que fait
`clean` peut être annulé jusqu'à `purge`.

## 0. Une seule fois : créer vos dossiers

```powershell
mkdir "$HOME\media-hygiene\reports", "$HOME\media-hygiene\config", "$HOME\media-hygiene\journal", "$HOME\media-hygiene\quarantine"
```

| Dossier | Ce qu'il reçoit |
|---|---|
| `reports` | Les rapports HTML, à ouvrir dans votre navigateur. |
| `config` | `config.toml`, vos réglages. |
| `journal` | Le journal de chaque nettoyage : ce qui permet `undo`. |
| `quarantine` | Les fichiers mis de côté, jusqu'à ce que vous les effaciez. |

Créez-les **avant** le premier lancement : un dossier que Docker crée lui-même appartient à
l'administrateur, et l'outil ne pourrait pas y écrire.

## 1. Auditer et regarder le rapport

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene --locale fr audit
```

Rien n'est modifié (`:ro`). Le premier audit lit tout ; grâce au cache (`/cache`), les suivants
prennent quelques secondes. À la fin, Ctrl+clic sur le chemin de `report.html` (ou ouvrez
`index.html` dans `$HOME\media-hygiene\reports`).

Dans le rapport, regardez surtout **les paires de dossiers** : pour chacune, quel dossier garde
ses copies. Pas d'accord ? Voyez [choisir la copie gardée](05-choose-the-kept-copy.md)
(`--prefer`, `--protect`), puis relancez l'audit. Détails : [le rapport HTML](04-html-report.md).

## 2. Mettre les doublons exacts de côté

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene --locale fr clean
```

Deux changements : `:ro` est retiré (`clean` déplace des fichiers), et `/journal` et
`/quarantine` sont ajoutés. `clean` refait l'audit, dit ce qu'il va faire et demande
confirmation : répondez `o`. Les copies en trop partent en quarantaine, jamais par-dessus un autre
fichier. Détails : [nettoyer](08-clean.md).

## 3. Vérifier, ou annuler

```powershell
explorer "$HOME\media-hygiene\quarantine"
```

La quarantaine reproduit vos dossiers, sous un dossier par nettoyage. Vous changez d'avis ?
Lancez la commande de l'étape 2 en remplaçant `clean` par `undo` : tout revient à sa place.
Détails : [annuler, historique, purge](09-undo-history-purge.md).

## 4. Les quasi-doublons (facultatif)

Les copies réduites ou recompressées (WhatsApp, e-mail…) et les vidéos réencodées ne sont pas
identiques à l'original : regardez-les d'abord dans le rapport de l'étape 1, sections
*Quasi-doublons* et *Vidéos réencodées*. Puis la commande de l'étape 2, avec `--tier near` :

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene --locale fr clean --tier near
```

`--tier near` ne déplace que les groupes **sûrs** (même image et même son, empreintes
identiques, copie plus petite dans un dossier de messagerie) et dit combien de groupes à vérifier
restent en place : décidez-les un à un dans le navigateur avec `review --near`, puis la même
commande avec `--tier near --decisions` ; ou `--tier near-all` les déplace tous. La plus haute
résolution reste, tout part en quarantaine : `undo` si un groupe ne vous plaît pas. Détails :
[les quasi-doublons](11-near-duplicates.md).

## 5. Les rafales (facultatif)

Les séries de photos prises à quelques secondes d'intervalle : vous choisissez lesquelles garder,
dans votre navigateur.

```powershell
docker run --rm -it -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene --locale fr review
```

Ouvrez l'adresse affichée, `http://127.0.0.1:8088/`, dans votre navigateur (Ctrl+clic) et triez
au clavier. Chaque choix est enregistré aussitôt dans `decisions.json`, dans votre dossier de
rapports ; **Ctrl+C** arrête, le `review` suivant reprend où vous en étiez. Ensuite, la commande
de l'étape 2 avec `--decisions` met les photos écartées en quarantaine :

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene --locale fr clean --decisions
```

Détails : [trier les rafales dans le navigateur](10-review-bursts.md).

## 6. Libérer l'espace, pour de bon

Jusqu'ici, rien n'est effacé : la quarantaine occupe toujours la place. Une fois que vous avez
vérifié, la commande de l'étape 2 avec `purge` à la place de `clean` vide la quarantaine :

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene --locale fr purge
```

Elle demande confirmation. Après `purge`, `undo` ne peut plus ramener ces fichiers.

## 7. Contrôler

Relancez l'audit de l'étape 1 : il doit dire *Rien à nettoyer*. Ses quasi-doublons et rafales
restants sont ceux que vous avez choisi de garder.

Et ensuite ? Votre photothèque est prête à être rangée : [trier en bref](../sort/quick-guide.md).

---

[Documentation](../README.md) · Pas à pas : **[4. Le rapport HTML](04-html-report.md)** →
