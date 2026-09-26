#!/bin/sh
# Boucle rapide (sans fetch ni packaging) ; journal dans build/ci.log. Filtre optionnel : ./run_ci.sh r3
cd "$(dirname "$0")"
mkdir -p build
{ python3 src/build_packs.py && python3 tools/lint.py && python3 tools/worldbuild.py && python3 tools/tests.py "$@"; echo "EXIT $?"; } > build/ci.log 2>&1
tail -3 build/ci.log
