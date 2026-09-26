"""Salle 6 — Les Quatre Saisons. (Solutions : design/SPOILERS_NE_PAS_LIRE/SALLE6_SAISONS.md)

La même vallée en 4 exemplaires (z0 = 0/200/400/600). On voyage avec le Cadran (horloge en main + s’accroupir).
Ce qu’on fait dans une saison modifie les suivantes : le datapack suit des drapeaux et régénère les structures.
#step = nombre de cristaux rendus (0..4). Rendre un cristal fige sa saison (#lockN).
"""
import random

from .core import (fillbiome, V, T, jdump, tellraw, title, orel, narr, actionbar, fill, setblock, text_display, interaction,
                   Item, sound, SC, item_display)
from .flow import obj
from .hints import hint_fn
from .build import tree, disc, ring, box, gable_roof, lamp_post
from .lantern import LPRED
from . import rp

OX, Y = 6000, 100
S = {1: ("Printemps", "light_purple", 0, "minecraft:cherry_grove"),
     2: ("Été", "yellow", 200, "minecraft:plains"),
     3: ("Automne", "gold", 400, "minecraft:wooded_badlands"),
     4: ("Hiver", "aqua", 600, "minecraft:snowy_plains")}
DE = {1: "du Printemps", 2: "de l’Été", 3: "de l’Automne", 4: "de l’Hiver"}
LE = {1: "le Printemps", 2: "l’Été", 3: "l’Automne", 4: "l’Hiver"}


def Z(s):
    return S[s][2]


def P(s, lx, ly, lz):
    """Coordonnées absolues d’un point local (ly relatif au sol y=100)."""
    return (OX + lx, Y + ly, Z(s) + lz)


# ------------------------------------------------------------------ éléments (coordonnées locales)
ARRIVAL = (0.5, 1, 24.5)
ALTAR = (0, 8)
BELL = (3, 8)
HOURGLASS = (-3, 8)
SABLIER = (-5, 24)
RIVER_X = (-13, -11)
RIVER_Z = (-17, 31)
POOL = (-14, -19, -10, -17)
CHANNEL = (-10, -12, 5, -11)          # x1 z1 x2 z2 (canal latéral, sec par défaut)
GATE_X = -10
WHEEL = (-9, -14)
BASIN = (6, -18, 22, -4)
ISLAND = (13, -12, 15, -10)
RAVINE_Z = (-24, -21)
SPOT = (-4, -18)                      # terre fertile / tronc
BRIDGE = (-4, -3, -27, -19)           # x1 x2 z1 z2
PLATEAU_PED = (-16, -29)
CAVE_M = (24, -2, 31, 14)             # montagne de la grotte
CAVE = (24, 5, 30, 7)                 # x1 z1 x2 z2 (galerie y 101..103)
BRAZIER = (22, 3)
CAVE_PED = (29, 6)
CHAPEL = (-27, 2, -19, 10)
CHEST = (-23, 6)
FORGE = (-28, 16, -20, 22)
FLAME = (-25, 19)
BELLOWS = (-22, 19)
SHED = (17, 19, 23, 25)
TABLE = (20, 23)
ORCHARD = [(10, 13), (15, 16), (19, 12)]
BUD = (15, 15)
OAK = (-6, 12)
LEAVES = (-6, 16)
DECOR_TREES = [(-24, -8), (-20, -15), (-29, -2), (-26, 28), (8, 29), (27, 26), (0, -4), (27, -9), (-9, 2),
               (-26, -29), (6, -29), (20, -28), (26, -29), (-10, 26), (12, 3)]

ACORN = Item("oak_sapling", "Gland d’horloge", "gold", lore=["Il fait tic-tac. Il rêve d’être planté."],
             data="{sol:{acorn:1b}}", glint=True, cmd=6001)
BUD_I = Item("small_amethyst_bud", "Bourgeon de cristal", "light_purple",
             lore=["Il n’est pas mûr. Il lui faudrait du temps.", "Beaucoup de temps."], data="{sol:{bud:1b}}",
             glint=True, cmd=6002)
AXE = Item("iron_axe", "Hache de Lise", "dark_green", lore=["Pour le vieux bois seulement."],
           data="{sol:{axe:1b}}", extra={"unbreakable": "{show_in_tooltip:false}"}, cmd=6003)
CADRAN = Item("clock", "Cadran des Saisons", "gold",
              lore=["En main, accroupissez-vous : vous passez", "à la saison suivante, au même endroit."],
              data="{sol:{cadran:1b}}", glint=True)
CRYST = {k: Item("amethyst_shard", f"Cristal {DE[k]}", S[k][1],
                 lore=[f"Il appartient à l’autel {DE[k]}."], data=f"{{sol:{{cr{k}:1b}}}}", glint=True,
                 rarity="epic", stack=1, cmd=6010 + k) for k in S}


def cpred(k):
    return f"amethyst_shard[custom_data~{{sol:{{cr{k}:1b}}}}]"


APRED = "oak_sapling[custom_data~{sol:{acorn:1b}}]"
BPRED = "small_amethyst_bud[custom_data~{sol:{bud:1b}}]"
XPRED = "iron_axe[custom_data~{sol:{axe:1b}}]"
CPRED = "clock[custom_data~{sol:{cadran:1b}}]"

FLAGS = ["#acorn_got", "#planted", "#chopped", "#bud_got", "#bud_in", "#sp_taken", "#axe_got", "#sluice",
         "#ember", "#burn", "#melt", "#melted", "#pump", "#su_taken", "#au_taken", "#wi_taken", "#placed",
         "#lock1", "#lock2", "#lock3", "#lock4", "#conf", "#conf_t", "#bell1", "#bell2", "#bell3", "#bell4",
         "#chord", "#hg", "#hgs", "#rconf", "#chop", "#deadmsg", "#r6done"]


# ------------------------------------------------------------------ construction du terrain
PAL = {
    1: dict(top="grass_block", path="dirt_path", leaves="flowering_azalea_leaves", log="oak_log", cover="grass_block",
            peak="moss_block", ground_decor=[("pink_petals[flower_amount=4,facing=north]", 0.10), ("short_grass", 0.12),
                                             ("allium", 0.02), ("oxeye_daisy", 0.03), ("pink_tulip", 0.02)]),
    2: dict(top="grass_block", path="dirt_path", leaves="oak_leaves", log="oak_log", cover="grass_block",
            peak="grass_block", ground_decor=[("short_grass", 0.25), ("poppy", 0.03), ("dandelion", 0.04),
                                              ("cornflower", 0.02)]),
    3: dict(top="grass_block", path="coarse_dirt", leaves="oak_leaves", log="oak_log", cover="coarse_dirt",
            peak="coarse_dirt", ground_decor=[("dead_bush", 0.03), ("brown_mushroom", 0.03), ("red_mushroom", 0.01),
                                              ("pumpkin", 0.012), ("short_grass", 0.06)]),
    4: dict(top="snow_block", path="packed_ice", leaves=None, log="spruce_log", cover="snow_block",
            peak="snow_block", ground_decor=[("snow[layers=2]", 0.25), ("snow[layers=1]", 0.25)]),
}


def occupied(lx, lz):
    """Cases réservées aux éléments de jeu (pas de décor aléatoire)."""
    zones = [(-6, 19, 6, 29), (-5, 4, 5, 12), (-15, -20, -9, 31), (-10, -14, 6, -9), (4, -20, 24, -2),
             (-32, -25, 31, -19), (-9, -21, 1, -12), (22, -3, 31, 15), (-29, 0, -17, 12), (-29, 14, -19, 24),
             (15, 17, 25, 27), (7, 9, 22, 20), (-9, 9, -3, 18), (-2, -12, 2, 20), (-20, 4, 0, 8)]
    return any(x1 <= lx <= x2 and z1 <= lz <= z2 for x1, z1, x2, z2 in zones)


def season_tree(s, x, y, z, seed, big=False):
    p = PAL[s]
    h = 6 if big else 5
    r = 3 if big else 2
    if s == 1 and seed % 3 == 0:
        return tree(x, y, z, "cherry_log", "cherry_leaves", h, r, seed)
    if s == 4:
        out = fill(x, y, z, x, y + h - 1, z, "spruce_log")
        for dy, (dx, dz) in ((h - 2, (1, 0)), (h - 3, (-1, 0)), (h - 1, (0, 1)), (h - 2, (0, -1))):
            out.append(setblock(x + dx, y + dy, z + dz, "spruce_log[axis=x]" if dx else "spruce_log[axis=z]"))
            out.append(setblock(x + dx, y + dy + 1, z + dz, "snow", "keep"))
        out.append(setblock(x, y + h, z, "snow", "keep"))
        return out
    return tree(x, y, z, p["log"], p["leaves"], h, r, seed)


def build_season(s):
    p = PAL[s]
    rnd = random.Random(1000 + s)
    rnd_shared = random.Random(77)          # même tirage pour les 4 saisons (même vallée)
    x0, _, z0 = P(s, 0, 0, 0)
    b = [f"kill @e[type=!player,tag=sol.r6s{s}]"]
    b += fill(x0 - 40, 84, z0 - 40, x0 + 39, 130, z0 + 39, "air")
    # biomes : appliqués par tools/worldbuild.py (RCON, réponse vérifiée), voir meta « biomes »
    b += fill(x0 - 36, 90, z0 - 36, x0 + 35, 96, z0 + 35, "stone")
    b += fill(x0 - 36, 97, z0 - 36, x0 + 35, 99, z0 + 35, "dirt")
    b += fill(x0 - 36, 100, z0 - 36, x0 + 35, 100, z0 + 35, p["top"])
    # montagnes d’enceinte (bande de 4 blocs, hauteur pseudo-aléatoire commune)
    for lx in range(-36, 36):
        for lz in range(-36, 36):
            if -32 <= lx <= 31 and -32 <= lz <= 31:
                continue
            h = 104 + int(4 + 3 * ((lx * 7 + lz * 13) % 5) / 2 + (abs(lx) + abs(lz)) % 3)
            b += fill(x0 + lx, 101, z0 + lz, x0 + lx, h - 1, z0 + lz, "stone")
            b.append(setblock(x0 + lx, h, z0 + lz, p["peak"]))
    # montagne de la grotte
    x1, z1, x2, z2 = CAVE_M
    for lx in range(x1, x2 + 1):
        for lz in range(z1, z2 + 1):
            h = 106 + (lx - x1) // 2 + ((lz * 5) % 3)
            b += fill(x0 + lx, 101, z0 + lz, x0 + lx, h - 1, z0 + lz, "stone")
            b.append(setblock(x0 + lx, h, z0 + lz, p["peak"]))
    cx1, cz1, cx2, cz2 = CAVE
    b += fill(x0 + cx1, 101, z0 + cz1, x0 + cx2, 103, z0 + cz2, "air")
    b += fill(x0 + cx1, 100, z0 + cz1, x0 + cx2, 100, z0 + cz2, "gravel")
    b.append(setblock(x0 + CAVE_PED[0], 101, z0 + CAVE_PED[1], "chiseled_stone_bricks"))
    # ravin
    b += fill(x0 - 32, 84, z0 + RAVINE_Z[0], x0 + 31, 100, z0 + RAVINE_Z[1], "air")
    # rivière (source au sud du ravin) + petits ponts
    b += fill(x0 + POOL[0], 97, z0 + POOL[1], x0 + POOL[2], 100, z0 + POOL[3], "air")
    b += fill(x0 + RIVER_X[0], 97, z0 + RIVER_Z[0], x0 + RIVER_X[1], 100, z0 + RIVER_Z[1], "air")
    b += fill(x0 + POOL[0], 96, z0 + POOL[1], x0 + POOL[2], 96, z0 + POOL[3], "gravel")
    b += fill(x0 + RIVER_X[0], 96, z0 + RIVER_Z[0], x0 + RIVER_X[1], 96, z0 + RIVER_Z[1], "gravel")
    water_top = "ice" if s == 4 else "water"
    b += fill(x0 + POOL[0], 97, z0 + POOL[1], x0 + POOL[2], 98, z0 + POOL[3], "water")
    b += fill(x0 + RIVER_X[0], 97, z0 + RIVER_Z[0], x0 + RIVER_X[1], 98, z0 + RIVER_Z[1], "water")
    b += fill(x0 + POOL[0], 99, z0 + POOL[1], x0 + POOL[2], 99, z0 + POOL[3], water_top)
    b += fill(x0 + RIVER_X[0], 99, z0 + RIVER_Z[0], x0 + RIVER_X[1], 99, z0 + RIVER_Z[1], water_top)
    for bz in (6, 20, -6):
        b += fill(x0 + RIVER_X[0] - 1, 100, z0 + bz - 1, x0 + RIVER_X[1] + 1, 100, z0 + bz + 1, "spruce_planks")
        b += fill(x0 + RIVER_X[0], 99, z0 + bz - 1, x0 + RIVER_X[1], 99, z0 + bz + 1, "spruce_planks")
    # canal latéral (sec) et bassin (vide) : l’état réel est posé par r6/regen_water
    cx1, cz1, cx2, cz2 = CHANNEL
    b += fill(x0 + cx1, 99, z0 + cz1, x0 + cx2, 100, z0 + cz2, "air")
    b += fill(x0 + cx1, 98, z0 + cz1, x0 + cx2, 98, z0 + cz2, "gravel")
    bx1, bz1, bx2, bz2 = BASIN
    b += fill(x0 + bx1, 93, z0 + bz1, x0 + bx2, 93, z0 + bz2, "stone")
    b += fill(x0 + bx1, 94, z0 + bz1, x0 + bx2, 100, z0 + bz2, "air")
    ix1, iz1, ix2, iz2 = ISLAND
    b += fill(x0 + ix1, 94, z0 + iz1, x0 + ix2, 99, z0 + iz2, "stone")
    b += fill(x0 + ix1, 100, z0 + iz1, x0 + ix2, 100, z0 + iz2, p["top"])
    b.append(setblock(x0 + 14, 101, z0 - 11, "chiseled_stone_bricks"))
    # plateau nord : piédestal
    b.append(setblock(x0 + PLATEAU_PED[0], 101, z0 + PLATEAU_PED[1], "chiseled_stone_bricks"))
    # chemins
    for (ax, az, bx, bz) in [(0, 20, 0, 11), (-18, 6, -4, 6), (0, 5, 0, -8), (4, 8, 16, 19), (-4, 21, -19, 21),
                             (-2, -9, -4, -15), (0, -9, 5, -9)]:
        for t in range(0, 101):
            px = round(ax + (bx - ax) * t / 100)
            pz = round(az + (bz - az) * t / 100)
            for dd in (0, 1):
                if not (RIVER_X[0] - 1 <= px <= RIVER_X[1] + 1) and not (bx1 <= px <= bx2 and bz1 <= pz <= bz2):
                    b.append(setblock(x0 + px + dd * (1 if abs(bz - az) > abs(bx - ax) else 0), 100,
                                      z0 + pz + dd * (1 if abs(bx - ax) >= abs(bz - az) else 0), p["path"]))
    # cercle des saisons
    b += disc(x0, 100, z0 + 24, 4, "polished_andesite")
    b += ring(x0, 100, z0 + 24, 4, "mossy_stone_bricks")
    for k in range(8):
        import math
        a = math.radians(k * 45 + 22.5)
        sx, sz = round(5 * math.cos(a)), round(5 * math.sin(a))
        b += fill(x0 + sx, 101, z0 + 24 + sz, x0 + sx, 102 + (k % 2), z0 + 24 + sz, "mossy_cobblestone_wall")
    b.append(setblock(x0 + SABLIER[0], 101, z0 + SABLIER[1], "chiseled_sandstone"))
    b.append(setblock(x0 + SABLIER[0], 102, z0 + SABLIER[1], "glass"))
    # autel
    ax, az = ALTAR
    b += disc(x0 + ax, 100, z0 + az, 3, "stone_bricks")
    b += ring(x0 + ax, 100, z0 + az, 3, "chiseled_stone_bricks")
    b.append(setblock(x0 + ax, 101, z0 + az, "chiseled_stone_bricks"))
    b.append(setblock(x0 + BELL[0], 101, z0 + BELL[1], "bell[attachment=floor,facing=west]"))
    b.append(setblock(x0 + HOURGLASS[0], 101, z0 + HOURGLASS[1], "chiseled_sandstone"))
    # chapelle en ruine + coffre du temps
    cx1, cz1, cx2, cz2 = CHAPEL
    b += fill(x0 + cx1, 100, z0 + cz1, x0 + cx2, 100, z0 + cz2, "stone_bricks")
    for (wx, wz, h) in [(cx1, cz1, 4), (cx2, cz1, 3), (cx1, cz2, 5), (cx2, cz2, 2)]:
        b += fill(x0 + wx, 101, z0 + wz, x0 + wx, 100 + h, z0 + wz, "mossy_stone_bricks")
    b += fill(x0 + cx1, 101, z0 + cz1, x0 + cx1, 102, z0 + cz2, "mossy_cobblestone")
    b += fill(x0 + cx1 + 1, 101, z0 + cz1, x0 + cx2 - 1, 101, z0 + cz1, "cobblestone_wall")
    b.append(setblock(x0 + CHEST[0], 101, z0 + CHEST[1], "chest[facing=east]"))
    # forge d’été (flamme éternelle + soufflet)
    fx1, fz1, fx2, fz2 = FORGE
    b += fill(x0 + fx1, 100, z0 + fz1, x0 + fx2, 100, z0 + fz2, "cobblestone")
    b += fill(x0 + fx1, 101, z0 + fz2, x0 + fx2, 102, z0 + fz2, "bricks")
    b.append(setblock(x0 + FLAME[0], 101, z0 + FLAME[1], "campfire[lit=true]" if s == 2 else "campfire[lit=false]"))
    b.append(setblock(x0 + BELLOWS[0], 101, z0 + BELLOWS[1], "barrel[facing=west]"))
    b.append(setblock(x0 + FLAME[0], 101, z0 + FLAME[1] + 2, "anvil"))
    # atelier de Lise
    hx1, hz1, hx2, hz2 = SHED
    b += box(x0 + hx1, 100, z0 + hz1, x0 + hx2, 104, z0 + hz2, "spruce_planks", floor="spruce_planks")
    b += gable_roof(x0 + hx1, z0 + hz1, x0 + hx2, z0 + hz2, 105, "spruce", axis="x")
    b += fill(x0 + 20, 101, z0 + hz1, x0 + 20, 102, z0 + hz1, "air")
    b.append(setblock(x0 + TABLE[0], 101, z0 + TABLE[1], "crafting_table" if s != 2 else "lectern[facing=north]"))
    b.append(setblock(x0 + TABLE[0] - 2, 101, z0 + TABLE[1], "barrel[facing=up]"))
    b.append(setblock(x0 + 20, 103, z0 + 22, "lantern[hanging=true]"))
    # verger (bourgeon) et grand chêne (tas de feuilles)
    for i, (tx, tz) in enumerate(ORCHARD):
        if s == 1:
            b += tree(x0 + tx, 101, z0 + tz, "cherry_log", "cherry_leaves", 5, 2, i)
        else:
            b += season_tree(s, x0 + tx, 101, z0 + tz, i + 3)
    b += season_tree(s, x0 + OAK[0], 101, z0 + OAK[1], 99, big=True)
    if s == 3:
        b += fill(x0 + LEAVES[0] - 1, 101, z0 + LEAVES[1], x0 + LEAVES[0], 101, z0 + LEAVES[1], "oak_leaves[persistent=true]")
    # terre fertile
    b.append(setblock(x0 + SPOT[0], 100, z0 + SPOT[1], "podzol" if s != 4 else "snow_block"))
    # arbres de décor
    for i, (tx, tz) in enumerate(DECOR_TREES):
        b += season_tree(s, x0 + tx, 101, z0 + tz, i)
    # décor au sol aléatoire (même positions candidates pour les 4 saisons)
    for lx in range(-31, 32):
        for lz in range(-31, 32):
            roll = rnd_shared.random()
            if occupied(lx, lz) or RAVINE_Z[0] - 1 <= lz <= RAVINE_Z[1] + 1:
                continue
            acc = 0
            for blk, pr in p["ground_decor"]:
                acc += pr
                if roll < acc:
                    b.append(setblock(x0 + lx, 101, z0 + lz, blk, "keep"))
                    break
    # lanternes au sol pour guider
    for (lx, lz) in [(2, 18), (-2, 12), (-16, 7), (13, 17), (-3, -12), (-17, 21)]:
        b += lamp_post(x0 + lx, 101, z0 + lz, 2, "spruce_fence" if s != 4 else "spruce_fence")
    return b


# ------------------------------------------------------------------ entités (toutes saisons)
def entities(s):
    x0, _, z0 = P(s, 0, 0, 0)
    tg = lambda k: ["sol.r6", f"sol.r6s{s}", "sol.r6i", f"sol.k_{k}"]
    e = []

    def it(k, lx, lz, dy=0.0, w=1.0, h=1.0):
        e.append(interaction(x0 + lx + 0.5, Y + 1 + dy, z0 + lz + 0.5, tg(k), w, h))

    it("altar", ALTAR[0], ALTAR[1], -0.05, 1.25, 1.7)
    it("bell", BELL[0], BELL[1], -0.05, 1.3, 1.4)
    it("hourglass", HOURGLASS[0], HOURGLASS[1], -0.05, 1.25, 1.3)
    it("sablier", SABLIER[0], SABLIER[1], -0.05, 1.25, 2.2)
    it("chest", CHEST[0], CHEST[1], -0.05, 1.25, 1.1)
    it("tree", SPOT[0], SPOT[1], -0.05, 1.3, 2.2)
    it("wheel", WHEEL[0], WHEEL[1], 0, 1.25, 1.4)
    it("flame", FLAME[0], FLAME[1], -0.05, 1.25, 1.0)
    it("bellows", BELLOWS[0], BELLOWS[1], -0.05, 1.25, 1.2)
    it("brazier", BRAZIER[0], BRAZIER[1], -0.05, 1.25, 1.0)
    it("leaves", LEAVES[0], LEAVES[1], 0, 2.2, 1.0)
    it("bud", BUD[0], BUD[1], 0.2, 1.0, 1.6)
    it("table", TABLE[0], TABLE[1], -0.05, 1.25, 1.3)
    it("pick_au", PLATEAU_PED[0], PLATEAU_PED[1], -0.05, 1.25, 1.7)
    it("pick_su", CAVE_PED[0], CAVE_PED[1], -0.05, 1.25, 1.7)
    it("pick_wi", 14, -11, -0.05, 1.25, 1.7)
    # décor : la roue de la vanne, le sablier
    e.append(f"summon block_display {x0 + WHEEL[0]} {Y + 1} {z0 + WHEEL[1]} {{Tags:[\"sol\",\"sol.r6\",\"sol.r6s{s}\"],"
             f"block_state:{{Name:\"minecraft:{'stripped_oak_log' if s != 4 else 'packed_ice'}\",Properties:{{axis:\"z\"}}}},"
             f"transformation:{{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],translation:[0f,0.1f,0f],scale:[1f,1f,0.3f]}}}}")
    # inscriptions du Cercle
    rules = ["", T(f"Vallée des Saisons — {S[s][0]}\n", S[s][1], bold=True),
             T("Rendez chaque cristal à son autel,\ndans l’ordre : Printemps, Été, Automne, Hiver.\n", "white"),
             T("Un cristal rendu fige sa saison :\nplus rien n’y pourra changer.\n\n", "yellow"),
             T("« Ce que le Printemps n’a pas semé, l’Automne ne l’abattra pas.\n", "gray", italic=True),
             T("Ce que l’Été n’a pas détourné, l’Hiver ne le figera pas. »", "gray", italic=True)]
    e.append(text_display(x0 + 0.5, Y + 3.4, z0 + 19.2, rules, ["sol.r6", f"sol.r6s{s}"], scale=0.55,
                          billboard="fixed", yaw=0, line_width=330))
    e.append(text_display(x0 + SABLIER[0] + 0.5, Y + 3.3, z0 + SABLIER[1] + 0.5,
                          ["", T("Sablier de Remontée\n", "gold", bold=True), T("Remonte toute la vallée au début.\n", "gray"),
                           T("(coûteux : 30 secondes de temps figé)", "dark_gray")], ["sol.r6", f"sol.r6s{s}"], scale=0.6))
    e.append(text_display(x0 + ALTAR[0] + 0.5, Y + 3.2, z0 + ALTAR[1] + 0.5,
                          ["", T(f"Autel {DE[s]}", S[s][1], bold=True)], ["sol.r6", f"sol.r6s{s}"], scale=0.8))
    e.append(text_display(x0 + HOURGLASS[0] + 0.5, Y + 2.4, z0 + HOURGLASS[1] + 0.5,
                          ["", T("Sablier du Solstice", "gold")], ["sol.r6", f"sol.r6s{s}"], scale=0.55))
    e.append(text_display(x0 + CHEST[0] + 0.5, Y + 2.3, z0 + CHEST[1] + 0.5,
                          ["", T("Coffre du Temps", "gold")], ["sol.r6", f"sol.r6s{s}"], scale=0.55))
    if s == 1:
        e.append(text_display(x0 + SPOT[0] + 0.5, Y + 1.6, z0 + SPOT[1] + 0.5, ["", T("Terre fertile", "green")],
                              ["sol.r6", f"sol.r6s{s}", "sol.r6spot"], scale=0.5))
    return e


# ------------------------------------------------------------------ état dynamique
def regen_tree():
    """Arbre planté / adulte / vieux / abattu (pont) selon #planted et #chopped, dans les 4 saisons."""
    out = []
    for s in S:
        x0, _, z0 = P(s, 0, 0, 0)
        sx, sz = x0 + SPOT[0], z0 + SPOT[1]
        out += fill(sx - 3, 101, sz - 3, sx + 3, 110, sz + 3, "air")
        bx1, bx2, bz1, bz2 = BRIDGE
        out += fill(x0 + bx1, 100, z0 + RAVINE_Z[0], x0 + bx2, 101, z0 + RAVINE_Z[1], "air")
        out.append(setblock(sx, 100, sz, "podzol" if s != 4 else "snow_block"))
        if s == 1:
            out.append(f"execute if score #planted {V} matches 1 run setblock {sx} 101 {sz} oak_sapling")
        elif s == 2:
            grown = tree(sx, 101, sz, "oak_log", "oak_leaves", 7, 3, 5)
            out.append(f"execute if score #planted {V} matches 1 run function solstice:r6/tree/grown")
        else:
            out.append(f"execute if score #planted {V} matches 1 if score #chopped {V} matches 0 run function solstice:r6/tree/old{s}")
            out.append(f"execute if score #chopped {V} matches 1 run function solstice:r6/tree/fallen{s}")
    return out


def tree_parts(dp):
    s = 2
    x0, _, z0 = P(s, 0, 0, 0)
    sx, sz = x0 + SPOT[0], z0 + SPOT[1]
    dp.fn("r6/tree/grown", tree(sx, 101, sz, "oak_log", "oak_leaves", 7, 3, 5))
    for s in (3, 4):
        x0, _, z0 = P(s, 0, 0, 0)
        sx, sz = x0 + SPOT[0], z0 + SPOT[1]
        old = fill(sx, 101, sz, sx, 107, sz, "oak_log" if s == 3 else "spruce_log")
        for (dx, dy, dz) in [(1, 5, 0), (-1, 4, 0), (0, 6, 1), (0, 5, -1), (1, 6, 1)]:
            old.append(setblock(sx + dx, 101 + dy, sz + dz, "oak_log[axis=x]" if dx else "oak_log[axis=z]"))
        if s == 3:
            for (dx, dy, dz) in [(2, 5, 0), (1, 6, 0), (-1, 5, 1), (0, 7, 0), (0, 6, -1)]:
                old.append(setblock(sx + dx, 101 + dy, sz + dz, "oak_leaves[persistent=true]", "keep"))
        else:
            old.append(setblock(sx, 108, sz, "snow"))
        dp.fn(f"r6/tree/old{s}", old)
        bx1, bx2, bz1, bz2 = BRIDGE
        fallen = [setblock(sx, 101, sz, "stripped_oak_log" if s == 3 else "stripped_spruce_log")]
        fallen += fill(x0 + bx1, 100, z0 + RAVINE_Z[0] - 3, x0 + bx2, 100, sz - 1, "oak_log[axis=z]")
        if s == 4:
            fallen += fill(x0 + bx1, 101, z0 + RAVINE_Z[0] - 3, x0 + bx2, 101, sz - 1, "snow")
        else:
            fallen += [setblock(x0 + bx1 - 1, 101, z0 + RAVINE_Z[0] - 3, "oak_leaves[persistent=true]"),
                       setblock(x0 + bx2 + 1, 101, z0 + RAVINE_Z[0] - 2, "oak_leaves[persistent=true]")]
        dp.fn(f"r6/tree/fallen{s}", fallen)


def regen_water():
    """Vanne fermée : canal et bassin secs. Ouverte (#sluice = 4) : eau en été et automne, glace en hiver."""
    out = []
    cx1, cz1, cx2, cz2 = CHANNEL
    bx1, bz1, bx2, bz2 = BASIN
    ix1, iz1, ix2, iz2 = ISLAND
    for s in (2, 3, 4):
        x0, _, z0 = P(s, 0, 0, 0)
        out += fill(x0 + GATE_X, 99, z0 + cz1, x0 + GATE_X, 100, z0 + cz2, "spruce_planks")
        out += fill(x0 + cx1 + 1, 99, z0 + cz1, x0 + cx2, 100, z0 + cz2, "air")
        out += fill(x0 + bx1, 94, z0 + bz1, x0 + bx2, 100, z0 + bz2, "air")
        out += fill(x0 + ix1, 94, z0 + iz1, x0 + ix2, 99, z0 + iz2, "stone")
    for s in (2, 3, 4):
        out.append(f"execute if score #sluice {V} matches 4.. run function solstice:r6/water/on{s}")
    # printemps : jamais affecté (c’est le passé)
    x0, _, z0 = P(1, 0, 0, 0)
    out += fill(x0 + GATE_X, 99, z0 + cz1, x0 + GATE_X, 100, z0 + cz2, "spruce_planks")
    return out


def water_parts(dp):
    cx1, cz1, cx2, cz2 = CHANNEL
    bx1, bz1, bx2, bz2 = BASIN
    ix1, iz1, ix2, iz2 = ISLAND
    for s in (2, 3, 4):
        x0, _, z0 = P(s, 0, 0, 0)
        top = "ice" if s == 4 else "water"
        on = [*fill(x0 + GATE_X, 99, z0 + cz1, x0 + GATE_X, 100, z0 + cz2, "air"),
              *fill(x0 + GATE_X, 99, z0 + cz1, x0 + GATE_X, 99, z0 + cz2, top),
              *fill(x0 + cx1 + 1, 99, z0 + cz1, x0 + cx2, 99, z0 + cz2, top),
              *fill(x0 + bx1, 94, z0 + bz1, x0 + bx2, 98, z0 + bz2, "water"),
              *fill(x0 + bx1, 99, z0 + bz1, x0 + bx2, 99, z0 + bz2, top),
              *fill(x0 + ix1, 94, z0 + iz1, x0 + ix2, 99, z0 + iz2, "stone")]
        if s == 4:
            on += fill(x0 + GATE_X, 99, z0 + cz1, x0 + GATE_X, 99, z0 + cz2, "packed_ice")
        dp.fn(f"r6/water/on{s}", on)


def regen_cave():
    x0, _, z0 = P(4, 0, 0, 0)
    cx1, cz1, cx2, cz2 = CAVE
    return [*fill(x0 + cx1, 101, z0 + cz1, x0 + cx1, 103, z0 + cz2, "packed_ice"),
            f"execute if score #melted {V} matches 1 run fill {x0 + cx1} 101 {z0 + cz1} {x0 + cx1} 103 {z0 + cz2} air",
            setblock(x0 + BRAZIER[0], 101, z0 + BRAZIER[1], "campfire[lit=false]"),
            f"execute if score #burn {V} matches 1.. run setblock {x0 + BRAZIER[0]} 101 {z0 + BRAZIER[1]} campfire[lit=true]"]


# ------------------------------------------------------------------ logique
def build(dp):
    for s in S:
        x0, _, z0 = P(s, 0, 0, 0)
        dp.meta.setdefault("biomes", []).extend(fillbiome(x0 - 40, 80, z0 - 40, x0 + 39, 130, z0 + 39, S[s][3]))
        dp.fn(f"build/r6_s{s}", build_season(s))
        dp.meta.setdefault("builds", []).append(f"build/r6_s{s}")
        x0, _, z0 = P(s, 0, 0, 0)
        dp.meta.setdefault("forceload", []).append((x0 - 40, z0 - 40, x0 + 39, z0 + 39))
    dp.fn("build/r6", ["function solstice:r6/reset_valley"])
    dp.meta["builds"].append("build/r6")
    dp.fn("r6/spawn_entities", ["kill @e[type=!player,tag=sol.r6]", *[l for s in S for l in entities(s)],
                                "function solstice:r6/displays"])
    tree_parts(dp)
    water_parts(dp)
    dp.fn("r6/regen_tree", regen_tree())
    dp.fn("r6/regen_water", regen_water())
    dp.fn("r6/regen_cave", regen_cave())
    dp.add("load", ["scoreboard objectives add sol.sea dummy", "scoreboard objectives add sol.trv dummy"])

    # affichages dépendants de l’état (cristaux, bourgeon…)
    disp = ["kill @e[type=!player,tag=sol.r6disp]"]

    def show(cond, s, lx, lz, dy, item, scale=0.6):
        x0, _, z0 = P(s, 0, 0, 0)
        disp.append(f"execute {cond}run " + item_display(x0 + lx + 0.5, Y + 1 + dy, z0 + lz + 0.5, item,
                                                          ["sol.r6", "sol.r6disp"], scale, billboard="vertical"))
    for k in S:
        show(f"if score #placed {V} matches {k}.. ", k, ALTAR[0], ALTAR[1], 1.6, CRYST[k], 0.8)
    show(f"if score #au_taken {V} matches 0 ", 3, PLATEAU_PED[0], PLATEAU_PED[1], 0.8, CRYST[3])
    show(f"if score #melted {V} matches 1 if score #su_taken {V} matches 0 ", 4, CAVE_PED[0], CAVE_PED[1], 0.8, CRYST[2])
    show(f"if score #wi_taken {V} matches 0 ", 4, 14, -11, 0.8, CRYST[4])
    show(f"if score #bud_got {V} matches 0 ", 1, BUD[0], BUD[1], 1.3, BUD_I, 0.5)
    show(f"if score #bud_in {V} matches 1 if score #sp_taken {V} matches 0 ", 1, CHEST[0], CHEST[1], 0.9, BUD_I, 0.4)
    show(f"if score #bud_in {V} matches 1 if score #sp_taken {V} matches 0 ", 2, CHEST[0], CHEST[1], 0.9,
         Item("medium_amethyst_bud"), 0.5)
    show(f"if score #bud_in {V} matches 1 if score #sp_taken {V} matches 0 ", 3, CHEST[0], CHEST[1], 1.0, CRYST[1], 0.6)
    show(f"if score #axe_got {V} matches 0 ", 4, TABLE[0], TABLE[1], 1.0, AXE, 0.6)
    show(f"if score #acorn_got {V} matches 0 ", 3, LEAVES[0], LEAVES[1], 0.6, ACORN, 0.4)
    dp.fn("r6/displays", disp)

    # réinitialisation complète de la vallée
    dp.fn("r6/reset_valley", [
        *[f"scoreboard players set {f} {V} 0" for f in FLAGS],
        "function solstice:r6/regen_tree", "function solstice:r6/regen_water", "function solstice:r6/regen_cave",
        "function solstice:r6/spawn_entities",
        "bossbar set solstice:r6hg visible false",
    ])
    dp.add("load", ["bossbar add solstice:r6hg \"Sablier du Solstice\"", "bossbar set solstice:r6hg color yellow",
                    "bossbar set solstice:r6hg max 600", "bossbar set solstice:r6hg visible false"])

    # --------------------------------------------------------------- entrée
    ax, ay, az = ARRIVAL
    dp.fn("r6/start", [
        "function solstice:r6/reset_valley",
        f"scoreboard players set #r6resets {V} 0",
        f"execute unless score #lantern {V} matches 1 run scoreboard players set #lantern {V} 1",
        "weather clear",
        "function solstice:r6/obj",
        orel("La Vallée des Saisons ! Enfin, les quatre vallées. Enfin, la même, quatre fois. Vous me suivez ?"),
        orel("Le Calendrier y cache ses quatre cristaux. Avec le Cadran, vous passez d’une saison à l’autre, au même endroit."),
        orel("Et souvenez-vous : ce qu’on fait au printemps, l’été s’en souvient. C’est comme mes genoux."),
    ])
    for s in S:
        x0, _, z0 = P(s, 0, 0, 0)
        dp.fn(f"r6/arrive{s}", [f"tp @s {x0 + ax} {Y + ay} {z0 + az} 180 0"])
    dp.fn("r6/cp", [
        f"execute unless score @s sol.sea matches 1..4 run scoreboard players set @s sol.sea 1",
        *[f"execute if score @s sol.sea matches {s} run function solstice:r6/arrive{s}" for s in S],
        f"spawnpoint @s {OX} {Y + 1} {24}",
    ])
    dp.fn("r6/enter", [
        "function solstice:r6/cp",
        "function solstice:r6/sync_items",
        *title("@s", "Les Quatre Saisons", "Cadran en main + accroupi : saison suivante", color="green"),
        narr("Tenez le Cadran des Saisons en main et accroupissez-vous : vous passez à la saison suivante, au même endroit.", "@s"),
    ])
    dp.fn("r6/respawn", ["function solstice:r6/cp", "function solstice:r6/sync_items"])
    # objets de groupe : chacun en reçoit une copie tant que l’objet est « au groupe »
    sync = [f"execute unless items entity @s container.* {CPRED} run give @s {CADRAN.give()}",
            f"execute if score #acorn_got {V} matches 1 if score #planted {V} matches 0 unless items entity @s container.* {APRED} run give @s {ACORN.give()}",
            f"execute if score #bud_got {V} matches 1 if score #bud_in {V} matches 0 unless items entity @s container.* {BPRED} run give @s {BUD_I.give()}",
            f"execute if score #axe_got {V} matches 1 if score #chopped {V} matches 0 unless items entity @s container.* {XPRED} run give @s {AXE.give()}"]
    for k, flag in ((1, "#sp_taken"), (2, "#su_taken"), (3, "#au_taken"), (4, "#wi_taken")):
        sync.append(f"execute if score {flag} {V} matches 1 if score #placed {V} matches ..{k - 1} unless items entity @s "
                    f"container.* {cpred(k)} unless items entity @s weapon.offhand {cpred(k)} run give @s {CRYST[k].give()}")
    dp.fn("r6/sync_items", sync)
    dp.fn("r6/sync_all", ["execute as @a[scores={sol.room=6}] run function solstice:r6/sync_items"])

    # --------------------------------------------------------------- tick joueur : saison, voyage, chutes
    pt = [
        "scoreboard players set @s sol.sea 0",
        *[f"execute if entity @s[x={OX - 100},y=0,z={Z(s) - 50},dx=200,dy=300,dz=100] run scoreboard players set @s sol.sea {s}" for s in S],
        f"execute if items entity @s weapon.mainhand {CPRED} if score @s sol.sneak matches 1.. run scoreboard players add @s sol.trv 1",
        f"execute unless score @s sol.sneak matches 1.. run scoreboard players set @s sol.trv 0",
        f"execute unless items entity @s weapon.mainhand {CPRED} run scoreboard players set @s sol.trv 0",
        "execute if score @s sol.trv matches 8.. unless score @s sol.cool matches 1.. run function solstice:r6/travel",
        "scoreboard players set @s sol.sneak 0",
        f"execute if score @s sol.y matches ..96 run function solstice:r6/fell",
        f"execute if score #m20 {V} matches 5 run function solstice:r6/season_bar",
        f"execute if score #m4 {V} matches 0 at @s run function solstice:r6/ambience",
        f"execute if score #ember {V} matches 1.. if items entity @s weapon.* {LPRED} at @s run particle minecraft:flame ~ ~1.2 ~ 0.15 0.2 0.15 0.01 2",
    ]
    dp.fn("r6/ptick", pt)
    dp.fn("r6/fell", ["function solstice:r6/cp", actionbar("@s", "Vous remontez au Cercle des Saisons.", "gray")])
    dp.fn("r6/season_bar", [
        *[f"execute if score @s sol.sea matches {s} run " + actionbar("@s", ["", T("Vous êtes : ", "gray"),
                                                                             T(S[s][0], S[s][1], bold=True),
                                                                             T("   (Cadran + accroupi → saison suivante)", "dark_gray")])
          for s in S],
    ])
    dp.fn("r6/ambience", [
        "execute if score @s sol.sea matches 1 run particle minecraft:cherry_leaves ~ ~6 ~ 6 1 6 0 3",
        "execute if score @s sol.sea matches 2 if score #m20 sol.var matches 0 run particle minecraft:wax_on ~ ~2 ~ 5 2 5 0 2",
        "execute if score @s sol.sea matches 3 run particle minecraft:falling_dust{block_state:\"minecraft:orange_terracotta\"} ~ ~6 ~ 6 1 6 0 2",
        "execute if score @s sol.sea matches 4 run particle minecraft:snowflake ~ ~5 ~ 6 1 6 0 6",
    ])
    # voyage : même position dans la saison suivante, atterrissage sûr (remontée jusqu’à 12 blocs)
    trav = ["scoreboard players set @s sol.trv 0", "scoreboard players set @s sol.cool 30",
            f"scoreboard players set #tpd {V} 0"]
    for s in S:
        nxt = s % 4 + 1
        dz = Z(nxt) - Z(s)
        lines = [f"execute if score #tpd {V} matches 0 positioned ~ ~{k} ~{dz} if block ~ ~ ~ #solstice:passable "
                 f"if block ~ ~1 ~ #solstice:passable run function solstice:r6/tp_here" for k in range(0, 13)]
        lines.append(f"execute if score #tpd {V} matches 0 run function solstice:r6/arrive{nxt}")
        lines += [*title("@s", S[nxt][0], "La saison change autour de vous…", color=S[nxt][1], times=(5, 30, 10)),
                  "playsound minecraft:block.amethyst_block.resonate master @s ~ ~ ~ 1 1.4",
                  "effect give @s blindness 1 0 true",
                  f"scoreboard players set @s sol.sea {nxt}"]
        dp.fn(f"r6/travel{s}", lines)
        trav.append(f"execute if score @s sol.sea matches {s} at @s run return run function solstice:r6/travel{s}")
    dp.fn("r6/travel", trav)
    dp.fn("r6/tp_here", ["tp @s ~ ~ ~", f"scoreboard players set #tpd {V} 1"])
    dp.json("data/solstice/tags/block/passable.json", {"values": [
        "minecraft:air", "minecraft:cave_air", "minecraft:void_air", "minecraft:snow", "minecraft:short_grass",
        "minecraft:tall_grass", "minecraft:fern", "minecraft:large_fern", "#minecraft:small_flowers",
        "minecraft:pink_petals", "minecraft:water", "minecraft:dead_bush", "#minecraft:saplings",
        "minecraft:brown_mushroom", "minecraft:red_mushroom", "minecraft:light"]})

    # --------------------------------------------------------------- clics
    kinds = ["altar", "bell", "hourglass", "sablier", "chest", "tree", "wheel", "flame", "bellows", "brazier",
             "leaves", "bud", "table", "pick_au", "pick_su", "pick_wi"]
    dp.fn("r6/clicked", [
        *[f"execute if entity @s[tag=sol.k_{k}] if data entity @s interaction on target run function solstice:r6/c/{k}"
          for k in kinds],
        *[f"execute if entity @s[tag=sol.k_{k}] if data entity @s attack on attacker run function solstice:r6/c/{k}"
          for k in kinds],
        "data remove entity @s interaction", "data remove entity @s attack",
    ])

    def per_season(name, bodies, default=None):
        """bodies : {saison: [commandes]} ; dispatch selon la saison du joueur."""
        lines = ["execute if score @s sol.cool matches 1.. run return 0", "scoreboard players set @s sol.cool 8"]
        for s, cmds in bodies.items():
            sub = dp.fn(f"r6/c/{name}_s{s}", cmds)
            lines.append(f"execute if score @s sol.sea matches {s} run return run function {sub}")
        if default:
            lines.append(default)
        dp.fn(f"r6/c/{name}", lines)

    def frozen(s):
        return (f"execute if score #lock{s} {V} matches 1 run return run " +
                actionbar("@s", f"{S[s][0]} est figé : son cristal a été rendu. Plus rien n’y change.", "gray"))

    # autels
    al = {}
    for s in S:
        al[s] = [
            f"execute if score #placed {V} matches {s}.. run return run " + actionbar("@s", f"Le cristal {DE[s]} brille déjà sur l’autel.", S[s][1]),
            f"execute unless items entity @s weapon.* {cpred(s)} run return run " +
            actionbar("@s", f"Cet autel attend le Cristal {DE[s]}.", S[s][1]),
            f"execute unless score #placed {V} matches {s - 1} run return run " +
            actionbar("@s", "Pas encore : les cristaux se rendent dans l’ordre — Printemps, Été, Automne, Hiver.", "red"),
            f"execute if score #conf {V} matches {s} if score #conf_t {V} matches 1.. run return run function solstice:r6/place{s}",
            f"scoreboard players set #conf {V} {s}", f"scoreboard players set #conf_t {V} 120",
            tellraw("@s", T("⚠ ", "gold"), T(f"Rendre ce cristal figera {LE[s]} pour toujours : plus aucune action n’y sera possible. ", "yellow"),
                    T("Tout est prêt ? Recliquez sur l’autel pour confirmer.", "white")),
            "playsound minecraft:block.note_block.bass master @s ~ ~ ~ 1 0.8",
        ]
        dp.fn(f"r6/place{s}", [
            f"scoreboard players set #placed {V} {s}", f"scoreboard players set #lock{s} {V} 1",
            f"scoreboard players set #conf {V} 0",
            f"clear @a {cpred(s)}",
            "function solstice:r6/displays",
            *title("@a", f"Le Cristal {DE[s]} est rendu", f"{S[s][0]} retrouve sa place… et se fige.", color=S[s][1]),
            sound("minecraft:block.beacon.power_select", "@a", 1, 1.2),
            sound("minecraft:block.bell.resonate", "@a", 0.7, 1.4),
            f"particle minecraft:end_rod {OX + ALTAR[0] + 0.5} {Y + 2.5} {Z(s) + ALTAR[1] + 0.5} 0.5 1 0.5 0.1 80 force",
            f"scoreboard players set #step {V} {s}", "function solstice:hints/reset", "function solstice:r6/obj",
            f"execute if score #placed {V} matches 4 run " + orel("Les quatre cristaux ! Maintenant les cloches : elles doivent sonner ENSEMBLE, dans les quatre saisons. "
                                                                  "Vous n’êtes que trois ? Le Sablier du Solstice sonnera la quatrième."),
        ])
    per_season("altar", al)

    # cloches, sablier du solstice
    per_season("bell", {s: [
        f"execute unless score #placed {V} matches 4 run return run " + actionbar("@s", "La cloche reste muette : les quatre cristaux ne sont pas rendus.", "gray"),
        f"function solstice:r6/ring{s}"] for s in S})
    for s in S:
        x0, _, z0 = P(s, 0, 0, 0)
        dp.fn(f"r6/ring{s}", [
            f"scoreboard players set #bell{s} {V} 1",
            f"execute if score #chord {V} matches 0 run scoreboard players operation #chord {V} = #win {V}",
            f"playsound minecraft:block.bell.use master @a {x0 + BELL[0]} 101 {z0 + BELL[1]} 3 {0.8 + 0.1 * s:.1f}",
            "execute as @a at @s run playsound minecraft:block.bell.resonate master @s ~ ~ ~ 0.4 " + f"{0.8 + 0.1 * s:.1f}",
            tellraw("@a", T("🔔 La cloche ", "gray"), T(DE[s], S[s][1], bold=True), T(" a sonné.", "gray")),
        ])
    per_season("hourglass", {s: [
        f"execute unless score #placed {V} matches 4 run return run " + actionbar("@s", "Le sablier attend que les quatre cristaux soient rendus.", "gray"),
        f"execute if score #hg {V} matches 1.. run return run " + actionbar("@s", "Le sablier s’écoule déjà.", "gold"),
        f"scoreboard players set #hg {V} 600", f"scoreboard players set #hgs {V} {s}",
        "bossbar set solstice:r6hg players @a", "bossbar set solstice:r6hg visible true",
        tellraw("@a", T("⏳ Le Sablier du Solstice est retourné ", "gold"), T(DE[s], S[s][1]),
                T(" : sa cloche sonnera dans 30 secondes.", "gold")),
        "playsound minecraft:block.sand.place master @a ~ ~ ~ 1 0.6"] for s in S})

    # sablier de remontée (reset complet)
    per_season("sablier", {s: [
        f"execute if score #rconf {V} matches 1.. run return run function solstice:r6/rewind",
        f"scoreboard players set #rconf {V} 120",
        tellraw("@s", T("⏳ ", "gold"), T("Remonter le temps ramène TOUTE la vallée à son début (objets, arbres, eau, cristaux). "
                                          "Cela coûte 30 secondes. Recliquez pour confirmer.", "yellow")),
        "playsound minecraft:block.note_block.bass master @s ~ ~ ~ 1 0.6"] for s in S})
    dp.fn("r6/rewind", [
        f"scoreboard players add #r6resets {V} 1",
        "function solstice:r6/reset_valley",
        f"scoreboard players set #step {V} 0", "function solstice:hints/reset", "function solstice:r6/obj",
        "execute as @a[scores={sol.room=6}] run function solstice:r6/rewind_player",
        *title("@a", "Le temps remonte…", "La vallée revient à son premier matin.", color="gold", times=(10, 80, 20)),
        orel("Hop, on rembobine ! Ça grince un peu. Trente secondes et c’est reparti."),
    ])
    dp.fn("r6/rewind_player", [
        f"clear @s {APRED}", f"clear @s {BPRED}", f"clear @s {XPRED}", *[f"clear @s {cpred(k)}" for k in S],
        "scoreboard players set @s sol.sea 1", "function solstice:r6/arrive1",
        "effect give @s slowness 30 255 true", "effect give @s blindness 3 0 true", "effect give @s jump_boost 30 250 true",
        "function solstice:r6/sync_items",
    ])

    # coffre du temps
    per_season("chest", {
        1: [frozen(1),
            f"execute if score #bud_in {V} matches 0 if items entity @s weapon.* {BPRED} run return run function solstice:r6/bud_deposit",
            f"execute if score #bud_in {V} matches 1 if score #sp_taken {V} matches 0 run return run function solstice:r6/bud_withdraw",
            actionbar("@s", "Un vieux coffre à la serrure en forme de sablier. Ce qu’on y laisse… attend.", "gray")],
        2: [f"execute if score #bud_in {V} matches 1 if score #sp_taken {V} matches 0 run return run "
            + actionbar("@s", "Dans le coffre, le bourgeon a grossi. Il n’est pas encore mûr.", "light_purple"),
            actionbar("@s", "Le coffre est vide.", "gray")],
        3: [f"execute if score #bud_in {V} matches 1 if score #sp_taken {V} matches 0 run return run function solstice:r6/take_spring",
            actionbar("@s", "Le coffre est vide… Rien n’y a été laissé au printemps.", "gray")],
        4: [actionbar("@s", "Le coffre est vide. Le bois craque de froid.", "gray")]})
    dp.fn("r6/bud_deposit", [
        f"scoreboard players set #bud_in {V} 1", f"clear @a {BPRED}", "function solstice:r6/displays",
        narr("Vous déposez le Bourgeon de cristal dans le Coffre du Temps. Le couvercle se referme avec un tic-tac.", "@a"),
        "playsound minecraft:block.chest.close master @a ~ ~ ~ 1 0.8"])
    dp.fn("r6/bud_withdraw", [
        f"scoreboard players set #bud_in {V} 0", "function solstice:r6/displays", "function solstice:r6/sync_all",
        actionbar("@s", "Vous reprenez le bourgeon.", "gray")])
    dp.fn("r6/take_spring", [
        f"scoreboard players set #sp_taken {V} 1", "function solstice:r6/displays", "function solstice:r6/sync_all",
        tellraw("@a", T("✦ Le bourgeon a mûri à travers le temps : ", "light_purple"), T("Cristal du Printemps", "light_purple", bold=True),
                T(" obtenu !", "light_purple")),
        "playsound minecraft:block.amethyst_block.resonate master @a ~ ~ ~ 1 1"])

    # arbre : planter (printemps), abattre (automne)
    per_season("tree", {
        1: [frozen(1),
            f"execute if score #planted {V} matches 1 run return run " + actionbar("@s", "Le jeune chêne est planté. Laissez-lui le temps.", "green"),
            f"execute if items entity @s weapon.* {APRED} run return run function solstice:r6/plant",
            actionbar("@s", "Une terre fertile, au bord du ravin. Il faudrait y planter quelque chose.", "green")],
        2: [f"execute if score #planted {V} matches 1 run return run " + actionbar("@s", "Le chêne planté au printemps est devenu immense.", "green"),
            actionbar("@s", "Rien ne pousse ici : rien n’a été planté au printemps.", "gray")],
        3: [frozen(3),
            f"execute if score #chopped {V} matches 1 run return run " + actionbar("@s", "Le vieux chêne est couché en travers du ravin.", "gold"),
            f"execute if score #planted {V} matches 0 run return run " + actionbar("@s", "Une terre nue. Aucun arbre n’y a jamais poussé.", "gray"),
            f"execute unless items entity @s weapon.mainhand {XPRED} run return run " + actionbar("@s", "Un vieux chêne penché vers le ravin. Il faudrait une hache.", "gold"),
            "function solstice:r6/chop"],
        4: [f"execute if score #chopped {V} matches 1 run return run " + actionbar("@s", "Le tronc enneigé fait un pont solide.", "aqua"),
            actionbar("@s", "Le bois gelé est dur comme la pierre.", "aqua")]})
    dp.fn("r6/plant", [
        f"scoreboard players set #planted {V} 1", f"clear @a {APRED}", "function solstice:r6/regen_tree",
        "kill @e[type=!player,tag=sol.r6spot]",
        narr("Vous plantez le Gland d’horloge. La terre fait tic… tac.", "@a"),
        "playsound minecraft:item.bone_meal.use master @a ~ ~ ~ 1 1",
        "particle minecraft:happy_villager ~ ~1 ~ 0.5 0.5 0.5 0 20"])
    dp.fn("r6/chop", [
        f"scoreboard players add #chop {V} 1",
        "playsound minecraft:item.axe.strip master @a ~ ~ ~ 1 0.8",
        "particle minecraft:block{block_state:\"minecraft:oak_log\"} ~ ~1 ~ 0.3 0.5 0.3 0 20",
        f"execute if score #chop {V} matches ..2 run " + actionbar("@s", "Le vieux tronc craque…", "gold"),
        f"execute if score #chop {V} matches 3.. run function solstice:r6/fall"])
    dp.fn("r6/fall", [
        f"scoreboard players set #chopped {V} 1", f"clear @a {XPRED}", "function solstice:r6/regen_tree",
        *title("@a[scores={sol.sea=3}]", "TIMBEEER !", "Le vieux chêne tombe en travers du ravin.", color="gold", times=(5, 40, 10)),
        tellraw("@a", T("🌳 Le vieux chêne est tombé en travers du ravin : un pont (en automne… et en hiver).", "gold")),
        "playsound minecraft:entity.generic.explode master @a ~ ~ ~ 0.6 0.5"])

    # vanne (été)
    per_season("wheel", {
        2: [frozen(2),
            f"execute if score #sluice {V} matches 4.. run return run " + actionbar("@s", "La vanne est grande ouverte. L’eau file vers le bassin.", "aqua"),
            f"scoreboard players add #sluice {V} 1", "playsound minecraft:block.chain.place master @a ~ ~ ~ 1 0.6",
            f"execute if score #sluice {V} matches ..3 run " + actionbar("@s", ["", T("La roue tourne… ", "aqua"), SC("#sluice"), T(" / 4", "gray")]),
            f"execute if score #sluice {V} matches 4 run function solstice:r6/sluice_open"],
        1: [actionbar("@s", "Une vanne neuve, bien fermée. Elle ne tournera qu’en été : la rivière y est la plus basse.", "gray")],
        3: [actionbar("@s", "La roue de la vanne est rouillée, elle ne tourne plus.", "gray")],
        4: [actionbar("@s", "La vanne est prise dans la glace.", "aqua")]})
    dp.fn("r6/sluice_open", [
        "function solstice:r6/regen_water",
        tellraw("@a", T("🌊 La vanne s’ouvre : la rivière se détourne vers le bassin.", "aqua")),
        "playsound minecraft:block.water.ambient master @a ~ ~ ~ 1 1", "playsound minecraft:block.piston.extend master @a ~ ~ ~ 1 0.6"])

    # flamme éternelle, soufflet (été), brasero (hiver)
    per_season("flame", {
        2: [frozen(2),
            f"execute unless items entity @s weapon.* {LPRED} run return run " + actionbar("@s", "La Flamme éternelle. Il faudrait de quoi emporter une braise…", "gold"),
            f"scoreboard players set #ember {V} 1200",
            tellraw("@a", T("🔥 La Lanterne capture une braise de la Flamme éternelle. Elle tiendra une minute.", "gold")),
            "playsound minecraft:item.firecharge.use master @a ~ ~ ~ 1 1"]},
        default=actionbar("@s", "Un foyer éteint depuis longtemps.", "gray"))
    per_season("bellows", {
        2: [frozen(2), f"scoreboard players set #pump {V} 30",
            "playsound minecraft:entity.breeze.wind_burst master @a ~ ~ ~ 0.4 1.6",
            "particle minecraft:cloud ~ ~0.8 ~ 0.2 0.2 0.2 0.05 6",
            actionbar("@s", "Pfff… Le soufflet souffle. (Les foyers de la vallée sont reliés à travers le temps.)", "gold")]},
        default=actionbar("@s", "Un vieux soufflet de forge.", "gray"))
    x4, _, z4 = P(4, 0, 0, 0)
    per_season("brazier", {
        4: [frozen(4),
            f"execute if score #melted {V} matches 1 run return run " + actionbar("@s", "La glace a fondu : la grotte est ouverte.", "aqua"),
            f"execute if score #burn {V} matches 1.. run return run " + actionbar("@s", "Le brasero brûle ! Il faut souffler dessus… d’une manière ou d’une autre.", "gold"),
            f"execute if score #ember {V} matches 1.. if items entity @s weapon.* {LPRED} run return run function solstice:r6/brazier_lit",
            actionbar("@s", "Un brasero glacé devant la grotte. Il lui faudrait une braise qui ne s’éteint jamais.", "aqua")]},
        default=actionbar("@s", "Un brasero vide.", "gray"))
    dp.fn("r6/brazier_lit", [
        f"scoreboard players set #ember {V} 0", f"scoreboard players set #burn {V} 400", f"scoreboard players set #melt {V} 0",
        f"setblock {x4 + BRAZIER[0]} 101 {z4 + BRAZIER[1]} campfire[lit=true]",
        tellraw("@a", T("🔥 Le brasero de l’hiver s’embrase… mais il faiblit déjà. La glace ne fondra pas sans qu’on souffle dessus.", "gold")),
        "playsound minecraft:item.flintandsteel.use master @a ~ ~ ~ 1 1"])
    dp.fn("r6/melt_tick", [
        f"scoreboard players remove #burn {V} 1",
        f"execute if score #pump {V} matches 1.. run scoreboard players add #melt {V} 1",
        f"execute if score #need {V} matches 1 run scoreboard players add #melt {V} 1",
        f"execute if score #m20 {V} matches 0 run particle minecraft:flame {x4 + BRAZIER[0] + 0.5} 101.6 {z4 + BRAZIER[1] + 0.5} 0.2 0.3 0.2 0.02 12",
        f"execute if score #m20 {V} matches 0 as @a[scores={{sol.sea=4}}] run " + actionbar("@s", ["", T("La glace fond… ", "aqua"), SC("#melt"), T(" / 200", "gray"),
                                                                                                   T("  (le soufflet d’été doit souffler)", "dark_gray")]),
        f"execute if score #melt {V} matches 200.. run function solstice:r6/melted",
        f"execute if score #burn {V} matches 0 if score #melted {V} matches 0 run function solstice:r6/brazier_out",
    ])
    dp.fn("r6/melted", [
        f"scoreboard players set #melted {V} 1", f"scoreboard players set #burn {V} 0", "function solstice:r6/regen_cave",
        "function solstice:r6/displays",
        tellraw("@a", T("❄ La glace de la grotte a fondu ! Quelque chose brille à l’intérieur.", "aqua")),
        "playsound minecraft:block.glass.break master @a ~ ~ ~ 1 0.6"])
    dp.fn("r6/brazier_out", [
        f"scoreboard players set #melt {V} 0", "function solstice:r6/regen_cave",
        tellraw("@a", T("Le brasero s’est éteint avant que la glace ne fonde. Il faudra une nouvelle braise.", "gray"))])

    # objets à trouver
    per_season("leaves", {
        3: [f"execute if score #acorn_got {V} matches 1 run return run " + actionbar("@s", "Il n’y a plus que des feuilles mortes.", "gold"),
            f"scoreboard players set #acorn_got {V} 1", "function solstice:r6/displays", "function solstice:r6/sync_all",
            tellraw("@a", T("Sous les feuilles mortes, un ", "gold"), T("Gland d’horloge", "gold", bold=True), T(" fait tic-tac.", "gold")),
            "playsound minecraft:block.azalea_leaves.break master @a ~ ~ ~ 1 1"]},
        default=actionbar("@s", "Rien d’intéressant sous ce vieux chêne… en cette saison.", "gray"))
    per_season("bud", {
        1: [frozen(1),
            f"execute if score #bud_got {V} matches 1 run return run " + actionbar("@s", "La branche est nue.", "gray"),
            f"scoreboard players set #bud_got {V} 1", "function solstice:r6/displays", "function solstice:r6/sync_all",
            tellraw("@a", T("Sur le cerisier, un ", "light_purple"), T("Bourgeon de cristal", "light_purple", bold=True),
                    T(". Il n’est pas mûr.", "light_purple")),
            "playsound minecraft:block.amethyst_cluster.break master @a ~ ~ ~ 1 1.2"]},
        default=actionbar("@s", "Un arbre du verger.", "gray"))
    per_season("table", {
        2: ["function solstice:story/found_lettre",
            narr("Sur le lutrin de Lise, une lettre jamais envoyée…", "@s")],
        4: [f"execute if score #axe_got {V} matches 1 run return run " + actionbar("@s", "L’établi de Lise, couvert de givre.", "aqua"),
            f"scoreboard players set #axe_got {V} 1", "function solstice:r6/displays", "function solstice:r6/sync_all",
            tellraw("@a", T("Vous trouvez la ", "dark_green"), T("Hache de Lise", "dark_green", bold=True),
                    T(" : « pour le vieux bois seulement ».", "dark_green")),
            "playsound minecraft:item.armor.equip_iron master @a ~ ~ ~ 1 1"]},
        default=actionbar("@s", "L’atelier de Lise, la jardinière de la vallée.", "gray"))
    for key, s, flag, k, needs in (("pick_au", 3, "#au_taken", 3, None), ("pick_su", 4, "#su_taken", 2, "#melted"),
                                   ("pick_wi", 4, "#wi_taken", 4, None)):
        body = [f"execute if score {flag} {V} matches 1 run return run " + actionbar("@s", "Le piédestal est vide.", "gray")]
        if needs:
            body.append(f"execute unless score {needs} {V} matches 1 run return 0")
        body += [f"scoreboard players set {flag} {V} 1", "function solstice:r6/displays", "function solstice:r6/sync_all",
                 tellraw("@a", T("✦ ", S[k][1]), T(f"Cristal {DE[k]}", S[k][1], bold=True), T(" obtenu !", S[k][1])),
                 "playsound minecraft:block.amethyst_block.resonate master @a ~ ~ ~ 1 1.2"]
        per_season(key, {s: body}, default=actionbar("@s", "Un piédestal vide.", "gray"))

    # --------------------------------------------------------------- tick global
    dp.fn("r6/tick", [
        "execute as @e[type=interaction,tag=sol.r6i] at @s if data entity @s interaction run function solstice:r6/clicked",
        "execute as @e[type=interaction,tag=sol.r6i] at @s if data entity @s attack run function solstice:r6/clicked",
        f"execute if score #ember {V} matches 1.. run scoreboard players remove #ember {V} 1",
        f"execute if score #ember {V} matches 1 run " + tellraw("@a", T("La braise de la Lanterne s’est éteinte.", "gray")),
        f"execute if score #pump {V} matches 1.. run scoreboard players remove #pump {V} 1",
        f"execute if score #burn {V} matches 1.. run function solstice:r6/melt_tick",
        f"execute if score #conf_t {V} matches 1.. run scoreboard players remove #conf_t {V} 1",
        f"execute if score #rconf {V} matches 1.. run scoreboard players remove #rconf {V} 1",
        f"execute if score #hg {V} matches 1.. run function solstice:r6/hg_tick",
        f"execute if score #chord {V} matches 1.. run function solstice:r6/chord_tick",
        f"execute if score #m20 {V} matches 0 if score #m60 {V} matches 0 run function solstice:r6/deadlock",
        f"scoreboard players operation #m60 {V} = #rt {V}",
        f"scoreboard players operation #m60 {V} %= #c1200 {V}",
    ])
    dp.fn("r6/hg_tick", [
        f"scoreboard players remove #hg {V} 1",
        f"execute store result bossbar solstice:r6hg value run scoreboard players get #hg {V}",
        *[f"execute if score #hg {V} matches 0 if score #hgs {V} matches {s} run function solstice:r6/ring{s}" for s in S],
        f"execute if score #hg {V} matches 0 run bossbar set solstice:r6hg visible false",
    ])
    dp.fn("r6/chord_tick", [
        f"scoreboard players remove #chord {V} 1",
        f"execute if score #bell1 {V} matches 1 if score #bell2 {V} matches 1 if score #bell3 {V} matches 1 if score #bell4 {V} matches 1 run return run function solstice:r6/win",
        f"execute if score #chord {V} matches 0 run function solstice:r6/chord_fail",
    ])
    dp.fn("r6/chord_fail", [
        *[f"scoreboard players set #bell{s} {V} 0" for s in S],
        tellraw("@a", T("Les cloches se sont tues, chacune de son côté. Elles doivent sonner ensemble !", "gray")),
    ])
    dp.fn("r6/win", [
        f"scoreboard players set #chord {V} 0",
        f"execute if score #r6done {V} matches 1 run return 0",
        f"scoreboard players set #r6done {V} 1",
        "bossbar set solstice:r6hg visible false",
        f"execute if score #r6resets {V} matches 0 run function solstice:challenge/grant_premier_sablier",
        *title("@a", "Les quatre saisons chantent", "Le Calendrier retrouve son rythme.", color="green", times=(10, 80, 20)),
        sound("minecraft:ui.toast.challenge_complete", "@a", 1, 1),
        "function solstice:flow/complete",
    ])
    # impasses détectées : on le dit clairement, avec la sortie (Sablier de Remontée)
    dp.fn("r6/deadlock", [
        f"execute if score #lock1 {V} matches 1 if score #planted {V} matches 0 if score #au_taken {V} matches 0 run " +
        orel("Hmm… Le Printemps est figé, et rien n’y a été planté. Sans arbre, pas de pont en automne. Le Sablier de Remontée, au Cercle, peut tout rembobiner."),
        f"execute if score #lock2 {V} matches 1 if score #sluice {V} matches ..3 if score #wi_taken {V} matches 0 run " +
        orel("Aïe. L’Été est figé et la vanne n’a jamais été ouverte : l’hiver n’aura pas de lac gelé. Le Sablier de Remontée est votre ami."),
    ])
    dp.fn("r6/obj", [
        f"execute if score #placed {V} matches 0..3 run " + "bossbar set solstice:obj name " +
        jdump(["", T("◆ ", "gold"), T("Rendez les cristaux à leurs autels, dans l’ordre des saisons  ", "white"), SC("#placed", color="green"),
               T(" / 4", "gray")]),
        f"execute if score #placed {V} matches 4 run " + "bossbar set solstice:obj name " +
        jdump(["", T("◆ ", "gold"), T("Faites sonner les quatre cloches ensemble", "white")]),
    ])
    dp.fn("r6/wipe", [])
    dp.fn("r6/on_complete", ["bossbar set solstice:r6hg visible false"])
    hint_fn(dp, 6, {
        0: ("Le bourgeon du verger n’est pas mûr. Le Coffre du Temps, dans la chapelle, garde les choses… longtemps.",
            "Déposez le Bourgeon dans le coffre au Printemps, reprenez-le mûr en Automne. Et avant de rendre ce cristal, "
            "plantez le Gland d’automne dans la terre fertile, au bord du ravin, au Printemps."),
        1: ("Le cristal de l’Été dort là où il fait le plus froid. Et l’Été a peut-être encore une chose à faire…",
            "Avant de rendre le cristal de l’Été, tournez la vanne du canal (en été). Braise d’été dans la Lanterne → brasero "
            "de la grotte gelée en hiver, pendant qu’un coéquipier actionne le soufflet de la forge d’été."),
        2: ("Un pont peut naître d’un arbre.",
            "L’arbre planté au Printemps a vieilli : abattez-le en Automne avec la hache de l’atelier de Lise (trouvée en Hiver)."),
        3: ("L’eau détournée en Été gèle en Hiver.", "En Hiver, marchez sur le lac gelé jusqu’à l’îlot du bassin."),
        4: ("Les quatre cloches doivent sonner ensemble. Vous n’êtes que trois.",
            "Retournez le Sablier du Solstice à côté d’un autel : sa cloche sonnera dans 30 s. Allez chacun dans une autre saison et sonnez au même moment."),
    })

    # --------------------------------------------------------------- tests structurels, registre, méta
    for s in S:
        x0, _, z0 = P(s, 0, 0, 0)
        dp.test(f"saisons : autel {S[s][0]}", f"block {x0 + ALTAR[0]} 101 {z0 + ALTAR[1]} chiseled_stone_bricks")
        dp.test(f"saisons : biome {S[s][3]} ({S[s][0]})", f"biome {x0} 101 {z0} {S[s][3]}")
        dp.test(f"saisons : biome {S[s][3]} au bord ({S[s][0]})", f"biome {x0 - 30} 115 {z0 + 30} {S[s][3]}")
        dp.test(f"saisons : cloche {S[s][0]}", f"block {x0 + BELL[0]} 101 {z0 + BELL[1]} bell")
        dp.test(f"saisons : 16 entités cliquables {S[s][0]}", f"entity @e[type=interaction,tag=sol.r6s{s},tag=sol.k_altar]")
    dp.test("saisons : grotte gelée en hiver", f"block {x4 + CAVE[0]} 102 {z4 + CAVE[1]} packed_ice")
    dp.test("saisons : bassin vide au départ (été)", f"block {P(2, 14, 0, -6)[0]} 97 {P(2, 14, 0, -6)[2]} air")
    dp.test("saisons : vanne fermée (été)", f"block {P(2, GATE_X, 0, 0)[0]} 99 {Z(2) + CHANNEL[1]} spruce_planks")
    for key, pz in (("season-plant-propagation", "Planter au printemps, abattre en automne pour faire un pont."),
                    ("season-aging-chest", "Coffre du Temps : un objet laissé dans le passé est récupéré vieilli."),
                    ("season-water-freeze", "Détourner l’eau en été pour marcher sur un lac gelé en hiver."),
                    ("season-heat-bellows", "Braise portée d’une saison à l’autre + soufflet simultané dans une autre saison."),
                    ("season-order-lock", "Ordre de restitution qui fige les saisons : anticiper avant de rendre un cristal."),
                    ("season-chord-hourglass", "Quatre cloches ensemble dans quatre saisons, à trois joueurs + un sablier.")):
        dp.puzzle(6, key, key, pz)
    meta = {"cp": (OX + ARRIVAL[0], Y + ARRIVAL[1], ARRIVAL[2]), "z": {s: Z(s) for s in S}, "ox": OX,
            "k": {"altar": ALTAR, "bell": BELL, "hourglass": HOURGLASS, "sablier": SABLIER, "chest": CHEST, "tree": SPOT,
                  "wheel": WHEEL, "flame": FLAME, "bellows": BELLOWS, "brazier": BRAZIER, "leaves": LEAVES, "bud": BUD,
                  "table": TABLE, "pick_au": PLATEAU_PED, "pick_su": CAVE_PED, "pick_wi": (14, -11)},
            "channel": CHANNEL, "basin": BASIN, "bridge": BRIDGE, "ravine": RAVINE_Z, "cave": CAVE, "gate_x": GATE_X,
            "spot": SPOT, "arrival": ARRIVAL}
    dp.meta.setdefault("rooms", {})["6"] = meta
    rp.register("amethyst_shard", {"parent": "minecraft:item/generated", "textures": {"layer0": "minecraft:item/amethyst_shard"}},
                6011, "cristal_printemps", lambda: _crystal_tex((255, 150, 210, 255)))
    for k, col in ((2, (255, 215, 60, 255)), (3, (235, 120, 40, 255)), (4, (150, 215, 255, 255))):
        rp.register("amethyst_shard", None, 6010 + k, f"cristal_{['', 'printemps', 'ete', 'automne', 'hiver'][k]}",
                    (lambda c: (lambda: _crystal_tex(c)))(col))


def _crystal_tex(col):
    from .png import Canvas, shade
    c = Canvas(16, 16)
    c.polygon([(8, 0.5), (12.5, 5), (10.5, 15), (5.5, 15), (3.5, 5)], col)
    for y in range(16):
        for x in range(16):
            if c.get(x, y)[3]:
                c.set(x, y, shade(col, 1.25 - x / 16 * 0.55))
    c.outline(shade(col, 0.45))
    c.set(6, 4, (255, 255, 255, 255)); c.set(7, 3, (255, 255, 255, 255))
    return c
