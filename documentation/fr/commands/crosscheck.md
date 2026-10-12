# `crosscheck` : un deuxième avis, indépendant

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `crosscheck` · 🇬🇧 [English](../../en/commands/crosscheck.md)

## En bref

**Être sûr de vos doublons avant de supprimer des photos de famille : un deuxième outil,
indépendant, les vérifie groupe par groupe.**

`crosscheck` refait l'audit, puis compare ses doublons avec ceux de
[Czkawka](https://github.com/qarmin/czkawka), un détecteur de doublons libre écrit
indépendamment, avec une autre fonction de hachage. Quand les deux sont d'accord, vous pouvez
nettoyer en confiance.

**Quand** : facultatif, une fois, avant un premier grand `clean` (`clean` ne l'exige jamais). Le
premier lancement affiche la commande de Czkawka à coller ; le suivant compare.

**Essayer** :

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene --locale fr crosscheck
```

## D'un coup d'œil

| | |
|---|---|
| Vos photos | 🔒 Jamais modifiées : montez-les en `:ro`. |
| Il faut | Vos dossiers, et `/reports`, où Czkawka a écrit `czkawka.json`. |
| Conseillé | `/cache` (l'audit prend quelques secondes), `/config`. |
| Écrit | Le cache, un rapport de contre-vérification dans `/reports`. |
| Annuler | Rien à annuler. |
| Avec `mh` | `mh crosscheck`. |

## Lancer, en trois étapes

1. **La commande Czkawka.** Tant que Czkawka n'a pas tourné, `crosscheck` (et un audit lancé avec
   `--verbosity verbose`) affiche la commande exacte pour vos dossiers : les mêmes options `-v`,
   extensions et dossiers exclus. Elle utilise l'image communautaire `jlesage/czkawka` (environ
   500 Mo).
2. **Lancez Czkawka.** Collez cette commande, avec votre dossier de rapports là où elle le dit.
   Sur des dizaines de milliers de photos, comptez plusieurs minutes. Il écrit `czkawka.json`
   dans votre dossier de rapports.
3. **Comparez**, avec les mêmes options que votre audit :

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v "D:\Ancien disque:/data/d/Ancien disque:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene --locale fr crosscheck
```

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

## Bon à savoir

- Les fichiers que media-hygiene laisse de côté exprès (autres types de fichiers, dossiers exclus
  ou système, fichiers cassés) sont comptés à part, pas signalés comme des différences ; les
  dossiers jamais analysés sont nommés, les plus gros d'abord.
- **Des photos déplacées ou supprimées depuis que Czkawka a tourné** (par un `clean`, par exemple)
  rendent ses résultats périmés : ils sont ignorés, et le message donne la sortie : relancer
  Czkawka, ou supprimer `czkawka.json` si vous ne voulez plus de deuxième avis.

## Pour aller plus loin

- [13. Un deuxième avis](../clean/13-second-opinion.md)
- [Comment vos photos restent en sécurité : qu'est-ce qu'un doublon ?](../reference-safety.md#quest-ce-quun-doublon-)

## L'aide intégrée

<details>
<summary><code>crosscheck --help</code></summary>

<!-- capture: help-crosscheck.txt -->
```text
 Utilisation : media-hygiene crosscheck [OPTIONS]

 🔒 Lecture seule : ne modifie jamais vos photos. Compare un nouvel audit aux
 résultats de Czkawka : un second avis, indépendant.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help  -h        Affiche ce message et quitte.                              │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Avancé : dossiers (remplacent folders.* de config.toml) ────────────────────╮
│ --prefer         <str>  Dossier dont les copies sont conservées en priorité. │
│                         Répétable ; l'ordre compte.                          │
│ --protect        <str>  Dossier jamais modifié ; ses fichiers sont les       │
│                         copies conservées. Répétable.                        │
│ --exclude        <str>  Dossier jamais analysé, p. ex. une vraie sauvegarde  │
│                         à garder. Répétable.                                 │
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
```

</details>

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
