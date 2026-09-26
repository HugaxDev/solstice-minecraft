"""Salle 5. Conception : design/SPOILERS_NE_PAS_LIRE/SALLE5.md (ne pas lire si vous jouez)."""
import random

from .core import (V, T, jdump, tellraw, title, narr, actionbar, fill, setblock, text_display, interaction, SC, sound)
from .flow import obj
from .hints import hint_fn
from .build import box
from . import secret5

OX, Y = 5000, 100
# zone A (nef), B (couloir), C (place) — z décroissant vers le nord
A = (4987, 10, 5013, 30)
B = (4997, -32, 5003, 9)
C = (4975, -72, 5025, -34)
A_CP = (5000.5, 101, 28.5, 180)
B_CP = (5000.5, 101, 7.5, 180)
C_CP = (5000.5, 101, -35.5, 180)
WATCH_SPOTS = [(4988, 11), (5012, 11), (4990, 21), (5010, 22), (4995, 17), (5006, 18), (4988, 29), (5012, 29)]
LOCKS = [(4997, -8), (5003, -17), (4997, -26)]
VEIL_HOME = (5000.5, 101, -30.5)
PATROL = [(4985, -44), (5015, -44), (5015, -62), (5000, -68), (4985, -62)]
LAMPS = [(4979, -40), (5021, -48), (4981, -66)]
LODGE = (5017, -66)
BELL = (5000, -70)


def build(dp):
    b = ["kill @e[type=!player,tag=sol.r5]"]
    b += fill(4960, 90, -80, 5040, 125, 40, "air")
    # --- zone A
    x1, z1, x2, z2 = A
    b += box(x1 - 1, Y, z1 - 1, x2 + 1, Y + 9, z2 + 1, "deepslate_bricks", floor="dark_oak_planks", ceil="deepslate_tiles")
    for x in range(x1 + 2, x2, 5):
        b += fill(x, Y + 1, z1 + 2, x, Y + 7, z1 + 2, "dark_oak_log")
        b += fill(x, Y + 1, z2 - 2, x, Y + 7, z2 - 2, "dark_oak_log")
    for x in range(x1 + 1, x2, 4):
        for z in (z1 + 5, z1 + 9, z1 + 13):
            b.append(setblock(x, Y + 1, z, "dark_oak_stairs[facing=north]"))
    b += fill(OX - 1, Y + 1, z1 - 1, OX + 1, Y + 3, z1 - 1, "iron_bars")
    b.append(setblock(OX, Y + 5, z1 + 1, "cobweb"))
    # --- zone B (couloir)
    bx1, bz1, bx2, bz2 = B
    b += box(bx1 - 1, Y, bz1 - 1, bx2 + 1, Y + 5, bz2 + 1, "stone_bricks", floor="cracked_stone_bricks", ceil="stone_bricks")
    b += fill(OX - 1, Y + 1, bz2 + 1, OX + 1, Y + 3, bz2 + 1, "air")
    for z in range(bz1 + 2, bz2, 6):
        b.append(setblock(bx1 - 1, Y + 3, z, "soul_wall_torch[facing=east]"))
        b.append(setblock(bx2 + 1, Y + 3, z, "soul_wall_torch[facing=west]"))
    b += fill(OX - 1, Y + 1, bz1 - 1, OX + 1, Y + 3, bz1 - 1, "iron_bars")
    for (x, z) in LOCKS:
        b.append(setblock(x + (-1 if x < OX else 1), Y + 2, z, "chiseled_stone_bricks"))
    # --- zone C (place)
    cx1, cz1, cx2, cz2 = C
    b += fill(cx1 - 1, Y - 1, cz1 - 1, cx2 + 1, Y - 1, cz2 + 1, "stone")
    b += fill(cx1, Y, cz1, cx2, Y, cz2, "cobblestone")
    b += fill(cx1 + 3, Y, cz1 + 3, cx2 - 3, Y, cz2 - 3, "mossy_cobblestone")
    for (x, z) in [(cx1 - 1, z) for z in range(cz1 - 1, cz2 + 2)] + [(cx2 + 1, z) for z in range(cz1 - 1, cz2 + 2)] + \
                  [(x, cz1 - 1) for x in range(cx1 - 1, cx2 + 2)] + [(x, cz2 + 1) for x in range(cx1 - 1, cx2 + 2)]:
        b += fill(x, Y + 1, z, x, Y + 7, z, "deepslate_bricks")
    b += fill(OX - 1, Y + 1, cz2 + 1, OX + 1, Y + 3, cz2 + 1, "air")
    rnd = random.Random(55)
    keep_clear = [(lx_ - 3, lz_ - 3, lx_ + 3, lz_ + 3) for (lx_, lz_) in LAMPS] + \
                 [(LODGE[0] - 5, LODGE[1] - 4, LODGE[0] + 4, LODGE[1] + 4), (BELL[0] - 3, BELL[1] - 3, BELL[0] + 3, BELL[1] + 5),
                  (OX - 3, cz2 - 6, OX + 3, cz2)]
    for i in range(18):   # obstacles pour se cacher (charrettes, tonneaux, murets)
        x, z = rnd.randint(cx1 + 3, cx2 - 3), rnd.randint(cz1 + 4, cz2 - 4)
        if any(a - 2 <= x <= c and b_ <= z <= d for a, b_, c, d in keep_clear):
            continue
        b += fill(x, Y + 1, z, x + rnd.randint(0, 2), Y + 1 + rnd.randint(0, 1), z, rnd.choice(["barrel[facing=up]", "hay_block", "cobblestone_wall", "spruce_planks"]))
    for (x, z) in LAMPS:
        b += [setblock(x, Y + 1, z, "cobblestone_wall"), setblock(x, Y + 2, z, "soul_lantern")]
    lx, lz = LODGE
    b += box(lx - 3, Y, lz - 3, lx + 3, Y + 4, lz + 3, "spruce_planks", floor="spruce_planks")
    b += fill(lx - 3, Y + 1, lz, lx - 3, Y + 2, lz, "air")
    b.append(setblock(lx, Y + 1, lz, "lectern[facing=west]"))
    bx, bz = BELL
    b += fill(bx - 2, Y, bz - 2, bx + 2, Y + 8, bz + 2, "polished_blackstone_bricks")
    b += fill(bx - 1, Y + 1, bz - 1, bx + 1, Y + 7, bz + 1, "air")
    b += fill(bx - 1, Y, bz + 2, bx + 1, Y + 3, bz + 2, "iron_bars")
    b += fill(bx - 1, Y + 1, bz + 2, bx + 1, Y + 3, bz + 2, "iron_bars")
    b.append(setblock(bx, Y + 4, bz, "bell[attachment=ceiling,facing=south]"))
    b.append(setblock(bx, Y + 5, bz, "polished_blackstone_bricks"))
    dp.meta.setdefault("builds", []).append("build/r5")
    dp.meta.setdefault("forceload", []).append((4960, -80, 5040, 40))
    dp.json("data/solstice/tags/block/seethrough.json", {"values": [
        "minecraft:air", "minecraft:cave_air", "minecraft:light", "minecraft:iron_bars", "minecraft:glass_pane", "minecraft:cobweb",
        "#minecraft:candles", "minecraft:soul_wall_torch", "minecraft:soul_torch", "minecraft:water", "minecraft:short_grass"]})

    # ---------------------------------------------------------------- entités
    e = ["kill @e[type=!player,tag=sol.r5d]"]

    def it(x, y, z, key, w=1.25, h=1.2):
        e.append(interaction(x, y, z, ["sol.r5", "sol.r5d", "sol.r5i", f"sol.k5_{key}"], w, h))
    for i, (x, z) in enumerate(WATCH_SPOTS):
        e.append(f"summon marker {x + 0.5} {Y + 1} {z + 0.5} {{Tags:[\"sol\",\"sol.r5\",\"sol.r5d\",\"sol.w5spot\",\"sol.w5s{i}\"]}}")
    for i, (x, z) in enumerate(LOCKS):
        it(x + 0.5, Y + 1.4, z + 0.5, f"lock{i}", 0.9, 1.0)
        e.append(f"summon block_display {x + (0.0 if x < OX else 0.6)} {Y + 1.5} {z + 0.2} {{Tags:[\"sol\",\"sol.r5\",\"sol.r5d\",\"sol.l5d{i}\"],"
                 f"block_state:{{Name:\"minecraft:chain\",Properties:{{axis:\"x\"}}}},transformation:{{left_rotation:[0f,0f,0f,1f],"
                 f"right_rotation:[0f,0f,0f,1f],translation:[0f,0f,0f],scale:[0.4f,1f,0.6f]}}}}")
    for i, (x, z) in enumerate(LAMPS):
        it(x + 0.5, Y + 0.95, z + 0.5, f"lamp{i}", 1.3, 2.2)
    it(LODGE[0] + 0.5, Y + 0.95, LODGE[1] + 0.5, "book", 1.3, 1.3)
    it(BELL[0] + 0.5, Y + 3.9, BELL[1] + 0.5, "bell", 1.3, 1.3)
    e.append(f"summon armor_stand {VEIL_HOME[0]} {VEIL_HOME[1]} {VEIL_HOME[2]} {{Tags:[\"sol\",\"sol.r5\",\"sol.r5d\",\"sol.r5veil\"],"
             f"NoGravity:1b,Invulnerable:1b,ShowArms:1b,NoBasePlate:1b,DisabledSlots:4144959,Rotation:[0f,0f],"
             f"Pose:{{RightArm:[-90f,0f,0f],LeftArm:[-90f,0f,0f]}},"
             f"ArmorItems:[{{id:\"minecraft:leather_boots\",count:1,components:{{\"minecraft:dyed_color\":{{rgb:1118481}}}}}},"
             f"{{id:\"minecraft:leather_leggings\",count:1,components:{{\"minecraft:dyed_color\":{{rgb:1118481}}}}}},"
             f"{{id:\"minecraft:leather_chestplate\",count:1,components:{{\"minecraft:dyed_color\":{{rgb:1118481}}}}}},"
             f"{{id:\"minecraft:wither_skeleton_skull\",count:1}}]}}")
    px, pz = PATROL[0]
    e.append(f"summon armor_stand {px + 0.5} {Y + 1} {pz + 0.5} {{Tags:[\"sol\",\"sol.r5\",\"sol.r5d\",\"sol.r5sh\"],NoGravity:1b,"
             f"Invulnerable:1b,ShowArms:1b,NoBasePlate:1b,DisabledSlots:4144959,Invisible:0b,"
             f"Pose:{{RightArm:[-60f,0f,0f]}},HandItems:[{{id:\"minecraft:soul_lantern\",count:1}},{{}}],"
             f"ArmorItems:[{{id:\"minecraft:leather_boots\",count:1,components:{{\"minecraft:dyed_color\":{{rgb:0}}}}}},"
             f"{{id:\"minecraft:leather_leggings\",count:1,components:{{\"minecraft:dyed_color\":{{rgb:0}}}}}},"
             f"{{id:\"minecraft:leather_chestplate\",count:1,components:{{\"minecraft:dyed_color\":{{rgb:0}}}}}},"
             f"{{id:\"minecraft:wither_skeleton_skull\",count:1}}],attributes:[{{id:\"minecraft:generic.scale\",base:1.35d}}]}}")
    e.append(f"summon armor_stand {OX + 0.5} {Y + 1} {A[1] + 1.5} {{Tags:[\"sol\",\"sol.r5\",\"sol.r5d\",\"sol.r5sil\"],NoGravity:1b,"
             f"Invulnerable:1b,Invisible:1b,NoBasePlate:1b,DisabledSlots:4144959,ArmorItems:[{{}},{{}},"
             f"{{id:\"minecraft:leather_chestplate\",count:1,components:{{\"minecraft:dyed_color\":{{rgb:0}}}}}},"
             f"{{id:\"minecraft:wither_skeleton_skull\",count:1}}]}}")
    dp.fn("r5/entities", e)
    dp.fn("build/r5", b + ["function solstice:r5/entities"])

    # ---------------------------------------------------------------- remise à zéro
    reset = ["function solstice:r5/entities",
             *[f"scoreboard players set {f} {V} 0" for f in ("#w5n", "#l5n", "#lamp5n", "#r5caught", "#r5book", "#r5done", "#r5t", "#veilon",
                                                             "#shw", "#shs", "#r5ev", "#r5evt", "#r5freeze")],
             *fill(OX - 1, Y + 1, A[1] - 1, OX + 1, Y + 3, A[1] - 1, "iron_bars"),
             *fill(OX - 1, Y + 1, B[1] - 1, OX + 1, Y + 3, B[1] - 1, "iron_bars"),
             *fill(BELL[0] - 1, Y + 1, BELL[1] + 2, BELL[0] + 1, Y + 3, BELL[1] + 2, "iron_bars"),
             *[setblock(x, Y + 2, z, "soul_lantern") for (x, z) in LAMPS],
             # trois montres parmi huit emplacements
             "tag @e[type=marker,tag=sol.w5spot] remove sol.w5on",
             f"scoreboard players set #pick {V} 0", "function solstice:r5/pick_watch"]
    dp.fn("r5/reset", reset)
    pick = [f"execute if score #pick {V} matches 3.. run return 0",
            f"execute store result score #rnd {V} run random value 0..{len(WATCH_SPOTS) - 1}"]
    for i in range(len(WATCH_SPOTS)):
        pick.append(f"execute if score #rnd {V} matches {i} as @e[type=marker,tag=sol.w5s{i},tag=!sol.w5on] run function solstice:r5/put_watch")
    pick.append("function solstice:r5/pick_watch")
    dp.fn("r5/pick_watch", pick)
    dp.fn("r5/put_watch", [
        "tag @s add sol.w5on", f"scoreboard players add #pick {V} 1",
        "execute at @s run summon item_display ~ ~0.3 ~ {Tags:[\"sol\",\"sol.r5\",\"sol.r5d\",\"sol.w5it\"],item:{id:\"minecraft:clock\",count:1},"
        "transformation:{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],translation:[0f,0f,0f],scale:[0.4f,0.4f,0.4f]}}",
        "execute at @s run summon interaction ~ ~ ~ {Tags:[\"sol\",\"sol.r5\",\"sol.r5d\",\"sol.r5i\",\"sol.k5_watch\"],width:0.9f,height:0.9f,response:1b}",
    ])

    # ---------------------------------------------------------------- cycle
    dp.fn("r5/start", ["function solstice:r5/reset", f"scoreboard players set #step {V} 1", "function solstice:r5/obj",
                       "weather clear"])
    dp.fn("r5/cp", [f"execute if score #step {V} matches ..1 run tp @s {A_CP[0]} {A_CP[1]} {A_CP[2]} {A_CP[3]} 0",
                    f"execute if score #step {V} matches 2 run tp @s {B_CP[0]} {B_CP[1]} {B_CP[2]} {B_CP[3]} 0",
                    f"execute if score #step {V} matches 3.. run tp @s {C_CP[0]} {C_CP[1]} {C_CP[2]} {C_CP[3]} 0",
                    f"spawnpoint @s {int(A_CP[0])} {A_CP[1]} {int(A_CP[2])}"])
    dp.fn("r5/enter", ["function solstice:r5/cp", "effect clear @s night_vision",
                       *title("@s", "…", "Il fait nuit. Il fera toujours nuit.", color="dark_purple", times=(40, 60, 40)),
                       "playsound minecraft:ambient.cave master @s ~ ~ ~ 1 0.6"])
    dp.fn("r5/respawn", ["function solstice:r5/cp"])
    dp.fn("r5/wipe", [])
    dp.fn("r5/on_complete", [f"execute if score #r5caught {V} matches 0 run function solstice:challenge/grant_sang_froid",
                             "effect clear @a darkness"])
    dp.fn("r5/obj", [
        f"execute if score #step {V} matches 1 run bossbar set solstice:obj name " + jdump(["", T("◆ ", "dark_purple"), T("Écoutez. Quelque chose fait tic-tac dans le noir.", "gray")]),
        f"execute if score #step {V} matches 2 run bossbar set solstice:obj name " + jdump(["", T("◆ ", "dark_purple"), T("Trois verrous. Ne la quittez pas des yeux.", "gray")]),
        f"execute if score #step {V} matches 3 run bossbar set solstice:obj name " + jdump(["", T("◆ ", "dark_purple"), T("Trois lanternes, puis la cloche de l’aube. Qu’elle ne vous voie pas.", "gray")]),
        f"execute if score #step {V} matches 4 run bossbar set solstice:obj name " + jdump(["", T("◆ ", "dark_purple"), T("La cloche de l’aube. Ensemble.", "gray")]),
    ])

    # ---------------------------------------------------------------- clics
    keys = ["watch", "lock0", "lock1", "lock2", "lamp0", "lamp1", "lamp2", "book", "bell"]
    clk = []
    for k in keys:
        clk.append(f"execute if entity @s[tag=sol.k5_{k}] if data entity @s interaction on target run function solstice:r5/cc/{k}")
        clk.append(f"execute if entity @s[tag=sol.k5_{k}] if data entity @s attack on attacker run function solstice:r5/cc/{k}")
        dp.fn(f"r5/cc/{k}", ["execute if score @s sol.cool matches 1.. run return 0", "scoreboard players set @s sol.cool 8",
                             f"function solstice:r5/c/{k}"])
    clk += ["data remove entity @s interaction", "data remove entity @s attack"]
    dp.fn("r5/clicked", clk)
    # la montre cliquée est celle de l’interaction qui porte sol.cur (étiquetée avant le « on target »)
    dp.fn("r5/c/watch", [
        f"execute unless score #step {V} matches 1 run return 0",
        "execute as @e[type=interaction,tag=sol.cur] at @s run function solstice:r5/take_watch",
    ])
    dp.fn("r5/take_watch", [
        "kill @e[type=item_display,tag=sol.w5it,distance=..1]", "kill @s",
        f"scoreboard players add #w5n {V} 1",
        "playsound minecraft:item.armor.equip_gold master @a ~ ~ ~ 1 0.6",
        f"execute if score #w5n {V} matches 1 run function solstice:r5/scare1",
        f"execute if score #w5n {V} matches 2 run function solstice:r5/scare2",
        f"execute if score #w5n {V} matches 3 run function solstice:r5/to_b",
        actionbar("@a", ["", T("Montres : ", "gray"), SC("#w5n"), T(" / 3", "gray")]),
    ])
    dp.fn("r5/scare1", [
        "effect give @a[scores={sol.room=5}] darkness 4 0 true",
        "execute as @a[scores={sol.room=5}] at @s run playsound minecraft:ambient.cave master @s ~ ~ ~ 1 0.5",
        f"execute as @e[type=armor_stand,tag=sol.r5sil] run data merge entity @s {{Invisible:0b}}",
        f"scoreboard players set #sil {V} 50",
    ])
    dp.fn("r5/scare2", [
        f"execute as @a[scores={{sol.room=5}}] at @s run playsound minecraft:block.wooden_door.close master @s ~ ~ ~-4 2 0.5",
        f"execute as @a[scores={{sol.room=5}}] at @s run playsound minecraft:block.bell.resonate master @s ~ ~ ~ 0.6 0.4",
        "effect give @a[scores={sol.room=5}] darkness 3 0 true",
    ])
    dp.fn("r5/to_b", [
        f"scoreboard players set #step {V} 2", "function solstice:hints/reset", "function solstice:r5/obj",
        *fill(OX - 1, Y + 1, A[1] - 1, OX + 1, Y + 3, A[1] - 1, "air"),
        f"scoreboard players set #veilon {V} 1",
        "execute as @a[scores={sol.room=5}] at @s run playsound minecraft:block.iron_door.open master @s ~ ~ ~ 1 0.5",
        narr("La grille se lève. Au bout du couloir, quelque chose attend, immobile… tant qu’on la regarde.", "@a"),
    ])
    for i, (x, z) in enumerate(LOCKS):
        dp.fn(f"r5/c/lock{i}", [
            f"execute unless score #step {V} matches 2 run return 0",
            f"execute if score #l5{i} {V} matches 1 run return 0",
            f"scoreboard players set #l5{i} {V} 1", f"scoreboard players add #l5n {V} 1",
            f"kill @e[type=block_display,tag=sol.l5d{i}]",
            "playsound minecraft:block.chain.break master @a ~ ~ ~ 1 0.6",
            f"execute if score #l5n {V} matches 3 run function solstice:r5/to_c"])
    dp.add("r5/reset", [f"scoreboard players set #l5{i} {V} 0" for i in range(3)])
    dp.fn("r5/to_c", [
        f"scoreboard players set #step {V} 3", f"scoreboard players set #veilon {V} 0", "function solstice:hints/reset", "function solstice:r5/obj",
        *fill(OX - 1, Y + 1, B[1] - 1, OX + 1, Y + 3, B[1] - 1, "air"),
        f"tp @e[type=armor_stand,tag=sol.r5veil] {VEIL_HOME[0]} {VEIL_HOME[1]} {VEIL_HOME[2]}",
        "execute as @a[scores={sol.room=5}] at @s run playsound minecraft:block.iron_door.open master @s ~ ~ ~ 1 0.5",
        narr("Le dernier verrou cède. Dehors, la place… et une lanterne qui se promène toute seule.", "@a"),
    ])
    for i, (x, z) in enumerate(LAMPS):
        dp.fn(f"r5/c/lamp{i}", [
            f"execute unless score #step {V} matches 3 run return 0",
            f"execute if block {x} {Y + 2} {z} lantern run return 0",
            setblock(x, Y + 2, z, "lantern"), f"scoreboard players add #lamp5n {V} 1",
            "playsound minecraft:item.firecharge.use master @a ~ ~ ~ 1 0.8",
            actionbar("@a", ["", T("Lanternes de l’aube : ", "gold"), SC("#lamp5n"), T(" / 3", "gray")]),
            f"execute if score #lamp5n {V} matches 3 run function solstice:r5/lamps_done"])
    dp.fn("r5/lamps_done", [f"scoreboard players set #step {V} 4", "function solstice:hints/reset", "function solstice:r5/obj",
                            *fill(BELL[0] - 1, Y + 1, BELL[1] + 2, BELL[0] + 1, Y + 3, BELL[1] + 2, "air"),
                            "execute as @a[scores={sol.room=5}] at @s run playsound minecraft:block.iron_door.open master @s ~ ~ ~ 1 0.4",
                            narr("La grille du clocher s’ouvre. La cloche de l’aube attend… tous les trois.", "@a")])
    dp.fn("r5/c/book", [f"execute unless score #step {V} matches 3.. run return 0",
                        narr("Le carnet du veilleur, ouvert à la dernière page…", "@s"),
                        f"function solstice:story/found_{secret5.CLUE_ID}"])
    bx, bz = BELL
    dp.fn("r5/c/bell", [
        f"execute unless score #step {V} matches 4 run return 0",
        f"execute store result score #atbell {V} if entity @a[x={bx - 1},y={Y + 1},z={bz - 1},dx=2,dy=3,dz=3,gamemode=!spectator]",
        f"execute if score #atbell {V} >= #need {V} if score #atbell {V} >= #np {V} run return run function solstice:r5/dawn",
        "playsound minecraft:block.bell.use master @a ~ ~ ~ 1 0.5",
        actionbar("@a", ["", T("La cloche ne sonne qu’à plein. Au clocher : ", "gray"), SC("#atbell"), T(" / ", "gray"), SC("#np")])])
    dp.fn("r5/dawn", [
        f"execute if score #r5done {V} matches 1 run return 0", f"scoreboard players set #r5done {V} 1",
        "time set 23500", "effect clear @a darkness",
        "execute as @a at @s run playsound minecraft:block.bell.use master @s ~ ~ ~ 2 1",
        *title("@a", "L’aube", "La nuit la plus longue est finie.", color="gold", times=(20, 60, 20)),
        "function solstice:flow/complete"])

    # ---------------------------------------------------------------- la Veilleuse (zone B)
    dp.fn("r5/ray", [
        f"scoreboard players add #rs {V} 1",
        f"execute if entity @e[type=armor_stand,tag=sol.r5veil,distance=..1.1] run return run scoreboard players set #seen {V} 1",
        f"execute positioned ~ ~-1 ~ if entity @e[type=armor_stand,tag=sol.r5veil,distance=..1.1] run return run scoreboard players set #seen {V} 1",
        "execute unless block ~ ~ ~ #solstice:seethrough run return 0",
        f"execute if score #rs {V} matches 90.. run return 0",
        "execute positioned ^ ^ ^0.5 run function solstice:r5/ray",
    ])
    dp.fn("r5/look", [f"scoreboard players set #rs {V} 0", "execute anchored eyes positioned ^ ^ ^ run function solstice:r5/ray"])
    dp.fn("r5/veil_tick", [
        f"scoreboard players set #seen {V} 0",
        f"execute as @a[scores={{sol.room=5}},gamemode=!spectator,x={B[0] - 2},y=95,z={B[1] - 2},dx={B[2] - B[0] + 4},dy=12,dz={B[3] - B[1] + 4}] at @s run function solstice:r5/look",
        f"execute if score #seen {V} matches 0 as @e[type=armor_stand,tag=sol.r5veil] at @s if entity @a[distance=..40,gamemode=!spectator] "
        f"facing entity @a[scores={{sol.room=5}},gamemode=!spectator,sort=nearest,limit=1] feet rotated ~ 0 run tp @s ^ ^ ^0.28 ~ 0",
        f"execute if score #seen {V} matches 0 if score #m20 {V} matches 0 as @e[type=armor_stand,tag=sol.r5veil] at @s run playsound minecraft:block.stone.step master @a ~ ~ ~ 0.8 0.5",
        f"execute as @e[type=armor_stand,tag=sol.r5veil] at @s as @a[distance=..1.3,gamemode=adventure] run function solstice:r5/caught_b",
    ])
    dp.fn("r5/caught_b", [
        f"scoreboard players add #r5caught {V} 1",
        f"tp @s {B_CP[0]} {B_CP[1]} {B_CP[2]} {B_CP[3]} 0",
        f"tp @e[type=armor_stand,tag=sol.r5veil] {VEIL_HOME[0]} {VEIL_HOME[1]} {VEIL_HOME[2]}",
        "effect give @s blindness 2 0 true", "effect give @s darkness 5 0 true",
        "playsound minecraft:entity.warden.sonic_charge master @s ~ ~ ~ 1 1.4",
        *title("@s", "…", "Elle vous a touché.", color="dark_red", times=(2, 30, 10)),
    ])

    # ---------------------------------------------------------------- l’Ombre (zone C)
    pat = []
    for i, (x, z) in enumerate(PATROL):
        nx, nz = PATROL[(i + 1) % len(PATROL)]
        pat.append(f"execute if score #shw {V} matches {i} as @e[type=armor_stand,tag=sol.r5sh] at @s facing {nx + 0.5} {Y + 1} {nz + 0.5} "
                   f"run tp @s ^ ^ ^0.12 ~ ~")
        pat.append(f"execute if score #shw {V} matches {i} if score #lamp5n {V} matches 2.. as @e[type=armor_stand,tag=sol.r5sh] at @s facing {nx + 0.5} {Y + 1} {nz + 0.5} "
                   f"run tp @s ^ ^ ^0.08 ~ ~")
        pat.append(f"execute if score #shw {V} matches {i} as @e[type=armor_stand,tag=sol.r5sh] at @s if entity @s[x={nx},y={Y},z={nz},dx=0,dy=3,dz=0] "
                   f"run scoreboard players set #shn {V} 1")
    pat += [f"execute if score #shn {V} matches 1 run scoreboard players add #shw {V} 1",
            f"execute if score #shw {V} matches {len(PATROL)}.. run scoreboard players set #shw {V} 0",
            f"scoreboard players set #shn {V} 0"]
    dp.fn("r5/shadow_move", pat)
    pat = [f"execute unless score #r5freeze {V} matches 1 run function solstice:r5/shadow_move",   # (tests : ronde suspendue)
            "execute as @e[type=armor_stand,tag=sol.r5sh] at @s run particle minecraft:soul_fire_flame ^ ^1.4 ^0.6 0.1 0.1 0.1 0 1",
            # détection : devant (sphère centrée 6 blocs devant), trop près ; accroupi = plus discret
            "execute as @e[type=armor_stand,tag=sol.r5sh] at @s positioned ^ ^ ^6 as @a[distance=..6,gamemode=adventure,scores={sol.room=5}] unless predicate solstice:sneaking run function solstice:r5/seen_c",
            "execute as @e[type=armor_stand,tag=sol.r5sh] at @s positioned ^ ^ ^3 as @a[distance=..3,gamemode=adventure,scores={sol.room=5}] run function solstice:r5/seen_c",
            "execute as @e[type=armor_stand,tag=sol.r5sh] at @s as @a[distance=..2.5,gamemode=adventure,scores={sol.room=5}] run function solstice:r5/caught_c"]
    dp.fn("r5/shadow_tick", pat)
    dp.pred("sneaking", {"condition": "minecraft:entity_properties", "entity": "this", "predicate": {"flags": {"is_sneaking": True}}})
    # ligne de vue : rayon de l’Ombre vers le joueur (un obstacle cache)
    dp.fn("r5/seen_c", ["tag @s add sol.me", f"scoreboard players set #los {V} 0", f"scoreboard players set #rs {V} 0",
                        "execute as @e[type=armor_stand,tag=sol.r5sh] at @s anchored eyes facing entity @a[tag=sol.me,limit=1] eyes positioned ^ ^ ^0.6 run function solstice:r5/los",
                        "tag @s remove sol.me",
                        f"execute if score #los {V} matches 1 run function solstice:r5/caught_c"])
    dp.fn("r5/los", [f"scoreboard players add #rs {V} 1",
                     f"execute if entity @a[tag=sol.me,distance=..1.2] run return run scoreboard players set #los {V} 1",
                     f"execute positioned ~ ~-1 ~ if entity @a[tag=sol.me,distance=..1.2] run return run scoreboard players set #los {V} 1",
                     "execute unless block ~ ~ ~ #solstice:seethrough run return 0",
                     f"execute if score #rs {V} matches 40.. run return 0",
                     "execute positioned ^ ^ ^0.5 run function solstice:r5/los"])
    dp.fn("r5/caught_c", [
        f"scoreboard players add #r5caught {V} 1",
        f"tp @s {C_CP[0]} {C_CP[1]} {C_CP[2]} {C_CP[3]} 0",
        "effect give @s blindness 2 0 true", "effect give @s darkness 5 0 true",
        "playsound minecraft:entity.warden.roar master @s ~ ~ ~ 0.6 1.6",
        *title("@s", "…", "L’Ombre vous a vu.", color="dark_red", times=(2, 30, 10)),
    ])

    # ---------------------------------------------------------------- ambiance, fausses alertes
    dp.fn("r5/ambient", [
        f"scoreboard players add #r5evt {V} 1",
        f"execute if score #r5evt {V} matches 500.. run function solstice:r5/event",
        f"execute if score #m20 {V} matches 0 run effect give @a[scores={{sol.room=5}}] darkness 3 0 true",
        f"execute if score #step {V} matches 1 if score #m20 {V} matches 0 as @e[type=marker,tag=sol.w5on] at @s run playsound minecraft:block.note_block.hat master @a[distance=..18] ~ ~ ~ 0.9 1.9",
        f"execute if score #step {V} matches 1 if score #m20 {V} matches 10 as @e[type=marker,tag=sol.w5on] at @s run playsound minecraft:block.comparator.click master @a[distance=..18] ~ ~ ~ 0.9 1.4",
        f"execute if score #sil {V} matches 1.. run scoreboard players remove #sil {V} 1",
        f"execute if score #sil {V} matches 1 as @e[type=armor_stand,tag=sol.r5sil] run data merge entity @s {{Invisible:1b}}",
    ])
    dp.fn("r5/event", [
        f"scoreboard players set #r5evt {V} 0",
        f"execute store result score #r5ev {V} run random value 0..4",
        f"execute if score #r5ev {V} matches 0 as @a[scores={{sol.room=5}}] at @s run playsound minecraft:block.stone.step master @s ^ ^ ^-3 1 0.7",
        f"execute if score #r5ev {V} matches 1 as @a[scores={{sol.room=5}}] at @s run playsound minecraft:ambient.soul_sand_valley.mood master @s ~ ~ ~ 1 0.6",
        f"execute if score #r5ev {V} matches 2 as @a[scores={{sol.room=5}}] at @s run playsound minecraft:block.wooden_door.close master @s ^3 ^ ^ 1 0.6",
        f"execute if score #r5ev {V} matches 3 as @a[scores={{sol.room=5}}] at @s run playsound minecraft:entity.allay.ambient_without_item master @s ^ ^ ^-5 0.5 0.3",
        f"execute if score #r5ev {V} matches 4 as @a[scores={{sol.room=5}}] at @s run playsound minecraft:block.bell.resonate master @s ~ ~10 ~ 0.4 0.4",
    ])
    dp.fn("r5/tick", [
        "execute as @e[type=interaction,tag=sol.r5i] at @s if data entity @s interaction run tag @s add sol.cur",
        "execute as @e[type=interaction,tag=sol.r5i] at @s if data entity @s attack run tag @s add sol.cur",
        "execute as @e[type=interaction,tag=sol.cur] at @s run function solstice:r5/clicked",
        "tag @e[type=interaction,tag=sol.cur] remove sol.cur",
        f"execute if score #veilon {V} matches 1 run function solstice:r5/veil_tick",
        f"execute if score #step {V} matches 3.. run function solstice:r5/shadow_tick",
        "function solstice:r5/ambient",
    ])
    dp.fn("r5/ptick", [f"execute if score @s sol.y matches ..95 run function solstice:r5/cp"])
    hint_fn(dp, 5, {
        1: ("Fermez les yeux… enfin, montez le son. Les tic-tac viennent de trois endroits.", "Les sous-titres du jeu (Options › Accessibilité) indiquent la direction des sons."),
        2: ("Elle ne bouge que si personne ne la regarde.", "Un joueur la fixe pendant que les autres ouvrent les verrous, puis on échange. Parlez-vous !"),
        3: ("La lumière de l’Ombre éclaire devant elle. Cachez-vous derrière les obstacles.", "Accroupi, on se fait discret. Le carnet du veilleur est dans sa loge, au sud-est de la place."),
        4: ("La cloche de l’aube ne sonne qu’à trois.", "Rejoignez tous le clocher, au nord, puis sonnez."),
    })
    for key, typ, desc in (("a", "sound-localization", "Salle 5 (voir SPOILERS)."), ("b", "watched-statue", "Salle 5 (voir SPOILERS)."),
                           ("c", "stealth-patrol", "Salle 5 (voir SPOILERS).")):
        dp.puzzle(5, key, typ, desc)
    dp.test("salle 5 : élément A", "entity @e[type=marker,tag=sol.w5spot]")
    dp.test("salle 5 : élément B", "entity @e[type=armor_stand,tag=sol.r5veil]")
    dp.test("salle 5 : élément C", "entity @e[type=armor_stand,tag=sol.r5sh]")
    dp.meta.setdefault("rooms", {})["5"] = {"cp": A_CP, "A": A, "B": B, "C": C, "b_cp": B_CP, "c_cp": C_CP, "locks": LOCKS,
                                            "lamps": LAMPS, "lodge": LODGE, "bell": BELL, "veil_home": VEIL_HOME, "patrol": PATROL}
