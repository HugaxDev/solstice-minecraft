#!/bin/sh
# SOLSTICE — régénère tout depuis zéro : cache vérifié, datapack, resource pack, lint, monde (serveur vanilla),
# tests E2E à 3 joueurs factices (serveur de test Fabric + Carpet, 127.0.0.1), parcours complet, durée,
# packaging dist/ et rapport de tests. Aucun serveur ne reste lancé à la fin.
set -e
cd "$(dirname "$0")"
mkdir -p build dist
echo "== 1/9 cache (Java Mojang, server.jar, Fabric, Carpet : sources officielles, hashes vérifiés)"; python3 tools/fetch.py
echo "== 2/9 génération datapack + resource pack";              python3 src/build_packs.py
echo "== 3/9 lint (py_compile, JSON, références, blocs, audit sélecteurs, registre d’énigmes)"; python3 tools/lint.py
echo "== 4/9 construction du monde (serveur vanilla headless)";  python3 tools/worldbuild.py
echo "== 5/9 tests E2E, 3 joueurs factices";                    python3 tools/tests.py
echo "== 6/9 parcours complet, indices, mode 1 joueur";          python3 tools/test_journey.py
echo "== 7/9 estimation de durée";                               python3 tools/durations.py
echo "== 8/9 packaging";                                         python3 tools/package.py
echo "== 9/9 processus orphelins + rapport";                     python3 tools/orphans.py && python3 tools/report.py
echo "OK — livrables dans dist/ (détail des tests : design/SPOILERS_NE_PAS_LIRE/, ne pas lire si vous jouez)"
