#!/usr/bin/env python3
"""Parcours complet (serveur à part, monde neuf) :
1. Trois joueurs enchaînent TOUTES les salles du prologue aux crédits (gestes réels au prologue, puis fonctions de
   debug « salle suivante » là où un geste humain n’est pas simulable en un temps raisonnable). À chaque salle :
   ordre strictement croissant, retour en arrière impossible (téléportation vers toutes les salles précédentes).
2. Indices progressifs : déclenchement à 5 min puis 8 min sur une même étape, remise à zéro au changement d’étape.
3. Mode debug à 1 joueur : la partie démarre seule, rôles vacants cumulés, automate de la Tour.
Résultats → build/journey_results.json."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from testlib import BOTS, V, run_server  # noqa: E402

ORIGINS = {0: 0, 1: 1000, 2: 2000, 3: 3000, 4: 4000, 5: 5000, 6: 6000, 7: 7000}


def journey(t):
    t.section = "parcours complet"
    for b in BOTS:
        t.join(b)
    t.wait(20)
    t.ok("3 joueurs au prologue, la cinématique démarre", t.g("#step") == 1)
    t.sprint(820)
    seq = [t.g("#room")]
    for n in range(0, 7):
        if n == 0:
            for i, b in enumerate(BOTS):
                t.tp(b, -2.5 + 3 * i, 101, -33.5)
            t.wait(10)
        else:
            t.secret = (n == 5)
            t.rc("function solstice:debug/salle_suivante")
        t.sprint(230)
        t.wait(10)
        t.wait_until(lambda: t.g("#room") == n + 1 and t.all_score("sol.room", n + 1), 300)
        t.secret = False
        seq.append(t.g("#room"))
        t.ok(f"salle {n} → salle {n + 1} : téléportation automatique des 3", t.all_score("sol.room", n + 1))
        back = 0
        for m in range(0, n + 1):         # tentative de retour dans chaque salle précédente
            t.tp("Bot1", ORIGINS[m] + 0.5, 101, 0.5)
            t.wait(4)
            p = t.pos("Bot1")
            if not (p and abs(p[0] - ORIGINS[n + 1]) < 80):
                back += 1
        t.ok(f"salle {n + 1} : impossible de revenir dans les {n + 1} salle(s) précédente(s)", back == 0, str(back))
    t.ok("ordre des salles strictement croissant 0 → 7", seq == list(range(0, 8)), str(seq))
    t.rc("function solstice:debug/salle_suivante")
    t.sprint(1600)
    t.wait(10)
    t.ok("crédits : advancement final pour les 3", all(t.adv(b, "fin") for b in BOTS))
    t.ok("épilogue : retour au village (#room = 8)", t.g("#room") == 8)
    t.ok("journal : les 8 salles sont validées", all(t.adv("Bot2", f"room/r{n}") for n in range(8)))


def hints(t):
    t.section = "indices progressifs"
    t.rc("function solstice:debug/aller_salle_2")
    t.wait(20)
    t.setg("#ht", 5990)
    t.wait(20)
    t.ok("5 minutes bloqués sur une étape → premier indice", t.g("#hk") == 1)
    t.setg("#ht", 9590)
    t.wait(20)
    t.ok("8 minutes → second indice", t.g("#hk") == 2)
    t.rc("function solstice:r2/solve_a1")
    t.rc("function solstice:r2/solve_b1")
    t.rc("function solstice:r2/solve_c1")
    t.wait(5)
    t.ok("changement d’étape → compteur d’indices remis à zéro", t.g("#ht") < 100 and t.g("#hk") == 0)


def solo(t):
    t.section = "mode debug à 1 joueur"
    for b in BOTS[1:]:
        t.leave(b)
    t.rc("function solstice:debug/nouvelle_partie")
    t.wait(10)
    t.rc("function solstice:debug/joueurs_1")
    t.wait(20)
    t.ok("à 1 joueur (debug), le prologue démarre seul", t.g("#step") == 1 and t.g("#need") == 1)
    t.rc("function solstice:debug/aller_salle_1")
    t.wait(30)
    t.ok("salle 1 : le joueur seul cumule les trois rôles vacants",
         all(t.tag("Bot1", f"sol.ro{r}") for r in (1, 2, 3)) and all(t.g(f"#vac{r}") == 1 for r in (2, 3)))
    t.rc("function solstice:debug/aller_salle_2")
    t.wait(30)
    tr = t.score("Bot1", "sol.role")
    others = [x for x in (1, 2, 3) if x != tr]
    solved = [t.g(f"#s_{'abc'[x - 1]}1") for x in others]
    t.ok("salle 2 : l’automate d’Orel résout les puits vacants", solved == [1, 1], str(solved))
    t.rc("function solstice:debug/joueurs_3")
    t.wait(5)
    t.ok("retour au réglage à 3 joueurs", t.g("#need") == 3 and t.g("#win") == 60)


if __name__ == "__main__":
    ok = run_server("server-journey", [journey, hints, solo], "journey_results.json")
    sys.exit(0 if ok else 1)
