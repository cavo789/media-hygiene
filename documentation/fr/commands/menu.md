# `menu` : chaque étape, la prochaine en premier

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `menu` · 🇬🇧 [English](../../en/commands/menu.md)

## En bref

**Perdu ? Tapez `mh menu` : chaque étape des guides dans le terminal, la prochaine proposée,
Entrée la lance.** `mh` seul montre les mêmes étapes sur la [page d'accueil](home.md), dans votre
navigateur.

Inutile de retenir le nom des commandes. `mh menu` montre chaque action de l'outil, rangée comme
le cycle avance : **importer** (depuis un téléphone, depuis votre NAS ou un ancien disque),
**nettoyer** ([guide](../clean/quick-guide.md)), **trier** ([guide](../sort/quick-guide.md)),
**retrouver** ([guide](../find/quick-guide.md)), **sauvegarder** (prévu), puis les outils :
historique et annulation, rapports, réglages. Chaque ligne a sa commande `mh …` complète, et le
menu en propose **une** : celle que donnerait [`status`](status.md). Appuyez sur Entrée pour la
lancer, ou tapez le numéro d'une autre étape. La commande choisie est ensuite rappelée, *La
prochaine fois, tapez-la directement : mh clean* : vous apprenez les commandes en vous en servant.

**Quand** : chaque fois que vous ne savez plus quelle est la suite.

**Essayer** (une fois `mh` écrit, [étape 0 des guides](../clean/quick-guide.md#0-une-seule-fois--écrire-la-commande-mh)) :

```powershell
mh menu
```

## D'un coup d'œil

| | |
|---|---|
| Vos photos | 🔒 Le menu lui-même ne les modifie jamais, ne les lit même pas. L'étape choisie dit ce qu'elle risque : 🔒, ↩️ ou ⚠️. |
| Il faut | `mh` : le menu lance par lui l'étape choisie, avec les bons dossiers. |
| Écrit | Rien. |
| Annuler | Rien à annuler ; chaque étape garde sa propre annulation. |
| Avec `mh` | `mh menu`. |

## Ce qu'il montre

Sous *Où vous en êtes* (le dernier audit, la quarantaine), une ligne par étape :

- **👉** l'étape proposée, celle que lance Entrée ; **✅** une étape que les dossiers de l'outil
  prouvent faite (un audit vu, plus aucune copie, un tri appliqué, des mots ou des visages
  trouvés). Rien n'est marqué quand l'outil ne peut pas le savoir.
- le **numéro** à taper, puis la **commande** que vous taperez plus tard vous-même ;
- ce que fait l'étape, et son badge : 🔒 photos intactes, ↩️ annulable, ⚠️ définitif,
  *facultatif* ; 🤖 à côté de `classify` et `tags` quand un modèle local est indiqué
  (`[classify.ai] model`). La ligne sous le tableau rappelle ce que veulent dire 🔒, ↩️ et ⚠️.
- Une étape que l'outil remplit d'après ce qu'il sait prend son argument (`mh purge <exécution>`,
  `mh undo <exécution>`) ; sans rien à purger ni à annuler, elle n'a pas de numéro. Une étape qui
  demande des mots que vous seul connaissez (le nom d'un album, le dossier de votre NAS, un
  dossier à retirer, combien de rapports garder) montre un exemple, *(à taper vous-même)* :
  `mh album "Crète 2023"`. Sur la [page d'accueil](home.md), son formulaire les
  remplit. `mh push` s'affiche *(prévu)*.

Chaque action est listée une fois, numérotée d'un espace à l'autre, dans l'espace où elle vient
en premier : `mh open`, `mh history`, `mh undo` et `mh purge` sont dans le guide du nettoyage, là
où ils viennent. Tant qu'une étape est proposée, les autres espaces sont estompés. Le menu prend
la largeur de votre fenêtre ; *Lecture de là où vous en êtes…* s'affiche pendant qu'il compte la
quarantaine, ce qui prend quelques secondes quand elle contient des milliers de fichiers.

Le téléphone, `mh shortcut` (une icône sur le Bureau) et `mh explorer` (le clic droit d'un
dossier) sont pour Windows : le `mh` de bash les laisse de côté. `mh` lance lui-même `open`,
`folders`, `update`, `import --phone`, `shortcut` et `explorer` : [ce que `mh` fait
lui-même](launcher.md#ce-que-mh-fait-lui-même). Une commande qui n'a pas encore sa place dans le
menu s'affiche quand même, en dernier, sous *Autres commandes*.

<!-- capture: menu.txt -->
```text
─────────────────────── media-hygiene — où vous en êtes ────────────────────────
Dernier audit: 2026-10-25 08:48 (aujourd'hui) — 10 fichiers, 4 copies en trop
(5,9 Mo), 1 illisibles.
Quarantaine : vide.

      Importer des photos
      Depuis un téléphone
    1 mh import --phone                                        Copier les   🔒
                                                      nouvelles
                                                      photos du
                                                      téléphone
    2 mh import --phone --free                                 Faire de la  ⚠️ facultatif
                                                      place sur le
                                                      téléphone
      Depuis votre NAS ou un ancien disque
      mh folders add --backup "\\NAS\Photos"          Brancher     🔒
                                                      votre NAS ou
                                                      un ancien
                                                      disque (à
                                                      taper
                                                      vous-même)
      mh import                                       Récupérer ce ↩️
                                                      que seul le
                                                      NAS contient
                                                      (rien à
                                                      faire pour
                                                      l'instant)
      Pour aller plus loin
    3 mh folders add                                  Ajouter un   🔒
                                                      dossier de
                                                      photos
      Nettoyer les doublons
      Le parcours
✅  4 mh audit                                        Trouver les  🔒
                                                      doublons et
                                                      les fichiers
                                                      abîmés
    5 mh open                                         Lire les     🔒
                                                      rapports
                                                      dans votre
                                                      navigateur
👉  6 mh clean                                        Mettre les   ↩️
                                                      copies en
                                                      trop de côté
    7 mh history                                      Voir ce qu'a 🔒
                                                      fait chaque
                                                      exécution
      mh undo                                         Remettre les ↩️
                                                      fichiers de
                                                      la dernière
                                                      exécution
                                                      (rien à
                                                      faire pour
                                                      l'instant)
    8 mh review                                       Choisir les  🔒 facultatif
                                                      meilleures
                                                      photos de
                                                      chaque
                                                      rafale
    9 mh clean --tier near --decisions                Appliquer    ↩️ facultatif
                                                      vos choix
      mh purge                                        Libérer la   ⚠️
                                                      place de la
                                                      quarantaine
                                                      (rien à
                                                      faire pour
                                                      l'instant)
      Pour aller plus loin
   10 mh review --near                                Trancher les 🔒 facultatif
                                                      quasi-doubl…
   11 mh review --pairs                               Décider      🔒 facultatif
                                                      dossier par
                                                      dossier
   12 mh review --junk                                Écarter les  🔒 facultatif
                                                      photos
                                                      ratées
   13 mh review --gone                                Revoir les   🔒 facultatif
                                                      photos
                                                      disparues
   14 mh crosscheck                                   Demander un  🔒 facultatif
                                                      second avis
   15 mh shrink --try                                 Alléger les  ↩️ facultatif
                                                      vidéos
                                                      lourdes
   16 mh clean --delete                               Supprimer    ⚠️ facultatif
                                                      les copies
                                                      tout de
                                                      suite
      Trier les photos
✅ 17 mh classify                                     Proposer une 🔒
                                                      arborescence
                                                      rangée
   18 mh review-sort                                  Nommer les   🔒 facultatif
                                                      événements
   19 mh places                                       Nommer vos   🔒 facultatif
                                                      lieux sur
                                                      une carte
   20 mh people                                       Nommer les   🔒 facultatif
                                                      visages
   21 mh sort                                         Déplacer les ↩️
                                                      photos comme
                                                      le dit le
                                                      classeur
      Retrouver une photo
      Le parcours
   22 mh tags                                         Donner des   🔒
                                                      mots à vos
                                                      photos
   23 mh search                                       Retrouver    🔒
                                                      une photo
                                                      par ses mots
      Pour aller plus loin
   24 mh browse                                       Parcourir    🔒 facultatif
                                                      vos dossiers
   25 mh xmp                                          Emporter les ↩️ facultatif
                                                      mots dans
                                                      d'autres
                                                      logiciels
                                                      photo
   26 mh inventory                                    Toutes vos   🔒 facultatif
                                                      photos dans
                                                      Excel
      Sauvegarder sur le NAS
      Le parcours
      mh push --to "\\NAS\backup_photos"            Choisir le   🔒
                                                      dossier de
                                                      sauvegarde
                                                      sur le NAS
                                                      (à taper
                                                      vous-même)
   27 mh push                                       Sauvegarder  ↩️
                                                      ce qui
                                                      manque au
                                                      NAS
      Partager vos photos
      Les commandes
      mh slideshow --folder "C:\Photos\2026 Holidays" Montrer vos  🔒 facultatif
                                                      photos sur
                                                      la télé (à
                                                      taper
                                                      vous-même)
      mh share --album "Crète 2023"                   Préparer un  🔒 facultatif
                                                      album pour
                                                      l'envoyer (à
                                                      taper
                                                      vous-même)
      mh album "Crète 2023"                           Un dossier   ↩️ facultatif
                                                      de liens sur
                                                      le disque (à
                                                      taper
                                                      vous-même)
      Rapports
   28 mh reports                                      Lister les   🔒
                                                      rapports
      mh reports --prune 10                           Ne garder    🔒 facultatif
                                                      que les
                                                      rapports
                                                      récents (à
                                                      taper
                                                      vous-même)
      Réglages
      Vos dossiers
   29 mh folders                                      Voir vos     🔒
                                                      dossiers
      mh folders remove "E:\Archives"                 Retirer un   🔒 facultatif
                                                      dossier (à
                                                      taper
                                                      vous-même)
      Mise à jour
   30 mh update                                       Installer la 🔒
                                                      nouvelle
                                                      version
      Windows
   31 mh shortcut                                     Une icône    🔒 facultatif
                                                      sur le
                                                      Bureau et
                                                      dans le menu
                                                      Démarrer
   32 mh explorer                                     Media        🔒 facultatif
                                                      Hygiene dans
                                                      le clic
                                                      droit de
                                                      l'Explorate…
   33 mh explorer --remove                            Retirer      🔒 facultatif
                                                      Media
                                                      Hygiene du
                                                      clic droit
      Vie privée
   34 mh people --forget                              Oublier tous 🔒 facultatif
                                                      les visages
      Avancé
   35 mh config                                       Voir chaque  🔒
                                                      réglage et
                                                      d'où il
                                                      vient
   36 mh status                                       Où en        🔒 facultatif
                                                      suis-je,
                                                      dans la
                                                      console
   37 mh menu                                         Le menu dans 🔒 facultatif
                                                      la console
   38 mh launcher                                     Réécrire mh  🔒 facultatif
   39 mh home                                         La page      🔒 facultatif
                                                      d'accueil

🔒 vos photos ne sont pas touchées · ↩️ peut être annulé · ⚠️ définitif
🤖 classify et tags peuvent aussi interroger un modèle d'IA local : indiquez
[classify.ai] model dans config.toml (mh config).
Une étape à taper vous-même demande des mots que vous seul connaissez :
https://cavo789.github.io/media-hygiene/fr/reference-commands/
Entrée lance l'étape 6 (mh clean). Un autre numéro lance cette étape. Ctrl+C
pour quitter.
⚠️  Le menu lance ses étapes par mh : écrivez-le une fois avec 'launcher' (étape
0 des guides), puis tapez mh menu.
```

## Bon à savoir

- `menu` n'a pas d'option.
- Le menu ne répond jamais à votre place : `clean`, `sort` et `purge` demandent toujours avant
  d'agir.
- Après l'étape, le menu ne revient pas : tapez de nouveau `mh menu`, il montre où vous en êtes
  désormais. La [page d'accueil](home.md) (`mh` seul), elle, revient après chaque étape.
- Pour une session à distance, un PC lent ou sans navigateur : `mh menu` n'ouvre aucune page.
- `docker run … cavo789/media-hygiene` sans commande affiche toujours le `--help` : seul `mh` peut
  lancer l'étape choisie avec les bons dossiers.
- `docker run -it … menu` montre le menu mais ne peut lancer aucune étape : écrivez d'abord `mh`.

## Aller plus loin

- [`status`](status.md) : où vous en êtes, en détail.
- [`launcher`](launcher.md) : écrire `mh`.

## L'aide intégrée

<details>
<summary><code>menu --help</code></summary>

<!-- capture: help-menu.txt -->
```text
 Utilisation : media-hygiene menu [OPTIONS]

 🔒 Lecture seule : ne modifie jamais vos photos. Chaque étape des guides avec
 sa commande, la prochaine en premier : ce que montre 'mh' seul, Entrée la
 lance.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help  -h        Affiche ce message et quitte.                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
