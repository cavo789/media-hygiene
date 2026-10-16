# Dépannage

[Documentation](README.md) › Référence · 🇬🇧 [English](../en/reference-troubleshooting.md)

## Docker répond à la place de l'outil

*Le terme « docker » n'est pas reconnu*, *command not found*, *error during connect*, *Cannot
connect to the Docker daemon*, *permission denied … docker.sock* : l'outil n'a pas encore
démarré, c'est Docker lui-même qui manque ou est arrêté. Ouvrez Docker Desktop et attendez
*Engine running* (Windows), ou suivez [installer Docker](start/00-install-docker.md#si-ça-ne-marche-pas)
(Windows et Linux).

**Docker Desktop fermé, sous Windows**, `docker run` affiche :

```text
failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine; check if the path is correct and if the daemon is running: open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified.
```

`mh` ajoute en dessous une ligne en clair : *Docker Desktop n'est pas démarré : lancez-le depuis
le menu Démarrer, attendez qu'il dise qu'il tourne, puis tapez à nouveau la commande.* Après un
redémarrage de l'ordinateur, Docker Desktop met quelques secondes à répondre.

## Une vraie sauvegarde est vue comme des doublons

Si `D:\sauvegarde` doit rester une seconde copie de vos photos,
[excluez-la](clean/05-choose-the-kept-copy.md#exclure-un-dossier) (ou ne la montez pas). Sinon l'outil
voit ses fichiers comme des doublons, ce qui est exact.

## Un dossier est refusé parce qu'il est monté deux fois

Un dossier inclut déjà ses sous-dossiers : montez `C:\Photos` seul, pas `C:\Photos` **et**
`C:\Photos\2019`. Windows ignore la casse, Docker non : `C:\Photos` plus `C:\photos\2019`, c'est
le même dossier deux fois. L'outil le refuse plutôt que de prendre une photo pour un doublon
d'elle-même.

## OneDrive « fichiers à la demande »

Analyser un dossier dont les fichiers sont uniquement en ligne les télécharge tous. Rendez-les
d'abord disponibles hors connexion, ou laissez ce dossier de côté.

## Les disques Windows sont lents via Docker

Le premier audit lit chaque image, ainsi que chaque fichier qui a la même taille qu'un autre.
Avec [`-v media-hygiene-cache:/cache`](start/02-keep-the-cache.md), les audits suivants ne lisent que les
fichiers nouveaux ou modifiés. Rien que lister des dizaines de milliers de fichiers prend quelques
minutes : [chaque étape affiche sa progression](start/01-first-audit.md#ce-qui-saffiche-pendant-lanalyse).

## L'ordinateur est lent pendant un audit

L'outil utilise tous les processeurs pour aller plus vite. Pour en garder pour le reste :
[limiter les processeurs utilisés](reference-advanced.md#limiter-les-processeurs-utilisés).

## L'analyse s'est arrêtée pendant la nuit

L'ordinateur s'est mis en veille : Docker Desktop se met en pause avec lui, et l'exécution
s'arrête là où elle en était. Lancez-la avec [`mh`](commands/launcher.md#ce-que-mh-fait-pour-chaque-commande),
qui garde l'ordinateur éveillé jusqu'à la fin d'une commande longue, ou réglez *Veille* sur
*Jamais* dans les paramètres de Windows pour cette nuit-là. Relancez la commande : ce qui a déjà
été lu est dans le cache.

## `mh.ps1` ne peut pas être écrit : « Access to the path … is denied »

Votre antivirus bloque ce fichier : après avoir signalé quelque chose dans un dossier, certains
(Avast) refusent tout nouveau fichier au même chemin, sans nouvelle alerte. Cherchez `mh.ps1` dans
sa quarantaine et son historique ; restaurez-le, ou ajoutez une exception pour
`$HOME\media-hygiene\mh.ps1`, puis relancez la ligne `launcher` de [l'étape 0](clean/quick-guide.md).

## « Impossible de demander confirmation sans terminal interactif »

Lancez avec `-it` : sans terminal, `clean`, `sort`, `undo` (d'un tri lancé plusieurs fois) et
`purge` ne peuvent pas demander confirmation, et les couleurs sont désactivées. Dans un script, ajoutez plutôt `--yes`.

## Dossiers où l'outil ne peut pas écrire

Quand un dossier donné à `-v` n'existe pas encore, Docker le crée pour l'administrateur
(`root`), et l'outil (qui ne tourne pas en `root`) ne peut pas y écrire. La commande s'arrête
alors avant l'analyse et nomme le dossier.

- Créez vos dossiers **avant** `docker run` (`mkdir …`).
- Depuis WSL ou Linux, ajoutez `--user "$(id -u):$(id -g)"` ; un dossier déjà créé par Docker
  redevient le vôtre avec `sudo chown "$(id -u):$(id -g)" <dossier>`.
- Un `:ro` sur `/journal`, `/quarantine`, `/reports` ou `/cache` l'arrête de la même façon. Seul
  `config.toml` est facultatif : il n'est alors pas créé.
- Si seul le rapport échoue après un audit, un avertissement le signale et les résultats restent
  à l'écran.

## C: est plein après un nettoyage

Les photos étaient sur un autre disque que la quarantaine : chaque fichier mis de côté a été copié
sur le disque de la quarantaine (avec `mh`, `C:`). `clean` le dit avant de demander, et refuse
quand les fichiers ne tiendraient pas
([nettoyer, étape 8](clean/08-clean.md#photos-sur-un-autre-disque-que-la-quarantaine)). Pour
récupérer la place, vérifiez les fichiers mis de côté, puis effacez-les avec `purge`
([étape 9](clean/09-undo-history-purge.md)). Pour le prochain nettoyage, donnez à ce disque sa
propre quarantaine : `mh` le fait pour chaque disque de ses dossiers de photos (`mh folders add`),
ou `-v "E:\media-hygiene\quarantine:/quarantine/e"`.

## `undo` demande de brancher un disque déjà branché

`undo` ou `purge <exécution>` dit *… mis de côté dans la quarantaine de E:, qui n'est pas montée*
alors que le disque USB est branché : Windows lui a donné une autre lettre. Gardez un de ses
dossiers de photos dans `mh` (`mh folders add "F:\Photos"`, qui monte aussi la quarantaine de
`F:`) : l'exécution est alors retrouvée dans la quarantaine de `F:`, et `undo` le dit. S'il dit
que l'exécution est dans deux quarantaines, l'une est une copie faite à la main : gardez-en une.

## Un chemin Windows de `config.toml` est refusé

Écrivez les chemins Windows entre **apostrophes** : `'D:\backup'`. Entre guillemets, TOML
transforme le `\b` de `"D:\backup"` en caractère de contrôle, et l'outil refuse ce chemin au lieu
de l'ignorer ([étape 7 du nettoyage](clean/07-configuration-file.md#le-remplir)).

## Un réglage de `config.toml` est inconnu de cette version

```text
❌ « timezon » dans [general] de config.toml n'existe pas dans la version 0.3.0 : une faute de
frappe, ou un réglage d'une version plus récente ? Vouliez-vous dire « timezone » ?
💡 Corrigez ou supprimez la ligne, ou mettez l'image à jour :
docker pull cavo789/media-hygiene
```

Une faute de frappe est nommée avec le réglage qui lui ressemble. Un réglage copié d'une
documentation plus récente demande l'image plus récente : `docker pull cavo789/media-hygiene`. Il
en va de même pour une variable `MEDIA_HYGIENE_<SECTION>__<CLÉ>` passée avec `-e`. Une valeur
refusée (`verbosity = "loud"`) dit ce qui est attendu à la place. Plusieurs problèmes à la fois
sont listés un par ligne, sous un seul titre. Un problème dans une entrée `[[classify.rules]]`,
un lieu ou une personne la nomme par son numéro et son `name` : `« match » dans
[[classify.rules]] n° 2 (« Anniversaire ») de config.toml : ce réglage est obligatoire.`

## La page de tri ne s'ouvre pas

- Avec `mh review`, votre navigateur s'ouvre tout seul sur la page, dès qu'elle répond.
- Avez-vous publié le port ? La commande a besoin de `-p 127.0.0.1:8088:8088` : le même numéro des
  deux côtés, sinon l'adresse affichée par le tri n'est pas la bonne
  ([étape 10 du nettoyage](clean/10-review-bursts.md#étape-2--ouvrir-la-page)).
- *port is already allocated* : un autre programme utilise 8088. Choisissez un autre numéro, le
  même trois fois : `-p 127.0.0.1:9000:9000` et `review --port 9000`.
- Ouvrez-la avec `127.0.0.1` ou `localhost` : la page refuse les autres noms d'hôte.
- *« Le tri ne tourne plus »* : la fenêtre du tri a été fermée ou arrêtée avec Ctrl+C.
  Relancez-le ; vos choix sont conservés.

## Les accents s'affichent mal avec `type` dans PowerShell

`type .\decisions.json` affiche `DÃ©cembre` au lieu de `Décembre` : le fichier est bon. L'outil
l'écrit en UTF-8, comme le veut JSON, et Windows PowerShell 5.1 lit un fichier sans marque
d'ordre des octets (BOM) dans l'ancienne page de code de Windows. Pour le voir correctement :

```powershell
Get-Content -Encoding UTF8 .\decisions.json
```

PowerShell 7 et le Bloc-notes l'affichent correctement tel quel. L'outil relit aussi les
fichiers réécrits par les outils Windows : « UTF-8 avec BOM » du Bloc-notes,
`Set-Content -Encoding UTF8`, ou l'UTF-16 de `>` et `Out-File`. Il en va de même pour
`config.toml`.

## `mh` monte un dossier vide au lieu d'un dossier accentué

Un `mh.ps1` écrit par une image plus ancienne contient `Vid├®os` là où votre dossier s'appelle
`Vidéos` : PowerShell a décodé la sortie de l'outil avec l'ancienne page de codes de la console
avant que `>` ne l'enregistre. `mh` monte alors un dossier qui n'existe pas, Docker Desktop le crée
vide, et l'audit n'y trouve rien. Relancez `launcher`, avec les mêmes dossiers, vers le même
fichier : le nouveau script ne contient que de l'ASCII et garde chaque accent.

## Une commande du guide est inconnue

*No such command*, ou `mh` affiche l'aide de l'image à la place : votre image est plus ancienne
que le guide. Tapez `mh update` : il télécharge la nouvelle version et réécrit `mh` avec vos
dossiers. Un `mh` plus ancien que `mh update` lui-même ne le connaît pas : relancez une fois la
ligne `launcher` du [guide](clean/quick-guide.md#0-une-seule-fois--écrire-la-commande-mh), avec
vos dossiers.

## « Erreur inattendue pendant … »

Un bogue de l'outil, pas une erreur de votre part. Le message dit ce qui a échoué et si vos
photos ont été touchées : une commande en lecture seule n'y touche jamais ; après `clean` ou
`sort`, ce qui a déjà été fait est dans le journal, et `undo` le remet en place.

Merci d'[ouvrir un ticket](https://github.com/cavo789/media-hygiene/issues) avec la version, la
commande tapée et le message : la dernière ligne 💡 contient les trois. Pour plus de détails,
relancez la même commande avec `-e MEDIA_HYGIENE_DEBUG=1` après `docker run` : elle montre alors
où l'erreur s'est produite (la trace Python), à coller aussi dans le ticket.
