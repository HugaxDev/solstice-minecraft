# Journal d’avancement — SOLSTICE

## 2026-09-25
- [x] Setup : projet `~/Desktop/Solstice`, outillage copié de Fragments (non modifié), cache Java/serveurs copié.
- [x] pack_format relus dans le jar : données 48, ressources 34.
- [x] Rapports officiels du jeu générés depuis server.jar (`cache/reports`) : le lint valide chaque bloc, état de bloc et objet.
- [x] Monde construit par un **serveur vanilla** ; tests sur serveur Fabric + Carpet (copie du monde).
- [x] Squelette linéaire : prologue (attente des 3, cinématique, 2 indices, embarquement) → salles factices → fin (crédits, épilogue).
      **154/154 PASS** : téléportations automatiques, pas de retour arrière, morts, spectateur 10 s, anéantissement, reconnexion,
      tirages au sort uniques (30 tirages), exclusion du Guérisseur précédent.
  - Appris : Carpet connecte les joueurs factices de façon asynchrone (~5 s) → le harnais attend la connexion réelle.
  - Appris : un factice reconnecté ne récupère pas toujours le mode aventure → la reconnexion le réimpose.
- [x] Salle 1 — L’Express du Solstice — 66/66 (rôles, postes réservés, 6 types d’évènements, parcours complet, morts).
  - Corrigé : rôles effacés par l’arrivée des joueurs → chaque rôle est lié à la salle où il a été tiré (sol.rroom).
  - Corrigé : étiquettes de rôle renommées sol.ro1..3 (collision avec les étiquettes d’entités sol.r1) ; le lint
    interdit désormais tout `kill @e[...]` sans `type=`.
- [x] Salle 2 — La Tour des Engrenages — 37/37 (9 énigmes distinctes, grilles croisées, niveaux, sommet).
  - Corrigé : une salle qui démarre avant le chargement de ses chunks perdait ses entités → démarrage différé
    tant que la zone n’est pas chargée (#pstart) ; le harnais attend le chargement complet des zones forcées.
- [x] Salle 3 — L’Atelier d’Orel — 39/39 (3 missions, assemblage simultané, Lanterne unique, encre, passage secret).
  - Corrigé : zones cliquables de l’établi masquées par le bloc (test faussement vert repéré et durci).
- [x] Salle 4 — Le Siège du Sanctuaire — 48/48 (6 sceaux distincts, Guérisseur toujours différent, vagues, soin,
  provocation, butins, 2 indices, mort/spectateur, anéantissement = le sceau en cours recommence, reconnexion).
  - Corrigé : deux éléments de décor masquaient ou chevauchaient des mécanismes (déplacés) ; une zone piégée
    testait la boîte du joueur (faux déclenchements) → bloc sous les pieds.
  - Corrigé (build) : biomes appliqués par RCON avec réponse vérifiée ; test de biome éloigné du bord (lissage aléatoire).
- [x] Salle 5 : faite, 27/27 tests OK.
- [x] Salle 6 — Les Quatre Saisons (faite en premier : la plus risquée) — 83/83 en isolation.
  - 4 vallées (biomes), voyage entre saisons, chaînes de propagation régénérées, remontée du temps, étape
    finale simultanée, objets « de groupe » (copie par joueur, resynchronisés). Détail : dossier spoilers.
  - Appris : une `interaction` alignée sur les faces d’un bloc perd le clic (bloc prioritaire à égalité) → largeur ≥ 1,25.
  - Appris (tests) : un coéquipier sur la ligne de visée intercepte le clic ; le gardien de la Lanterne supprime
    les doublons transitoires (il marche !) → le harnais déplace les objets en le suspendant.
- [x] Salle 7 — Le Cœur du Calendrier — 33/33 (vote unanime, deux branches, 3 systèmes, opérateur tournant, fin).
  - Corrigé : après un anéantissement, le même joueur pouvait redevenir Opérateur (ordre des étiquettes).
  - Corrigé : la place de la salle 5 dépassait sa boîte de sécurité → le lint vérifie désormais que toute zone
    construite est couverte par une boîte.
- [x] Maître Orel à skin joueur (`skin.png` → noyé retexturé, décision 17) — build.sh complet en copie isolée :
  monde 97/97, E2E 351/351, parcours 28/28 ; dist/Solstice-resourcepack.zip et Solstice-world.zip régénérés.
  - Appris : un noyé NoAI brûle au soleil ; une barrière au-dessus ne l’en protège pas, un bloc plein si.
- [x] Enquête : 10 indices (dont 3 trompeurs), Carnet d’enquête régénéré, tableau d’enquête au Cœur, deux branches.
- [x] Indices progressifs (5 et 8 min par étape), journal « Solstice » (salles, indices cachés, 8 défis cachés).
- [x] Parcours complet (tools/test_journey.py) : ordre 0→7 strict, aucun retour vers chaque salle précédente,
      indices progressifs, mode debug à 1 joueur — 28/28.
- [x] Protection anti-Paisible dans toutes les salles (chaque seconde).
- [x] Intégration du travail d’une session voisine (apparence de Maître Orel : skin joueur sur un noyé, auvent,
      tests du prologue) — conservé tel quel, reconstruit et retesté.
- [x] Estimation de durée : 1 h 56 (tools/durations.py).
- [x] Packaging : monde vanilla (level.dat au 1er niveau vérifié par dézippage), resource pack, .mrpack optionnel.
- [x] Validation finale depuis zéro : `rm -rf build dist && ./build.sh` → lint OK, monde OK, E2E 354/354, parcours 28/28, 0 processus orphelin.

## Reprise après interruption
`python3 src/build_packs.py && python3 tools/lint.py && python3 tools/worldbuild.py && python3 tools/tests.py`
(`python3 tools/tests.py r3` pour ne lancer que certains scénarios). Débogage : `python3 tools/dbg.py "cmd" "wait:20" …`.
