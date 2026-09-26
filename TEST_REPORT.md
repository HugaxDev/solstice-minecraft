# Rapport de tests — SOLSTICE 1.0

Généré automatiquement par `tools/report.py` le 2026-09-26 05:01 (relancé à chaque `./build.sh`).

## Résumé

| Étape | Résultat |
|---|---|
| py_compile + lint JSON + références (fonctions, advancements, loot, prédicats, blocs, objets) | OK — 50 fichiers Python, 50 JSON, 1083 fonctions (34551 commandes), 30 advancements |
| Audit des sélecteurs (jeu à 3 : pas de @p/@r, pas de sélection d’un joueur unique, @s toujours avec exécutant) | OK — 1083 fonctions, 2345 usages de @s vérifiés |
| Registre d’énigmes (aucun type répété sur la carte) | OK — 37 énigmes, 37 types distincts |
| Monde construit par un serveur **vanilla** : `test/all` structurel | **97/97 PASS** |
| Erreurs/avertissements du datapack dans les logs (build) | 0 |
| Advancements chargés | 1429 (attendu 1429) |
| Scénarios E2E, 3 joueurs factices (toutes les salles, salle 5 comprise) | **359/359 PASS** |
| Parcours complet + indices progressifs + mode 1 joueur | **28/28 PASS** |
| Processus orphelins / ports ouverts après les runs | 0 / aucun |
| Durée estimée (découverte) | **116.2 min** (cible 105–120) |
| Monde livré : `level.dat` au premier niveau du dossier une fois dézippé | vérifié |

## Méthode

1. `src/build_packs.py` génère tout le datapack (et le resource pack) ; `tools/lint.py` valide chaque bloc, état de bloc et objet contre les rapports officiels extraits du `server.jar` 1.21.1.
2. `tools/worldbuild.py` construit le monde sur un **serveur vanilla** headless (127.0.0.1), vérifie chaque commande de biome, lance `test/all`, analyse les logs, puis nettoie `level.dat`.
3. `tools/tests.py` rejoue la partie sur une **copie** du monde, serveur Fabric + **Carpet (tests uniquement)**, avec 3 joueurs factices : chemin nominal de chaque salle, tirages de rôles répétés, mort d’un joueur, mort des 3, déconnexion/reconnexion, retour arrière impossible.
4. `tools/test_journey.py` : parcours complet du prologue aux crédits (ordre, retours interdits vers chaque salle précédente), indices progressifs, mode debug à 1 joueur.
5. `tools/package.py` : zips contrôlés (dézippage réel), aucune trace de Fabric/Carpet dans le monde.

## Scénarios E2E par section

Le détail nominatif des tests dévoile des solutions (et l’enquête) : il est rangé dans `design/SPOILERS_NE_PAS_LIRE/TEST_REPORT_DETAILLE.md`.

| Section | Résultat | Ce qui est couvert |
|---|---|---|
| général | ✅ 1/1 | chargement des zones de jeu |
| prologue | ✅ 22/22 | attente des 3 joueurs, cinématique, PNJ cliquables, indices, Carnet, tirages au sort répétés, embarquement |
| tirages au sort | ✅ 4/4 | 30 tirages : rôles uniques, hasard réel, exclusion du précédent |
| salle 1 : rôles | ✅ 9/9 | rôles et postes réservés, chaque évènement du trajet en réussite et en erreur, parcours complet, mort, reconnexion |
| salle 1 : postes | ✅ 9/9 | rôles et postes réservés, chaque évènement du trajet en réussite et en erreur, parcours complet, mort, reconnexion |
| salle 1 : départ naturel | ✅ 5/5 | rôles et postes réservés, chaque évènement du trajet en réussite et en erreur, parcours complet, mort, reconnexion |
| salle 1 : évènements | ✅ 16/16 | rôles et postes réservés, chaque évènement du trajet en réussite et en erreur, parcours complet, mort, reconnexion |
| salle 1 : morts et reconnexion | ✅ 7/7 | rôles et postes réservés, chaque évènement du trajet en réussite et en erreur, parcours complet, mort, reconnexion |
| salle 1 : parcours complet | ✅ 24/24 | rôles et postes réservés, chaque évènement du trajet en réussite et en erreur, parcours complet, mort, reconnexion |
| salle 2 : niveau 1 | ✅ 14/14 | tirage des puits, 9 énigmes (erreurs comprises), grilles croisées, niveaux, sommet, mort, reconnexion |
| salle 2 : niveau 2 | ✅ 7/7 | tirage des puits, 9 énigmes (erreurs comprises), grilles croisées, niveaux, sommet, mort, reconnexion |
| salle 2 : morts et reconnexion | ✅ 4/4 | tirage des puits, 9 énigmes (erreurs comprises), grilles croisées, niveaux, sommet, mort, reconnexion |
| salle 2 : niveau 3 et sommet | ✅ 10/10 | tirage des puits, 9 énigmes (erreurs comprises), grilles croisées, niveaux, sommet, mort, reconnexion |
| salle 3 : missions | ✅ 16/16 | missions réservées et résolues en vrais clics, assemblage simultané, objet unique, encre invisible, passage secret |
| salle 3 : morts et reconnexion | ✅ 4/4 | missions réservées et résolues en vrais clics, assemblage simultané, objet unique, encre invisible, passage secret |
| salle 3 : assemblage et Lanterne | ✅ 7/7 | missions réservées et résolues en vrais clics, assemblage simultané, objet unique, encre invisible, passage secret |
| salle 3 : encre invisible | ✅ 10/10 | missions réservées et résolues en vrais clics, assemblage simultané, objet unique, encre invisible, passage secret |
| salle 4 : rôles et équipement | ✅ 12/12 | rôles re-tirés à chaque étape, équipements, capacités, 6 étapes (erreurs comprises), mort/spectateur, anéantissement |
| salle 4 : sceaux I à III | ✅ 13/13 | rôles re-tirés à chaque étape, équipements, capacités, 6 étapes (erreurs comprises), mort/spectateur, anéantissement |
| salle 4 : morts, anéantissement, reconnexion | ✅ 7/7 | rôles re-tirés à chaque étape, équipements, capacités, 6 étapes (erreurs comprises), mort/spectateur, anéantissement |
| salle 4 : sceaux IV à VI | ✅ 15/15 | rôles re-tirés à chaque étape, équipements, capacités, 6 étapes (erreurs comprises), mort/spectateur, anéantissement |
| salle 6 : voyage | ✅ 13/13 | voyage entre saisons, chaque chaîne de propagation, piège d’anticipation et remontée du temps, étape finale, morts |
| salle 6 : anticipation | ✅ 15/15 | voyage entre saisons, chaque chaîne de propagation, piège d’anticipation et remontée du temps, étape finale, morts |
| salle 6 : propagations | ✅ 38/38 | voyage entre saisons, chaque chaîne de propagation, piège d’anticipation et remontée du temps, étape finale, morts |
| salle 6 : morts et reconnexion | ✅ 8/8 | voyage entre saisons, chaque chaîne de propagation, piège d’anticipation et remontée du temps, étape finale, morts |
| salle 6 : cloches | ✅ 9/9 | voyage entre saisons, chaque chaîne de propagation, piège d’anticipation et remontée du temps, étape finale, morts |
| salle 7 : accusation | ✅ 11/11 | vote (désaccord puis unanimité), les deux branches de l’accusation, machine-boss, mort, anéantissement, reconnexion |
| salle 7 : machine-boss | ✅ 17/17 | vote (désaccord puis unanimité), les deux branches de l’accusation, machine-boss, mort, anéantissement, reconnexion |
| fin de partie | ✅ 5/5 | cinématique, crédits (temps, morts), advancement final, épilogue |
| serveur | ✅ 1/1 | aucune erreur/avertissement du datapack, zones chargées |
| salle 5 | ✅ 26/26 | salle 5 : faite, 26/26 tests OK (détail non publié) |
| général | ✅ 1/1 | chargement des zones de jeu |
| parcours complet | ✅ 19/19 | prologue → crédits dans l’ordre, retour impossible vers chaque salle précédente, journal complet |
| indices progressifs | ✅ 3/3 | indice à 5 min puis à 8 min, remise à zéro au changement d’étape |
| mode debug à 1 joueur | ✅ 4/4 | partie lancée à 1 joueur, rôles vacants, automate d’Orel, retour à 3 |
| serveur | ✅ 1/1 | aucune erreur/avertissement du datapack, zones chargées |

## Estimation de durée (joueurs qui découvrent)

| Salle | Visé | Estimé | Étapes |
|---|---|---|---|
| 0 — Prologue : Brumeval | 3-5 min | 4 min | arrivée des trois joueurs, attente (1) · cinématique de Maître Orel (38 s) (0.7) · promenade au village, PNJ, premiers indices (1.8) · embarquement (0.5) |
| 1 — L’Express du Solstice | 10-12 min | 10 min | tirage des rôles, prise en main des postes (1) · 9 tronçons à vitesse moyenne (≈ 35 s chacun) (5.3) · erreurs de débutants : ≈ 4 reculs d’un tronçon (2.7) · coordination, imprévus à bord (1) |
| 2 — La Tour des Engrenages | 15 min | 14 min | tirage des puits, découverte (0.7) · niveau 1 : trois énigmes en parallèle + attente (4) · niveau 2 : trois énigmes (4.5) · niveau 3 : trois énigmes (4.5) · réunion au sommet (0.3) |
| 3 — L’Atelier d’Orel | 12-15 min | 12 min | découverte de l’atelier, tirage des missions (0.8) · trois missions individuelles en parallèle (5.5) · assemblage à trois (1.2) · énigme finale de l’atelier (4.5) |
| 4 — Le Siège du Sanctuaire | 18-20 min | 18.5 min | introduction, rôles et équipement (0.8) · six sceaux, une énigme différente chacun, sous les vagues (16.7) · morts, spectateur, pauses entre sceaux (1) |
| 5 — La Nuit la plus longue | 15 min | 14.5 min | (détail non publié) (14.5) |
| 6 — Les Quatre Saisons | 30 min | 29.5 min | apprendre à voyager, première exploration des 4 saisons (5) · quatre chaînes de cause à effet entre saisons (16) · rendre les cristaux (allers-retours) (3.5) · étape finale à plusieurs saisons (2) · une remontée du temps probable (erreur d’anticipation) (3) |
| 7 — Le Cœur du Calendrier | 12-15 min | 12.5 min | relecture de l’enquête, discussion, vote (4) · révélation (0.5) · machine-boss (trois phases) (6.5) · cinématique de fin et crédits (1.5) |
| transitions | — | 1.2 min | 7 transitions narratives de 10 s |
| **Total** | **105–120** | **116.2 min** | |

## Ce qui n’a pas pu être testé

Tout ce qui suit dépend du **client graphique** ou de **vrais humains**, que je ne pouvais pas lancer ni simuler :

- **Rendu client** : textures du resource pack (Lanterne, cristaux, apparence de Maître Orel), text_display et
  item_display, particules, titres, bossbars, sons, obscurité, biomes des quatre vallées, onglet « Solstice » des
  progrès. Les fichiers sont validés (PNG 16×16, modèles de base identiques au vanilla du `client.jar`, chemins),
  mais leur affichage n’a jamais été vu.
- **Vraie partie en LAN** : « Ouvrir au réseau local » (serveur intégré de l’hôte), connexion de deux vrais
  clients, pare-feu macOS, latence. Les tests utilisent un serveur dédié local et 3 joueurs factices Carpet.
- **Gestes humains** : les joueurs factices cliquent pour de vrai (`look at` + `use`/`attack`), marchent sur les
  dalles, s’accroupissent, meurent, se déconnectent ; mais les déplacements longs sont des téléportations, les
  combats sont raccourcis (monstres tués par commande, résistance accordée) et certains réglages sont forcés
  par le test (pression du train, position d’un évènement, butin donné). La difficulté réelle n’est pas éprouvée.
- **Ressenti** : peur, rythme, clarté des énigmes, équilibrage des combats, durée réelle (l’estimation ci-dessous
  est une estimation, pas une mesure).
- **Lecture des livres** (Carnet, feuille de route) : le contenu des pages est vérifié, pas l’interface.
- **Chat vocal** : indispensable pour la coopération, évidemment non testé.

## Bugs connus et limites

- **Sans le resource pack**, tout reste jouable : les objets sont des objets vanilla nommés (lanterne, horloge,
  éclats d’améthyste…), mais Maître Orel apparaît comme un noyé nommé « Maître Orel ».
- **Les interactions se font sur des zones cliquables invisibles** (entités `interaction`) : viser le centre de
  l’objet. Un coéquipier ou un monstre placé entre vous et l’objet « prend » le clic.
- **Difficulté Paisible** : repassée automatiquement en Normal (sinon plus de monstres au Siège et au Cœur).
- **Mode 1 ou 2 joueurs (debug)** : prévu pour tester, pas pour jouer. Certaines énigmes pensées pour trois
  (informations visibles ailleurs) sont affichées en clair dans le chat, et des étapes simultanées deviennent
  séquentielles.
- **Anéantissement dans une salle longue** : la salle se réinitialise proprement mais conserve les étapes déjà
  franchies (Siège : le sceau en cours recommence ; Cœur : le combat recommence, le verdict est conservé).
- **Plus de 3 joueurs** : possible, mais l’équilibrage et les rôles sont pensés pour exactement trois.
- **Hôte LAN** : si l’hôte quitte, la partie s’arrête pour tout le monde (limite du mode LAN) ; la progression
  est sauvegardée dans son monde.

