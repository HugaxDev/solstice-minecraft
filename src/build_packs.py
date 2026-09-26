#!/usr/bin/env python3
"""Génère le datapack `solstice` et le resource pack `solstice_rp` dans build/.

    python3 src/build_packs.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from gen import core, system, flow, roles, hints, story, lantern, adv, debug, ending, placeholder  # noqa: E402
from gen.core import V  # noqa: E402

# Salles livrées : module rN s’il existe, sinon salle factice
ROOM_MODULES = {}
for _n in range(0, 8):
    try:
        ROOM_MODULES[_n] = __import__(f"gen.r{_n}", fromlist=["build"])
    except ModuleNotFoundError:
        pass


def build_tests(dp):
    t = [f"scoreboard players set #pass sol.test 0", "scoreboard players set #fail sol.test 0",
         f"scoreboard players set #total sol.test {len(dp.tests)}", "say TEST_BEGIN"]
    for o, _, _ in system.OBJECTIVES:
        t.append(f"scoreboard players set #probe {o} 7")
    for name, cond in dp.tests:
        t.append(f"execute if {cond} run scoreboard players add #pass sol.test 1")
        t.append(f"execute unless {cond} run scoreboard players add #fail sol.test 1")
        t.append(f"execute if {cond} run say PASS {name}")
        t.append(f"execute unless {cond} run say FAIL {name}")
    t += ["scoreboard players operation #sum sol.test = #pass sol.test",
          "scoreboard players operation #sum sol.test += #fail sol.test",
          *[f"scoreboard players reset #probe {o}" for o, _, _ in system.OBJECTIVES],
          "say TEST_END"]
    dp.fn("test/all", t)


def main():
    dp = core.Datapack()
    system.build(dp)
    flow.build(dp)
    roles.build(dp)
    hints.build(dp)
    story.build(dp)
    lantern.build(dp)
    debug.build(dp)
    cine = None
    for n in range(0, 8):
        if n in ROOM_MODULES:
            r = ROOM_MODULES[n].build(dp)
            if n == 7:
                cine = r
        else:
            placeholder.build(dp, n, done="function solstice:end/start" if n == 7 else "function solstice:flow/complete")
    ending.build(dp, cine or [(20, ["title @a title {\"text\":\"Fin\",\"color\":\"gold\"}"])])
    lantern.build_late(dp)
    adv.build(dp)
    flow.stub_missing(dp)
    dp.add("flow/tick", [f"execute if score #ended {V} matches 1 if score #room {V} matches 7 run function solstice:end/tick",
                         f"execute if score #m20 {V} matches 0 run bossbar set solstice:obj players @a"])
    from gen.layout import ROOMS
    dp.meta["room_combat"] = {str(n): r["combat"] for n, r in ROOMS.items()}
    # forceload (lancé par le build du monde)
    dp.fn("build/forceload", [f"forceload add {x1} {z1} {x2} {z2}" for (x1, z1, x2, z2) in dp.meta["forceload"]])
    dp.fn("build/all", [f"function solstice:{b}" for b in dp.meta["builds"]])
    dp.test("système : chargement effectué (#loaded)", f"score #loaded {V} matches 1")
    dp.test("système : partie au prologue (#room = 0)", f"score #room {V} matches 0")
    dp.test("système : pas de transition en cours", f"score #trans {V} matches 0")
    dp.test("système : 3 joueurs requis par défaut (#need = 3)", f"score #need {V} matches 3")
    dp.test("système : bossbar d’objectif créée", "score #loaded sol.var matches 1")
    for o, _, _ in system.OBJECTIVES:
        dp.test(f"scoreboard {o} créé", f"score #probe {o} matches 7")
    build_tests(dp)
    out = os.path.join(ROOT, "build", "datapack")
    os.makedirs(out, exist_ok=True)
    base = dp.write(out)
    from gen import rp
    rpath = rp.build(os.path.join(ROOT, "build", "resourcepack"))
    meta = {"functions": len(dp.functions), "advancements": dp.meta.get("advancements"),
            "tests": len(dp.tests), "rooms_real": sorted(ROOM_MODULES), "meta": dp.meta,
            "builds": dp.meta["builds"], "puzzles": dp.puzzles}
    with open(os.path.join(ROOT, "build", "manifest.json"), "w") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    # registre d’énigmes (privé : contient les mécaniques ; la salle 5 n’y figure que par renvoi)
    reg = ["# Registre des énigmes (PRIVÉ — contient des solutions)", "",
           "Généré par `src/build_packs.py`. Le lint refuse deux énigmes du même type sur toute la carte.", "",
           "| salle | id | type | mécanique |", "|---|---|---|---|"]
    for pz in dp.puzzles:
        if pz["room"] == 5:
            reg.append(f"| 5 | — | (voir design/SPOILERS_NE_PAS_LIRE/SALLE5.md) | — |")
        else:
            reg.append(f"| {pz['room']} | {pz['id']} | `{pz['type']}` | {pz['desc']} |")
    reg += ["", f"Total : {len(dp.puzzles)} énigmes, {len({p['type'] for p in dp.puzzles})} types distincts."]
    os.makedirs(os.path.join(ROOT, "design"), exist_ok=True)
    with open(os.path.join(ROOT, "design", "PUZZLES_PRIVATE.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(reg) + "\n")
    print(f"datapack : {base} ({len(dp.functions)} fonctions, {meta['advancements']} advancements, "
          f"{len(dp.tests)} tests structurels) · salles réelles : {meta['rooms_real']}")
    print(f"resource pack : {rpath}")


if __name__ == "__main__":
    main()
