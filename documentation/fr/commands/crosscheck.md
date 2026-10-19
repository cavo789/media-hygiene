# `crosscheck` : un deuxième avis, indépendant

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `crosscheck` · 🇬🇧 [English](../../en/commands/crosscheck.md)

## En bref

**Être sûr de vos doublons avant de supprimer des photos de famille : un deuxième outil,
indépendant, les vérifie groupe par groupe.**

`crosscheck` refait l'audit, lance [Czkawka](https://github.com/qarmin/czkawka), un détecteur de
doublons libre écrit indépendamment, avec une autre fonction de hachage, puis compare les deux,
groupe par groupe. Czkawka est livré dans l'image : une seule commande fait tout. Quand les deux
sont d'accord, vous pouvez nettoyer en confiance.

**Quand** : facultatif, avant un premier grand `clean` (`clean` ne l'exige jamais), et de nouveau
après un nettoyage si vous le souhaitez : avec `/cache`, Czkawka ne relit que ce qui a changé.

**Essayer** :

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene --locale fr crosscheck
```

## D'un coup d'œil

| | |
|---|---|
| Vos photos | 🔒 Jamais modifiées : montez-les en `:ro`. |
| Il faut | Vos dossiers, et `/reports`, où sont gardés les résultats de Czkawka (`czkawka.json`). |
| Conseillé | `/cache` : l'audit prend quelques secondes, et Czkawka y garde son propre cache. `/config`. |
| Écrit | Le cache, `czkawka.json` et un rapport de contre-vérification dans `/reports`. |
| Annuler | Rien à annuler. |
| Avec `mh` | `mh crosscheck`. |

## Lancer

Avec les mêmes dossiers et options que votre audit :

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v "D:\Ancien disque:/data/d/Ancien disque:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene --locale fr crosscheck
```

1. **L'audit**, rapide grâce au cache.
2. **Czkawka** lit les mêmes dossiers, les mêmes extensions, sans les dossiers exclus, toutes les
   tailles de fichier. Il ne fait que lire : rien n'est modifié. Sur des dizaines de milliers de
   photos, comptez quelques minutes la première fois ; avec `/cache`, les fois suivantes ne
   relisent que ce qui a changé. Il écrit `czkawka.json` dans votre dossier de rapports.
3. **La comparaison**, groupe par groupe, et son rapport.

## Lire le verdict

- *Czkawka est d'accord : les mêmes N copies en trop dans G groupes* : les deux outils ont trouvé
  exactement les mêmes doublons.
- *Czkawka n'est pas d'accord sur N groupes*, suivi de chaque groupe trouvé par un seul des deux :
  regardez-les avant de nettoyer.

Le verdict figure en haut du rapport de contre-vérification, dans chaque `clean` suivant avant sa
question, et dans le rapport de nettoyage.

## Options

Les mêmes options de dossiers et d'analyse qu'[`audit`](audit.md#options) : `--prefer`,
`--protect`, `--exclude`, `--exclude-name`, `--ext`. Donnez celles de votre audit.

| Option | Ce qu'elle fait |
|---|---|
| `--fresh` | Czkawka relit et recalcule l'empreinte de chaque fichier, sans tenir compte de son cache : un deuxième avis qui ne doit rien au précédent. Plus lent. |
| `--print-command` | Czkawka n'est pas lancé ici : `crosscheck` affiche la commande qui le lance dans sa propre image (l'image communautaire `jlesage/czkawka`, environ 500 Mo), puis compare le `czkawka.json` qu'il a écrit. Pour qui veut lancer Czkawka de ses propres yeux. |

## Bon à savoir

- Les fichiers que media-hygiene laisse de côté exprès (autres types de fichiers, dossiers exclus
  ou système, fichiers cassés) sont comptés à part, pas signalés comme des différences ; les
  dossiers jamais analysés sont nommés, les plus gros d'abord.
- **Des photos déplacées ou supprimées depuis que Czkawka a tourné** (par un `clean`, par exemple)
  rendent ses résultats périmés pour les `audit` et `clean` suivants : ils sont ignorés, et le
  message donne la sortie : relancer `crosscheck`, ou supprimer `czkawka.json` si vous ne voulez
  plus de deuxième avis.
- Czkawka est le binaire publié par son propre projet (licence MIT), tel quel, épinglé dans
  l'image. Seul l'emballage est commun : son code et sa fonction de hachage restent les siens.

## Pour aller plus loin

- [13. Un deuxième avis](../clean/13-second-opinion.md)
- [Comment vos photos restent en sécurité : qu'est-ce qu'un doublon ?](../reference-safety.md#quest-ce-quun-doublon-)

## L'aide intégrée

<details>
<summary><code>crosscheck --help</code></summary>

<!-- capture: help-crosscheck.txt -->
```text
 Utilisation : media-hygiene crosscheck [OPTIONS]

 🔒 Lecture seule : ne modifie jamais vos photos. Lance Czkawka, un détecteur
 de doublons indépendant, puis compare ses groupes à un nouvel audit : un
 second avis.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help  -h        Affiche ce message et quitte.                              │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Avancé : dossiers (remplacent folders.* de config.toml) ────────────────────╮
│ --prefer         <str>  Dossier dont les copies sont conservées en priorité. │
│                         Répétable ; l'ordre compte.                          │
│ --protect        <str>  Dossier jamais modifié ; ses fichiers sont les       │
│                         copies conservées. Répétable.                        │
│ --exclude        <str>  Dossier jamais analysé, même pas lu. Répétable.      │
│ --backup         <str>  Une sauvegarde ou un ancien disque : comparé, jamais │
│                         modifié. Dit ce qui lui manque et ce que lui seul    │
│                         contient. Répétable.                                 │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Avancé : analyse (remplace scan.* de config.toml) ──────────────────────────╮
│ --ext                 <str>  N'analyse que ces catégories ou extensions, p.  │
│                              ex. --ext photo,video ou --ext png,webp         │
│                              (répétable). Catégories : photo, raw, video,    │
│                              media et celles de scan.categories dans         │
│                              config.toml. D'autres types aussi, comme --ext  │
│                              pdf,docx : leurs copies sont déplacées en       │
│                              quarantaine. Par défaut : media (toutes les     │
│                              photos, RAW et vidéos).                         │
│ --exclude-name        <str>  Nom de dossier jamais analysé, où qu'il soit,   │
│                              sans tenir compte de la casse ; * et ? permis,  │
│                              p. ex. --exclude-name Thumbnails,.Trash-*       │
│                              (répétable). S'ajoute aux dossiers système déjà │
│                              ignorés. Pour un dossier précis, utilisez       │
│                              --exclude.                                      │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options avancées ───────────────────────────────────────────────────────────╮
│ --fresh                  Czkawka relit et recalcule l'empreinte de chaque    │
│                          fichier, sans tenir compte de ce que son cache dans │
│                          /cache retient de sa dernière exécution. Plus lent  │
│                          ; pour un second avis qui ne doit rien au           │
│                          précédent.                                          │
│ --print-command          Ne pas lancer Czkawka ici : afficher la commande    │
│                          qui le lance dans sa propre image, puis comparer    │
│                          les résultats qu'il a écrits dans /reports          │
│                          (czkawka.json).                                     │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
