#!/usr/bin/env python3
"""Tests E2E à 3 joueurs factices (Carpet, serveur de test uniquement) sur une copie du monde construit.

Chaque salle : chemin nominal, tirages de rôles, mort d’un joueur, mort des 3, déconnexion/reconnexion.
Résultats → build/test_results.json (salle 5 : compteurs uniquement)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from testlib import BOTS, V, run_server  # noqa: E402
import scenarios  # noqa: E402


def main():
    only = [a for a in sys.argv[1:] if not a.startswith("-")]
    scs = scenarios.all_scenarios()
    if only:
        scs = [s for s in scs if any(o in s.__name__ for o in only)]
    ok = run_server("server-test", scs, "test_results.json")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
