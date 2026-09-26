"""Salle 3 — L’Atelier d’Orel. Fabriquer la Lanterne des Saisons.
Trois missions individuelles (tirées au sort) aux gameplays différents :
  1. Le Grenier aux Caisses — pousser des caisses sur des repères (Cage de laiton)
  2. La Cave aux Cloches — mémoire musicale : rejouer des mélodies (Mèche éternelle)
  3. Le Cabinet d’optique — orienter des miroirs pour guider un rayon (Verre de lune)
Assemblage : les trois pièces posées ENSEMBLE sur l’établi (fenêtre #win). La Lanterne révèle ensuite l’encre
invisible de l’atelier (lettres d’un mot à épeler en marchant sur les dalles), un passage secret et deux indices.
#step : 1 missions · 2 assemblage · 3 lanterne (encre + mot) ."""
from collections import deque

from .core import (V, T, jdump, tellraw, title, orel, narr, actionbar, fill, setblock, text_display, interaction,
                   Item, SC, snbt_str, item_display)
from .flow import obj
from .hints import hint_fn
from .roles import announce
from . import lantern as LN

Y = 100
HALL = (2985, -10, 3015, 10)
BENCH = [(2999, 0), (3000, 0), (3001, 0)]
PADS = {1: (2991, -9), 2: (3000, -9), 3: (3009, -9)}
MISSIONS = {1: ("Le Grenier aux Caisses", "gold", "Cage de laiton", "iron_bars"),
            2: ("La Cave aux Cloches", "aqua", "Mèche éternelle", "string"),
            3: ("Le Cabinet d’optique", "light_purple", "Verre de lune", "glass_pane")}
COMP = {k: Item(v[3], v[2], v[1], lore=["Une pièce de la Lanterne des Saisons."], data=f"{{sol:{{comp{k}:1b}}}}", glint=True, stack=1)
        for k, v in MISSIONS.items()}
WORD = "TEMPS"
TILES = ["A", "T", "R", "E", "O", "L", "M", "I", "C", "P", "N", "S"]   # 4 colonnes × 3 rangées
INK_SPOTS = [(2986.1, 103.5, -6.5, -90), (3014.9, 102.2, 7.5, 90), (3006.5, 106.5, -9.9, 0), (2993.5, 101.4, 9.9, 180),
             (3012.5, 104.0, -9.9, 0)]
HALL_CP = (3000.5, 101, 5.5, 180)

# ---- mission 1 : sokoban
M1 = (2997, -44)                    # case (0,0)
LEVEL = ["...#...", ".C...T.", "..##...", "....C..", "#....#.", "..T....", "......."]
M1_ENTRY = (2999.5, 101, -34.5, 180)
# ---- mission 2 : cloches
M2_BELLS = [(2996, 45), (2998, 46), (3000, 46), (3002, 46), (3004, 45)]
M2_PITCH = ["0.7", "0.9", "1.05", "1.2", "1.4"]
M2_ENTRY = (3000.5, 101, 36.5, 0)
# ---- mission 3 : optique (grille 6×6, x 3037..3042, z -3..2)
M3 = (3037, -3)
M3_WALLS = {(2, 0), (2, 1), (3, 2), (5, 3)}
M3_MIRRORS = [(1, 2), (1, 4), (4, 4), (4, 0)]
M3_SRC = (-1, 2, "e")               # à l’ouest de la case (0,2), vers l’est
M3_RCV = (6, 0)                     # hors grille, à l’est de la case (5,0)
M3_ENTRY = (3039.5, 101, 5.5, 180)


def beam(config):
    """Trace le rayon pour une configuration (bit i = miroir i en « \\ »). Renvoie (cases, succès)."""
    x, z, d = M3_SRC
    dirs = {"e": (1, 0), "w": (-1, 0), "n": (0, -1), "s": (0, 1)}
    path = []
    for _ in range(40):
        dx, dz = dirs[d]
        x, z = x + dx, z + dz
        if (x, z) == M3_RCV:
            return path, True
        if not (0 <= x < 6 and 0 <= z < 6) or (x, z) in M3_WALLS:
            return path, False
        path.append((x, z))
        if (x, z) in M3_MIRRORS:
            i = M3_MIRRORS.index((x, z))
            back = (config >> i) & 1
            d = ({"e": "s", "s": "e", "w": "n", "n": "w"} if back else {"e": "n", "n": "e", "w": "s", "s": "w"})[d]
    return path, False


def sokoban_solution():
    walls = {(x, y) for y, r in enumerate(LEVEL) for x, c in enumerate(r) if c == "#"}
    crates = tuple(sorted((x, y) for y, r in enumerate(LEVEL) for x, c in enumerate(r) if c == "C"))
    targets = {(x, y) for y, r in enumerate(LEVEL) for x, c in enumerate(r) if c == "T"}

    def reach(p, cr):
        seen, dq = {p}, deque([p])
        while dq:
            x, y = dq.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (x + dx, y + dy)
                if 0 <= n[0] < 7 and 0 <= n[1] < 7 and n not in walls and n not in cr and n not in seen:
                    seen.add(n)
                    dq.append(n)
        return seen
    init = ((3, 6), crates)
    prev = {init: None}
    dq = deque([init])
    goal = None
    while dq:
        p, cr = dq.popleft()
        if set(cr) == targets:
            goal = (p, cr)
            break
        R = reach(p, cr)
        for i, (cx_, cy_) in enumerate(cr):
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                dest = (cx_ + dx, cy_ + dy)
                if (cx_ - dx, cy_ - dy) in R and 0 <= dest[0] < 7 and 0 <= dest[1] < 7 and dest not in walls and dest not in cr:
                    st = ((cx_, cy_), tuple(sorted(cr[:i] + cr[i + 1:] + (dest,))))
                    if st not in prev:
                        prev[st] = ((p, cr), ((cx_, cy_), (dx, dy)))
                        dq.append(st)
    assert goal, "niveau de caisses insoluble"
    moves, s = [], goal
    while prev[s]:
        s, m = prev[s]
        moves.append(m)
    return walls, crates, targets, moves[::-1]


def addc(holder, n):
    return f"scoreboard players {'add' if n >= 0 else 'remove'} {holder} {V} {abs(n)}"


def build(dp):
    SK_WALLS, SK_CRATES, SK_TARGETS, SK_SOL = sokoban_solution()
    CONFIGS = {c: beam(c) for c in range(16)}
    GOOD = [c for c, (p, ok) in CONFIGS.items() if ok]
    assert GOOD and 0 not in GOOD, "optique : il faut au moins une solution, et pas au départ"
    b = ["kill @e[type=!player,tag=sol.r3]"]
    b += fill(2950, 90, -50, 3050, 125, 50, "air")
    # ------------------------------------------------------------ atelier (hall)
    x1, z1, x2, z2 = HALL
    b += fill(x1 - 1, Y - 1, z1 - 1, x2 + 1, Y + 9, z2 + 1, "stripped_spruce_log")
    b += fill(x1, Y + 1, z1, x2, Y + 8, z2, "air")
    b += fill(x1, Y, z1, x2, Y, z2, "spruce_planks")
    b += fill(x1, Y, -1, x2, Y, 1, "dark_oak_planks")
    b += fill(x1, Y + 9, z1, x2, Y + 9, z2, "dark_oak_planks")
    for x in range(x1, x2 + 1, 5):
        b += fill(x, Y + 8, z1, x, Y + 8, z2, "stripped_dark_oak_log[axis=z]")
        b.append(setblock(x, Y + 7, 0, "lantern[hanging=true]"))
    # étagères, horloges, engrenages de décor
    b += fill(x1, Y + 1, z1, x1, Y + 4, z2, "bookshelf")
    b += fill(x2, Y + 1, z1, x2, Y + 4, z2, "bookshelf")
    for z in range(z1 + 2, z2, 4):
        b += [setblock(x1, Y + 2, z, "chiseled_bookshelf[facing=east]"), setblock(x2, Y + 2, z, "chiseled_bookshelf[facing=west]")]
    b += [setblock(3003, Y + 1, -4, "anvil"), setblock(2996, Y + 1, -4, "grindstone[face=floor,facing=north]"),
          setblock(3005, Y + 1, -2, "smithing_table"), setblock(2994, Y + 1, -2, "loom"),
          setblock(3010, Y + 1, 2, "cartography_table"), setblock(2990, Y + 1, 2, "fletching_table")]
    # grande horloge murale (décor, côté nord)
    b += fill(2998, Y + 5, z1, 3002, Y + 8, z1, "white_concrete")
    b += [setblock(3000, Y + 7, z1, "black_concrete"), setblock(3000, Y + 6, z1, "black_concrete"), setblock(3001, Y + 6, z1, "black_concrete")]
    # établi d’Orel (3 emplacements)
    for (x, z) in BENCH:
        b.append(setblock(x, Y + 1, z, "stripped_oak_log[axis=x]"))
    b += [setblock(2998, Y + 1, 0, "spruce_stairs[facing=east]"), setblock(3002, Y + 1, 0, "spruce_stairs[facing=west]")]
    # portes des missions (plaques) sur le mur nord
    for k, (x, z) in PADS.items():
        name, color, _, _ = MISSIONS[k]
        b += fill(x - 1, Y + 1, z1, x + 1, Y + 3, z1, "air")
        b += fill(x - 1, Y + 1, z1 - 1, x + 1, Y + 3, z1 - 1, "black_stained_glass")
        b.append(setblock(x, Y, z, "gold_block" if k == 1 else ("diamond_block" if k == 2 else "amethyst_block")))
        b.append(text_display(x + 0.5, Y + 4.2, z1 + 0.1, ["", T(name, color, bold=True), T(f"\nMission {k}", "gray")],
                              ["sol.r3"], scale=0.7, billboard="fixed", yaw=0))
    # dalles-lettres (4 × 3), au sud de l’établi
    for idx, letter in enumerate(TILES):
        c, r = idx % 4, idx // 4
        tx, tz = 2995 + 3 * c, 3 + 3 * r
        b += fill(tx, Y, tz, tx + 1, Y, tz + 1, "smooth_quartz")
        b.append(f"summon text_display {tx + 1} {Y + 1.02} {tz + 1} {{Tags:[\"sol\",\"sol.r3\"],Rotation:[180f,-90f],billboard:\"fixed\","
                 f"text:'{jdump(T(letter, 'dark_gray', bold=True))}',background:0,"
                 f"transformation:{{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],translation:[0f,0f,0f],scale:[3f,3f,3f]}}}}")
    # alcôve secrète (ouest) derrière les étagères
    b += fill(2979, Y, 3, 2983, Y + 4, 8, "stripped_spruce_log")
    b += fill(2980, Y + 1, 4, 2983, Y + 3, 7, "air")
    b.append(setblock(2981, Y + 1, 6, "chest[facing=east]"))
    # ------------------------------------------------------------ mission 1 : grenier aux caisses
    gx, gz = M1
    b += fill(gx - 1, Y, gz - 1, gx + 7, Y + 5, gz + 11, "dark_oak_planks")
    b += fill(gx, Y + 1, gz, gx + 6, Y + 4, gz + 10, "air")
    b += fill(gx, Y + 1, gz + 7, gx + 6, Y + 1, gz + 7, "dark_oak_fence")
    b += fill(gx + 3, Y + 1, gz + 7, gx + 3, Y + 1, gz + 7, "air")
    for (x, y) in SK_WALLS:
        b += fill(gx + x, Y + 1, gz + y, gx + x, Y + 2, gz + y, "barrel[facing=up]")
    for (x, y) in SK_TARGETS:
        b.append(setblock(gx + x, Y, gz + y, "gold_block"))
    b.append(setblock(gx + 1, Y + 1, gz + 9, "glass"))
    b.append(text_display(gx + 3.5, Y + 3.5, gz + 10.8, ["", T("Le Grenier aux Caisses\n", "gold", bold=True),
                                                        T("Clic sur une caisse : elle est poussée devant vous.\n", "white"),
                                                        T("Amenez les deux caisses sur les dalles d’or.", "gray")], ["sol.r3"], scale=0.6,
                          billboard="fixed", yaw=180))
    # ------------------------------------------------------------ mission 2 : cave aux cloches
    b += fill(2993, Y, 33, 3007, Y + 6, 48, "deepslate_bricks")
    b += fill(2994, Y + 1, 34, 3006, Y + 5, 47, "air")
    for i, (x, z) in enumerate(M2_BELLS):
        b.append(setblock(x, Y + 1, z, "polished_deepslate"))
        b.append(setblock(x, Y + 2, z, "bell[attachment=floor,facing=north]"))
    b.append(setblock(3000, Y + 1, 40, "jukebox"))
    b.append(setblock(2996, Y + 1, 37, "polished_deepslate"))
    b.append(text_display(3000.5, Y + 4.5, 47.8, ["", T("La Cave aux Cloches\n", "aqua", bold=True),
                                                  T("Clic sur la boîte à musique : écoutez la mélodie.\n", "white"),
                                                  T("Puis rejouez-la sur les cloches. Trois mélodies.", "gray")], ["sol.r3"], scale=0.6,
                          billboard="fixed", yaw=180))
    # ------------------------------------------------------------ mission 3 : cabinet d’optique
    ox, oz = M3
    b += fill(ox - 3, Y, oz - 3, ox + 9, Y + 6, oz + 10, "polished_blackstone")
    b += fill(ox - 2, Y + 1, oz - 2, ox + 8, Y + 5, oz + 9, "air")
    b += fill(ox, Y, oz, ox + 5, Y, oz + 5, "white_concrete")
    for (x, z) in M3_WALLS:
        b += fill(ox + x, Y + 1, oz + z, ox + x, Y + 2, oz + z, "obsidian")
    sx, sz, _ = M3_SRC
    b.append(setblock(ox + sx, Y + 1, oz + sz, "redstone_lamp[lit=true]"))
    b.append(setblock(ox + sx, Y + 2, oz + sz, "lightning_rod[facing=up]"))
    rx, rz = M3_RCV
    b.append(setblock(ox + rx, Y + 1, oz + rz, "target"))
    b.append(setblock(ox + 1, Y + 1, oz + 8, "glass"))
    b.append(text_display(ox + 3, Y + 4.5, oz + 9.8, ["", T("Le Cabinet d’optique\n", "light_purple", bold=True),
                                                      T("Clic sur un miroir : il pivote.\n", "white"),
                                                      T("Guidez la lumière jusqu’à la cible.", "gray")], ["sol.r3"], scale=0.6,
                          billboard="fixed", yaw=180))
    dp.meta.setdefault("builds", []).append("build/r3")
    dp.meta.setdefault("forceload", []).append((2950, -50, 3050, 50))

    # ------------------------------------------------------------ entités (remises à zéro au départ)
    e = ["kill @e[type=!player,tag=sol.r3d]"]

    def it(x, y, z, key, w=1.0, h=1.0):
        e.append(interaction(x, y, z, ["sol.r3", "sol.r3d", "sol.r3i", f"sol.k3_{key}"], w, h))
    for k, (x, z) in enumerate(BENCH, 1):
        it(x + 0.5, Y + 2.0, z + 0.5, f"slot{k}", 0.9, 0.7)
    for k in MISSIONS:
        e.append(text_display(BENCH[k - 1][0] + 0.5, Y + 3.0, BENCH[k - 1][1] + 0.5, ["", T(MISSIONS[k][2], MISSIONS[k][1])],
                              ["sol.r3", "sol.r3d"], scale=0.45))
    # sokoban : caisses (display + barrière posée par r3/sk_show) et interactions
    for i in (1, 2):
        e.append(f"summon block_display {gx} {Y + 1} {gz} {{Tags:[\"sol\",\"sol.r3\",\"sol.r3d\",\"sol.crate{i}\"],teleport_duration:3,"
                 f"block_state:{{Name:\"minecraft:barrel\",Properties:{{facing:\"up\"}}}}}}")
        e.append(interaction(gx + 0.5, Y + 0.95, gz + 0.5, ["sol.r3", "sol.r3d", "sol.r3i", f"sol.k3_crate{i}", f"sol.cratei{i}"], 1.3, 1.2))
    it(gx + 1.5, Y + 0.95, gz + 9.5, "m1_ped", 1.3, 1.2)
    it(gx + 5.5, Y + 0.95, gz + 9.5, "m1_reset", 1.0, 1.0)
    e.append(text_display(gx + 5.5, Y + 2.2, gz + 9.5, ["", T("Remettre les caisses", "gray")], ["sol.r3", "sol.r3d"], scale=0.45))
    # cloches
    for i, (x, z) in enumerate(M2_BELLS):
        it(x + 0.5, Y + 1.9, z + 0.5 - 0.25, f"bell{i}", 1.25, 1.2)
    it(3000.5, Y + 0.95, 40.5, "m2_box", 1.3, 1.2)
    it(2996.5, Y + 0.95, 37.5, "m2_ped", 1.3, 1.2)
    # miroirs
    for i, (x, z) in enumerate(M3_MIRRORS):
        e.append(f"summon item_display {ox + x + 0.5} {Y + 1.6} {oz + z + 0.5} {{Tags:[\"sol\",\"sol.r3\",\"sol.r3d\",\"sol.mir{i}\"],"
                 f"item:{{id:\"minecraft:glass_pane\",count:1}},transformation:{{left_rotation:[0f,0.3827f,0f,0.9239f],"
                 f"right_rotation:[0f,0f,0f,1f],translation:[0f,0f,0f],scale:[1.2f,1.2f,1.2f]}}}}")
        it(ox + x + 0.5, Y + 0.95, oz + z + 0.5, f"mir{i}", 1.0, 1.3)
    it(ox + 1.5, Y + 0.95, oz + 8.5, "m3_ped", 1.3, 1.2)
    # retours vers l’atelier (plaques)
    # encre invisible : 5 lettres + 2 indices
    for i, (x, y, z, yaw) in enumerate(INK_SPOTS):
        e.append(text_display(x, y, z, ["", T(f"{i + 1}", "dark_aqua", bold=True), T(" · ", "gray"), T(WORD[i], "aqua", bold=True)],
                              ["sol.r3", "sol.r3d", "sol.ink"], scale=1.2, billboard="fixed", yaw=yaw, hidden=True, bg=0))
    e.append(text_display(3000.5, Y + 0.6, -0.9, ["", T("« Orel, je sais ce que tu caches sous l’établi. Arrête avant le solstice,\n"
                                                        "ou je le ferai à ta place. — Y. »", "aqua", italic=True)],
                          ["sol.r3", "sol.r3d", "sol.ink", "sol.once", "sol.i_mot"], scale=0.5, billboard="fixed", yaw=0, hidden=True,
                          line_width=300, bg=0))
    e.append(text_display(2981.5, Y + 2.4, 7.9, ["", T("VERROU … DERNIER JOUR …\n", "aqua", bold=True),
                                                 T("à minuit du solstice", "aqua", italic=True)],
                          ["sol.r3", "sol.r3d", "sol.ink", "sol.once", "sol.i_plan"], scale=0.6, billboard="fixed", yaw=180, hidden=True, bg=0))
    e.append(f"summon marker 2985 {Y + 2} 5.5 {{Tags:[\"sol\",\"sol.r3\",\"sol.r3d\",\"sol.secret\",\"sol.s_r3alcove\"]}}")
    dp.fn("r3/entities", e)
    LN.ink_once("mot", ["function solstice:story/found_mot"])
    LN.ink_once("plan", ["function solstice:story/found_plan"])
    LN.secret("r3alcove", [*fill(2984, Y + 1, 5, 2985, Y + 3, 6, "air"),
                           tellraw("@a", T("✦ La Lanterne révèle un passage derrière les étagères !", "gold")),
                           "playsound minecraft:block.piston.contract master @a 2985 102 5 1 0.6"])

    # ------------------------------------------------------------ remise à zéro
    reset = ["function solstice:r3/entities",
             *fill(2984, Y + 1, 5, 2985, Y + 3, 6, "bookshelf"),
             *[f"scoreboard players set {f} {V} 0" for f in (
                 "#m1done", "#m2done", "#m3done", "#m1got", "#m2got", "#m3got", "#slot1", "#slot2", "#slot3", "#asm",
                 "#m2round", "#m2in", "#m2play", "#m2pt", "#spell", "#r3done", "#m3cfg")],
             setblock(gx + 1, Y + 1, gz + 9, "glass"), setblock(2996, Y + 2, 37, "glass"),
             setblock(ox + 1, Y + 1, oz + 8, "glass"), setblock(ox + rx, Y + 1, oz + rz, "target"),
             "function solstice:r3/sk_reset", "function solstice:r3/m2_new", "function solstice:r3/mir_show"]
    dp.fn("r3/reset", reset)
    dp.fn("build/r3", b + ["function solstice:r3/reset"])

    # ------------------------------------------------------------ cycle
    ROLES = [(MISSIONS[k][0], MISSIONS[k][1], f"Votre mission : rapporter la pièce « {MISSIONS[k][2]} ».") for k in MISSIONS]
    announce(dp, "r3/announce", ROLES, "yellow")
    dp.fn("r3/start", [
        "function solstice:r3/reset",
        f"scoreboard players set #step {V} 1", "function solstice:r3/obj",
        "function solstice:roles/draw", "function solstice:r3/announce",
        orel("Mon vieil atelier ! Pour voir ce que le temps a caché, il nous faut la Lanterne des Saisons. "
             "Trois pièces, trois missions, une par personne. Les portes sont au nord. Et on assemble ENSEMBLE, hein !"),
    ])
    hx, hy, hz, hyaw = HALL_CP
    dp.fn("r3/cp", [f"tp @s {hx} {hy} {hz} {hyaw} 0", f"spawnpoint @s {int(hx)} {hy} {int(hz)}"])
    dp.fn("r3/enter", ["execute unless score @s sol.role matches 1..3 run function solstice:roles/fill_vacant",
                       "function solstice:r3/cp", "effect give @s night_vision infinite 0 true"])
    dp.fn("r3/respawn", ["function solstice:r3/cp"])
    dp.fn("r3/wipe", [])
    dp.fn("r3/on_complete", [])
    dp.fn("r3/obj", [
        f"execute if score #step {V} matches 1 run bossbar set solstice:obj name " +
        jdump(["", T("◆ ", "gold"), T("Chacun sa mission (portes au nord) : rapportez les trois pièces de la Lanterne", "white")]),
        f"execute if score #step {V} matches 2 run bossbar set solstice:obj name " +
        jdump(["", T("◆ ", "gold"), T("Posez les trois pièces sur l’établi… en même temps !", "white")]),
        f"execute if score #step {V} matches 3 run bossbar set solstice:obj name " +
        jdump(["", T("◆ ", "gold"), T("La Lanterne révèle ce qui était caché dans l’atelier", "white")]),
    ])

    # portes de mission : plaque au sol → téléportation (réservée au joueur de la mission)
    entries = {1: M1_ENTRY, 2: M2_ENTRY, 3: M3_ENTRY}
    pt = []
    for k, (x, z) in PADS.items():
        ex, ey, ez, eyaw = entries[k]
        dp.fn(f"r3/go{k}", [
            f"execute unless entity @s[tag=sol.ro{k}] run return run " + actionbar("@s", f"Cette mission n’est pas la vôtre.", "red"),
            f"tp @s {ex} {ey} {ez} {eyaw} 0", f"spawnpoint @s {int(ex)} {ey} {int(ez)}",
            "playsound minecraft:block.portal.travel master @s ~ ~ ~ 0.2 1.6",
            *title("@s", MISSIONS[k][0], f"Rapportez : {MISSIONS[k][2]}", color=MISSIONS[k][1], times=(5, 40, 10))])
        pt.append(f"execute if entity @s[x={x - 1},y={Y + 1},z={z},dx=2,dy=1,dz=0] if score @s sol.cool matches 0 run function solstice:r3/go{k}")
    # retour : plaques de sortie des missions
    backs = [(gx + 6, gz + 10), (2995, 35), (ox + 7, oz + 8)]
    for (x, z) in backs:
        b_ = f"execute if entity @s[x={x},y={Y + 1},z={z},dx=0,dy=1,dz=0] run function solstice:r3/back"
        pt.append(b_)
    dp.fn("r3/back", ["function solstice:r3/cp", "scoreboard players set @s sol.cool 30",
                      "playsound minecraft:block.portal.travel master @s ~ ~ ~ 0.2 1.9"])
    for (x, z) in backs:
        b.append(setblock(x, Y, z, "crying_obsidian"))
    dp.add("build/r3", [setblock(x, Y, z, "crying_obsidian") for (x, z) in backs] +
           [text_display(x + 0.5, Y + 1.6, z + 0.5, ["", T("↩ Atelier", "gray")], ["sol.r3"], scale=0.6) for (x, z) in backs])
    pt.append(f"execute if score #step {V} matches 3 run function solstice:r3/spell_tick")
    dp.fn("r3/ptick", pt)

    # ------------------------------------------------------------ clics
    keys = ["slot1", "slot2", "slot3", "crate1", "crate2", "m1_ped", "m1_reset", "m2_box", "m2_ped", "m3_ped"] + \
           [f"bell{i}" for i in range(5)] + [f"mir{i}" for i in range(4)]
    clk = []
    for k in keys:
        clk.append(f"execute if entity @s[tag=sol.k3_{k}] if data entity @s interaction on target run function solstice:r3/cc/{k}")
        clk.append(f"execute if entity @s[tag=sol.k3_{k}] if data entity @s attack on attacker run function solstice:r3/cc/{k}")
        dp.fn(f"r3/cc/{k}", ["execute if score @s sol.cool matches 1.. run return 0", "scoreboard players set @s sol.cool 5",
                             f"function solstice:r3/c/{k}"])
    clk += ["data remove entity @s interaction", "data remove entity @s attack"]
    dp.fn("r3/clicked", clk)

    # --- mission 1 : caisses
    dp.fn("r3/sk_reset", [
        *[f"scoreboard players set #cr{i}x {V} {SK_CRATES[i - 1][0]}" for i in (1, 2)],
        *[f"scoreboard players set #cr{i}z {V} {SK_CRATES[i - 1][1]}" for i in (1, 2)],
        f"fill {gx} {Y + 1} {gz} {gx + 6} {Y + 1} {gz + 6} air replace barrier",
        "function solstice:r3/sk_show"])
    show = [f"fill {gx} {Y + 1} {gz} {gx + 6} {Y + 1} {gz + 6} air replace barrier"]
    for i in (1, 2):
        for x in range(7):
            for z in range(7):
                if (x, z) in SK_WALLS:
                    continue
                show.append(f"execute if score #cr{i}x {V} matches {x} if score #cr{i}z {V} matches {z} run function solstice:r3/sk_put/{i}_{x}_{z}")
                dp.fn(f"r3/sk_put/{i}_{x}_{z}", [
                    f"tp @e[type=block_display,tag=sol.crate{i}] {gx + x} {Y + 1} {gz + z}",
                    f"tp @e[type=interaction,tag=sol.cratei{i}] {gx + x + 0.5} {Y + 0.95} {gz + z + 0.5}",
                    setblock(gx + x, Y + 1, gz + z, "barrier")])
    show.append(f"scoreboard players set #onT {V} 0")
    for i in (1, 2):
        for (x, z) in SK_TARGETS:
            show.append(f"execute if score #cr{i}x {V} matches {x} if score #cr{i}z {V} matches {z} run scoreboard players add #onT {V} 1")
    show.append(f"execute if score #onT {V} matches 2 if score #m1done {V} matches 0 run function solstice:r3/m1_solved")
    dp.fn("r3/sk_show", show)
    for i in (1, 2):
        j = 3 - i
        dp.fn(f"r3/c/crate{i}", [
            f"execute if score #m1done {V} matches 1 run return 0",
            # direction : du joueur vers la caisse (axe dominant)
            f"execute store result score #px {V} run data get entity @s Pos[0] 100",
            f"execute store result score #pz {V} run data get entity @s Pos[2] 100",
            f"scoreboard players operation #qx {V} = #cr{i}x {V}", f"scoreboard players operation #qz {V} = #cr{i}z {V}",
            f"scoreboard players operation #qx {V} *= #c100 {V}", f"scoreboard players operation #qz {V} *= #c100 {V}",
            addc("#qx", gx * 100 + 50), addc("#qz", gz * 100 + 50),
            f"scoreboard players operation #qx {V} -= #px {V}", f"scoreboard players operation #qz {V} -= #pz {V}",
            f"scoreboard players operation #ax {V} = #qx {V}", f"scoreboard players operation #az {V} = #qz {V}",
            f"execute if score #ax {V} matches ..-1 run scoreboard players operation #ax {V} *= #cm1 {V}",
            f"execute if score #az {V} matches ..-1 run scoreboard players operation #az {V} *= #cm1 {V}",
            f"scoreboard players set #ddx {V} 0", f"scoreboard players set #ddz {V} 0",
            f"execute if score #ax {V} > #az {V} if score #qx {V} matches 1.. run scoreboard players set #ddx {V} 1",
            f"execute if score #ax {V} > #az {V} if score #qx {V} matches ..0 run scoreboard players set #ddx {V} -1",
            f"execute unless score #ax {V} > #az {V} if score #qz {V} matches 1.. run scoreboard players set #ddz {V} 1",
            f"execute unless score #ax {V} > #az {V} if score #qz {V} matches ..0 run scoreboard players set #ddz {V} -1",
            f"scoreboard players operation #nx {V} = #cr{i}x {V}", f"scoreboard players operation #nz {V} = #cr{i}z {V}",
            f"scoreboard players operation #nx {V} += #ddx {V}", f"scoreboard players operation #nz {V} += #ddz {V}",
            f"scoreboard players set #free {V} 1",
            f"execute unless score #nx {V} matches 0..6 run scoreboard players set #free {V} 0",
            f"execute unless score #nz {V} matches 0..6 run scoreboard players set #free {V} 0",
            *[f"execute if score #nx {V} matches {x} if score #nz {V} matches {z} run scoreboard players set #free {V} 0" for (x, z) in SK_WALLS],
            f"execute if score #nx {V} = #cr{j}x {V} if score #nz {V} = #cr{j}z {V} run scoreboard players set #free {V} 0",
            f"execute if score #free {V} matches 1 run function solstice:r3/sk_player_check",
            f"execute if score #free {V} matches 0 run playsound minecraft:block.wood.hit master @a ~ ~ ~ 1 0.6",
            f"execute if score #free {V} matches 1 run scoreboard players operation #cr{i}x {V} = #nx {V}",
            f"execute if score #free {V} matches 1 run scoreboard players operation #cr{i}z {V} = #nz {V}",
            f"execute if score #free {V} matches 1 run playsound minecraft:block.barrel.close master @a ~ ~ ~ 1 0.8",
            "function solstice:r3/sk_show"])
    # personne dans la case d’arrivée
    pc = []
    for x in range(7):
        for z in range(7):
            pc.append(f"execute if score #nx {V} matches {x} if score #nz {V} matches {z} if entity @a[x={gx + x},y={Y + 1},z={gz + z},dx=0,dy=1,dz=0] "
                      f"run scoreboard players set #free {V} 0")
    dp.fn("r3/sk_player_check", pc)
    dp.add("load", [f"scoreboard players set #cm1 {V} -1"])
    dp.fn("r3/c/m1_reset", ["function solstice:r3/sk_reset", "playsound minecraft:block.barrel.open master @a ~ ~ ~ 1 1",
                            actionbar("@s", "Les caisses reprennent leur place.", "gray")])
    dp.fn("r3/m1_solved", [f"scoreboard players set #m1done {V} 1", setblock(gx + 1, Y + 1, gz + 9, "air"),
                           "execute as @a[tag=sol.ro1] at @s run playsound minecraft:block.chest.open master @s ~ ~ ~ 1 1",
                           tellraw("@a", T("✦ Grenier : les caisses sont en place, la vitrine s’ouvre.", "gold"))])
    # --- mission 2 : cloches (mélodie aléatoire de 5 notes ; manches de 3, 4, 5 notes)
    m2new = [f"scoreboard players set #m2round {V} 1", f"scoreboard players set #m2in {V} 0",
             *[f"execute store result score #mel{i} {V} run random value 0..4" for i in range(5)],
             # pas deux fois la même note de suite
             *[f"execute if score #mel{i} {V} = #mel{i - 1} {V} run function solstice:r3/m2_bump{i}" for i in range(1, 5)]]
    dp.fn("r3/m2_new", m2new)
    for i in range(1, 5):
        dp.fn(f"r3/m2_bump{i}", [f"scoreboard players add #mel{i} {V} 1",
                                 f"execute if score #mel{i} {V} matches 5.. run scoreboard players set #mel{i} {V} 0"])
    for i, (x, z) in enumerate(M2_BELLS):
        dp.fn(f"r3/m2_ring{i}", [f"playsound minecraft:block.note_block.bell master @a {x} {Y + 2} {z} 2 {M2_PITCH[i]}",
                                 f"particle minecraft:note {x + 0.5} {Y + 3.2} {z + 0.5} 0.2 0.2 0.2 1 6 force",
                                 f"particle minecraft:end_rod {x + 0.5} {Y + 2.5} {z + 0.5} 0.3 0.3 0.3 0.02 10 force"])
    dp.fn("r3/c/m2_box", [f"execute if score #m2done {V} matches 1 run return 0",
                          f"scoreboard players set #m2play {V} 1", f"scoreboard players set #m2pt {V} 0", f"scoreboard players set #m2in {V} 0",
                          "playsound minecraft:block.note_block.chime master @a ~ ~ ~ 1 1.6"])
    play = [f"scoreboard players add #m2pt {V} 1",
            f"scoreboard players operation #m2len {V} = #m2round {V}", f"scoreboard players add #m2len {V} 2"]
    for n in range(5):
        for bell in range(5):
            play.append(f"execute if score #m2pt {V} matches {20 + n * 14} if score #m2len {V} matches {n + 1}.. if score #mel{n} {V} matches {bell} "
                        f"run function solstice:r3/m2_ring{bell}")
    play.append(f"execute if score #m2pt {V} matches 100.. run scoreboard players set #m2play {V} 0")
    dp.fn("r3/m2_play_tick", play)
    for i in range(5):
        dp.fn(f"r3/c/bell{i}", [
            f"execute if score #m2done {V} matches 1 run return run function solstice:r3/m2_ring{i}",
            f"execute if score #m2play {V} matches 1 run return 0",
            f"function solstice:r3/m2_ring{i}",
            f"scoreboard players set #want {V} -1",
            *[f"execute if score #m2in {V} matches {n} run scoreboard players operation #want {V} = #mel{n} {V}" for n in range(5)],
            f"execute unless score #want {V} matches {i} run return run function solstice:r3/m2_wrong",
            f"scoreboard players add #m2in {V} 1",
            f"scoreboard players operation #m2len {V} = #m2round {V}", f"scoreboard players add #m2len {V} 2",
            f"execute if score #m2in {V} = #m2len {V} run function solstice:r3/m2_round_ok"])
    dp.fn("r3/m2_wrong", [f"scoreboard players set #m2in {V} 0", "playsound minecraft:block.note_block.didgeridoo master @a ~ ~ ~ 1 0.6",
                          actionbar("@a[tag=sol.ro2]", "Fausse note… la boîte à musique rejoue la mélodie.", "red"),
                          f"scoreboard players set #m2play {V} 1", f"scoreboard players set #m2pt {V} -20"])
    dp.fn("r3/m2_round_ok", [
        f"scoreboard players add #m2round {V} 1", f"scoreboard players set #m2in {V} 0",
        "playsound minecraft:entity.player.levelup master @a ~ ~ ~ 0.6 1.4",
        f"execute if score #m2round {V} matches 4.. run return run function solstice:r3/m2_solved",
        actionbar("@a[tag=sol.ro2]", "Juste ! Une mélodie plus longue arrive…", "aqua"),
        f"scoreboard players set #m2play {V} 1", f"scoreboard players set #m2pt {V} -20"])
    dp.fn("r3/m2_solved", [f"scoreboard players set #m2done {V} 1", setblock(2996, Y + 2, 37, "air"),
                           tellraw("@a", T("✦ Cave : les cloches ont chanté juste, la vitrine s’ouvre.", "aqua"))])
    # --- mission 3 : miroirs (4 bits), rayon précalculé pour les 16 configurations
    for i in range(4):
        dp.fn(f"r3/c/mir{i}", [f"execute if score #m3done {V} matches 1 run return 0",
                               f"scoreboard players set #bit {V} {1 << i}",
                               f"scoreboard players operation #tmp {V} = #m3cfg {V}", f"scoreboard players operation #tmp {V} /= #bit {V}",
                               f"scoreboard players operation #tmp {V} %= #c2 {V}",
                               f"execute if score #tmp {V} matches 1 run scoreboard players operation #m3cfg {V} -= #bit {V}",
                               f"execute if score #tmp {V} matches 0 run scoreboard players operation #m3cfg {V} += #bit {V}",
                               "playsound minecraft:block.glass.hit master @a ~ ~ ~ 1 1.3", "function solstice:r3/mir_show",
                               *[f"execute if score #m3cfg {V} matches {c} run function solstice:r3/m3_solved" for c in GOOD]])
    ms = []
    for i in range(4):
        for bit, q in ((0, "0.3827f"), (1, "-0.3827f")):
            ms.append(f"scoreboard players set #bit {V} {1 << i}")
            ms.append(f"scoreboard players operation #tmp {V} = #m3cfg {V}")
            ms.append(f"scoreboard players operation #tmp {V} /= #bit {V}")
            ms.append(f"scoreboard players operation #tmp {V} %= #c2 {V}")
            ms.append(f"execute if score #tmp {V} matches {bit} run data merge entity @e[type=item_display,tag=sol.mir{i},limit=1] "
                      f"{{start_interpolation:0,interpolation_duration:5,transformation:{{left_rotation:[0f,{q},0f,0.9239f]}}}}")
    dp.fn("r3/mir_show", ms)
    for c, (path, ok) in CONFIGS.items():
        dp.fn(f"r3/beam/{c}", [f"particle minecraft:dust{{color:[1.0,0.85,0.3],scale:1.2}} {ox + x + 0.5} {Y + 1.6} {oz + z + 0.5} 0.15 0.05 0.15 0 3 force"
                               for (x, z) in path] or [f"particle minecraft:smoke {ox + sx + 1} {Y + 1.6} {oz + sz + 0.5} 0.1 0.1 0.1 0 2"])
    dp.fn("r3/beam", [f"execute if score #m3cfg {V} matches {c} run function solstice:r3/beam/{c}" for c in CONFIGS])
    dp.fn("r3/m3_solved", [f"execute if score #m3done {V} matches 1 run return 0", f"scoreboard players set #m3done {V} 1",
                           setblock(ox + 1, Y + 1, oz + 8, "air"), setblock(ox + rx, Y + 1, oz + rz, "sea_lantern"),
                           tellraw("@a", T("✦ Cabinet : la lumière touche la cible, la vitrine s’ouvre.", "light_purple"))])
    # --- piédestaux : la pièce (réservée au joueur de la mission, ou à tous si la mission est vacante)
    for k, key in ((1, "m1_ped"), (2, "m2_ped"), (3, "m3_ped")):
        dp.fn(f"r3/c/{key}", [
            f"execute if score #m{k}done {V} matches 0 run return run " + actionbar("@s", "La vitrine est fermée : terminez d’abord la mission.", "gray"),
            f"execute if score #m{k}got {V} matches 1 run return run " + actionbar("@s", "La vitrine est vide.", "gray"),
            f"scoreboard players set #m{k}got {V} 1", f"give @s {COMP[k].give()}",
            tellraw("@a", T("✦ ", MISSIONS[k][1]), {"selector": "@s", "color": "white"}, T(" rapporte la pièce « ", "gray"),
                    T(MISSIONS[k][2], MISSIONS[k][1]), T(" ».", "gray")),
            "playsound minecraft:entity.item.pickup master @a ~ ~ ~ 1 1",
            f"execute if score #m1got {V} matches 1 if score #m2got {V} matches 1 if score #m3got {V} matches 1 run function solstice:r3/to_step2"])
    dp.fn("r3/to_step2", [f"scoreboard players set #step {V} 2", "function solstice:hints/reset", "function solstice:r3/obj",
                          orel("Les trois pièces ! Revenez à l’établi et posez-les ensemble : un, deux, trois… maintenant !")])
    # --- établi : pose simultanée
    for k in (1, 2, 3):
        dp.fn(f"r3/c/slot{k}", [
            f"execute if score #lantern {V} matches 1 if score #step {V} matches 3 run return run " + actionbar("@s", "La Lanterne est déjà assemblée.", "gold"),
            f"execute if score #slot{k} {V} matches 1 run return run " + actionbar("@s", "Cette pièce est déjà posée.", "gray"),
            f"execute unless items entity @s weapon.* {COMP[k].id}[custom_data~{{sol:{{comp{k}:1b}}}}] run return run " +
            actionbar("@s", f"Cet emplacement attend : {MISSIONS[k][2]}.", MISSIONS[k][1]),
            f"clear @s {COMP[k].id}[custom_data~{{sol:{{comp{k}:1b}}}}]", f"scoreboard players set #slot{k} {V} 1",
            f"execute if score #asm {V} matches 0 run scoreboard players operation #asm {V} = #win {V}",
            item_display(BENCH[k - 1][0] + 0.5, Y + 2.35, BENCH[k - 1][1] + 0.5, COMP[k], ["sol.r3", "sol.r3d", "sol.placed"], 0.6, billboard="vertical"),
            "playsound minecraft:block.anvil.use master @a ~ ~ ~ 0.5 1.6",
            f"execute if score #slot1 {V} matches 1 if score #slot2 {V} matches 1 if score #slot3 {V} matches 1 run function solstice:r3/assemble"])
    dp.fn("r3/asm_tick", [f"scoreboard players remove #asm {V} 1", f"execute if score #asm {V} matches 0 run function solstice:r3/asm_fail"])
    dp.fn("r3/asm_fail", [
        *[f"execute if score #slot{k} {V} matches 1 as @a[tag=sol.ro{k}] run give @s {COMP[k].give()}" for k in (1, 2, 3)],
        *[f"execute if score #slot{k} {V} matches 1 unless entity @a[tag=sol.ro{k}] as @a run give @s {COMP[k].give()}" for k in (1, 2, 3)],
        *[f"scoreboard players set #slot{k} {V} 0" for k in (1, 2, 3)],
        "kill @e[type=!player,tag=sol.placed]", "playsound minecraft:block.anvil.land master @a ~ ~ ~ 0.5 0.8",
        tellraw("@a", T("Les pièces glissent de l’établi : elles doivent être posées ENSEMBLE (en même temps).", "red"))])
    dp.fn("r3/assemble", [
        f"scoreboard players set #asm {V} 0", "kill @e[type=!player,tag=sol.placed]",
        f"scoreboard players set #step {V} 3", "function solstice:hints/reset", "function solstice:r3/obj",
        f"scoreboard players set #lantern {V} 1",
        "function solstice:lantern/regive",
        *title("@a", "La Lanterne des Saisons", "Elle révèle ce que le temps a caché", color="gold", times=(10, 70, 20)),
        "particle minecraft:end_rod 3000.5 102.5 0.5 1 1 1 0.1 120 force",
        "execute as @a at @s run playsound minecraft:block.beacon.activate master @s ~ ~ ~ 1 1.2",
        orel("Elle brille ! Promenez-la dans l’atelier : l’encre invisible, les passages cachés… Et je crois que j’avais "
             "laissé la porte de sortie fermée par un mot. Un mot écrit… à l’encre invisible. Oui. C’était très malin à l’époque."),
        narr("Tenez la Lanterne en main près des murs. Épelez le mot caché en marchant sur les dalles-lettres, au sud de l’établi."),
    ])
    # --- épeler le mot en marchant sur les dalles
    sp = []
    for idx, letter in enumerate(TILES):
        c, r = idx % 4, idx // 4
        tx, tz = 2995 + 3 * c, 3 + 3 * r
        sp.append(f"execute if entity @s[x={tx},y={Y + 1},z={tz},dx=1,dy=1,dz=1] unless score @s sol.k matches {idx + 1} run function solstice:r3/tile{idx}")
        body = [f"scoreboard players set @s sol.k {idx + 1}", "playsound minecraft:block.wood.step master @a ~ ~ ~ 1 1.2"]
        for pos, want in enumerate(WORD):
            if want == letter:
                body.append(f"execute if score #spell {V} matches {pos} run return run function solstice:r3/spell_ok")
        body.append("function solstice:r3/spell_bad")
        dp.fn(f"r3/tile{idx}", body)
    sp.append(f"execute unless entity @s[x=2995,y={Y + 1},z=3,dx=11,dy=1,dz=8] run scoreboard players set @s sol.k 0")
    dp.fn("r3/spell_tick", sp)
    dp.fn("r3/spell_ok", [f"scoreboard players add #spell {V} 1", "playsound minecraft:block.note_block.pling master @a ~ ~ ~ 1 1.5",
                          actionbar("@a", ["", T("Le plancher tinte… ", "aqua"), SC("#spell"), T(f" / {len(WORD)}", "gray")]),
                          f"execute if score #spell {V} matches {len(WORD)} run function solstice:r3/done"])
    dp.fn("r3/spell_bad", [f"execute if score #spell {V} matches 0 run return 0", f"scoreboard players set #spell {V} 0",
                           "playsound minecraft:block.wood.break master @a ~ ~ ~ 1 0.6",
                           actionbar("@a", "Le plancher grince : mauvaise lettre, on recommence depuis le début.", "red")])
    dp.fn("r3/done", [f"execute if score #r3done {V} matches 1 run return 0", f"scoreboard players set #r3done {V} 1",
                      *title("@a", "TEMPS", "La grande horloge s’ouvre", color="gold"),
                      orel("« Temps ». Évidemment. J’ai toujours manqué d’imagination pour les mots de passe."),
                      "function solstice:flow/complete"])
    # --- tick
    dp.fn("r3/tick", [
        "execute as @e[type=interaction,tag=sol.r3i] at @s if data entity @s interaction run function solstice:r3/clicked",
        "execute as @e[type=interaction,tag=sol.r3i] at @s if data entity @s attack run function solstice:r3/clicked",
        f"execute if score #asm {V} matches 1.. run function solstice:r3/asm_tick",
        f"execute if score #m2play {V} matches 1 run function solstice:r3/m2_play_tick",
        f"execute if score #m4 {V} matches 0 run function solstice:r3/beam",
    ])
    hint_fn(dp, 3, {
        1: ("Chacun a sa mission, derrière sa porte au nord. Les panneaux de chaque salle expliquent le mécanisme.",
            "Grenier : on pousse une caisse en cliquant dessus, elle part dans la direction où l’on regarde. Cave : écoutez "
            "la boîte à musique puis rejouez. Cabinet : chaque miroir pivote ; suivez la lumière jusqu’à la cible."),
        2: ("L’établi a trois emplacements, un par pièce.", "Posez vos trois pièces à moins de 3 secondes d’intervalle : comptez à voix haute !"),
        3: ("La Lanterne en main révèle l’encre invisible : promenez-la le long des murs, en hauteur aussi.",
            "Cinq lettres numérotées sont cachées dans l’atelier. Épelez le mot en marchant sur les dalles, dans l’ordre."),
    })
    for key, typ, desc in (("m1", "sokoban", "Pousser deux caisses sur des repères (caisses solides, murs)."),
                           ("m2", "melody-memory", "Écouter une mélodie de cloches et la rejouer (3 manches)."),
                           ("m3", "mirror-beam", "Faire pivoter des miroirs pour guider un rayon jusqu’à une cible."),
                           ("sync", "sync-assembly", "Poser trois pièces sur l’établi en même temps, à trois."),
                           ("ink", "lantern-ink-spelling", "Révéler à la Lanterne des lettres à l’encre invisible, puis épeler le mot en marchant sur des dalles.")):
        dp.puzzle(3, key, typ, desc)
    dp.test("atelier : établi à 3 emplacements", "entity @e[type=interaction,tag=sol.k3_slot3]")
    dp.test("atelier : encre invisible (5 lettres)", "entity @e[type=text_display,tag=sol.ink,tag=sol.r3d]")
    dp.test("atelier : passage secret (marqueur)", "entity @e[type=marker,tag=sol.s_r3alcove]")
    dp.test("atelier : caisses du grenier", "entity @e[type=block_display,tag=sol.crate2]")
    dp.meta.setdefault("rooms", {})["3"] = {
        "cp": HALL_CP, "pads": PADS, "m1": M1, "sk_walls": sorted(SK_WALLS), "sk_crates": list(SK_CRATES),
        "sk_targets": sorted(SK_TARGETS), "sk_solution": SK_SOL, "m1_entry": M1_ENTRY, "m2_entry": M2_ENTRY, "m3_entry": M3_ENTRY,
        "bells": M2_BELLS, "m3": M3, "mirrors": M3_MIRRORS, "good": GOOD, "bench": BENCH, "tiles": TILES, "word": WORD,
        "ink": INK_SPOTS}
