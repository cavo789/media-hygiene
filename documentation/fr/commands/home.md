# `home` : la page d'accueil, dans votre navigateur

[Documentation](../README.md) › [Commandes](../reference-commands.md) › `home` · 🇬🇧 [English](../../en/commands/home.md)

> `mh` seul ouvre cette page ; `mh home` reste là pour un script, mais `mh --help` ne la liste plus.

## En bref

**Une page dans votre navigateur : où en sont vos photos, l'étape suivante en un gros bouton,
chaque action de l'outil à un clic ou à <kbd>Ctrl</kbd>+<kbd>K</kbd>.**

`home` montre dans votre navigateur ce que [`status`](status.md) et [`menu`](menu.md) montrent
dans le terminal, rangé comme le cycle de vos photos : **Importer** (un téléphone, votre NAS ou
un ancien disque), **Nettoyer**, **Trier**, **Retrouver**, **Sauvegarder** (prévu) ; puis, à part du cycle, **Partager**
(vos photos sur la télé : [`slideshow`](slideshow.md), un dossier ou un
[album](search.md#mettre-des-photos-dans-un-album)) et trois outils : **Historique et annulation**,
**Rapports**, **Réglages**. Chaque espace a sa page : son
parcours, numéroté, puis « Pour aller plus loin ». Chaque action montre sa commande `mh`, à
copier, et mène à son chapitre de cette documentation. La page peut aussi lancer l'audit
elle-même, sa progression affichée dans la page.

**Quand** : chaque fois que vous préférez cliquer plutôt que taper, ou que vous ne savez plus
quelle est la suite.

**Essayer** :

```powershell
docker run --rm -it `
  -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/[cache](../reference-glossary.md#cache) `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene home
```

![La page d'accueil : le menu de gauche avec les cinq étapes du cycle et les outils, l'étape suivante en gros bouton, le cycle, les tuiles de là où vous en êtes, ce que le dernier audit a trouvé, les rapports et l'audit dans la page](../images/home.webp)

## D'un coup d'œil

| | |
|---|---|
| Vos photos | 🔒 Rien ne bouge sans votre GO sur une page (review-sort, search), noté au journal : `undo` le remet. `mh home` les monte accessibles en écriture, avec `/journal` ; l'audit lancé depuis la page ne fait que les lire. |
| Il faut | Les dossiers de l'outil (`/reports`, `/journal`, `/quarantine`, `/cache`), comme pour `status` ; vos dossiers pour l'audit ; `-p 127.0.0.1:8088:8088` pour la page. |
| Écrit | Rien par elle-même ; l'audit lancé depuis la page écrit son cache et son rapport, comme `audit` ; la [page des albums](#vos-albums-sur-le-téléphone) ne change que `albums.json`. |
| Annuler | Rien à annuler ; chaque étape garde sa propre annulation. |
| Avec `mh` | `mh home`. |

## Ce que montre la page

- **Le menu de gauche** : les cinq étapes du cycle, **Partager** (un but, pas une étape : sans numéro) et les outils, chacun avec son compte (*9*
  copies à mettre de côté, *214* fichiers que seul le NAS garde), *Vos dossiers* (chacun trouvé
  ou non), la version (*0.5.0 disponible* quand une plus récente est publiée,
  [`mh update`](launcher.md#une-nouvelle-version--mh-update)) et le choix du thème.
- **Un bandeau quand `mh` est plus ancien que son image** (une nouvelle image téléchargée ou
  construite, `mh` pas réécrit) : la ligne que dit la console, et un bouton **Mise à jour**
  qui lance [`mh update`](launcher.md#une-nouvelle-version--mh-update) ; il disparaît dès que
  `mh` est réécrit.
- **La barre du haut** : *Que voulez-vous faire ?* (la palette), **Annuler la dernière
  exécution** tant qu'une exécution est annulable, et **Documentation** : le chapitre de la page
  où vous êtes, et son jumeau anglais.
- **L'étape suivante** : pourquoi, ce qu'elle risque en mots (*Annulable*), le bouton qui la
  lance et sa commande : *le dernier audit a trouvé des copies en trop : 'clean' les met de
  côté*, **mh clean**. Son bouton a le focus à l'ouverture : <kbd>Entrée</kbd> la lance, comme
  dans `mh menu`. Quand tout est appliqué, la page le dit.
- **Le cycle de vos photos** : les cinq étapes, la prochaine mise en évidence (*Vous êtes ici*),
  chacune avec une ligne (*9 copies à mettre de côté*, *Une proposition à appliquer*) et le
  nombre d'étapes faites de son parcours.
- **Où vous en êtes** : une tuile par fait (le dernier audit, les copies en trop, la
  quarantaine, les fichiers seulement sur le NAS, le tri, les mots, les visages), chacune mène à
  son espace.
- **Ce que le dernier audit a trouvé** : chaque constat avec son bouton (*9 copies
  identiques* : **Mettre les copies en trop de côté** ; *3 fichiers illisibles* : le rapport), et
  quelques aperçus de son rapport. Avant tout audit : trois choses à savoir (rien ne bouge sans
  vous, tout ce qui bouge s'annule, une seule chose est définitive).
- **Rapports récents**, et **Auditer dans cette page** 🔒 : **Auditer maintenant** lit vos
  dossiers comme `mh audit`, avec les mêmes réglages. Chaque étape s'affiche avec ses comptes au
  fil de l'eau ; à la fin, les chiffres de l'audit, le temps de chaque étape, *Ce que vous
  pouvez faire*, et un lien vers le nouveau rapport. Un audit à la fois ; **Arrêter l'audit**
  l'arrête entre deux fichiers : le cache garde ce qu'il a lu, et l'audit suivant repart de là.
- **Une page par espace** : son parcours, numéroté, puis « Pour aller plus loin » en cartes.
  Chaque action dit ce qu'elle risque (🔒 *Photos intactes*, ↩️ *Annulable*, ⚠️ *Définitif*),
  *Facultatif*, *Windows*, *IA locale* (🤖), *Prévu* ; **Fait** quand les dossiers de l'outil le
  prouvent ; quand elle ne peut pas encore tourner, pourquoi à la place de son texte (*Rien à
  annuler pour l'instant.*). *Historique et annulation* montre l'exécution encore annulable et
  la quarantaine par exécution ; *Réglages* vos dossiers, la mise à jour, Windows, l'IA locale,
  la vie privée, les actions avancées et *À propos*.

Ouverte par un clic droit sur un dossier (ou `mh --photos "E:\Dossier"`), la page nomme ce
dossier en premier : *Cette page analyse aussi : E:\Dossier* ; l'audit de la page et chaque
étape lancée depuis elle l'analysent aussi.

## Lancer une étape

La page ne modifie jamais vos photos elle-même. Ce que fait le bouton d'une étape dépend du `mh`
qui a ouvert la page :

- **`mh` seul** (et donc le raccourci du Bureau et le clic droit d'un dossier) lance les étapes
  de la page : **Lancer** (ou le gros bouton) confie l'étape à `mh`, dans la fenêtre où `mh`
  tourne (PowerShell sous Windows), avec les dossiers dont l'étape a besoin. Avec les rapports
  dans un dossier de votre disque (le cas par défaut), la page **reste ouverte** pendant qu'une
  étape tourne dans cette fenêtre : *mh clean s'exécute dans la fenêtre PowerShell de mh (dans
  la barre des tâches) : répondez-y s'il vous demande quelque chose. Cette page reste ouverte
  et montre le résultat à la fin* ; puis *mh clean : terminée.* et la page montre son nouvel
  état, sans se recharger. *search* s'ouvre aussitôt dans ce même onglet,
  servies par la page d'accueil elle-même ; une étape qui ouvre une autre page à elle (review,
  people…) ferme celle-ci entre-temps : *Retour à l'accueil* la ramène. Une deuxième étape demandée pendant
  qu'une autre tourne attend : *Une étape tourne dans la fenêtre de mh : attendez sa fin.*
  Sinon (rapports dans un volume nommé, un `mh` plus ancien), la page se ferme et revient
  d'elle-même après l'étape. Dans les deux cas, la page dit aussitôt, en gras, *Passez maintenant à la fenêtre PowerShell de mh (dans la barre des
  tâches) (Alt+Tab, ou son bouton dans la barre des tâches) : mh peut vous y demander quelque
  chose*. `mh` fait aussi sonner la cloche du terminal et joue le son de Windows, souvent
  inaudible (haut-parleurs coupés). Ce qui se voit : Windows Terminal fait clignoter son bouton
  dans la barre des tâches sur cette cloche une fois ses paramètres réglés (par défaut, le son
  seulement) : *Paramètres* → *Ouvrir le fichier JSON*, puis `"bellStyle": "taskbar"` dans
  `profiles` → `defaults` (`["audible", "taskbar"]` pour garder le son). Avec la console
  classique, `mh` ramène aussi sa fenêtre au premier plan quand Windows le permet (une fenêtre
  réduite reste réduite). Après 30
  secondes elle ajoute *Rien ne bouge ? Regardez la fenêtre PowerShell de mh (dans la
  barre des tâches) (Alt+Tab)*. L'étape choisie arrive à `mh` par `.mh-step.json` de votre dossier
  des rapports, comme les mots d'un formulaire ci-dessous : `mh` les lance aussitôt (il lançait
  d'abord `mh menu` dans un conteneur à lui, 2 s par clic). Avec des rapports dans un volume
  nommé, c'est le code de sortie de la commande, `20 + n` pour l'étape `n` de `mh menu`.
  L'onglet montre la page suivante dès que son serveur répond. Ctrl+C pendant une
  étape (ou sur une page qu'elle a ouverte) rend l'invite : la page d'accueil ne revient pas,
  et aucune autre étape ne se lance.
- **Une étape qui prend des mots** (le nom d'un album, le dossier de votre NAS,
  un dossier à retirer, combien de rapports garder) : **Compléter** ouvre son formulaire,
  l'exemple déjà rempli. Le serveur vérifie chaque valeur et dit pourquoi il en refuse une (*pas
  de guillemet double*, *aucun caractère de contrôle*, *elle ne peut pas commencer par '-'*, *un
  dossier tel que l'Explorateur le montre*) ; puis il écrit les mots dans `.mh-step.json` de
  votre dossier des rapports et s'arrête avec `199`. `mh` lit ce fichier une fois, le retire, et
  lance ces mots : `Noël 2025` reste un seul mot. Avec des rapports dans un volume nommé, ou un
  `mh` plus ancien, la page donne la commande à copier à la place.
- **⚠️ Définitif** (`purge`, `clean --delete`, `import --phone --free`) : la page demande d'abord ; `mh`
  redemande dans sa fenêtre avant de toucher quoi que ce soit.
- **Sinon** (`mh home` tapé, un `mh` plus ancien, ou `docker run` seul) : le bouton copie la
  commande (*Commande copiée*) et la page continue ; arrêtez-la avec Ctrl+C dans la fenêtre où
  `mh` tourne, collez-y la commande (clic droit) et appuyez sur Entrée. Quand le navigateur
  refuse de copier (une adresse autre que `127.0.0.1` ou `localhost`), la commande est
  sélectionnée : faites Ctrl+C.

Chaque autre page ([`review`](review.md), [`review-sort`](search.md#les-événements-du-dernier-classify),
[`places`](places.md), [`search`](search.md), [`people`](people.md))
prend l'allure et le thème de la page d'accueil, sous une barre : **Documentation** ouvre le
chapitre de cette page, à côté de son jumeau anglais (*In English*). Quand la page d'accueil l'a
ouverte, la page s'affiche dans **le même onglet** (pas de nouvel onglet), et **⌂ Retour à
l'accueil** la ferme (ce que vous y avez décidé est déjà enregistré) et ramène cet onglet à la
page d'accueil, sur l'espace que vous aviez quitté (*Nettoyage*, *Tri*…). Fermer l'onglet, au
contraire, arrête la page et `mh` avec elle : l'invite revient.

La documentation elle-même est dans l'image : chaque lien **Doc** et **Documentation** de ces
pages ouvre son chapitre servi par l'outil, avec la même allure, hors ligne, et écrit pour la
version que vous utilisez (le site peut déjà décrire une version plus récente). Sa barre latérale
liste chaque chapitre, sa barre du haut passe à l'autre langue (**EN**), chaque page liste ses
sections et se termine sur la précédente et la suivante. Les liens qu'affiche le terminal, et
les rapports HTML ouverts depuis le disque, mènent toujours au
[site](https://cavo789.github.io/media-hygiene/) : aucune page de l'outil n'y répond.

## Depuis un téléphone du Wi-Fi de la maison : `mh --lan`

Sous Windows, **`mh` et son raccourci du bureau ouvrent la page d'accueil aux téléphones du
même Wi-Fi aussi**, jusqu'à l'arrêt de `mh` : c'est le défaut (`lan = true`). Vous préférez la
page sur ce PC seulement ? Voyez [Garder la page sur ce PC seulement](#garder-la-page-sur-ce-pc-seulement)
plus bas.

1. `mh` trouve l'adresse du PC sur le réseau de la maison (*192.168.1.20*) et dit *La page
   d'accueil s'ouvre aussi aux téléphones du réseau de la maison*. Windows peut demander si
   **Docker Desktop** peut accepter des connexions : autorisez-le sur les **réseaux privés**
   seulement.
2. La page du PC montre, dans sa barre latérale, *Sur votre téléphone* : l'adresse, un **code**
   de 8 chiffres et son **QR code** (la fenêtre de `mh` dit la même adresse et le même code).
3. Sur le téléphone, scannez le QR code, ou ouvrez l'adresse et tapez le code : la page d'accueil
   s'ouvre. Le téléphone reste appairé **pour de bon** (un cookie à lui, 400 jours) : le
   `mh --lan` suivant s'y ouvre sans code. Sans HTTPS, jusqu'à l'arrêt de `mh` seulement.

Sur le téléphone, la page d'accueil est la porte de la famille, **Nos photos** : *Retrouver une
photo* (la recherche et le parcours), les albums et où vous en êtes ; les étapes qui changent les
photos (importer, nettoyer, trier, sauvegarder) et les outils n'y sont pas montrés, le PC garde
tout le cycle.

🔒 **Le téléphone ne fait que lire : tout changement se fait sur le PC.** Depuis le téléphone : la page, où vous en êtes, les rapports, l'avancement d'un audit lancé sur le PC,
[vos albums](#vos-albums-sur-le-téléphone), ainsi que **la recherche** et **le parcours** (leurs
photos ouvertes à la taille du téléphone, et leurs vidéos ; les originaux seulement avec `lan_phone_originals = true` sous `[review]` de `config.toml`, désactivé par défaut : pleine taille, position GPS comprise ; *mettre de côté*, *Appliquer maintenant* et un
déplacement restent au PC). Seul un téléphone appairé les atteint : tout autre appareil du Wi-Fi
(un invité, une télé) reçoit la page d'appairage, ou rien, à toute adresse. Tant que le téléphone montre une page, `mh` continue même onglet du
PC fermé ; une fois `mh` arrêté, la page du téléphone le dit.
Toute autre étape reste sur le PC (*Lancez cette étape sur le PC*) : ses questions sont posées
dans la fenêtre de `mh`, que personne ne voit depuis le canapé. Une exception :
**Montrer sur la télé**, sur la page du téléphone, propose trois choix : un album enregistré sur
le PC, **un dossier** (un des dossiers analysés) ou **un mois** (selon la date lue par l'audit).
Un appui lance ce [diaporama](slideshow.md) dans le serveur même de la page d'accueil, et le
téléphone ouvre aussitôt sa télécommande. Il ne fait que montrer : rien n'est écrit, rien ne
bouge. Aucun album enregistré : le dossier et le mois restent là. Le favori de la télé
(`http://<adresse du PC>:8089/screen`) attend un diaporama et reste appairé tant que `mh` tourne.

L'étape *Montrer vos photos sur la télé*, choisie sur le PC, ouvre aussi le [diaporama](slideshow.md)
au réseau de la maison : le téléphone déjà appairé recharge sa page et obtient la télécommande du
diaporama.

| | |
|---|---|
| Qui | Un appareil du même Wi-Fi **avec le code** ; 5 codes erronés ferment l'appairage jusqu'à l'arrêt de `mh`. |
| Où | L'adresse privée du PC seulement (`10.x`, `172.16–31.x`, `192.168.x`) : jamais toutes les interfaces, jamais Internet ; `mh` n'ouvre aucun port sur votre box. |
| Comment | HTTPS (`https://192.168.1.20:8088`), signé par une autorité de certification que `mh` crée sur votre PC : le téléphone l'installe une fois (ci-dessous) ; le code et le cookie ne circulent jamais en clair. |
| Gardé | `C:\Users\<vous>\media-hygiene\lan\` contient cette autorité et le certificat de la page (`ca.key` n'en sort jamais). Supprimé, `mh` en crée une nouvelle : réinstallez-la sur chaque téléphone. |
| La fois suivante | Un téléphone appairé ouvre la page directement. La carte du PC liste les **téléphones appairés pour de bon** (Android, iPhone… et la date) avec **Oublier ce téléphone** : son cookie n'ouvre plus rien. `phones.json` (dans le dossier `lan`) ne garde qu'un hash du jeton de chaque téléphone. |

### Une fois par téléphone : installer le certificat

La carte du PC dit *Première fois sur ce téléphone ? Installez d'abord le certificat :*
`http://192.168.1.20:8089/`. Ouvrez-la sur le téléphone, touchez **Télécharger le certificat**,
puis :

- **Android** : dans l'appli **Paramètres du téléphone** (la roue dentée de l'écran d'accueil,
  pas les paramètres de Chrome). N'appuyez pas sur *Ouvrir* après le téléchargement : Android 11
  et plus le refuse (*Impossible d'installer les certificats AC*).
  1. **Samsung** : *Paramètres › Sécurité et confidentialité › Autres paramètres de sécurité ›
     Installer depuis stock. appar. › Certificat AC › Installer quand même*.
     **Autres téléphones** (Pixel…) : *Paramètres › Sécurité › Autres paramètres › Chiffrement
     et identifiants › Installer un certificat › Certificat CA › Installer quand même*.
  2. Ouvrez le dossier *Download* et touchez `media-hygiene-ca.crt`.

  Android prévient que le réseau peut être surveillé : c'est votre propre PC. Le télécharger
  ne suffit pas, et **Certificat CA** compte (ni *VPN et appli*, ni *Wi-Fi*). Vérifiez : *Identifiants de confiance › Utilisateur* montre
  *Media Hygiene (this PC)*, et Chrome affiche `https` sans croix rouge ; sinon *Installer*
  échoue (*Impossible d'installer cette appli*).
- **iPhone, iPad** (dans Safari) : autorisez le profil, installez-le dans *Réglages › Général ›
  VPN et gestion de l'appareil*, puis activez **Media Hygiene** dans *Réglages › Général ›
  Informations › Réglages des certificats*.

Touchez ensuite **C'est fait : ouvrir Média Hygiène**, et appairez avec le code comme plus haut.
Quand l'adresse du PC change, `mh` signe pour elle un nouveau certificat avec la même autorité :
rien à réinstaller. Demandez à votre box une **réservation DHCP** du PC pour garder la même
adresse, et le favori du téléphone. Le [diaporama](slideshow.md) reste en HTTP simple : une
télé ne peut pas installer de certificat.

### Média Hygiène comme une app sur le téléphone

Une fois appairé en HTTPS, le téléphone peut garder la page d'accueil comme une app, avec le
suricate pour icône : **Android** (Chrome) propose *Installer l'application* (ou ⋮ › *Ajouter à
l'écran d'accueil*) ; sur un **iPhone**, Safari le dit en une ligne : *Partager*, puis *Sur
l'écran d'accueil*. L'icône ouvre alors directement la page d'accueil, sans QR code ni code.
Quand Média Hygiène ne tourne pas sur le PC, l'app montre le suricate endormi, *Média Hygiène
dort*, au lieu de l'erreur du navigateur, et rouvre la page d'elle-même dès que `mh` tourne.
L'app ne garde que cette page : jamais une photo. Rien n'est publié : ni magasin, ni compte, ni
Internet.

Le téléphone n'ouvre pas la page ? La carte *Sur votre téléphone* dit pourquoi : *Aucun réseau
domestique trouvé* (la page s'ouvre pour le PC seul, rien n'échoue), ou Windows considère le
Wi-Fi comme **public** : passez-le en privé dans *Paramètres › Réseau et Internet › Wi-Fi ›
Réseau privé*. La première fois, Windows peut poser une fois la question pour Docker Desktop :
cochez **Réseaux privés**, puis **Autoriser**.

### Garder la page sur ce PC seulement

Pas de téléphone à la maison, ou vous n'en voulez pas ? Coupez-le une fois, dans `config.toml` :

1. Dans Windows PowerShell, ouvrez le fichier (`mh config` le crée la première fois) :

   ```powershell
   mh config
   notepad "$HOME\media-hygiene\config\config.toml"
   ```

2. Trouvez la ligne `lan = true` (sous `[review]`) et changez-la en :

   ```toml
   lan = false
   ```

3. Enregistrez, fermez le Bloc-notes, puis tapez `mh update` (il écrit le changement dans `mh`
   et le raccourci).

Dès lors, `mh` et son raccourci gardent la page sur ce PC : pas de carte *Sur votre téléphone*,
pas de question du pare-feu de Windows. Pour une soirée avec un téléphone, tapez `mh --lan` :
la page s'ouvre au Wi-Fi pour cette fois seulement. Pour la rouvrir à chaque fois, remettez
`lan = true`, puis `mh update`.

Windows PowerShell seulement pour l'instant.

## Vos albums, sur le téléphone

À la maison, montrez un album à la famille **sur votre propre téléphone**, sans la télé :
appairez-le une fois avec `mh --lan` (ci-dessus), puis touchez **Ouvrir les albums** sur sa page
d'accueil (ou, sur le PC, *Partager › Vos albums*). Les proches regardent votre écran et
n'appairent rien.

- **La liste** : chaque [album](search.md#mettre-des-photos-dans-un-album), sa couverture, ses
  dates, son lieu et combien de photos il contient.
- **Un album**, comme le montrent les grandes applications de photos : une **couverture** (la
  photo la plus nette du premier jour), le nom de l'album, ses dates et son lieu (nommé hors
  ligne, d'après le GPS des photos), puis une **mosaïque** groupée par jour, *lundi 10 juillet
  2023 · Héraklion*.
- **Un toucher** ouvre la photo en plein écran ; **un glissement** passe à la suivante ou à la
  précédente ; **un toucher** (ou le *Retour* du téléphone) la ferme. Les photos suivantes sont
  chargées d'avance.
- **Les vidéos** se lisent sur place, comme sur la télé : le H.264 tel quel ; un autre format
  (HEVC, AVI) est signalé, jamais converti.
- 🔒 **Lecture seule** : les albums se font et se changent sur le PC (*➖ Retirer*, *➕ Ajouter*,
  *🖼 Couverture*, [la référence des albums](../reference-albums.md)) ; le téléphone les montre.

| | |
|---|---|
| Vos photos | 🔒 Seulement lues. Le téléphone reçoit des images à sa taille (1440 pixels au plus, gardées dans `/cache`), un original seulement avec `[review] lan_phone_originals = true`. |
| Ce que le téléphone atteint | Les albums et **leurs** fichiers ; le reste de votre bibliothèque par *Rechercher* et *Parcourir* seulement (en lecture). |
| Où | Le Wi-Fi de la maison seulement, tant que `mh` tourne sur le PC (dit sur la page). |

## Le clavier, la palette, le thème

| Touche | Ce qu'elle fait |
|---|---|
| <kbd>Entrée</kbd> | À l'ouverture, lance l'étape suivante : son bouton a le focus. |
| <kbd>Ctrl</kbd>+<kbd>K</kbd> ou <kbd>/</kbd> | *Que voulez-vous faire ?* : chaque action et chaque espace, trouvés par des mots de tous les jours (*téléphone*, *NAS*, *annuler*), puis les sections de la documentation (ouvertes dans un nouvel onglet) ; <kbd>↑</kbd> <kbd>↓</kbd> choisissent, <kbd>Entrée</kbd> lance. |
| <kbd>↑</kbd> <kbd>↓</kbd> | Dans le menu de gauche, d'un espace à l'autre (un seul arrêt de <kbd>Tab</kbd> pour tout le menu). |
| <kbd>?</kbd> | Les touches. |
| <kbd>Échap</kbd> | Ferme ce qui est ouvert. |

Un parcours au clavier seul : <kbd>Tab</kbd> une fois montre *Aller au contenu* ;
<kbd>Entrée</kbd> dessus saute le menu de gauche. <kbd>Maj</kbd>+<kbd>Tab</kbd> revient au menu,
<kbd>↓</kbd> jusqu'à *Nettoyer*, <kbd>Entrée</kbd> ouvre sa page. <kbd>Ctrl</kbd>+<kbd>K</kbd>,
tapez *téléphone*, <kbd>Entrée</kbd> : l'étape du téléphone se lance. Rechargez la page :
<kbd>Entrée</kbd> lance l'étape suivante. Le contour du focus ne s'affiche qu'au clavier ; les
messages passagers sont lus par les lecteurs d'écran.

Le thème suit Windows (clair ou sombre) ; **Auto**, **Clair** et **Sombre** en bas du menu de
gauche choisissent pour ce navigateur. Les animations s'arrêtent quand Windows demande moins de
mouvement. Les polices et les images viennent de l'image elle-même : la page ne demande rien à
aucun autre site.

## Options

| Option | Rôle |
|---|---|
| `--port PORT` | Port de la page, 8088 par défaut ; publiez le même. |

## Bon à savoir

- **Une clé USB ou un disque branché plus tard** (0359) : `mh` démarre la page d'accueil sans
  un dossier de photos absent (une ligne : *pas branché, affiché dès qu'il l'est*), regarde vos
  dossiers toutes les 3 secondes et relance la page avec le dossier dès qu'il est branché
  (2 à 3 s environ ; l'onglet se recharge seul). De même quand il est retiré. Une commande tapée
  seule refuse toujours un dossier absent.
- La page ne répond qu'à `127.0.0.1` ou `localhost` (et, sous `mh --lan`, à l'adresse du PC pour
  un téléphone appairé), et seulement à ses propres boutons : un autre site ne peut pas choisir
  une étape à votre place.
- Fermer l'onglet de la page, ou Ctrl+C dans le terminal arrête la
  page et rend l'invite ; un audit en cours s'arrête entre deux fichiers. Un onglet fermé est vu
  une dizaine de secondes plus tard (*L'onglet de la page d'accueil a été fermé : la page d'accueil
  s'est arrêtée.*) ; un rechargement, ou un onglet laissé en arrière-plan, ne l'arrête jamais.
- Les étapes sont relues dans les dossiers de l'outil à chaque chargement de la page : ce
  qu'une autre fenêtre a fait apparaît au rechargement suivant. Un bouton d'une page dessinée
  avant un tel changement est refusé (*Les étapes ont changé depuis l'affichage de la page*) et
  la page remontre les étapes.
- `config.toml` est relu quand vous le modifiez, y compris pour le prochain audit lancé depuis la
  page. Une faute de frappe qui le rend illisible est signalée en haut de la page (*…config.toml
  ne peut pas être lu : … Les derniers bons réglages restent jusqu'à sa correction.*) ; la ligne
  disparaît une fois le fichier corrigé.
- Si la page s'arrête de façon inattendue (un bug, Docker à court de mémoire), `mh` la relance
  tout seul (*La page d'accueil s'est arrêtée de façon inattendue : relancée.*) ; un second arrêt
  dans la minute rend l'invite.

## Aller plus loin

- [`menu` : les mêmes étapes dans le terminal](menu.md)
- [`status` : où vous en êtes, en une seconde](status.md)

## L'aide intégrée

<details>
<summary><code>home --help</code></summary>

<!-- capture: help-home.txt -->
```text
 Utilisation : media-hygiene home [OPTIONS]

 🔒 Lecture seule : ne modifie jamais vos photos. La page d'accueil dans votre
 navigateur : où vous en êtes, l'étape suivante en un bouton, toutes les étapes
 des guides, les rapports.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --port          <int range> [x>=1]  Port de la page. docker run le publie    │
│                                     sous le même numéro sur votre            │
│                                     ordinateur, par exemple -p               │
│                                     127.0.0.1:9000:9000 pour --port 9000.    │
│                                     Par défaut :  port dans config.toml,     │
│                                     8088.                                    │
│ --help  -h                          Affiche ce message et quitte.            │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [Toutes les commandes](../reference-commands.md) · [Documentation](../README.md)
