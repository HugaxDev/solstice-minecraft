"""Salle 2 — La Tour des Engrenages. Trois puits parallèles (Cuivre, Laiton, Fer), trois niveaux + sommet commun.
Chaque joueur (tiré au sort) résout des énigmes dans SON puits ; chacune ouvre la grille d’un AUTRE puits, et
l’information nécessaire est affichée chez un coéquipier (on se guide à la voix, à travers les vitres).
Solutions : design/SPOILERS_NE_PAS_LIRE/ (registre)."""
import random

from .core import (V, T, jdump, tellraw, title, orel, narr, actionbar, fill, setblock, text_display, interaction,
                   snbt_str, SC)
from .flow import obj
from .hints import hint_fn
from .roles import announce

Y0 = 100
TR = {1: ("A", "Cuivre", "gold", 1990), 2: ("B", "Laiton", "yellow", 2000), 3: ("C", "Fer", "gray", 2010)}
FL = {1: 100, 2: 110, 3: 120}
SUMMIT = 130
# (niveau, puits de l’énigme) -> puits dont la grille s’ouvre
DOORS = {(1, 1): 2, (1, 2): 3, (1, 3): 1, (2, 1): 3, (2, 2): 1, (2, 3): 2, (3, 1): 2, (3, 2): 3, (3, 3): 1}
PID = {(k, t): f"{'abc'[t - 1]}{k}" for k in (1, 2, 3) for t in (1, 2, 3)}
ARROWS = ["↑", "→", "↓", "←"]
GLYPHS = ["☀", "☾", "✦", "❄"]
PATTERNS = ["101/010/111", "110/011/010", "111/101/100", "010/111/100", "100/110/111", "011/110/010"]
CIRCUITS = [  # (formule du mécanisme, solution L1 L2 L3) — une seule combinaison allume la lampe
    ("LAMPE = ( L1  ET  NON L2 )  ET  L3", (1, 0, 1)),
    ("LAMPE = NON ( L1  OU  L2 )  ET  L3", (0, 0, 1)),
    ("LAMPE = ( L1  ET  L2 )  ET  NON L3", (1, 1, 0)),
    ("LAMPE = NON L1  ET  L2  ET  NON L3", (0, 1, 0)),
]
COLORS = {0: ("white", "rien"), 1: ("red", "rouge"), 2: ("yellow", "jaune"), 4: ("blue", "bleu"), 3: ("orange", "orange"),
          6: ("green", "vert"), 5: ("purple", "violet"), 7: ("brown", "brun")}
PAIRS = [(3, 6), (5, 3), (6, 5), (7, 3), (6, 7), (5, 6)]


def mazes():
    """3 labyrinthes parfaits 4×4 (DFS à graine fixe) : ensemble d’arêtes ouvertes ((c,r),(c2,r2))."""
    out = []
    for seed in (5, 17, 29):
        rnd = random.Random(seed)
        seen, open_e = {(0, 3)}, set()
        stack = [(0, 3)]
        while stack:
            c, r = stack[-1]
            nb = [(c + dc, r + dr) for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1))
                  if 0 <= c + dc < 4 and 0 <= r + dr < 4 and (c + dc, r + dr) not in seen]
            if not nb:
                stack.pop()
                continue
            n = rnd.choice(nb)
            seen.add(n)
            open_e.add(frozenset(((c, r), n)))
            stack.append(n)
        out.append(open_e)
    return out


MAZES = mazes()
M_START, M_EXIT = (0, 3), (3, 0)


def cx(t):
    return TR[t][3]


def ladder_corner(k):
    return 3 if k % 2 == 1 else -3


def door_cells(t, k):
    x0, F, lx = cx(t), FL[k], cx(t) + ladder_corner(k)
    d = 1 if ladder_corner(k) > 0 else -1
    return [(lx - d, -4), (lx + d, -4), (lx, -3)]


def settext(tag, parts):
    return f"data modify entity @e[type=text_display,tag={tag},limit=1] text set value {snbt_str(jdump(parts))}"


def td(x, y, z, parts, tags, yaw, scale=0.6, lw=220, bg=0x80000000):
    return text_display(x, y, z, parts, ["sol.r2", "sol.r2d"] + list(tags), scale=scale, billboard="fixed", yaw=yaw,
                        line_width=lw, bg=bg)


def it(x, y, z, key, w=0.9, h=0.9):
    return interaction(x, y, z, ["sol.r2", "sol.r2d", "sol.r2i", f"sol.k2_{key}"], w, h)


# faces : côté A du mur A|B (x=1994.95, regarde l’ouest yaw 90), côté B (1996.05, yaw -90), etc.
FACE = {"AB_A": (1994.95, 90), "AB_B": (1996.05, -90), "BC_B": (2004.95, 90), "BC_C": (2006.05, -90),
        "A_W": (1986.05, -90), "C_E": (2014.95, 90)}


def build(dp):
    b = ["kill @e[type=!player,tag=sol.r2]"]
    b += fill(1975, 95, -12, 2025, 145, 12, "air")
    # coque de la tour
    b += fill(1985, 99, -5, 2015, 139, 5, "polished_deepslate")
    b += fill(1986, 100, -4, 2014, 138, 4, "air")
    b += fill(1986, 99, -4, 2014, 99, 4, "deepslate_tiles")
    for k, F in FL.items():
        b += fill(1986, F, -4, 2014, F, 4, "polished_andesite" if k == 1 else "smooth_stone")
    b += fill(1986, SUMMIT, -4, 2014, SUMMIT, 4, "polished_andesite")
    # murs de séparation A|B et B|C jusqu’au sommet (exclu)
    for x in (1995, 2005):
        b += fill(x, 100, -4, x, SUMMIT - 1, 4, "deepslate_bricks")
        for F in FL.values():
            b += fill(x, F + 2, -1, x, F + 3, 1, "glass_pane")
    # éclairage, bandeaux de métal propres à chaque puits
    for t in TR:
        x0 = cx(t)
        for F in list(FL.values()) + [SUMMIT]:
            b.append(setblock(x0, F + 9, 0, "lantern[hanging=true]"))
        for F in FL.values():
            b += fill(x0 - 4, F + 8, 5, x0 + 4, F + 8, 5, "cut_copper" if t == 1 else ("chiseled_copper" if t == 2 else "iron_block"))
    b += fill(1986, 131, -4, 2014, 138, 4, "air")
    b.append(setblock(2000, 137, 0, "lantern[hanging=true]"))
    # échelles et grilles (fermées) : coin NE aux niveaux impairs, NO aux niveaux pairs
    for t in TR:
        for k, F in FL.items():
            lx = cx(t) + ladder_corner(k)
            b += fill(lx, F + 1, -4, lx, F + 10, -4, "ladder[facing=south]")
    # enseignes des puits
    for t, (letter, name, color, x0) in TR.items():
        for k, F in FL.items():
            b.append(text_display(x0 + 0.5, F + 7.5, 4.9, ["", T(f"Puits du {name}", color, bold=True), T(f"\nNiveau {k}", "gray")],
                                  ["sol.r2"], scale=0.7, billboard="fixed", yaw=180))
    b.append(text_display(2000.5, 136, 0.5, ["", T("Sommet de la Tour", "gold", bold=True)], ["sol.r2"], scale=1.0))
    dp.meta.setdefault("builds", []).append("build/r2")
    dp.meta.setdefault("forceload", []).append((1975, -12, 2025, 12))

    setup = ["kill @e[type=!player,tag=sol.r2d]", f"scoreboard players set #r2t {V} 0"]
    for (k, t), pid in PID.items():
        setup.append(f"scoreboard players set #s_{pid} {V} 0")
    for t in TR:
        for k in FL:
            setup += [f"function solstice:r2/close_{'abc'[t - 1]}{k}"]
            cells = door_cells(t, k)
            F = FL[k]
            dp.fn(f"r2/close_{'abc'[t - 1]}{k}", [fill(x, F + 1, z, x, F + 3, z, "iron_bars")[0] for x, z in cells])
            dp.fn(f"r2/open_{'abc'[t - 1]}{k}", [fill(x, F + 1, z, x, F + 3, z, "air")[0] for x, z in cells] + [
                f"particle minecraft:electric_spark {cells[2][0] + 0.5} {F + 2} {cells[2][1] + 0.5} 0.6 0.8 0.6 0.1 30 force",
                f"playsound minecraft:block.iron_door.open master @a {cells[2][0]} {F + 2} {cells[2][1]} 2 0.7"])

    # ================================================================ NIVEAU 1
    F = FL[1]
    # --- A1 : cadrans fléchés (cible affichée côté B)
    xA = cx(1)
    for i, x in enumerate((xA - 2, xA, xA + 2), 1):
        setup.append(it(x + 0.5, F + 1.3, 4.3, f"a1_{i}", 0.9, 0.9))
        setup.append(td(x + 0.5, F + 2.7, 4.9, ["", T("↑", "gold", bold=True)], [f"sol.a1d{i}"], 180, scale=1.6))
        setup.append(f"scoreboard players set #a1_{i} {V} 0")
        setup.append(f"execute store result score #a1t_{i} {V} run random value 1..3")
    setup.append(td(xA + 0.5, F + 4.2, 4.9, ["", T("Cadrans du Cuivre", "gold", bold=True),
                                            T("\nClic : tourner l’aiguille", "gray")], [], 180))
    fx, yaw = FACE["AB_B"]
    setup.append(td(fx, F + 5.0, 3.0, ["", T("Les aiguilles du puits voisin\ndoivent montrer :", "yellow")], [], yaw))
    for i in (1, 2, 3):
        setup.append(td(fx, F + 3.6, 3.0 + (i - 2) * 0.9, ["", T("?", "gold", bold=True)], [f"sol.a1t{i}"], yaw, scale=1.4))
    # --- B1 : compter les étoiles du puits du Fer
    xB, xC = cx(2), cx(3)
    stars = [(FACE["C_E"], z, F + y) for z in (-3, 0, 3) for y in (6, 7)] + [((xC - 3 + 0.5, 180), 4.95, F + 6),
                                                                              ((xC + 3 + 0.5, 180), 4.95, F + 6)]
    setup.append(f"function solstice:r2/b1_stars")
    st = [f"kill @e[type=!player,tag=sol.b1star]", f"scoreboard players set #b1n {V} 0"]
    for (a, yw), zz, yy in stars:
        if yw == 90:
            pos = (a, yy, zz + 0.5)
        else:
            pos = (a, yy, zz)
        st.append(f"execute store result score #rnd {V} run random value 0..1")
        st.append(f"execute if score #rnd {V} matches 1 run " + td(*pos, ["", T("✹", "gold", bold=True)], ["sol.b1star"], yw, scale=1.6))
        st.append(f"execute if score #rnd {V} matches 1 run scoreboard players add #b1n {V} 1")
    st.append(f"execute if score #b1n {V} matches ..1 run function solstice:r2/b1_stars")
    dp.fn("r2/b1_stars", st)
    setup += [f"scoreboard players set #b1c {V} 0",
              it(xB - 2 + 0.5, F + 1.3, 4.3, "b1_minus"), it(xB + 2 + 0.5, F + 1.3, 4.3, "b1_plus"),
              it(xB + 0.5, F + 1.0, 3.4, "b1_ok", 1.2, 1.0),
              td(xB - 2 + 0.5, F + 2.4, 4.9, ["", T("−", "yellow", bold=True)], [], 180, scale=1.6),
              td(xB + 2 + 0.5, F + 2.4, 4.9, ["", T("+", "yellow", bold=True)], [], 180, scale=1.6),
              td(xB + 0.5, F + 2.6, 4.9, ["", T("0", "white", bold=True)], ["sol.b1v"], 180, scale=1.8),
              td(xB + 0.5, F + 2.1, 3.4, ["", T("Valider", "green")], [], 180, scale=0.5),
              td(xB + 0.5, F + 4.3, 4.9, ["", T("Combien d’étoiles ✹ brillent\ndans le puits du Fer, à ce niveau ?", "yellow")], [], 180)]
    b1v = [f"execute if score #b1c {V} matches {n} run " + settext("sol.b1v", ["", T(str(n), "white", bold=True)]) for n in range(10)]
    dp.fn("r2/b1_show", b1v)
    # --- C1 : gabarits (cible affichée dans le puits du Cuivre, mur ouest)
    plaques = []
    for n, x1 in enumerate((xC - 4, xC - 1, xC + 2), 1):      # mur sud : vu de l’intérieur, la gauche est à l’est
        plaques.append(("S", n, [(x1 + 2 - i, F + 4 - j, 5) for j in range(3) for i in range(3)], (x1 + 1.5, F + 2.0, 4.3)))
    for n, z1 in ((4, -1), (5, 2)):                          # mur est : la gauche est au nord
        plaques.append(("E", n, [(2015, F + 4 - j, z1 + i) for j in range(3) for i in range(3)], (2014.3, F + 2.0, z1 + 1.5)))
    plaques.append(("N", 6, [(xC - 4 + i, F + 4 - j, -5) for j in range(3) for i in range(3)], (xC - 2.5, F + 2.0, -3.7)))
    for side, n, cells, (ix, iy, iz) in plaques:
        pat = PATTERNS[n - 1].replace("/", "")
        b += [setblock(x, y, z, "black_concrete" if pat[q] == "1" else "white_concrete") for q, (x, y, z) in enumerate(cells)]
        setup.append(it(ix, iy, iz, f"c1_{n}", 1.2, 1.2))
        lx, ly, lz = cells[1]
        if side == "S":
            setup.append(td(ix, F + 5.3, 4.9, ["", T(f"{'I II III IV V VI'.split()[n - 1]}", "white")], [], 180, scale=0.6))
        elif side == "E":
            setup.append(td(2014.95, F + 5.3, iz, ["", T(f"{'I II III IV V VI'.split()[n - 1]}", "white")], [], 90, scale=0.6))
        else:
            setup.append(td(ix, F + 5.3, -3.95, ["", T("VI", "white")], [], 0, scale=0.6))
    setup.append(td(xC + 0.5, F + 6.5, 4.9, ["", T("Gabarits de fer\n", "gray", bold=True), T("Clic : choisir celui qui correspond au modèle", "gray")], [], 180))
    # cible C1 dans le puits du Cuivre (mur ouest x=1985 ; vu de l’intérieur, la gauche est au sud)
    tgt_cells = [(1985, F + 4 - j, 1 - i) for j in range(3) for i in range(3)]
    setup.append(f"execute store result score #c1t {V} run random value 1..6")
    for n in range(1, 7):
        pat = PATTERNS[n - 1].replace("/", "")
        dp.fn(f"r2/c1_show{n}", [setblock(x, y, z, "black_concrete" if pat[q] == "1" else "white_concrete")
                                 for q, (x, y, z) in enumerate(tgt_cells)])
        setup.append(f"execute if score #c1t {V} matches {n} run function solstice:r2/c1_show{n}")
    setup.append(td(1986.05, F + 5.6, 0.5, ["", T("Modèle du gabarit (puits du Fer)", "gold")], [], -90))
    setup.append(f"scoreboard players set #c1lock {V} 0")

    # ================================================================ NIVEAU 2
    F = FL[2]
    # --- A2 : mélange de couleurs (cibles affichées côté B)
    for i, (x, col) in enumerate(((xA - 2, "red"), (xA, "yellow"), (xA + 2, "blue")), 1):
        b.append(setblock(x, F + 1, 3, "cauldron"))
        setup.append(it(x + 0.5, F + 0.95, 3.5, f"a2_{i}", 1.3, 1.2))
        setup.append(td(x + 0.5, F + 2.4, 3.5, ["", T(["Rouge", "Jaune", "Bleu"][i - 1], col)], [], 180, scale=0.6))
    b.append(setblock(xA, F + 3, 5, "white_stained_glass"))
    setup += [f"scoreboard players set #a2m {V} 0", f"scoreboard players set #a2s {V} 0",
              f"execute store result score #a2p {V} run random value 0..5",
              setblock(xA, F + 3, 5, "white_stained_glass"),
              td(xA + 0.5, F + 4.4, 4.9, ["", T("Vitrail du Cuivre\n", "gold", bold=True), T("Clic sur une cuve : ajouter/retirer sa couleur", "gray")], [], 180)]
    for m, (col, _) in COLORS.items():
        dp.fn(f"r2/a2_glass{m}", [setblock(xA, F + 3, 5, f"{col}_stained_glass")])
    fx, yaw = FACE["AB_B"]
    setup.append(td(fx, F + 5.4, -2.5, ["", T("Le vitrail voisin doit prendre\nces couleurs, dans l’ordre :", "yellow")], [], yaw))
    tg = []
    for pi, (c1, c2) in enumerate(PAIRS):
        tg.append(f"execute if score #a2p {V} matches {pi} run scoreboard players set #a2t1 {V} {c1}")
        tg.append(f"execute if score #a2p {V} matches {pi} run scoreboard players set #a2t2 {V} {c2}")
        for slot, cc in ((1, c1), (2, c2)):
            tg.append(f"execute if score #a2p {V} matches {pi} run summon block_display 1996.02 {F + 4.4 - 1.3 * slot} {-3.0 + 0.1} "
                      f"{{Tags:[\"sol\",\"sol.r2\",\"sol.r2d\"],block_state:{{Name:\"minecraft:{COLORS[cc][0]}_wool\"}},"
                      f"transformation:{{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],translation:[0f,0f,0f],"
                      f"scale:[0.05f,1f,1f]}}}}")
    dp.fn("r2/a2_targets", tg)
    setup.append("function solstice:r2/a2_targets")
    for slot in (1, 2):
        setup.append(td(1996.05, F + 4.4 - 1.3 * slot + 0.4, -3.3, ["", T(f"{slot}.", "white")], [], -90, scale=0.6))
    # --- B2 : glyphes (séquence côté C, légende côté A) → pavé numérique dans B
    setup += [f"execute store result score #b2seq {V} run random value 0..5",
              f"execute store result score #b2leg {V} run random value 0..5",
              f"scoreboard players set #b2n {V} 0", f"scoreboard players set #b2e {V} 0"]
    SEQS = [(0, 1, 2, 3), (2, 0, 3, 1), (1, 3, 0, 2), (3, 2, 1, 0), (0, 2, 1, 3), (2, 3, 0, 1)]
    LEGS = [(1, 2, 3, 4), (3, 1, 4, 2), (2, 4, 1, 3), (4, 3, 2, 1), (1, 3, 2, 4), (2, 1, 4, 3)]
    fxC, ywC = FACE["BC_C"]
    fxA, ywA = FACE["AB_A"]
    g = [td(fxC, F + 5.2, 2.5, ["", T("Inscription gravée dans la pierre :", "gray")], [], ywC)]
    for si, seq in enumerate(SEQS):
        g.append(f"execute if score #b2seq {V} matches {si} run " +
                 td(fxC, F + 4.2, 2.5, ["", T("   ".join(GLYPHS[q] for q in seq), "aqua", bold=True)], [], ywC, scale=1.3))
    g.append(td(fxA, F + 5.4, 2.5, ["", T("Table des signes", "gold", bold=True)], [], ywA))
    for li, leg in enumerate(LEGS):
        g.append(f"execute if score #b2leg {V} matches {li} run " +
                 td(fxA, F + 3.9, 2.5, ["", T("\n".join(f"{GLYPHS[q]}  =  {leg[q]}" for q in range(4)), "white")], [], ywA, scale=0.8))
    # code attendu = légende(séquence), sous forme d’un nombre à 4 chiffres
    for si, seq in enumerate(SEQS):
        for li, leg in enumerate(LEGS):
            code = int("".join(str(leg[q]) for q in seq))
            g.append(f"execute if score #b2seq {V} matches {si} if score #b2leg {V} matches {li} run scoreboard players set #b2code {V} {code}")
    dp.fn("r2/b2_setup", g)
    setup.append("function solstice:r2/b2_setup")
    for d, x in enumerate((xB - 3, xB - 1, xB + 1, xB + 3), 1):
        setup.append(it(x + 0.5, F + 1.3, 4.3, f"b2_{d}"))
        setup.append(td(x + 0.5, F + 2.5, 4.9, ["", T(str(d), "yellow", bold=True)], [], 180, scale=1.4))
    setup.append(td(xB + 0.5, F + 3.6, 4.9, ["", T("_ _ _ _", "white", bold=True)], ["sol.b2v"], 180, scale=1.2))
    setup.append(td(xB + 0.5, F + 4.8, 4.9, ["", T("Serrure du Laiton : quatre chiffres", "yellow")], [], 180))
    # --- C2 : cuves de 5 L et 3 L (niveau exigé affiché dans le Cuivre)
    setup += [f"scoreboard players set #c2b {V} 0", f"scoreboard players set #c2s {V} 0",
              f"execute store result score #rnd {V} run random value 0..1",
              f"execute if score #rnd {V} matches 0 run scoreboard players set #c2t {V} 4",
              f"execute if score #rnd {V} matches 1 run scoreboard players set #c2t {V} 1"]
    c2b = [("fill_b", xC - 3, "Remplir la grande"), ("fill_s", xC - 1, "Remplir la petite"),
           ("empty_b", xC + 1, "Vider la grande"), ("empty_s", xC + 3, "Vider la petite")]
    for key, x, lab in c2b:
        setup.append(it(x + 0.5, F + 1.3, 4.3, f"c2_{key}"))
        setup.append(td(x + 0.5, F + 2.3, 4.9, ["", T(lab, "aqua")], [], 180, scale=0.45))
    for key, z, lab in (("b2s", 0, "Grande → petite"), ("s2b", 2, "Petite → grande")):
        setup.append(it(2014.3, F + 1.3, z + 0.5, f"c2_{key}"))
        setup.append(td(2014.95, F + 2.3, z + 0.5, ["", T(lab, "aqua")], [], 90, scale=0.45))
    setup.append(td(xC + 0.5, F + 3.6, 4.9, ["", T("Grande cuve : 0 / 5 L", "white")], ["sol.c2vb"], 180, scale=0.8))
    setup.append(td(xC + 0.5, F + 3.0, 4.9, ["", T("Petite cuve : 0 / 3 L", "white")], ["sol.c2vs"], 180, scale=0.8))
    setup.append(td(xC + 0.5, F + 4.6, 4.9, ["", T("Cuves du Fer", "gray", bold=True)], [], 180))
    c2t = [td(1986.05, F + 4.5, 2.5, ["", T("Niveau exigé dans la GRANDE cuve\ndu puits du Fer :", "gold")], [], -90)]
    for n in (1, 4):
        c2t.append(f"execute if score #c2t {V} matches {n} run " + td(1986.05, F + 3.2, 2.5, ["", T(f"{n} litre{'s' if n > 1 else ''}", "white", bold=True)], [], -90, scale=1.2))
    dp.fn("r2/c2_target", c2t)
    setup.append("function solstice:r2/c2_target")
    # indice « graines » (puits du Fer, niveau 2)
    setup.append(it(xC + 1.5, F + 1.0, -3.2, "seeds", 0.8, 0.6))
    setup.append(f"execute unless score #clue_graines {V} matches 1 run summon item_display {xC + 1.5} {F + 1.2} -3.2 "
                 f"{{Tags:[\"sol\",\"sol.r2\",\"sol.r2d\",\"sol.r2seed\"],item:{{id:\"minecraft:sunflower\",count:1}},"
                 f"transformation:{{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],translation:[0f,0f,0f],scale:[0.5f,0.5f,0.5f]}}}}")

    # ================================================================ NIVEAU 3
    F = FL[3]
    # --- A3 : portes logiques (schéma côté B)
    for i, x in enumerate((xA - 2, xA, xA + 2), 1):
        setup.append(setblock(x, F + 2, 4, "lever[face=wall,facing=north,powered=false]"))
        setup.append(td(x + 0.5, F + 3.1, 4.9, ["", T(f"L{i}", "gold", bold=True)], [], 180, scale=0.8))
    b.append(setblock(xA, F + 1, 2, "polished_andesite"))
    setup += [it(xA + 0.5, F + 0.95, 2.5, "a3_ok", 1.3, 1.3),
              td(xA + 0.5, F + 2.3, 2.5, ["", T("Valider\n", "green"), T("(erreur : 20 s de blocage)", "gray")], [], 180, scale=0.45),
              setblock(xA, F + 5, 5, "black_concrete"),
              td(xA + 0.5, F + 6.3, 4.9, ["", T("Lampe du Cuivre", "gold")], [], 180),
              f"execute store result score #a3c {V} run random value 0..3", f"scoreboard players set #a3lock {V} 0"]
    fx, yaw = FACE["AB_B"]
    a3 = [td(fx, F + 6.2, 2.0, ["", T("Schéma du mécanisme voisin :", "yellow")], [], yaw)]
    for ci, (txt, sol) in enumerate(CIRCUITS):
        a3.append(f"execute if score #a3c {V} matches {ci} run " + td(fx, F + 4.0, 1.5, ["", T(txt, "white")], [], yaw, scale=0.55, lw=400))
    dp.fn("r2/a3_diagram", a3)
    setup.append("function solstice:r2/a3_diagram")
    # --- B3 : labyrinthe télécommandé (murs visibles seulement côté C, mur sud)
    setup += [f"execute store result score #b3m {V} run random value 0..2",
              f"scoreboard players set #mx {V} {M_START[0]}", f"scoreboard players set #my {V} {M_START[1]}"]
    for d, (x, lab) in enumerate(((xB - 3, "↑ Nord"), (xB - 1, "↓ Sud"), (xB + 1, "← Ouest"), (xB + 3, "→ Est"))):
        setup.append(it(x + 0.5, F + 1.3, 4.3, f"b3_{'nswe'[d]}"))
        setup.append(td(x + 0.5, F + 2.4, 4.9, ["", T(lab, "yellow", bold=True)], [], 180, scale=0.6))
    setup.append(td(xB + 0.5, F + 4.4, 4.9, ["", T("Guidez le palet d’or jusqu’à la dalle d’émeraude.\n", "yellow"),
                                            T("Les murs sont invisibles… d’ici.", "gray")], [], 180))
    # dalles de B (sol y=F) : cases (c,r) → x = 1997 + 2c, z = -3 + 2r
    for c in range(4):
        for r in range(4):
            b.append(setblock(1997 + 2 * c, F, -3 + 2 * r, "emerald_block" if (c, r) == M_EXIT else
                              ("gold_block" if (c, r) == M_START else "polished_blackstone")))
    setup.append(f"summon block_display 1997.1 {F + 1} -2.9 {{Tags:[\"sol\",\"sol.r2\",\"sol.r2d\",\"sol.mk\"],teleport_duration:4,"
                 f"block_state:{{Name:\"minecraft:gold_block\"}},transformation:{{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],"
                 f"translation:[0f,0f,0f],scale:[0.8f,0.4f,0.8f]}}}}")
    # fresque côté C (mur sud z=5, x 2006..2014, y F+1..F+9 ; vu de l’intérieur : gauche = est)
    for mi, maze in enumerate(MAZES):
        mur = []
        for mcol in range(9):
            for mrow in range(9):
                x, y = 2014 - mcol, F + 9 - mrow
                is_cell = mcol % 2 == 1 and mrow % 2 == 1
                if is_cell:
                    blk = "white_concrete"
                elif mcol % 2 == 0 and mrow % 2 == 0:
                    blk = "black_concrete"
                elif mcol % 2 == 0:       # mur vertical entre (c-1,r) et (c,r)
                    c, r = mcol // 2, (mrow - 1) // 2
                    blk = "white_concrete" if 0 < c < 4 and frozenset(((c - 1, r), (c, r))) in maze else "black_concrete"
                else:                      # mur horizontal entre (c,r-1) et (c,r)
                    c, r = (mcol - 1) // 2, mrow // 2
                    blk = "white_concrete" if 0 < r < 4 and frozenset(((c, r - 1), (c, r))) in maze else "black_concrete"
                mur.append(setblock(x, y, 5, blk))
        sx, sy = 2014 - (1 + 2 * M_EXIT[0]), F + 9 - (1 + 2 * M_EXIT[1])
        mur.append(setblock(sx, sy, 5, "emerald_block"))
        dp.fn(f"r2/b3_mural{mi}", mur)
        setup.append(f"execute if score #b3m {V} matches {mi} run function solstice:r2/b3_mural{mi}")
    setup.append(f"summon block_display 2013.1 {F + 2.1} 4.6 {{Tags:[\"sol\",\"sol.r2\",\"sol.r2d\",\"sol.mk2\"],teleport_duration:4,"
                 f"block_state:{{Name:\"minecraft:gold_block\"}},transformation:{{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],"
                 f"translation:[0f,0f,0f],scale:[0.8f,0.8f,0.3f]}}}}")
    setup += [td(xC + 0.5, F + 9.6, 4.9, ["", T("N", "white", bold=True)], [], 180, scale=0.8),
              td(2014.95 - 0.2, F + 5.2, 4.9, ["", T("E", "white", bold=True)], [], 180, scale=0.8),
              td(2005.9 + 0.3, F + 5.2, 4.9, ["", T("O", "white", bold=True)], [], 180, scale=0.8)]
    # --- C3 : lumières (mur est, 3×3)
    lo = []
    for rr in range(3):
        for cc in range(3):
            y, z = F + 4 - rr, -1 + cc
            q = rr * 3 + cc
            setup.append(it(2014.4, y + 0.05, z + 0.5, f"c3_{q}", 0.9, 0.9))
            nb = [q] + [rr2 * 3 + cc2 for rr2, cc2 in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)) if 0 <= rr2 < 3 and 0 <= cc2 < 3]
            dp.fn(f"r2/c3_press{q}", [f"function solstice:r2/c3_flip{n}" for n in nb] + ["function solstice:r2/c3_check"])
            dp.fn(f"r2/c3_flip{q}", [
                f"scoreboard players add #c3_{q} {V} 1", f"execute if score #c3_{q} {V} matches 2.. run scoreboard players set #c3_{q} {V} 0",
                f"execute if score #c3_{q} {V} matches 1 run setblock 2015 {y} {z} sea_lantern",
                f"execute if score #c3_{q} {V} matches 0 run setblock 2015 {y} {z} black_concrete"])
            lo.append(f"scoreboard players set #c3_{q} {V} 1")
            lo.append(setblock(2015, y, z, "sea_lantern"))
    lo += [f"scoreboard players set #c3scr {V} 1"]
    for _ in range(5):
        lo += [f"execute store result score #rnd {V} run random value 0..8"] + \
              [f"execute if score #rnd {V} matches {q} run function solstice:r2/c3_scramble{q}" for q in range(9)]
    lo += [f"scoreboard players set #c3scr {V} 0",
           f"execute if score #c3_0 {V} matches 1 if score #c3_1 {V} matches 1 if score #c3_2 {V} matches 1 if score #c3_3 {V} matches 1 "
           f"if score #c3_4 {V} matches 1 if score #c3_5 {V} matches 1 if score #c3_6 {V} matches 1 if score #c3_7 {V} matches 1 "
           f"if score #c3_8 {V} matches 1 run function solstice:r2/c3_press4"]
    for q in range(9):
        rr, cc = divmod(q, 3)
        nb = [q] + [rr2 * 3 + cc2 for rr2, cc2 in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)) if 0 <= rr2 < 3 and 0 <= cc2 < 3]
        dp.fn(f"r2/c3_scramble{q}", [f"function solstice:r2/c3_flip{n}" for n in nb])
    dp.fn("r2/c3_lights", lo)
    setup += ["function solstice:r2/c3_lights",
              td(2014.95, F + 5.5, 0.5, ["", T("Rallumez toutes les lampes\n", "gray", bold=True),
                                         T("(chaque lampe bascule aussi ses voisines)", "gray")], [], 90)]
    dp.fn("r2/c3_check", [
        f"execute if score #c3scr {V} matches 1 run return 0",
        f"execute if score #c3_0 {V} matches 1 if score #c3_1 {V} matches 1 if score #c3_2 {V} matches 1 if score #c3_3 {V} matches 1 "
        f"if score #c3_4 {V} matches 1 if score #c3_5 {V} matches 1 if score #c3_6 {V} matches 1 if score #c3_7 {V} matches 1 "
        f"if score #c3_8 {V} matches 1 run function solstice:r2/solve_c3"])
    # affichage des infos en mode debug (1–2 joueurs)
    setup.append(f"execute if score #debug {V} matches 1 run function solstice:r2/debug_info")
    dp.fn("r2/setup", setup + ["function solstice:r2/show_all"])
    dp.fn("build/r2", b + ["function solstice:r2/setup"])
    dp.fn("r2/show_all", ["function solstice:r2/a1_show", "function solstice:r2/b1_show", "function solstice:r2/mk_show"])

    # ================================================================ logique commune
    for (k, t), pid in PID.items():
        door = DOORS[(k, t)]
        dp.fn(f"r2/solve_{pid}", [
            f"execute if score #s_{pid} {V} matches 1 run return 0",
            f"scoreboard players set #s_{pid} {V} 1",
            f"function solstice:r2/open_{'abc'[door - 1]}{k}",
            tellraw("@a", T("⚙ ", "gold"), T(f"Puits du {TR[t][1]}", TR[t][2]), T(" : mécanisme résolu → la grille du ", "gray"),
                    T(f"puits du {TR[door][1]}", TR[door][2]), T(f" (niveau {k}) s’ouvre !", "gray")),
            "execute as @a at @s run playsound minecraft:block.note_block.chime master @s ~ ~ ~ 0.8 1.4",
            "function solstice:r2/progress",
        ])
    prog = [f"scoreboard players set #lv {V} 1"]
    for k in (1, 2, 3):
        cond = " ".join(f"if score #s_{PID[(k, t)]} {V} matches 1" for t in TR)
        prog.append(f"execute if score #lv {V} matches {k} {cond} run scoreboard players set #lv {V} {k + 1}")
    prog += [f"execute unless score #lv {V} = #step {V} run function solstice:r2/new_step"]
    dp.fn("r2/progress", prog)
    dp.fn("r2/new_step", [f"scoreboard players operation #step {V} = #lv {V}", "function solstice:hints/reset", "function solstice:r2/obj"])
    dp.fn("r2/obj", [
        *[f"execute if score #step {V} matches {k} run bossbar set solstice:obj name " +
          jdump(["", T("◆ ", "gold"), T(f"Niveau {k} : résolvez l’énigme de votre puits (elle ouvre la grille d’un autre)", "white")])
          for k in (1, 2, 3)],
        f"execute if score #step {V} matches 4.. run bossbar set solstice:obj name " +
        jdump(["", T("◆ ", "gold"), T("Retrouvez-vous tous au sommet de la Tour", "white")]),
    ])

    # --- A1
    for i in (1, 2, 3):
        dp.fn(f"r2/c/a1_{i}", [f"scoreboard players add #a1_{i} {V} 1", f"execute if score #a1_{i} {V} matches 4.. run scoreboard players set #a1_{i} {V} 0",
                              "playsound minecraft:block.chain.hit master @a ~ ~ ~ 1 1.2", "function solstice:r2/a1_show", "function solstice:r2/a1_check"])
    a1s = []
    for i in (1, 2, 3):
        for d in range(4):
            a1s.append(f"execute if score #a1_{i} {V} matches {d} run " + settext(f"sol.a1d{i}", ["", T(ARROWS[d], "gold", bold=True)]))
            a1s.append(f"execute if score #a1t_{i} {V} matches {d} run " + settext(f"sol.a1t{i}", ["", T(ARROWS[d], "gold", bold=True)]))
    dp.fn("r2/a1_show", a1s)
    dp.fn("r2/a1_check", [f"execute if score #a1_1 {V} = #a1t_1 {V} if score #a1_2 {V} = #a1t_2 {V} if score #a1_3 {V} = #a1t_3 {V} "
                          f"run function solstice:r2/solve_a1"])
    # --- B1
    dp.fn("r2/c/b1_plus", [f"scoreboard players add #b1c {V} 1", f"execute if score #b1c {V} matches 10.. run scoreboard players set #b1c {V} 0",
                           "playsound minecraft:block.wooden_button.click_on master @a ~ ~ ~ 1 1.2", "function solstice:r2/b1_show"])
    dp.fn("r2/c/b1_minus", [f"scoreboard players remove #b1c {V} 1", f"execute if score #b1c {V} matches ..-1 run scoreboard players set #b1c {V} 9",
                            "playsound minecraft:block.wooden_button.click_on master @a ~ ~ ~ 1 0.9", "function solstice:r2/b1_show"])
    dp.fn("r2/c/b1_ok", [f"execute if score #b1c {V} = #b1n {V} run return run function solstice:r2/solve_b1",
                         "playsound minecraft:block.note_block.bass master @a ~ ~ ~ 1 0.6",
                         actionbar("@s", "Le mécanisme ne bouge pas. Ce n’est pas le bon nombre.", "red")])
    # --- C1
    for n in range(1, 7):
        dp.fn(f"r2/c/c1_{n}", [
            f"execute if score #c1lock {V} matches 1.. run return run " + actionbar("@s", "Les gabarits sont bloqués… patientez.", "gray"),
            f"execute if score #c1t {V} matches {n} run return run function solstice:r2/solve_c1",
            f"scoreboard players set #c1lock {V} 100",
            "playsound minecraft:block.anvil.land master @a ~ ~ ~ 0.5 1.4",
            actionbar("@s", "Ce gabarit ne correspond pas. Les gabarits se bloquent 5 secondes.", "red")])
    # --- A2
    for i, bit in ((1, 1), (2, 2), (3, 4)):
        dp.fn(f"r2/c/a2_{i}", [
            f"scoreboard players set #bit {V} {bit}", "function solstice:r2/a2_toggle",
            "playsound minecraft:item.bucket.empty master @a ~ ~ ~ 0.8 1.2", "function solstice:r2/a2_after"])
    tog = [f"scoreboard players operation #tmp {V} = #a2m {V}", f"scoreboard players operation #tmp {V} /= #bit {V}",
           f"scoreboard players operation #tmp {V} %= #c2 {V}",
           f"execute if score #tmp {V} matches 1 run scoreboard players operation #a2m {V} -= #bit {V}",
           f"execute if score #tmp {V} matches 0 run scoreboard players operation #a2m {V} += #bit {V}"]
    dp.fn("r2/a2_toggle", tog)
    dp.fn("r2/a2_after", [*[f"execute if score #a2m {V} matches {m} run function solstice:r2/a2_glass{m}" for m in COLORS],
                          f"execute if score #a2s {V} matches 0 if score #a2m {V} = #a2t1 {V} run function solstice:r2/a2_first",
                          f"execute if score #a2s {V} matches 1 if score #a2m {V} = #a2t2 {V} run function solstice:r2/solve_a2"])
    dp.fn("r2/a2_first", [f"scoreboard players set #a2s {V} 1", "playsound minecraft:block.amethyst_block.chime master @a ~ ~ ~ 1 1.2",
                          actionbar("@a", "Le vitrail tinte : première couleur acceptée !", "gold")])
    # --- B2
    for d in (1, 2, 3, 4):
        dp.fn(f"r2/c/b2_{d}", [
            f"scoreboard players operation #b2e {V} *= #c10 {V}", f"scoreboard players add #b2e {V} {d}",
            f"scoreboard players add #b2n {V} 1", "playsound minecraft:block.stone_button.click_on master @a ~ ~ ~ 1 1.1",
            "function solstice:r2/b2_show",
            f"execute if score #b2n {V} matches 4.. run function solstice:r2/b2_check"])
    dp.fn("r2/b2_show", [f"execute if score #b2n {V} matches {n} run " + settext("sol.b2v", ["", T(" ".join(["●"] * n + ["_"] * (4 - n)), "white", bold=True)])
                         for n in range(5)])
    dp.fn("r2/b2_check", [f"execute if score #b2e {V} = #b2code {V} run function solstice:r2/solve_b2",
                          f"execute unless score #b2e {V} = #b2code {V} run function solstice:r2/b2_wrong",
                          f"scoreboard players set #b2e {V} 0", f"scoreboard players set #b2n {V} 0", "function solstice:r2/b2_show"])
    dp.fn("r2/b2_wrong", ["playsound minecraft:block.note_block.bass master @a ~ ~ ~ 1 0.5",
                          actionbar("@a", "La serrure du Laiton recrache la combinaison.", "red")])
    # --- C2
    ops = {
        "fill_b": [f"scoreboard players set #c2b {V} 5"], "fill_s": [f"scoreboard players set #c2s {V} 3"],
        "empty_b": [f"scoreboard players set #c2b {V} 0"], "empty_s": [f"scoreboard players set #c2s {V} 0"],
        "b2s": [f"scoreboard players set #room3 {V} 3", f"scoreboard players operation #room3 {V} -= #c2s {V}",
                f"execute if score #room3 {V} > #c2b {V} run scoreboard players operation #room3 {V} = #c2b {V}",
                f"scoreboard players operation #c2b {V} -= #room3 {V}", f"scoreboard players operation #c2s {V} += #room3 {V}"],
        "s2b": [f"scoreboard players set #room3 {V} 5", f"scoreboard players operation #room3 {V} -= #c2b {V}",
                f"execute if score #room3 {V} > #c2s {V} run scoreboard players operation #room3 {V} = #c2s {V}",
                f"scoreboard players operation #c2s {V} -= #room3 {V}", f"scoreboard players operation #c2b {V} += #room3 {V}"],
    }
    for key, body in ops.items():
        dp.fn(f"r2/c/c2_{key}", body + ["playsound minecraft:item.bucket.fill master @a ~ ~ ~ 0.8 1", "function solstice:r2/c2_show",
                                         f"execute if score #c2b {V} = #c2t {V} run function solstice:r2/solve_c2"])
    dp.fn("r2/c2_show", [f"execute if score #c2b {V} matches {n} run " + settext("sol.c2vb", ["", T(f"Grande cuve : {n} / 5 L", "white")]) for n in range(6)] +
          [f"execute if score #c2s {V} matches {n} run " + settext("sol.c2vs", ["", T(f"Petite cuve : {n} / 3 L", "white")]) for n in range(4)])
    dp.fn("r2/c/seeds", ["function solstice:story/found_graines", "kill @e[type=!player,tag=sol.r2seed]",
                         narr("Coincé dans un engrenage : un sachet de graines déchiré.", "@s")])
    # --- A3
    F3 = FL[3]
    lev = lambda i, on: f"block {xA - 4 + 2 * i} {F3 + 2} 4 lever[powered={'true' if on else 'false'}]"
    a3 = [f"execute if score #a3lock {V} matches 1.. run return run " + actionbar("@s", "Le mécanisme est bloqué. Patientez…", "red")]
    for ci, (txt, sol) in enumerate(CIRCUITS):
        cond = " ".join(f"if {lev(i, sol[i - 1])}" for i in (1, 2, 3))
        a3.append(f"execute if score #a3c {V} matches {ci} {cond} run return run function solstice:r2/solve_a3")
    a3.append("function solstice:r2/a3_wrong")
    dp.fn("r2/c/a3_ok", a3)
    dp.fn("r2/a3_wrong", [f"scoreboard players set #a3lock {V} 400",
                          *[setblock(xA - 4 + 2 * i, F3 + 2, 4, "lever[face=wall,facing=north,powered=false]") for i in (1, 2, 3)],
                          "playsound minecraft:entity.generic.extinguish_fire master @a ~ ~ ~ 1 0.6",
                          actionbar("@a", "Court-circuit ! Les leviers se relèvent et le mécanisme se bloque 20 secondes.", "red")])
    # --- B3
    for d, (dc, dr) in zip("nswe", ((0, -1), (0, 1), (-1, 0), (1, 0))):
        body = [f"scoreboard players set #okm {V} 0"]
        for mi, maze in enumerate(MAZES):
            for c in range(4):
                for r in range(4):
                    n = (c + dc, r + dr)
                    if frozenset(((c, r), n)) in maze:
                        body.append(f"execute if score #b3m {V} matches {mi} if score #mx {V} matches {c} if score #my {V} matches {r} "
                                    f"run scoreboard players set #okm {V} 1")
        body += [(f"execute if score #okm {V} matches 1 run scoreboard players {'add' if dc > 0 else 'remove'} #mx {V} {abs(dc)}") if dc else None,
                 (f"execute if score #okm {V} matches 1 run scoreboard players {'add' if dr > 0 else 'remove'} #my {V} {abs(dr)}") if dr else None,
                 f"execute if score #okm {V} matches 0 run function solstice:r2/b3_bump",
                 f"execute if score #okm {V} matches 1 run playsound minecraft:block.stone.step master @a ~ ~ ~ 1 1",
                 "function solstice:r2/mk_show",
                 f"execute if score #mx {V} matches {M_EXIT[0]} if score #my {V} matches {M_EXIT[1]} run function solstice:r2/solve_b3"]
        dp.fn(f"r2/c/b3_{d}", body)
    dp.fn("r2/b3_bump", [f"scoreboard players set #mx {V} {M_START[0]}", f"scoreboard players set #my {V} {M_START[1]}",
                         "playsound minecraft:block.anvil.land master @a ~ ~ ~ 0.5 1.5",
                         actionbar("@a", "Clang ! Un mur invisible… le palet revient au départ.", "red")])
    mk = []
    for c in range(4):
        for r in range(4):
            mk.append(f"execute if score #mx {V} matches {c} if score #my {V} matches {r} run tp @e[type=block_display,tag=sol.mk] "
                      f"{1997 + 2 * c + 0.1} {F3 + 1} {-3 + 2 * r + 0.1}")
            mk.append(f"execute if score #mx {V} matches {c} if score #my {V} matches {r} run tp @e[type=block_display,tag=sol.mk2] "
                      f"{2014 - (1 + 2 * c) + 0.1} {F3 + 9 - (1 + 2 * r) + 0.1} 4.6")
    dp.fn("r2/mk_show", mk)
    # --- C3
    for q in range(9):
        dp.fn(f"r2/c/c3_{q}", [f"function solstice:r2/c3_press{q}", "playsound minecraft:block.lever.click master @a ~ ~ ~ 1 1.3"])

    # --------------------------------------------------------------- clics (réservés au puits du joueur)
    keys = [f"a1_{i}" for i in (1, 2, 3)] + ["b1_plus", "b1_minus", "b1_ok"] + [f"c1_{n}" for n in range(1, 7)] + \
           [f"a2_{i}" for i in (1, 2, 3)] + [f"b2_{d}" for d in (1, 2, 3, 4)] + \
           [f"c2_{k}" for k in ops] + ["seeds", "a3_ok"] + [f"b3_{d}" for d in "nswe"] + [f"c3_{q}" for q in range(9)]
    owner = lambda k: {"a": 1, "b": 2, "c": 3}.get(k[0], 0) if k != "seeds" else 3
    clk = []
    for k in keys:
        clk.append(f"execute if entity @s[tag=sol.k2_{k}] if data entity @s interaction on target run function solstice:r2/cc/{k}")
        clk.append(f"execute if entity @s[tag=sol.k2_{k}] if data entity @s attack on attacker run function solstice:r2/cc/{k}")
        o = owner(k)
        pid = k.split("_")[0]
        dp.fn(f"r2/cc/{k}", [
            "execute if score @s sol.cool matches 1.. run return 0", "scoreboard players set @s sol.cool 5",
            f"execute unless entity @s[tag=sol.ro{o}] run return run " + actionbar("@s", "Ce mécanisme n’est pas dans votre puits.", "red"),
            (f"execute if score #s_{pid} {V} matches 1 run return run " + actionbar("@s", "Ce mécanisme est déjà résolu.", "green"))
            if pid in PID.values() else None,
            f"function solstice:r2/c/{k}"])
    clk += ["data remove entity @s interaction", "data remove entity @s attack"]
    dp.fn("r2/clicked", clk)

    # --------------------------------------------------------------- cycle de la salle
    ROLES = [(f"Puits du {TR[t][1]}", TR[t][2], "Vos énigmes ouvrent les grilles des autres. Parlez-vous !") for t in TR]
    announce(dp, "r2/announce", ROLES, "gold")
    dp.fn("r2/start", [
        "function solstice:r2/setup",
        f"scoreboard players set #step {V} 1", "function solstice:r2/obj",
        "function solstice:roles/draw", "function solstice:r2/announce",
        "execute as @a run scoreboard players set @s sol.cp 1",
        *[f"execute if score #vac{t} {V} matches 1 run function solstice:r2/auto{t}" for t in TR],
        orel("La Tour des Engrenages ! Trois puits, trois grimpeurs. Chaque mécanisme ouvre la grille d’un voisin. "
             "Regardez à travers les vitres et parlez-vous : les engrenages adorent la conversation."),
    ])
    for t in TR:
        dp.fn(f"r2/auto{t}", [f"function solstice:r2/solve_{PID[(k, t)]}" for k in (1, 2, 3)] +
              [tellraw("@a", T(f"[debug] Puits du {TR[t][1]} vacant : l’automate d’Orel résout ses mécanismes.", "red"))])
    for t in TR:
        for k in (1, 2, 3):
            dp.fn(f"r2/cp_{t}_{k}", [f"tp @s {cx(t) + 0.5} {FL[k] + 1} 1.5 180 0", f"spawnpoint @s {cx(t)} {FL[k] + 1} 1"])
    cp = []
    for t in TR:
        for k in (1, 2, 3):
            cp.append(f"execute if score @s sol.role matches {t} if score @s sol.cp matches {k} run return run function solstice:r2/cp_{t}_{k}")
    cp += [f"execute if score @s sol.cp matches 4 run return run tp @s 2000.5 131 0.5",
           f"tp @s 2000.5 {FL[1] + 1} 1.5 180 0"]
    dp.fn("r2/cp", cp)
    dp.fn("r2/enter", [
        "execute unless score @s sol.role matches 1..3 run function solstice:roles/fill_vacant",
        "execute unless score @s sol.cp matches 1..4 run scoreboard players set @s sol.cp 1",
        "function solstice:r2/cp", "effect give @s night_vision infinite 0 true"])
    dp.fn("r2/respawn", ["function solstice:r2/cp"])
    dp.fn("r2/wipe", [])
    dp.fn("r2/on_complete", [f"execute if score #rt {V} matches ..14400 run function solstice:challenge/grant_horlogerie_fine"])
    pt = [f"execute if score @s sol.y matches {FL[k] + 1}..{FL[k] + 9} if score @s sol.cp matches ..{k - 1} run scoreboard players set @s sol.cp {k}"
          for k in (2, 3)]
    pt.append(f"execute if score @s sol.y matches {SUMMIT + 1}.. run scoreboard players set @s sol.cp 4")
    dp.fn("r2/ptick", pt)
    dp.fn("r2/tick", [
        "execute as @e[type=interaction,tag=sol.r2i] at @s if data entity @s interaction run function solstice:r2/clicked",
        "execute as @e[type=interaction,tag=sol.r2i] at @s if data entity @s attack run function solstice:r2/clicked",
        f"execute if score #c1lock {V} matches 1.. run scoreboard players remove #c1lock {V} 1",
        f"execute if score #a3lock {V} matches 1.. run scoreboard players remove #a3lock {V} 1",
        f"execute store result score #atop {V} if entity @a[x=1986,y={SUMMIT + 1},z=-4,dx=28,dy=7,dz=8,gamemode=!spectator]",
        f"execute if score #atop {V} >= #np {V} if score #atop {V} >= #need {V} run function solstice:r2/done",
        f"execute if score #atop {V} matches 1.. if score #m20 {V} matches 0 as @a[y={SUMMIT + 1},dy=8] run " +
        actionbar("@s", ["", T("Au sommet : ", "gold"), SC("#atop"), T(" / ", "gray"), SC("#np")]),
    ])
    dp.fn("r2/done", [*title("@a", "Réunis au sommet !", "La Tour des Engrenages est vaincue", color="gold"),
                      orel("Magnifique. Mes engrenages n’avaient pas autant tourné depuis mon dernier anniversaire."),
                      "function solstice:flow/complete"])
    dp.fn("r2/debug_info", [
        tellraw("@a", T("[debug] Infos de la Tour (pour jouer à 1 ou 2) : ", "red")),
        tellraw("@a", T(" A1 cibles (0↑ 1→ 2↓ 3←) : ", "gray"), SC("#a1t_1"), T(" "), SC("#a1t_2"), T(" "), SC("#a1t_3"),
                T("  · B1 étoiles : ", "gray"), SC("#b1n"), T("  · C1 gabarit : ", "gray"), SC("#c1t")),
        tellraw("@a", T(" A2 couleurs (R1 J2 B4) : ", "gray"), SC("#a2t1"), T(" puis "), SC("#a2t2"),
                T("  · B2 code : ", "gray"), SC("#b2code"), T("  · C2 litres : ", "gray"), SC("#c2t"),
                T("  · A3 schéma : ", "gray"), SC("#a3c"), T("  · B3 labyrinthe : ", "gray"), SC("#b3m")),
    ])
    hint_fn(dp, 2, {
        1: ("Chaque énigme a besoin d’une information affichée dans un AUTRE puits. Décrivez ce que vous voyez à vos coéquipiers.",
            "Cuivre : le puits du Laiton voit la position des aiguilles. Laiton : comptez les étoiles… chez le Fer. "
            "Fer : le modèle du gabarit est dans le puits du Cuivre."),
        2: ("Couleurs, signes, litres : ce qui vous manque est écrit chez un voisin.",
            "Cuivre : mélangez rouge, jaune, bleu (le Laiton voit les couleurs demandées). Laiton : l’inscription est chez le Fer, "
            "la table des signes chez le Cuivre. Fer : grande 5 L, petite 3 L, transvasez (le Cuivre voit le niveau exigé)."),
        3: ("Le Laiton a besoin des yeux du Fer ; le Cuivre, du schéma du Laiton.",
            "Cuivre : ET = les deux, OU = l’un ou l’autre, NON = l’inverse. Laiton : le Fer voit les murs du labyrinthe sur son mur sud. "
            "Fer : chaque lampe bascule aussi ses voisines, visez le centre et les coins."),
        4: ("Tout le monde en haut !", "Montez l’échelle ouverte jusqu’au sommet commun."),
    })

    # tests structurels, registre, méta
    for t in TR:
        dp.test(f"tour : échelle du puits du {TR[t][1]}", f"block {cx(t) + 3} 102 -4 ladder")
        dp.test(f"tour : grille fermée du puits du {TR[t][1]} (niveau 1)", f"block {door_cells(t, 1)[2][0]} 102 {door_cells(t, 1)[2][1]} iron_bars")
    dp.test("tour : 45 éléments cliquables", "entity @e[type=interaction,tag=sol.k2_c3_8]")
    dp.test("tour : labyrinthe (palet)", "entity @e[type=block_display,tag=sol.mk]")
    for pid, typ, desc in (("a1", "arrow-dials", "Cadrans fléchés à régler selon un motif affiché chez un voisin."),
                           ("b1", "count-observe", "Compter des étoiles visibles dans un autre puits et saisir le nombre."),
                           ("c1", "silhouette-match", "Choisir le gabarit identique au modèle affiché ailleurs."),
                           ("a2", "color-mix", "Mélanger rouge/jaune/bleu pour obtenir deux couleurs dans l’ordre."),
                           ("b2", "symbol-legend", "Traduire une inscription en signes avec une légende (deux voisins) puis taper le code."),
                           ("c2", "measure-jugs", "Transvaser entre une cuve de 5 L et une de 3 L pour obtenir un niveau exact."),
                           ("a3", "logic-gates", "Leviers d’entrée d’un circuit ET/OU/NON dont le schéma est chez un voisin."),
                           ("b3", "remote-maze", "Guider un palet dans un labyrinthe dont seuls les voisins voient les murs."),
                           ("c3", "lights-out", "Grille 3×3 : chaque lampe bascule ses voisines ; tout rallumer.")):
        dp.puzzle(2, pid, typ, desc)
    dp.meta.setdefault("rooms", {})["2"] = {
        "cp": (2000.5, 101, 1.5), "cx": {t: cx(t) for t in TR}, "fl": FL, "summit": SUMMIT, "doors": {f"{k}{t}": d for (k, t), d in DOORS.items()},
        "door_cells": {f"{t}{k}": door_cells(t, k) for t in TR for k in FL}, "patterns": PATTERNS,
        "mazes": [[sorted(list(e)) for e in m] for m in MAZES], "circuits": [c[1] for c in CIRCUITS], "pairs": PAIRS}
