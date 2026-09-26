"""Brumeval : le village du prologue (et de l’épilogue). Place, horloge, bibliothèque, forge, serre, horlogerie, gare.
PNJ cliquables (entités interaction), traînée d’encre bleue (indice « encre »), horloge arrêtée (indice « minuit »)."""
from .core import (V, T, jdump, tellraw, fill, setblock, text_display, interaction, villager, skinned_npc, item_display,
                   say, narr, actionbar, Item)
from .build import house, tree, lamp_post, disc, ring, box, gable_roof

Y = 100
PLATFORM = (-10, 101, -36, 10, 104, -30)
NPCS = {
    "orel": ("Maître Orel", "gold", (2.5, 101, 4.5), 150, "cartographer"),
    "ysolde": ("Madame Ysolde", "dark_purple", (-11.5, 101, -2.5), 90, "librarian"),
    "bram": ("Bram", "dark_red", (12.5, 101, -3.5), -90, "armorer"),
    "lise": ("Lise", "dark_green", (15.5, 101, 8.5), 180, "farmer"),
}
SKIN_NPC = "orel"   # porte le skin joueur (noyé retexturé, voir skin.py) ; les autres PNJ sont des villageois
# auvent de l’horloger au-dessus de lui : un noyé brûle au soleil (épilogue en plein jour) ; un bloc plein qui coupe
# le ciel l’en empêche (vérifié sur serveur vanilla ; une barrière ou une dalle laissent passer le ciel)
ROOF_Y, ROOF = Y + 4, "spruce_planks"
LINES = {
    "orel": ["Le quai est au nord. L’Express ne s’arrête plus : montez tous en même temps !",
             "Mon Calendrier a mille ans cette année. Mille ! Et pas une ride. Enfin, jusqu’à cette nuit.",
             "Vos indices, gardez-les pour vous. Je veux dire : pour vous trois.",
             "Le temps, c’est comme une montre : on ne s’en soucie que le jour où il s’arrête. Ou qu’on voudrait qu’il s’arrête."],
    "ysolde": ["Des voyageurs ! Soyez prudents là-haut : le Calendrier n’aime pas les curieux.",
               "Je n’ai pas fermé l’œil de la nuit. Je classais de vieux plans… des histoires de gardiens.",
               "Orel est un homme merveilleux. Têtu comme une horloge arrêtée, mais merveilleux."],
    "bram": ["Hmpf. Des étrangers pour réparer MA mécanique ? J’ai forgé la moitié de ses engrenages.",
             "Quelqu’un m’a chipé ma lime la semaine dernière. Si je le trouve…",
             "La nuit du sabotage ? Je n’étais pas chez moi. C’est tout ce que vous saurez."],
    "lise": ["Regardez mes pauvres fleurs : de la neige sur les tulipes ! Qui a pu faire une chose pareille ?",
             "Mes tournesols géants ? Tout Brumeval en a eu des graines. J’en ai même donné à l’herbier de la bibliothèque.",
             "Cette nuit-là, je veillais ma serre. Je n’étais pas… toute seule. Mais ça ne vous regarde pas !"],
}


def npc_type(key):
    return "drowned" if key == SKIN_NPC else "villager"


def npc_summon(key):
    name, color, (x, y, z), yaw, prof = NPCS[key]
    tl = ["sol.r0", f"sol.npc0_{key}"]
    if key == SKIN_NPC:
        return skinned_npc(x, y, z, name, color, tl, yaw=yaw)
    return villager(x, y, z, name, color, tl, profession=prof, yaw=yaw)


INK = [(-12.6, 0.4), (-11.2, -0.3), (-9.8, 0.5), (-8.1, -0.2), (-6.4, 0.3), (-4.7, -0.9), (-3.0, -2.6),
       (-1.4, -4.3), (-0.6, -6.5), (0.3, -8.8), (-0.4, -11.2), (0.6, -13.9), (-0.2, -16.8), (0.5, -19.7),
       (-0.3, -22.6), (0.4, -25.5), (-0.1, -28.4)]
PUDDLE = (-13.5, 101, 3.5)
CLOCK = (-3.5, 101, -6.5)


def build(dp):
    b = ["kill @e[type=!player,tag=sol.r0]"]
    b += fill(-60, 60, -60, 60, 140, 60, "air")
    # île flottante
    b += disc(0, Y - 3, 0, 40, "stone")
    b += disc(0, Y - 2, 0, 42, "dirt")
    b += disc(0, Y - 1, 0, 44, "dirt")
    b += disc(0, Y, 0, 44, "grass_block")
    for r, dy in ((34, -4), (26, -6), (18, -9), (10, -13)):
        b += disc(0, Y + dy, 0, r, "stone")
    # place
    b += disc(0, Y, 0, 9, "stone_bricks")
    b += disc(0, Y, 0, 6, "polished_andesite")
    b += ring(0, Y, 0, 9, "mossy_stone_bricks")
    b += disc(0, Y + 1, 0, 2, "stone_brick_wall")
    b += disc(0, Y + 1, 0, 1, "water")
    b += [setblock(0, Y + 1, 0, "stone_bricks"), setblock(0, Y + 2, 0, "stone_brick_wall"),
          setblock(0, Y + 3, 0, "lantern")]
    # rues
    b += fill(-2, Y, -30, 2, Y, -9, "cobblestone")
    b += fill(-1, Y, -30, 1, Y, -9, "stone_bricks")
    b += fill(-14, Y, -1, -9, Y, 1, "cobblestone")
    b += fill(9, Y, -2, 14, Y, 0, "cobblestone")
    b += fill(-1, Y, 9, 1, Y, 24, "cobblestone")
    b += fill(-17, Y, 8, 17, Y, 9, "cobblestone")
    for (x, z) in [(-4, -12), (4, -12), (-4, -22), (4, -22), (-10, 4), (10, 4), (-6, 12), (6, 12), (4, 20), (-4, 20)]:
        b += lamp_post(x, Y + 1, z)
    # --------------------------------------------------------------- bibliothèque (Ysolde) — ouest
    b += house(-27, -7, -15, 6, Y, 6, wall="stripped_birch_log[axis=y]", frame="dark_oak_log", floor="dark_oak_planks",
               roof="deepslate_tile", axis="z", door=(-15, 0, "east"))
    b += fill(-26, Y + 1, -6, -26, Y + 4, 5, "bookshelf")
    b += fill(-26, Y + 1, -6, -16, Y + 4, -6, "bookshelf")
    b += fill(-24, Y + 1, 5, -17, Y + 3, 5, "bookshelf")
    b += fill(-26, Y + 1, -2, -26, Y + 3, 1, "air")
    b += [setblock(-22, Y + 1, -1, "lectern[facing=east]"), setblock(-22, Y + 1, 2, "dark_oak_slab[type=top]"),
          setblock(-22, Y + 2, 2, "candle[candles=3,lit=true]"), setblock(-20, Y + 1, -3, "dark_oak_stairs[facing=west]")]
    b.append(text_display(-14.4, Y + 4.3, 0.5, ["", T("Bibliothèque", "dark_purple", bold=True), T("\nde Brumeval", "gray")],
                          ["sol.r0"], billboard="fixed", yaw=-90))
    # --------------------------------------------------------------- forge (Bram) — est
    b += house(15, -8, 25, 4, Y, 5, wall="cobblestone", frame="stone_bricks", floor="stone_bricks", roof="dark_oak",
               axis="x", door=(15, -1, "west"))
    b += [setblock(22, Y + 1, -5, "anvil"), setblock(23, Y + 1, 1, "blast_furnace[facing=west,lit=true]"),
          setblock(23, Y + 1, -1, "smithing_table"), setblock(19, Y + 1, 2, "grindstone[face=floor,facing=north]")]
    b += fill(24, Y + 1, -7, 24, Y + 12, -6, "bricks")
    b += fill(24, Y + 1, -7, 24, Y + 1, -6, "campfire[lit=true]")
    b += [setblock(13, Y + 1, -6, "anvil[facing=north]"), setblock(13, Y + 1, 2, "barrel[facing=up]")]
    b.append(text_display(14.4, Y + 4.3, -0.5, ["", T("Forge", "dark_red", bold=True), T("\nde Bram", "gray")],
                          ["sol.r0"], billboard="fixed", yaw=90))
    # --------------------------------------------------------------- serre (Lise) — sud-est
    b += box(12, Y, 11, 24, Y + 5, 21, "glass", floor="farmland[moisture=7]")
    b += fill(12, Y, 11, 24, Y, 21, "mud_bricks")
    b += fill(13, Y, 12, 23, Y, 20, "moss_block")
    for (x, z, f) in [(14, 13, "sunflower"), (16, 13, "peony"), (18, 13, "rose_bush"), (20, 13, "lilac"),
                      (22, 15, "sunflower"), (14, 17, "sunflower"), (20, 18, "peony")]:
        b += [setblock(x, Y + 1, z, f"{f}[half=lower]"), setblock(x, Y + 2, z, f"{f}[half=upper]")]
    for (x, z, f) in [(15, 15, "red_tulip"), (17, 16, "white_tulip"), (19, 15, "orange_tulip"), (21, 17, "pink_tulip"),
                      (16, 19, "cornflower"), (18, 19, "azure_bluet"), (22, 19, "oxeye_daisy")]:
        b.append(setblock(x, Y + 1, z, f))
    b += [setblock(17, Y + 1, 16, "snow"), setblock(19, Y + 1, 17, "snow"), setblock(21, Y + 1, 14, "snow")]
    b += [setblock(18, Y + 1, 11, "air"), setblock(18, Y + 2, 11, "air")]
    b += gable_roof(12, 11, 24, 21, Y + 6, "prismarine", axis="x", overhang=0, cap="glass")
    b.append(text_display(18.5, Y + 4, 10.4, ["", T("Serre", "dark_green", bold=True), T("\nde Lise", "gray")],
                          ["sol.r0"], billboard="fixed", yaw=180))
    # --------------------------------------------------------------- horlogerie (Orel) — sud-ouest
    b += house(-24, 11, -12, 21, Y, 6, wall="spruce_planks", frame="stripped_spruce_log[axis=y]", floor="spruce_planks",
               roof="spruce", axis="x", door=(-18, 11, "north"))
    for (x, z) in [(-22, 13), (-20, 13), (-14, 13), (-22, 19)]:
        b += [setblock(x, Y + 1, z, "spruce_fence"), setblock(x, Y + 2, z, "spruce_trapdoor[half=bottom,open=false]")]
    b += [setblock(-15, Y + 1, 19, "crafting_table"), setblock(-16, Y + 1, 19, "loom"),
          setblock(-13, Y + 3, 15, "bell[attachment=single_wall,facing=east]")]
    b.append(text_display(-17.5, Y + 4.3, 10.4, ["", T("Horlogerie", "gold", bold=True), T("\nMaître Orel", "gray")],
                          ["sol.r0"], billboard="fixed", yaw=180))
    # --------------------------------------------------------------- tour de l’horloge (décor) + horloge de la place
    b += box(5, Y, -14, 9, Y + 18, -10, "stone_bricks", floor="stone_bricks")
    b += fill(6, Y + 19, -13, 8, Y + 19, -11, "deepslate_tile_slab[type=bottom]")
    b += fill(7, Y + 1, -10, 7, Y + 2, -10, "air")
    b += fill(6, Y + 12, -10, 8, Y + 14, -10, "white_concrete")
    b += [setblock(7, Y + 14, -10, "black_concrete"), setblock(7, Y + 13, -10, "black_concrete")]
    b += [setblock(7, Y + 17, -10, "bell[attachment=ceiling,facing=south]")]
    # grande horloge de parquet, aiguilles figées sur minuit (cliquable)
    cx, cy, cz = CLOCK
    b += [setblock(int(cx - 0.5), Y + 1, int(cz - 0.5), "dark_oak_log"),
          setblock(int(cx - 0.5), Y + 2, int(cz - 0.5), "dark_oak_log"),
          setblock(int(cx - 0.5), Y + 3, int(cz - 0.5), "dark_oak_slab[type=bottom]")]
    b.append(text_display(cx, Y + 2.2, cz + 0.52, ["", T("XII\n", "black", bold=True), T("│\n●", "black")],
                          ["sol.r0"], billboard="fixed", bg=0xFFF0E6C8, line_width=40, scale=0.6))
    b.append(interaction(cx, Y + 1, cz, ["sol.r0", "sol.clock0"], w=1.2, h=2.2))
    # --------------------------------------------------------------- gare
    b += fill(-12, Y, -37, 12, Y, -29, "stone_bricks")
    b += fill(-10, Y + 1, -36, 10, Y + 1, -30, "smooth_stone_slab[type=bottom]")
    b += fill(-12, Y + 1, -29, 12, Y + 1, -29, "stone_brick_wall")
    b += fill(-2, Y + 1, -29, 2, Y + 1, -29, "air")
    for x in (-10, -3, 3, 10):
        b += fill(x, Y + 2, -33, x, Y + 5, -33, "dark_oak_fence")
    b += fill(-11, Y + 6, -35, 11, Y + 6, -31, "dark_oak_slab[type=bottom]")
    b.append(text_display(0.5, Y + 4.5, -29.6, ["", T("Gare de Brumeval", "gold", bold=True),
                                                 T("\nExpress du Solstice → Pic du Solstice", "gray")], ["sol.r0"],
                          billboard="fixed", yaw=180))
    # voie et train (décor)
    b += fill(-40, Y, -40, 40, Y, -38, "gravel")
    b += fill(-40, Y + 1, -39, 40, Y + 1, -39, "rail[shape=east_west]")
    b += fill(-14, Y + 1, -41, 6, Y + 4, -37, "black_concrete")
    b += fill(-13, Y + 2, -41, 5, Y + 3, -37, "air")
    b += fill(-13, Y + 2, -37, 5, Y + 3, -37, "glass_pane")
    b += fill(7, Y + 1, -40, 16, Y + 3, -38, "black_concrete")
    b += fill(7, Y + 4, -40, 12, Y + 4, -38, "gray_concrete")
    b += fill(14, Y + 4, -39, 14, Y + 7, -39, "polished_blackstone_wall")
    b += [setblock(14, Y + 8, -39, "campfire[lit=true,signal_fire=true]"), setblock(17, Y + 2, -39, "redstone_lamp[lit=true]")]
    b += fill(-14, Y + 5, -41, 6, Y + 5, -37, "red_nether_brick_slab[type=bottom]")
    # arbres
    for i, (x, z) in enumerate([(-30, -20), (-34, 8), (-28, 26), (28, -22), (32, 12), (26, 30), (-8, 32), (10, 32),
                                (-36, -6), (36, -4), (-20, -26), (20, -28)]):
        b += tree(x, Y + 1, z, h=5 + i % 2, seed=i)
    # PNJ
    for key, (name, color, (x, y, z), yaw, prof) in NPCS.items():
        b.append(npc_summon(key))
        b.append(interaction(x, y, z, ["sol.r0", "sol.npc0", f"sol.npci_{key}"], w=0.9, h=2.0))
    # auvent de l’horloger (poteau derrière lui, lanterne suspendue devant)
    ox, oz = int(NPCS[SKIN_NPC][2][0]), int(NPCS[SKIN_NPC][2][2])
    b += fill(ox + 1, Y + 1, oz + 1, ox + 1, ROOF_Y - 1, oz + 1, "spruce_fence")
    b += fill(ox - 1, ROOF_Y, oz - 1, ox + 1, ROOF_Y, oz + 1, ROOF)
    b.append(setblock(ox - 1, ROOF_Y - 1, oz - 1, "lantern[hanging=true]"))
    # traînée d’encre bleue (gouttes = teinture bleue posée à plat)
    for i, (x, z) in enumerate(INK):
        b.append(f"summon item_display {x} {Y + 1.02} {z} {{Tags:[\"sol\",\"sol.r0\",\"sol.ink0\"],"
                 f"item:{{id:\"minecraft:blue_dye\",count:1}},item_display:\"ground\","
                 f"transformation:{{left_rotation:[0.7071f,0f,0f,0.7071f],right_rotation:[0f,0f,0f,1f],"
                 f"translation:[0f,0f,0f],scale:[0.35f,0.35f,0.35f]}}}}")
    px, py, pz = PUDDLE
    b += [setblock(int(px - 0.5), Y + 1, int(pz - 0.5), "air")]
    b.append(f"summon item_display {px} {Y + 1.03} {pz} {{Tags:[\"sol\",\"sol.r0\",\"sol.puddle\"],"
             f"item:{{id:\"minecraft:blue_carpet\",count:1}},"
             f"transformation:{{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],translation:[0f,0f,0f],"
             f"scale:[0.9f,0.08f,0.7f]}}}}")
    b.append(f"summon item_display {px + 0.3} {Y + 1.1} {pz - 0.2} {{Tags:[\"sol\",\"sol.r0\"],"
             f"item:{{id:\"minecraft:ink_sac\",count:1}},item_display:\"ground\","
             f"transformation:{{left_rotation:[0.7071f,0f,0f,0.7071f],right_rotation:[0f,0f,0f,1f],"
             f"translation:[0f,0f,0f],scale:[0.5f,0.5f,0.5f]}}}}")
    dp.fn("build/r0", b)
    dp.meta.setdefault("builds", []).append("build/r0")
    dp.meta.setdefault("forceload", []).append((-48, -48, 48, 48))

    # ------------------------------------------------------------- logique
    for key in NPCS:
        dp.add("load", [f"scoreboard objectives add sol.t_{key} dummy"])
        lines = LINES[key]
        name, color = NPCS[key][0], NPCS[key][1]
        body = [f"scoreboard players operation #i {V} = @s sol.t_{key}",
                f"scoreboard players set #n {V} {len(lines)}",
                f"scoreboard players operation #i {V} %= #n {V}"]
        for j, l in enumerate(lines):
            body.append(f"execute if score #i {V} matches {j} run " + say(name, color, l, "@s"))
        body += [f"scoreboard players add @s sol.t_{key} 1",
                 "playsound minecraft:entity.villager.ambient master @s ~ ~ ~ 0.7 0.9"]
        dp.fn(f"village/talk_{key}", body)
    dp.fn("village/npc_clicked", [
        *[f"execute if entity @s[tag=sol.npci_{k}] on target run function solstice:village/talk_{k}" for k in NPCS],
        "data remove entity @s interaction",
    ])
    dp.fn("village/clock_clicked", [
        "execute on target run function solstice:village/clock_read",
        "data remove entity @s interaction",
    ])
    dp.fn("village/clock_read", [
        narr("La grande horloge de la place s’est arrêtée. Ses aiguilles sont figées sur minuit pile.", "@s"),
        "playsound minecraft:block.wooden_door.close master @s ~ ~ ~ 0.6 0.6",
        "function solstice:story/found_minuit",
    ])
    dp.fn("village/tick", [
        "execute as @e[type=interaction,tag=sol.npc0] if data entity @s interaction run function solstice:village/npc_clicked",
        "execute as @e[type=interaction,tag=sol.clock0] if data entity @s interaction run function solstice:village/clock_clicked",
        f"execute if score #m20 {V} matches 0 run function solstice:village/npc_guard",
    ])
    # Paisible supprime tout monstre, même persistant : le PNJ à skin (un noyé) serait perdu. On repasse en Normal
    # (décision 16) et on le fait réapparaître si sa zone cliquable est chargée mais lui absent.
    dp.fn("village/npc_guard", [
        f"execute store result score #diff {V} run difficulty",
        f"execute if score #diff {V} matches 0 run function solstice:system/not_peaceful",
        f"execute if entity @e[type=interaction,tag=sol.npci_{SKIN_NPC}] "
        f"unless entity @e[type={npc_type(SKIN_NPC)},tag=sol.npc0_{SKIN_NPC}] run " + npc_summon(SKIN_NPC),
    ])
    dp.fn("village/ptick", [
        f"execute if score #clue_encre {V} matches 0 if entity @s[x={int(px - 0.5) - 1},y={Y},z={int(pz - 0.5) - 1},dx=2,dy=3,dz=2] "
        "run function solstice:village/puddle",
    ])
    dp.fn("village/puddle", [
        narr("Une flaque d’encre bleue devant la bibliothèque… et des gouttes qui filent vers le nord, jusqu’à la gare.", "@s"),
        "function solstice:story/found_encre",
    ])
    for key in NPCS:
        dp.test(f"prologue : PNJ {key} présent", f"entity @e[type={npc_type(key)},tag=sol.npc0_{key}]")
        dp.test(f"prologue : PNJ {key} cliquable", f"entity @e[type=interaction,tag=sol.npci_{key}]")
    dp.test("prologue : Maître Orel immobile, muet, invulnérable, persistant",
            f"entity @e[type=drowned,tag=sol.npc0_orel,nbt={{NoAI:1b,Silent:1b,Invulnerable:1b,PersistenceRequired:1b}}]")
    ox, oz = int(NPCS[SKIN_NPC][2][0]), int(NPCS[SKIN_NPC][2][2])
    dp.test("prologue : Maître Orel à l’abri du soleil (auvent)", f"block {ox} {ROOF_Y} {oz} minecraft:{ROOF}")
    dp.test("prologue : traînée d’encre (17 gouttes)", "entity @e[type=item_display,tag=sol.ink0]")
    dp.test("prologue : horloge figée cliquable", "entity @e[type=interaction,tag=sol.clock0]")
    dp.meta.setdefault("rooms", {})["village"] = {"npcs": {k: v[2] for k, v in NPCS.items()}, "clock": CLOCK,
                                                  "puddle": PUDDLE}
