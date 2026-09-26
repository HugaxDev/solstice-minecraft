"""Salle 7 — Le Cœur du Calendrier (finale).
#step 1 : accusation (vote unanime en frappant une statue) · 2 : révélation · 3..5 : machine-boss, un système par
phase (opérateur tiré au sort, différent à chaque phase ; les deux autres le protègent) · 6 : Verrou brisé → fin.
#accuse : 1 Ysolde (bon), 2 Bram, 3 Lise · #good : 1 si bon choix (version complète, aide d’Ysolde).
Systèmes : 1 fusibles (transporter), 2 balancier (tenir la plate-forme), 3 point faible (révélé par la Lanterne)."""
import math

from .core import (V, T, jdump, tellraw, title, orel, narr, actionbar, fill, setblock, text_display, interaction,
                   Item, SC, say, sound, villager, item_display)
from .flow import obj
from .hints import hint_fn
from .roles import announce
from .build import disc, ring
from .story import CLUES
from .lantern import LPRED

OX, Y = 7000, 100
VOTE_CP = (7000.5, 101, 30.5, 180)
ARENA_CP = (7000.5, 101, 12.5, 180)
SUSPECTS = {1: ("Madame Ysolde", "dark_purple", (6994, 24), "librarian"),
            2: ("Bram", "dark_red", (7000, 22), "armorer"),
            3: ("Lise", "dark_green", (7006, 24), "farmer")}
CRATE = (6985, 0)
SOCKETS = [(6995, -2), (6995, 0), (6995, 2)]
PLATFORM = (7000, -9)
GEARS = [(7006, z) for z in (-5, -3, -1, 1, 3, 5)]
GATES = [(7000 + round(15 * math.cos(math.radians(a))), round(15 * math.sin(math.radians(a)))) for a in (45, 135, 225, 315)]
SYSNAME = {1: "Les fusibles", 2: "Le balancier", 3: "Le point faible"}
FUSE = Item("lightning_rod", "Fusible du Verrou", "gold", lore=["À enfoncer dans une prise de la machine."], data="{sol:{fuse:1b}}", glint=True, stack=1)
APPLE = Item("golden_apple", "Pomme dorée de Lise", "gold", lore=["Pour tenir le coup."], data="{sol:{apple:1b}}")
DIAL = Item("clock", "Cadran des Saisons", "gold", lore=["Accroupi, Cadran en main : ralentit les automates (recharge 45 s)."],
            data="{sol:{dial7:1b}}", glint=True)
DPRED = "clock[custom_data~{sol:{dial7:1b}}]"


def automaton(x, z, hard):
    hp = 26 if hard else 20
    typ = "zombie"
    speed = ',{id:"minecraft:generic.movement_speed",base:0.28d}' if hard else ""
    return (f"summon {typ} {x + 0.5} {Y + 1} {z + 0.5} {{Tags:[\"sol\",\"sol.mob\",\"sol.r7mob\"],PersistenceRequired:1b,IsBaby:0b,"
            f"DeathLootTable:\"minecraft:empty\",CustomName:'{jdump(T('Automate', 'gray'))}',CanPickUpLoot:0b,"
            f"ArmorItems:[{{}},{{}},{{id:\"minecraft:iron_chestplate\",count:1}},{{id:\"minecraft:iron_helmet\",count:1}}],"
            f"ArmorDropChances:[0f,0f,0f,0f],attributes:[{{id:\"minecraft:generic.follow_range\",base:40d}},"
            f"{{id:\"minecraft:generic.max_health\",base:{hp}d}}{speed}],Health:{hp}f}}")


def build(dp):
    b = ["kill @e[type=!player,tag=sol.r7]"]
    b += fill(OX - 30, 90, -30, OX + 30, 130, 40, "air")
    # antichambre du vote
    b += fill(6988, Y - 1, 19, 7012, Y + 7, 34, "polished_blackstone_bricks")
    b += fill(6989, Y + 1, 20, 7011, Y + 6, 33, "air")
    b += fill(6989, Y, 20, 7011, Y, 33, "polished_deepslate")
    b += fill(6999, Y + 1, 19, 7001, Y + 4, 19, "iron_bars")
    for k, (name, color, (x, z), prof) in SUSPECTS.items():
        b.append(setblock(x, Y, z, "chiseled_polished_blackstone"))
    b.append(text_display(7000.5, Y + 5, 20.2, ["", T("Qui a saboté le Grand Calendrier ?\n", "gold", bold=True),
                                                 T("Frappez la statue du coupable. Le vote doit être unanime.", "gray")],
                          ["sol.r7"], scale=0.7, billboard="fixed", yaw=0))
    # arène du Cœur
    b += disc(OX, Y - 1, 0, 18, "deepslate_tiles")
    b += disc(OX, Y, 0, 17, "polished_deepslate")
    for h in range(1, 14):
        b += ring(OX, Y + h, 0, 18, "polished_blackstone_bricks" if h % 4 else "chiseled_polished_blackstone")
    b += fill(6999, Y + 1, 17, 7001, Y + 4, 19, "air")
    # le Verrou (machine centrale)
    b += fill(6997, Y + 1, -3, 7003, Y + 9, 3, "copper_block")
    b += fill(6998, Y + 10, -2, 7002, Y + 12, 2, "oxidized_copper")
    b += fill(6996, Y + 4, -1, 6996, Y + 8, 1, "white_concrete")
    b += fill(6996, Y + 6, 0, 6996, Y + 7, 0, "black_concrete")
    for (x, z) in SOCKETS:
        b.append(setblock(x + 1, Y + 1, z, "polished_blackstone"))
    b.append(setblock(CRATE[0], Y + 1, CRATE[1], "barrel[facing=east]"))
    px, pz = PLATFORM
    b += fill(px - 1, Y, pz - 1, px + 1, Y, pz + 1, "gold_block")
    b += fill(px, Y + 7, pz, px, Y + 11, pz, "chain")
    for (x, z) in GEARS:
        b.append(setblock(x - 1, Y + 2, z, "waxed_copper_grate"))
    for (gx, gz) in GATES:
        b.append(setblock(gx, Y, gz, "crying_obsidian"))
    dp.meta.setdefault("builds", []).append("build/r7")
    dp.meta.setdefault("forceload", []).append((OX - 30, -30, OX + 30, 40))

    # ------------------------------------------------------------ entités
    e = ["kill @e[type=!player,tag=sol.r7d]"]

    def it(x, y, z, key, w=1.3, h=1.3):
        e.append(interaction(x, y, z, ["sol.r7", "sol.r7d", "sol.r7i", f"sol.k7_{key}"], w, h))
    for k, (name, color, (x, z), prof) in SUSPECTS.items():
        e.append(villager(x + 0.5, Y + 1, z + 0.5, name, color, ["sol.r7", "sol.r7d", f"sol.sus{k}"], profession=prof, yaw=180))
        it(x + 0.5, Y + 0.95, z + 0.5, f"sus{k}", 1.3, 2.3)
    it(CRATE[0] + 0.5, Y + 0.95, CRATE[1] + 0.5, "crate")
    for i, (x, z) in enumerate(SOCKETS):
        it(x + 0.5, Y + 0.95, z + 0.5, f"sock{i}", 1.0, 1.3)
    for i, (x, z) in enumerate(GEARS):
        e.append(item_display(x - 0.3, Y + 2.5, z + 0.5, Item("clock"), ["sol.r7", "sol.r7d", f"sol.gear{i}"], 1.2, billboard="fixed"))
        it(x + 0.2, Y + 1.9, z + 0.5, f"gear{i}", 1.0, 1.2)
    # tableau d’enquête : un panneau par indice trouvé
    board = []
    for i, (cid, room, t, text, icon) in enumerate(CLUES):
        board.append(f"execute if score #clue_{cid} {V} matches 1 run " + text_display(
            7010.9, Y + 4.6 - 0.62 * (i % 6), 31.5 - 6 * (i // 6), ["", T(f"• {t}", "yellow")], ["sol.r7", "sol.r7d"], scale=0.45,
            billboard="fixed", yaw=90, line_width=260))
    board.append(text_display(7010.9, Y + 5.4, 28.5, ["", T("Tableau d’enquête", "gold", bold=True), T("\n(détails dans votre Carnet)", "gray")],
                              ["sol.r7", "sol.r7d"], scale=0.55, billboard="fixed", yaw=90))
    dp.fn("r7/board", board)
    e.append("function solstice:r7/board")
    dp.fn("r7/entities", e)
    dp.fn("build/r7", b + ["function solstice:r7/entities"])

    # ------------------------------------------------------------ accusation
    dp.fn("r7/start", [
        "function solstice:r7/entities",
        f"execute unless score #lantern {V} matches 1 run scoreboard players set #lantern {V} 1",
        *[f"scoreboard players set {f} {V} 0" for f in ("#accuse", "#good", "#votes", "#votefail", "#r7t", "#phase", "#sys", "#fuses",
                                                       "#hold", "#hits", "#pulse", "#yhelp", "#r7done", "#r7w")],
        *fill(6999, Y + 1, 19, 7001, Y + 4, 19, "iron_bars"),
        "execute as @a run scoreboard players set @s sol.vote 0",
        f"scoreboard players set #step {V} 1", "function solstice:r7/obj",
        orel("Nous y sommes : le Cœur du Calendrier. Avant de le réparer… il faut savoir à qui on a affaire. "
             "Regardez le tableau, relisez votre Carnet, et désignez le coupable. Tous d’accord, hein."),
    ])
    for k, (name, color, _, _) in SUSPECTS.items():
        dp.fn(f"r7/c/sus{k}", [
            f"execute unless score #step {V} matches 1 run return 0",
            f"scoreboard players set @s sol.vote {k}",
            tellraw("@a", {"selector": "@s", "color": "white"}, T(" désigne ", "gray"), T(name, color, bold=True), T(".", "gray")),
            "playsound minecraft:block.stone.hit master @a ~ ~ ~ 1 0.6",
            "function solstice:r7/count_votes"])
    dp.fn("r7/count_votes", [
        f"execute store result score #votes {V} if entity @a[scores={{sol.vote=1..3}}]",
        f"execute if score #votes {V} < #np {V} run return run " + actionbar("@a", ["", T("Votes : ", "gold"), SC("#votes"), T(" / ", "gray"), SC("#np")]),
        f"scoreboard players set #accuse {V} 0",
        *[f"execute store result score #v{k} {V} if entity @a[scores={{sol.vote={k}}}]" for k in SUSPECTS],
        *[f"execute if score #v{k} {V} = #np {V} run scoreboard players set #accuse {V} {k}" for k in SUSPECTS],
        f"execute if score #accuse {V} matches 0 run return run function solstice:r7/disagree",
        "function solstice:r7/verdict"])
    dp.fn("r7/disagree", [f"scoreboard players add #votefail {V} 1", "execute as @a run scoreboard players set @s sol.vote 0",
                          tellraw("@a", T("Les statues restent de marbre : vous n’êtes pas d’accord. Discutez, puis votez à nouveau — tous pour la même personne.", "red")),
                          "playsound minecraft:block.note_block.bass master @a ~ ~ ~ 1 0.5"])
    dp.fn("r7/verdict", [
        f"scoreboard players set #step {V} 2", f"scoreboard players set #r7t {V} 0",
        f"execute if score #accuse {V} matches 1 run scoreboard players set #good {V} 1",
        f"execute if score #good {V} matches 1 if score #votefail {V} matches 0 run function solstice:challenge/grant_fin_limier",
        "function solstice:r7/obj"])
    # révélation (courte), selon le verdict
    rv_good = [(20, [say("Madame Ysolde", "dark_purple", "…Oui. C’est moi. J’ai retiré les quatre cristaux, à minuit. Et je recommencerais.")]),
               (110, [say("Madame Ysolde", "dark_purple", "Je vous expliquerai tout. Mais à minuit, le Cœur va se verrouiller. Ce n’est pas le Calendrier qu’il faut briser : c’est le VERROU accroché à son cœur.")]),
               (210, [say("Madame Ysolde", "dark_purple", "Je reste avec vous. Quand les automates vous serreront de trop près, je les figerai."),
                      orel("Ysolde… ? Qu’est-ce que… Non, non, attendez, ne touchez pas au… Bon. Bon."),
                      "function solstice:r7/fight"])]
    rv_bad = [(20, [tellraw("@a", T("La statue accusée proteste : ", "gray"), T("« Ce n’est pas moi ! Cette nuit-là, j’étais à la serre ! »", "white", italic=True))]),
              (110, [orel("Peu importe, peu importe ! Le Cœur est complet… laissez-le faire, voilà tout. Laissez-le se refermer.")]),
              (200, [narr("Le Cœur gronde. Quelque chose s’enclenche trop tôt, et la machine se défend.", "@a", "red"),
                     "function solstice:r7/fight"])]
    for tag, steps in (("good", rv_good), ("bad", rv_bad)):
        body = []
        for tt, cmds in steps:
            sub = dp.fn(f"r7/rv_{tag}/t{tt}", cmds)
            body.append(f"execute if score #r7t {V} matches {tt} run function {sub}")
        dp.fn(f"r7/rv_{tag}", body)

    # ------------------------------------------------------------ combat
    dp.fn("r7/fight", [
        *fill(6999, Y + 1, 19, 7001, Y + 4, 19, "air"),
        "kill @e[type=!player,tag=sol.ysolde]",
        f"scoreboard players set #phase {V} 0", "tag @a remove sol.prev",
        # ordre des systèmes tiré au sort
        f"execute store result score #ord {V} run random value 0..5",
        *[f"execute if score #ord {V} matches {i} run function solstice:r7/ord{i}" for i in range(6)],
        "execute as @a run function solstice:r7/kit",
        f"execute if score #good {V} matches 1 run summon villager 7000.5 101 14.5 {{Tags:[\"sol\",\"sol.r7\",\"sol.r7d\",\"sol.ysolde\"],"
        f"NoAI:1b,Invulnerable:1b,Silent:1b,CustomNameVisible:1b,CustomName:'{jdump(T('Madame Ysolde', 'dark_purple', bold=True))}',"
        f"VillagerData:{{profession:\"minecraft:librarian\",level:5,type:\"minecraft:plains\"}},Offers:{{Recipes:[]}}}}",
        "function solstice:r7/next_phase",
    ])
    import itertools
    for i, perm in enumerate(itertools.permutations((1, 2, 3))):
        dp.fn(f"r7/ord{i}", [f"scoreboard players set #sysA {V} {perm[0]}", f"scoreboard players set #sysB {V} {perm[1]}",
                             f"scoreboard players set #sysC {V} {perm[2]}"])
    dp.fn("r7/kit", [f"execute unless items entity @s container.* {DPRED} run give @s {DIAL.give()}",
                     f"give @s {APPLE.give()} 2", "effect give @s instant_health 1 3 true"])
    dp.fn("r7/next_phase", [
        f"scoreboard players add #phase {V} 1",
        f"execute if score #phase {V} matches 4.. run return run function solstice:r7/broken",
        f"scoreboard players set #fuses {V} 0", f"scoreboard players set #hold {V} 0", f"scoreboard players set #hits {V} 0",
        f"execute if score #phase {V} matches 1 run scoreboard players operation #sys {V} = #sysA {V}",
        f"execute if score #phase {V} matches 2 run scoreboard players operation #sys {V} = #sysB {V}",
        f"execute if score #phase {V} matches 3 run scoreboard players operation #sys {V} = #sysC {V}",
        f"execute store result score #weak {V} run random value 0..5",
        "kill @e[type=!player,tag=sol.r7mob]", "kill @e[type=!player,tag=sol.weakink]", "clear @a lightning_rod[custom_data~{sol:{fuse:1b}}]",
        *[f"execute if score #weak {V} matches {i} run " + text_display(x + 0.9, Y + 3.4, z + 0.5, ["", T("✦ point faible ✦", "aqua", bold=True)],
                                                                          ["sol.r7", "sol.r7d", "sol.ink", "sol.weakink"], scale=0.6, billboard="fixed", yaw=-90, hidden=True, bg=0)
          for i, (x, z) in enumerate(GEARS)],
        f"scoreboard players set #noheal {V} 1", "function solstice:roles/draw", f"scoreboard players set #noheal {V} 0",
        "tag @a[scores={sol.role=1}] add sol.prev",
        "function solstice:r7/announce",
        f"scoreboard players operation #step {V} = #phase {V}", f"scoreboard players add #step {V} 2",
        "function solstice:hints/reset", "function solstice:r7/obj",
        "execute as @a run effect give @s instant_health 1 2 true",
        *[f"execute if score #sys {V} matches {s} run " + tellraw("@a", T(f"⚙ Système à désactiver : {SYSNAME[s]}", "gold", bold=True),
                                                                   T(" — par l’Opérateur ", "gray"), {"selector": "@a[tag=sol.ro1]", "color": "white"},
                                                                   T(" ; les autres le protègent !", "gray")) for s in SYSNAME],
    ])
    announce(dp, "r7/announce", [("Opérateur", "gold", "À vous de désactiver ce système ! Les autres vous protègent."),
                                 ("Garde du corps", "red", "Protégez l’Opérateur des automates."),
                                 ("Garde du corps", "red", "Protégez l’Opérateur des automates.")], "light_purple")
    dp.fn("r7/sys_down", [
        "execute as @a at @s run playsound minecraft:block.beacon.deactivate master @s ~ ~ ~ 1 0.8",
        *title("@a", "Système désactivé !", "Le Verrou vacille…", color="gold", times=(5, 40, 10)),
        "particle minecraft:explosion 7000.5 106 0.5 2 2 2 0 6 force",
        "function solstice:r7/next_phase"])
    dp.fn("r7/broken", [f"scoreboard players set #step {V} 6", f"scoreboard players set #r7done {V} 1",
                        "kill @e[type=!player,tag=sol.r7mob]", *fill(6997, Y + 1, -3, 7003, Y + 12, 3, "air"),
                        "particle minecraft:explosion_emitter 7000.5 105 0.5 1 1 1 0 3 force",
                        "execute as @a at @s run playsound minecraft:entity.generic.explode master @s ~ ~ ~ 1 0.6",
                        "function solstice:end/start"])
    # --- système 1 : fusibles
    dp.fn("r7/c/crate", [f"execute unless score #sys {V} matches 1 run return run " + actionbar("@s", "Une caisse de fusibles. Inutile pour l’instant.", "gray"),
                         f"execute unless entity @s[tag=sol.ro1] run return run " + actionbar("@s", "Seul l’Opérateur manipule les fusibles.", "red"),
                         f"execute if items entity @s container.* lightning_rod[custom_data~{{sol:{{fuse:1b}}}}] run return run " + actionbar("@s", "Un fusible à la fois !", "gold"),
                         f"give @s {FUSE.give()}", "playsound minecraft:item.armor.equip_chain master @a ~ ~ ~ 1 1"])
    for i in range(3):
        dp.fn(f"r7/c/sock{i}", [
            f"execute unless score #sys {V} matches 1 run return 0",
            f"execute unless entity @s[tag=sol.ro1] run return run " + actionbar("@s", "Seul l’Opérateur manipule les fusibles.", "red"),
            f"execute if score #sock{i} {V} matches 1 run return run " + actionbar("@s", "Cette prise est déjà remplie.", "gray"),
            f"execute unless items entity @s weapon.* lightning_rod[custom_data~{{sol:{{fuse:1b}}}}] run return run " + actionbar("@s", "Il faut un fusible (caisse à l’ouest).", "gold"),
            "clear @s lightning_rod[custom_data~{sol:{fuse:1b}}] 1", f"scoreboard players set #sock{i} {V} 1", f"scoreboard players add #fuses {V} 1",
            "playsound minecraft:block.copper_bulb.turn_on master @a ~ ~ ~ 1 1",
            f"execute if score #fuses {V} matches 3 run function solstice:r7/sys_down"])
    dp.add("r7/next_phase", [f"scoreboard players set #sock{i} {V} 0" for i in range(3)])
    # --- système 2 : balancier (tenir la plate-forme 15 s au total)
    dp.fn("r7/hold_tick", [
        f"execute if entity @a[tag=sol.ro1,tag=!sol.dn,x={px - 1},y={Y + 1},z={pz - 1},dx=2,dy=1,dz=2] run scoreboard players add #hold {V} 1",
        f"execute if score #m20 {V} matches 0 as @a run " + actionbar("@s", ["", T("Balancier : ", "gold"), SC("#hold"), T(" / 300", "gray")]),
        f"execute if score #hold {V} matches 300.. run function solstice:r7/sys_down"])
    # --- système 3 : point faible (à la Lanterne)
    for i in range(6):
        dp.fn(f"r7/c/gear{i}", [
            f"execute unless score #sys {V} matches 3 run return 0",
            f"execute unless entity @s[tag=sol.ro1] run return run " + actionbar("@s", "Seul l’Opérateur peut frapper les engrenages.", "red"),
            f"execute unless score #weak {V} matches {i} run return run function solstice:r7/shock",
            f"scoreboard players add #hits {V} 1", "playsound minecraft:block.anvil.land master @a ~ ~ ~ 1 1.4",
            "particle minecraft:crit ~ ~0.5 ~ 0.3 0.3 0.3 0.2 20",
            f"execute if score #hits {V} matches 3 run function solstice:r7/sys_down"])
    dp.fn("r7/shock", [f"scoreboard players set #hits {V} 0", "damage @s 3 minecraft:lightning_bolt",
                       "playsound minecraft:entity.lightning_bolt.impact master @a ~ ~ ~ 0.5 1.6",
                       actionbar("@s", "Mauvais engrenage ! Le Verrou vous électrise. (La Lanterne montre le point faible.)", "red")])
    # --- vagues d’automates, onde du Verrou, aide d’Ysolde, Cadran
    wave = [f"execute store result score #mobs {V} if entity @e[tag=sol.r7mob]",
            f"scoreboard players set #cap {V} 4", f"execute if score #good {V} matches 0 run scoreboard players set #cap {V} 7",
            f"scoreboard players operation #cap {V} += #phase {V}",
            f"execute if score #mobs {V} >= #cap {V} run return 0",
            f"execute store result score #g {V} run random value 0..3"]
    for gi, (gx, gz) in enumerate(GATES):
        wave.append(f"execute if score #g {V} matches {gi} if score #good {V} matches 1 run " + automaton(gx, gz, False))
        wave.append(f"execute if score #g {V} matches {gi} if score #good {V} matches 0 run " + automaton(gx, gz, True))
    dp.fn("r7/wave", wave)
    dp.fn("r7/pulse_warn", ["particle minecraft:electric_spark 7000.5 101.5 0.5 3 0.3 3 0.2 120 force",
                            "execute as @a at @s run playsound minecraft:block.beacon.power_select master @s ~ ~ ~ 1 0.5",
                            actionbar("@a", "⚡ Le Verrou se charge : éloignez-vous du centre !", "red")])
    dp.fn("r7/pulse", ["execute positioned 7000.5 101 0.5 as @a[distance=..7,gamemode=adventure] run damage @s 5 minecraft:magic",
                       "particle minecraft:sonic_boom 7000.5 102 0.5 2 0.2 2 0 12 force",
                       "execute as @a at @s run playsound minecraft:entity.warden.sonic_boom master @s ~ ~ ~ 0.6 1.2"])
    dp.fn("r7/ysolde", ["effect give @e[tag=sol.r7mob] slowness 4 6 true", "effect give @e[tag=sol.r7mob] glowing 4 0 true",
                        "effect give @a regeneration 3 1 true",
                        say("Madame Ysolde", "dark_purple", "Figez-vous !"),
                        "execute as @e[tag=sol.ysolde] at @s run particle minecraft:enchant ~ ~2 ~ 1 1 1 1 60 force"])
    dp.fn("r7/dial", ["execute if score @s sol.t matches 1.. run return run " + actionbar("@s", ["", T("Cadran : recharge… ", "gold"), SC("@s", "sol.t")]),
                      "scoreboard players set @s sol.t 900", "effect give @e[tag=sol.r7mob] slowness 5 4 true",
                      "particle minecraft:end_rod ~ ~1 ~ 3 1 3 0.02 40", "playsound minecraft:block.amethyst_block.resonate master @a ~ ~ ~ 1 0.6",
                      actionbar("@s", "Le temps ralentit autour des automates !", "gold")])
    dp.fn("r7/tick", [
        "execute as @e[type=interaction,tag=sol.r7i] at @s if data entity @s interaction run function solstice:r7/clicked",
        "execute as @e[type=interaction,tag=sol.r7i] at @s if data entity @s attack run function solstice:r7/clicked",
        f"scoreboard players add #r7t {V} 1",
        f"execute if score #step {V} matches 2 if score #good {V} matches 1 run function solstice:r7/rv_good",
        f"execute if score #step {V} matches 2 if score #good {V} matches 0 run function solstice:r7/rv_bad",
        f"execute unless score #step {V} matches 3..5 run return 0",
        f"scoreboard players add #r7w {V} 1",
        f"execute if score #good {V} matches 1 if score #r7w {V} matches 140.. run function solstice:r7/wave_go",
        f"execute if score #good {V} matches 0 if score #r7w {V} matches 90.. run function solstice:r7/wave_go",
        f"scoreboard players add #pulse {V} 1",
        f"execute if score #good {V} matches 1 if score #pulse {V} matches 280 run function solstice:r7/pulse_warn",
        f"execute if score #good {V} matches 1 if score #pulse {V} matches 320.. run function solstice:r7/pulse_go",
        f"execute if score #good {V} matches 0 if score #pulse {V} matches 180 run function solstice:r7/pulse_warn",
        f"execute if score #good {V} matches 0 if score #pulse {V} matches 220.. run function solstice:r7/pulse_go",
        f"execute if score #good {V} matches 1 run scoreboard players add #yhelp {V} 1",
        f"execute if score #yhelp {V} matches 400.. run function solstice:r7/ysolde_go",
        f"execute if score #sys {V} matches 2 run function solstice:r7/hold_tick",
        "execute as @e[tag=sol.r7mob] at @s unless entity @s[x=6980,y=95,z=-20,dx=40,dy=30,dz=40] run tp @s 7000 101 10",
    ])
    dp.fn("r7/wave_go", [f"scoreboard players set #r7w {V} 0", "function solstice:r7/wave"])
    dp.fn("r7/pulse_go", [f"scoreboard players set #pulse {V} 0", "function solstice:r7/pulse"])
    dp.fn("r7/ysolde_go", [f"scoreboard players set #yhelp {V} 0", "function solstice:r7/ysolde"])
    keys = [f"sus{k}" for k in SUSPECTS] + ["crate"] + [f"sock{i}" for i in range(3)] + [f"gear{i}" for i in range(6)]
    clk = []
    for k in keys:
        clk.append(f"execute if entity @s[tag=sol.k7_{k}] if data entity @s interaction on target run function solstice:r7/cc/{k}")
        clk.append(f"execute if entity @s[tag=sol.k7_{k}] if data entity @s attack on attacker run function solstice:r7/cc/{k}")
        dp.fn(f"r7/cc/{k}", ["execute if score @s sol.cool matches 1.. run return 0", "scoreboard players set @s sol.cool 8",
                             f"function solstice:r7/c/{k}"])
    clk += ["data remove entity @s interaction", "data remove entity @s attack"]
    dp.fn("r7/clicked", clk)
    dp.fn("r7/ptick", [
        "execute if score @s sol.t matches 1.. run scoreboard players remove @s sol.t 1",
        f"execute if score #step {V} matches 3..5 if items entity @s weapon.mainhand {DPRED} if score @s sol.sneak matches 1.. at @s run function solstice:r7/dial",
        "scoreboard players set @s sol.sneak 0",
        f"execute if score @s sol.y matches ..94 run function solstice:r7/cp",
    ])
    dp.fn("r7/cp", [f"execute if score #step {V} matches ..2 run tp @s {VOTE_CP[0]} {VOTE_CP[1]} {VOTE_CP[2]} {VOTE_CP[3]} 0",
                    f"execute if score #step {V} matches 3.. run tp @s {ARENA_CP[0]} {ARENA_CP[1]} {ARENA_CP[2]} {ARENA_CP[3]} 0",
                    f"spawnpoint @s {int(ARENA_CP[0])} {ARENA_CP[1]} {int(ARENA_CP[2])}"])
    dp.fn("r7/enter", ["function solstice:r7/cp", "effect give @s night_vision infinite 0 true",
                       f"execute if score #step {V} matches 3..5 run function solstice:r7/kit"])
    dp.fn("r7/respawn", ["function solstice:r7/cp"])
    dp.fn("r7/wipe", [
        "kill @e[type=!player,tag=sol.r7mob]",
        tellraw("@a", T("Le Verrou vous a tous renversés. Le combat reprend depuis le début ; votre verdict est conservé.", "gray")),
        f"execute if score #step {V} matches 3..5 run function solstice:r7/fight"])
    dp.fn("r7/on_complete", [])
    dp.fn("r7/obj", [
        f"execute if score #step {V} matches 1 run bossbar set solstice:obj name " + jdump(["", T("◆ ", "gold"), T("Désignez le coupable : frappez sa statue (vote unanime)", "white")]),
        f"execute if score #step {V} matches 2 run bossbar set solstice:obj name " + jdump(["", T("◆ ", "gold"), T("…", "white")]),
        f"execute if score #step {V} matches 3..5 run bossbar set solstice:obj name " + jdump(["", T("◆ ", "gold"), T("Brisez le Verrou : système ", "white"),
                                                                                                SC("#phase", color="gold"), T(" / 3 — l’Opérateur agit, les autres le protègent", "white")]),
    ])
    hint_fn(dp, 7, {
        1: ("Relisez votre Carnet : certains indices mentent, d’autres se recoupent. Où était chacun à minuit ?",
            "Les objets qui accusent Bram et Lise viennent tous… du même endroit. Et qui écrit à l’encre bleue ?"),
        3: ("L’Opérateur agit, les deux autres tiennent les automates à distance.", "Fusibles : caisse à l’ouest, prises sur la machine. Balancier : tenir la plate-forme dorée. Point faible : la Lanterne le révèle."),
        4: ("Changez les rôles : l’Opérateur n’est plus le même.", "Fusibles : caisse à l’ouest, prises sur la machine. Balancier : tenir la plate-forme dorée. Point faible : la Lanterne le révèle."),
        5: ("Dernier système !", "Fusibles : caisse à l’ouest, prises sur la machine. Balancier : tenir la plate-forme dorée. Point faible : la Lanterne le révèle."),
    })
    for key, typ, desc in (("vote", "vote-unanimous", "Accusation : vote unanime en frappant une statue."),
                           ("f", "boss-carry-fuses", "Machine : transporter trois fusibles vers les prises sous la pression des automates."),
                           ("h", "boss-hold-zone", "Machine : tenir la plate-forme du balancier 15 secondes."),
                           ("w", "boss-weakpoint-lantern", "Machine : frapper le point faible révélé par la Lanterne.")):
        dp.puzzle(7, key, typ, desc)
    dp.test("finale : trois statues des suspects", "entity @e[type=interaction,tag=sol.k7_sus3]")
    dp.test("finale : prises à fusibles", "entity @e[type=interaction,tag=sol.k7_sock2]")
    dp.test("finale : engrenages", "entity @e[type=interaction,tag=sol.k7_gear5]")
    dp.meta.setdefault("rooms", {})["7"] = {"cp": VOTE_CP, "arena_cp": ARENA_CP, "suspects": {k: v[2] for k, v in SUSPECTS.items()},
                                            "crate": CRATE, "sockets": SOCKETS, "platform": PLATFORM, "gears": GEARS}

    # ------------------------------------------------------------ cinématique de fin (utilisée par ending.py)
    G = f"execute if score #good {V} matches 1 run "
    B = f"execute if score #good {V} matches 0 run "
    cine = [
        (20, [*title("@a", "Le Verrou est brisé", "Le Cœur du Calendrier bat de nouveau", color="light_purple", times=(10, 70, 20))]),
        (80, [B + say("Madame Ysolde", "dark_purple", "Attendez ! Ne cherchez plus. C’est moi qui ai retiré les cristaux, la nuit du solstice. Pas Bram, pas Lise."),
              G + say("Madame Ysolde", "dark_purple", "Merci. Maintenant, vous méritez toute la vérité.")]),
        (180, [say("Madame Ysolde", "dark_purple", "La charte des gardiens est claire : au solstice de sa centième année, le gardien quitte Brumeval et rejoint les saisons. Ce solstice-ci était celui d’Orel.")]),
        (290, [say("Madame Ysolde", "dark_purple", "Il n’a pas voulu partir. Il a construit ce Verrou pour figer le dernier jour, pour toujours. "
                   "J’ai trouvé les plans sous son établi. Je l’ai supplié… puis j’ai volé les cristaux, pour que le Verrou ne puisse pas se fermer.")]),
        (400, [say("Madame Ysolde", "dark_purple", "Le marteau de Bram, les graines de Lise : je les avais prises à la bibliothèque. Pardon à eux. Il fallait gagner du temps.")]),
        (500, [orel("…C’est vrai. Tout est vrai. Je voulais un jour sans fin, avec vous tous dedans. Un jour sans printemps, aussi. J’avais oublié ce détail."),
               "execute as @a at @s run playsound minecraft:block.bell.resonate master @s ~ ~ ~ 0.6 0.6"]),
        (610, [orel("Vous avez eu raison. Le temps doit passer. Même le mien. Et puis… trois voyageurs, c’est un bon nombre pour une fin.")]),
        (700, [*title("@a", "Les saisons se remettent en ordre", "Printemps · Été · Automne · Hiver", color="green", times=(10, 80, 20)),
               "function solstice:r7/seasons1"]),
        (760, ["function solstice:r7/seasons2", "function solstice:r7/fireworks"]),
        (820, ["function solstice:r7/seasons3", "function solstice:r7/fireworks"]),
        (880, ["function solstice:r7/seasons4", "function solstice:r7/fireworks"]),
        (940, ["function solstice:r7/seasons1", "function solstice:r7/fireworks",
               narr("Au printemps suivant, Maître Orel rejoignit les saisons. On dit qu’à Brumeval, chaque fleur fait un peu tic-tac.", "@a", "white")]),
        (1040, [G + narr("Madame Ysolde garde la bibliothèque… et le Calendrier, désormais. Bram lui a forgé une clé. Lise lui a offert un tournesol géant.", "@a", "white"),
                B + narr("Bram et Lise ont pardonné. Il leur a fallu un hiver entier, et beaucoup de soupe.", "@a", "white")]),
    ]
    SEAS = {1: ("pink_petals[flower_amount=4]", "cherry_leaves"), 2: ("short_grass", "happy_villager"),
            3: ("dead_bush", "falling_dust{block_state:\"minecraft:orange_terracotta\"}"), 4: ("snow", "snowflake")}
    for k, (blk, part) in SEAS.items():
        dp.fn(f"r7/seasons{k}", [f"fill 6985 101 -15 7015 101 15 air replace pink_petals", f"fill 6985 101 -15 7015 101 15 air replace short_grass",
                                 f"fill 6985 101 -15 7015 101 15 air replace dead_bush", f"fill 6985 101 -15 7015 101 15 air replace snow",
                                 f"fill 6988 101 -12 7012 101 12 {blk} replace air",
                                 f"particle minecraft:{part} 7000.5 106 0.5 10 4 10 0 300 force",
                                 "execute as @a at @s run playsound minecraft:block.amethyst_block.chime master @s ~ ~ ~ 1 " + ["", "1.2", "1.0", "0.8", "0.6"][k]])
    colors = [16711680, 16766720, 65280, 3381759, 16733695]
    fw = []
    for i, (x, z) in enumerate(((6992, -8), (7008, -8), (6992, 8), (7008, 8), (7000, 0))):
        fw.append(f"summon firework_rocket {x} 104 {z} {{LifeTime:20,FireworksItem:{{id:\"minecraft:firework_rocket\",count:1,components:"
                  f"{{\"minecraft:fireworks\":{{flight_duration:1,explosions:[{{shape:\"large_ball\",colors:[I;{colors[i]}],"
                  f"fade_colors:[I;16777215],has_twinkle:1b}}]}}}}}}}}")
    dp.fn("r7/fireworks", fw)
    return cine
