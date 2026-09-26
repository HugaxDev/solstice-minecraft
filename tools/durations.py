#!/usr/bin/env python3
"""Estimation de durée de jeu pour des joueurs qui découvrent la carte (minutes).
Chaque salle : liste d’étapes (durée réaliste, erreurs et discussions comprises). Le total doit tomber entre
105 et 120 minutes, sinon le script échoue (il faut alors ajuster le contenu).
La salle 5 n’est publiée que sous forme de total (détail : design/SPOILERS_NE_PAS_LIRE)."""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ROOMS = [
    (0, "Prologue : Brumeval", 3, 5, [
        ("arrivée des trois joueurs, attente", 1.0), ("cinématique de Maître Orel (38 s)", 0.7),
        ("promenade au village, PNJ, premiers indices", 1.8), ("embarquement", 0.5)]),
    (1, "L’Express du Solstice", 10, 12, [
        ("tirage des rôles, prise en main des postes", 1.0), ("9 tronçons à vitesse moyenne (≈ 35 s chacun)", 5.3),
        ("erreurs de débutants : ≈ 4 reculs d’un tronçon", 2.7), ("coordination, imprévus à bord", 1.0)]),
    (2, "La Tour des Engrenages", 15, 15, [
        ("tirage des puits, découverte", 0.7), ("niveau 1 : trois énigmes en parallèle + attente", 4.0),
        ("niveau 2 : trois énigmes", 4.5), ("niveau 3 : trois énigmes", 4.5), ("réunion au sommet", 0.3)]),
    (3, "L’Atelier d’Orel", 12, 15, [
        ("découverte de l’atelier, tirage des missions", 0.8), ("trois missions individuelles en parallèle", 5.5),
        ("assemblage à trois", 1.2), ("énigme finale de l’atelier", 4.5)]),
    (4, "Le Siège du Sanctuaire", 18, 20, [
        ("introduction, rôles et équipement", 0.8), ("six sceaux, une énigme différente chacun, sous les vagues", 16.7),
        ("morts, spectateur, pauses entre sceaux", 1.0)]),
    (5, "La Nuit la plus longue", 15, 15, None),
    (6, "Les Quatre Saisons", 30, 30, [
        ("apprendre à voyager, première exploration des 4 saisons", 5.0),
        ("quatre chaînes de cause à effet entre saisons", 16.0),
        ("rendre les cristaux (allers-retours)", 3.5), ("étape finale à plusieurs saisons", 2.0),
        ("une remontée du temps probable (erreur d’anticipation)", 3.0)]),
    (7, "Le Cœur du Calendrier", 12, 15, [
        ("relecture de l’enquête, discussion, vote", 4.0), ("révélation", 0.5),
        ("machine-boss (trois phases)", 6.5), ("cinématique de fin et crédits", 1.5)]),
]
TRANSITIONS = 7 * 10 / 60
SALLE5 = [("zone 1", 4.0), ("zone 2", 5.0), ("zone 3", 5.5)]


def main():
    rows = []
    total = TRANSITIONS
    for rid, name, lo, hi, steps in ROOMS:
        if steps is None:
            est = round(sum(d for _, d in SALLE5), 1)
            steps_pub = [("(détail non publié)", est)]
        else:
            est = round(sum(d for _, d in steps), 1)
            steps_pub = steps
        total += est
        rows.append({"room": rid, "name": name, "target": f"{lo}-{hi}" if lo != hi else f"{lo}", "estimate": est,
                     "in_target": lo - 1 <= est <= hi + 1, "steps": steps_pub})
    total = round(total, 1)
    res = {"rooms": rows, "transitions": round(TRANSITIONS, 1), "total": total, "ok": 105 <= total <= 120 and all(r["in_target"] for r in rows)}
    os.makedirs(os.path.join(ROOT, "build"), exist_ok=True)
    with open(os.path.join(ROOT, "build", "durations.json"), "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    for r in rows:
        print(f"  salle {r['room']} {r['name']:28} {r['estimate']:5.1f} min (visé {r['target']})")
    print(f"  transitions {TRANSITIONS:.1f} min — TOTAL {total} min ({int(total // 60)} h {int(total % 60):02d})")
    if not res["ok"]:
        sys.exit("durée hors cible (1h45–2h) : ajuster le contenu")


if __name__ == "__main__":
    main()
