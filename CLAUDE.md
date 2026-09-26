# SOLSTICE — contexte projet

Aventure Minecraft **Java 1.21.1 vanilla**, coop **exactement 3 joueurs** en LAN, linéaire (salles 0 → 7), ~1h50.
Tout le jeu est un **datapack** (`solstice`) + un **resource pack** optionnel (`solstice_rp`), générés par du Python.
Aucun bloc posé à la main. Outillage repris (copié) de `~/Desktop/Fragments` — **ne jamais modifier Fragments**.

## Commande unique
```
./build.sh          # tout depuis zéro, tests compris
./run_ci.sh         # boucle rapide (génération + lint + monde + tests), log build/ci.log
```

## Arborescence
- `src/gen/` : générateurs. `core.py` (écriture datapack, textes, objets), `layout.py` (coordonnées),
  `system.py` (load/tick/joueur/morts/reconnexion), `flow.py` (enchaînement linéaire des salles, transitions),
  `roles.py` (tirages au sort), `hints.py` (indices progressifs), `story.py` (enquête, indices, carnet),
  `lantern.py`, `adv.py` (journal de quête), `build.py` (primitives de construction), `r0.py` … `r7.py` (salles), `rp.py`.
- `tools/` : fetch.py (+ rapports officiels du jeu), server.py (serveur headless + RCON), lint.py (blocs/objets validés
  contre `cache/reports`, audit sélecteurs, registre d’énigmes, zones ⊂ boîtes), worldbuild.py (**serveur vanilla**),
  tests.py + testlib.py + scenarios.py + sc_rN.py (E2E, 3 joueurs factices Carpet), test_journey.py (parcours complet),
  durations.py, package.py, report.py, orphans.py, dbg.py (débogage : `python3 tools/dbg.py "cmd" "wait:20"`).
- `src/gen/skin.py` + `skin.png` : apparence de Maître Orel (ajoutée par une autre session, à conserver).
- `design/PUZZLES_PRIVATE.md` (registre, généré) · `design/SPOILERS_NE_PAS_LIRE/` (salle 5, histoire complète).

## Interface d’une salle `rN`
`rN/build` (monde) · `rN/start` (global, à l’entrée du groupe) · `rN/enter` (@s, idempotent : arrivée, retardataire,
reconnexion) · `rN/tick` (global) · `rN/ptick` (@s) · `rN/cp` (@s → checkpoint) · `rN/respawn` (@s après mort)
· `rN/wipe` (global, tout le groupe à terre) · `rN/hint` (global, #hk = 1|2). Fin de salle : `flow/complete`.

## Règles
- MC 1.21.1 : datapack 48, resource pack 34 (lus dans `version.json` du server.jar). Dossiers au singulier.
- Composants d’items 1.21.1 : `custom_name='{"text":..}'`, `custom_model_data`, attributs `minecraft:generic.*`.
- Apostrophes françaises : toujours `’` (U+2019) dans les textes.
- Serveur de test : `server-ip=127.0.0.1`, RCON 127.0.0.1, toujours arrêté en fin de run. Le monde livré est
  construit par un serveur **vanilla** (aucune trace Fabric/Carpet). Carpet uniquement pour les tests.
- Jamais `@p`/`@r`, jamais `@a[...limit=1]` (sauf `spectate` avec `sort=nearest`), `@s` seulement avec exécutant.
- **Salle 5 : secret absolu.** Rien dans les messages, README, rapport, récap : « salle 5 : faite, X/X tests OK ».
  Les noms de tests de la salle 5 ne sont jamais affichés (compteurs uniquement).
- Registre d’énigmes : chaque salle déclare `PUZZLES` ; le lint refuse deux énigmes du même type.
- Entité `interaction` posée sur un bloc plein : largeur ≥ 1.25 et base 0.05 plus bas, sinon le bloc « gagne » le clic
  (à distance égale, le jeu vise le bloc — ex. l’établi s’ouvre au lieu de déclencher l’action).
- Tests : un coéquipier ou un monstre sur la ligne de visée « prend » un clic ; les joueurs factices se
  connectent de façon asynchrone ; la salle 5 s’affiche en compteurs (détails : design/SPOILERS_NE_PAS_LIRE/tests_*.json).
- Sortie console des tests SANS spoiler par défaut (numéros) ; `SOLSTICE_SPOILERS=1` pour les noms complets.
  Le public (README, TEST_REPORT, DECISIONS, PROGRESS) ne dévoile ni solutions ni coupable : l’utilisateur joue la carte.
- Rien n’est « fait » sans 100 % PASS. Journal : `PROGRESS.md`. Choix : `DECISIONS.md`.

## Coordonnées (monde vide « the_void », overworld, sol y=100)
R0 (0,0) · R1 x=1000 · R2 x=2000 · R3 x=3000 · R4 x=4000 · R5 x=5000 · R6 x=6000 (4 vallées z=0/200/400/600) · R7 x=7000.
