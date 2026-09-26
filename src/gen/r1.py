"""Salle 1 — L’Express du Solstice. Le train ne s’arrête jamais. Rôles tirés au sort :
r1 Aiguilleur (voit les panneaux à l’avant, règle l’aiguillage), r2 Chauffeur (charbon, chaudière, soupape),
r3 Garde-barrière (feuille de route, manivelle des barrières, repousse les Brumeux).

Le trajet = 9 tronçons de 1400 unités (#dist). Vitesse 0..3 selon la pression (#press). Chaque tronçon contient
des évènements (bifurcation, passage à niveau, virage/viaduc à vitesse lente, tunnel en montée, Brumeux).
Erreur → le train recule au début du tronçon (#errors +1). Personne ne meurt."""
from .core import (V, T, jdump, tellraw, title, orel, narr, actionbar, fill, setblock, text_display, interaction,
                   Item, sound, SC, item_display, snbt_str)
from .flow import obj
from .hints import hint_fn
from .roles import announce

OX, Y = 1000, 100
SEC = 1400
NSEC = 9
# tronçon -> évènements (position relative, type, paramètre)
FORKS = {1: ("Clocher-Vieux", "Marais-Noir"), 2: ("Pont-des-Brumes", "Hautes-Friches"), 3: ("Val-d’Automne", "Val-d’Été"),
         4: ("Col-Givré", "Col-Brûlé"), 5: ("Pic du Solstice", "Mine-Morte")}
ROUTE = ["Là où sonnent les heures.", "Là où l’eau devient nuage.", "Là où les feuilles tombent.",
         "Là où le souffle gèle.", "Là où le jour est le plus long."]
SECTIONS = {
    1: [(1100, "cross", 1)],
    2: [(300, "board", 2), (1000, "fork", 1)],
    3: [(500, "lim_on", "Virage du Ravin"), (1100, "lim_off", None), (1300, "cross", 2)],
    4: [(200, "board", 3), (900, "fork", 2)],
    5: [(400, "board", 2), (1200, "tunnel", None)],
    6: [(700, "fork", 3), (1200, "cross", 3)],
    7: [(300, "lim_on", "Viaduc des Brumes"), (900, "lim_off", None), (1000, "board", 4)],
    8: [(600, "fork", 4), (1100, "cross", 4)],
    9: [(800, "fork", 5), (1399, "arrive", None)],
}
SIGN_AHEAD = 700

# poste de chaque rôle (checkpoint) et éléments
CP = {0: (1000.5, 101, 0.5, 90), 1: (980.5, 101, 0.5, 90), 2: (986.5, 101, 0.5, 90), 3: (1016.5, 101, 0.5, -90)}
BTN_L = (978.5, 101, -1.5)
BTN_R = (978.5, 101, 2.5)
FIREBOX = (984.6, 101, 0.5)
VALVE = (984.6, 101, -1.5)
COAL = (991.5, 101, -1.5)
HAMMER = (993.5, 101.4, 1.6)
CRANK = (1013.5, 101, -1.5)
SIGN = (974.4, 103.2, 0.5)
BOARD_SPAWN = [(1024.5, 101, -1.5), (1024.5, 101, 1.5), (1023.5, 101, 0.5), (1025.5, 101, 0.5)]

COAL_I = Item("coal", "Pelletée de charbon", "dark_gray", lore=["Pour la chaudière."], data="{sol:{coal:1b}}", stack=4)
BROOM = Item("stick", "Balai du garde", "yellow", lore=["Pour repousser ce qui monte à bord."], data="{sol:{broom:1b}}",
             glint=True, extra={"enchantments": "{levels:{\"minecraft:knockback\":3}}"})
ROUTE_BOOK = Item("written_book", data="{sol:{route:1b}}", extra={
    "written_book_content": "{title:'Feuille de route',author:'Maître Orel',pages:[" + ",".join(snbt_str(jdump(p)) for p in [
        ["", T("Feuille de route\nde l’Express\n\n", "dark_blue", bold=True),
         T("Brumeval → Pic du Solstice\n\n", "black"),
         T("À chaque bifurcation, l’Aiguilleur voit deux noms. Dites-lui lequel prendre.", "dark_gray")],
        ["", T("Les cinq bifurcations\n\n", "dark_blue", bold=True)] +
        [T(f"{i}. {r}\n\n", "black") for i, r in enumerate(ROUTE, 1)],
        ["", T("Rappels du garde\n\n", "dark_blue", bold=True),
         T("• Passage à niveau : 3 tours de manivelle AVANT d’y arriver.\n\n", "black"),
         T("• Brumeux à bord : poussez-les dehors avec le balai.\n\n", "black"),
         T("• Virages, viaducs : on ralentit. Tunnels : pleine pression.", "black")]]) + "]}"})
ROLES = [("Aiguilleur", "aqua", "À l’avant : lisez les panneaux, réglez l’aiguillage."),
         ("Chauffeur", "gold", "Dans la cabine : charbon, chaudière, soupape. Gardez la pression !"),
         ("Garde-barrière", "yellow", "À l’arrière : feuille de route, barrières, et chassez les Brumeux.")]


def events():
    """Liste globale (index, position absolue, type, paramètre, tronçon)."""
    out = []
    for k in range(1, NSEC + 1):
        for pos, typ, par in SECTIONS[k]:
            out.append((len(out), SEC * (k - 1) + pos, typ, par, k))
    return out


def sign_text(typ, par, side=None):
    if typ == "fork":
        good, bad = FORKS[par]
        left, right = (good, bad) if side == 0 else (bad, good)
        return ["", T("⚑ BIFURCATION\n", "gold", bold=True), T(f"◀ {left}", "white"), T("   |   ", "dark_gray"),
                T(f"{right} ▶", "white")]
    if typ == "cross":
        return ["", T("⚠ PASSAGE À NIVEAU\n", "red", bold=True), T("La barrière est fermée !", "white")]
    if typ == "lim_on":
        return ["", T(f"⚠ {par.upper()}\n", "yellow", bold=True), T("Vitesse lente obligatoire (pression sous 40)", "white")]
    if typ == "lim_off":
        return ["", T("Fin de zone lente\n", "green", bold=True), T("On peut accélérer.", "white")]
    if typ == "tunnel":
        return ["", T("⚠ TUNNEL EN MONTÉE\n", "gold", bold=True), T("Pleine pression (60 ou plus) !", "white")]
    if typ == "arrive":
        return ["", T("Gare du Pic du Solstice\n", "aqua", bold=True), T("Terminus !", "white")]
    if typ == "board":
        return ["", T("…\n", "gray"), T("Des silhouettes courent le long de la voie.", "gray", italic=True)]
    return ["", T("Voie libre", "green")]


def build(dp):
    EV = events()
    b = ["kill @e[type=!player,tag=sol.r1]"]
    b += fill(OX - 50, 88, -30, OX + 50, 120, 30, "air")
    # sol lointain (remblai) + voie
    b += fill(OX - 45, 97, -5, OX + 45, 97, 5, "gravel")
    b += fill(OX - 45, 98, -2, OX + 45, 98, 2, "stone")
    # --- train : couloir x 976..1026, z -3..3
    b += fill(976, 100, -3, 1020, 104, 3, "dark_oak_planks")
    b += fill(977, 101, -2, 1019, 103, 2, "air")
    b += fill(977, 100, -2, 1019, 100, 2, "spruce_planks")
    for x in range(978, 1020, 3):
        b += fill(x, 102, -3, x, 102, -3, "glass_pane")
        b += fill(x, 102, 3, x, 102, 3, "glass_pane")
    b += fill(976, 101, -2, 976, 103, 2, "glass")               # vitre avant
    b += fill(976, 100, -3, 988, 104, -3, "black_concrete")     # locomotive
    b += fill(976, 100, 3, 988, 104, 3, "black_concrete")
    b += fill(976, 104, -3, 988, 104, 3, "black_concrete")
    for x in (979, 982, 985):
        b.append(setblock(x, 102, -3, "glass_pane")); b.append(setblock(x, 102, 3, "glass_pane"))
    b += fill(981, 101, -2, 981, 103, -2, "black_concrete")      # cloison poste / cabine (passage au centre)
    b += fill(981, 101, 2, 981, 103, 2, "black_concrete")
    # console de l’aiguilleur
    b += [setblock(977, 101, -2, "polished_blackstone"), setblock(977, 101, 2, "polished_blackstone"),
          setblock(977, 101, 0, "lectern[facing=east]")]
    # chaudière (cabine)
    b += fill(982, 101, -1, 983, 103, 1, "black_concrete")
    b += [setblock(983, 101, 0, "blast_furnace[facing=east,lit=true]"), setblock(983, 101, -2, "cut_copper"),
          setblock(983, 102, -2, "lightning_rod[facing=up]")]
    b += fill(982, 105, 0, 982, 107, 0, "polished_blackstone_wall")
    # tender : charbon sur les côtés, allée centrale libre
    b += fill(989, 101, -2, 994, 102, -2, "coal_block")
    b += fill(989, 101, 2, 994, 102, 2, "coal_block")
    b += [setblock(989, 103, -2, "coal_block"), setblock(994, 103, 2, "coal_block")]
    # voiture voyageurs : banquettes, lanternes
    for x in range(996, 1010, 3):
        b += [setblock(x, 101, -2, "spruce_stairs[facing=east]"), setblock(x, 101, 2, "spruce_stairs[facing=east]"),
              setblock(x, 103, 0, "lantern[hanging=true]")]
    b += fill(995, 101, -2, 995, 103, -2, "dark_oak_log"); b += fill(995, 101, 2, 995, 103, 2, "dark_oak_log")
    b += fill(1010, 101, -2, 1010, 103, -2, "dark_oak_log"); b += fill(1010, 101, 2, 1010, 103, 2, "dark_oak_log")
    # voiture du garde + manivelle, plate-forme arrière ouverte
    b += [setblock(1013, 101, -2, "polished_andesite"), setblock(1017, 101, 2, "barrel[facing=up]"),
          setblock(1018, 103, 0, "lantern[hanging=true]")]
    b += fill(1020, 101, -1, 1020, 103, 1, "air")
    b += fill(1021, 100, -3, 1026, 100, 3, "spruce_planks")
    b += fill(1021, 101, -3, 1026, 101, -3, "spruce_fence")
    b += fill(1021, 101, 3, 1026, 101, 3, "spruce_fence")
    # portes latérales ouvertes (pour jeter les Brumeux)
    for x in (1001, 1007):
        b += fill(x, 101, -3, x, 102, -3, "air"); b += fill(x, 101, 3, x, 102, 3, "air")
    # textes fixes
    b.append(text_display(978.6, 102.6, -1.5, ["", T("◀ Voie de gauche", "aqua")], ["sol.r1"], scale=0.5, yaw=90, billboard="fixed"))
    b.append(text_display(978.6, 102.6, 2.5, ["", T("Voie de droite ▶", "aqua")], ["sol.r1"], scale=0.5, yaw=90, billboard="fixed"))
    b.append(text_display(984.6, 102.8, -1.5, ["", T("Soupape", "gold")], ["sol.r1"], scale=0.5, yaw=90, billboard="fixed"))
    b.append(text_display(984.6, 102.8, 0.5, ["", T("Chaudière", "gold")], ["sol.r1"], scale=0.5, yaw=90, billboard="fixed"))
    b.append(text_display(991.5, 103.3, -1.2, ["", T("Tender : charbon", "gray")], ["sol.r1"], scale=0.5))
    b.append(text_display(1013.6, 102.8, -1.5, ["", T("Manivelle des barrières", "yellow")], ["sol.r1"], scale=0.5, yaw=-90, billboard="fixed"))
    dp.fn("build/r1", b + ["function solstice:r1/entities"])
    dp.meta.setdefault("builds", []).append("build/r1")
    dp.meta.setdefault("forceload", []).append((OX - 50, -30, OX + 50, 30))

    # --------------------------------------------------------------- entités (interactions, décor mobile)
    ent = ["kill @e[type=!player,tag=sol.r1e]"]
    for key, (x, y, z), w, h in (("left", BTN_L, 1.25, 1.2), ("right", BTN_R, 1.25, 1.2), ("fire", FIREBOX, 1.3, 1.3),
                                 ("valve", VALVE, 1.3, 1.6), ("coal", COAL, 1.4, 1.4), ("hammer", HAMMER, 0.8, 0.6),
                                 ("crank", CRANK, 1.3, 1.3)):
        ent.append(interaction(x, y - 0.05, z, ["sol.r1", "sol.r1e", "sol.r1i", f"sol.k1_{key}"], w, h))
    ent.append(f"summon item_display {HAMMER[0]} {HAMMER[1] + 0.35} {HAMMER[2]} {{Tags:[\"sol\",\"sol.r1\",\"sol.r1e\",\"sol.r1ham\"],"
               f"item:{{id:\"minecraft:mace\",count:1}},transformation:{{left_rotation:[0f,0f,0.38f,0.92f],right_rotation:[0f,0f,0f,1f],"
               f"translation:[0f,0f,0f],scale:[0.6f,0.6f,0.6f]}}}}")
    ent.append(text_display(*SIGN, sign_text("free", None), ["sol.r1", "sol.r1e", "sol.r1sign"], scale=0.9, billboard="fixed",
                            yaw=90, line_width=260, bg=0xC0101010))
    ent.append(text_display(978.6, 103.5, 0.5, ["", T("Aiguillage : ◀ GAUCHE", "aqua", bold=True)],
                            ["sol.r1", "sol.r1e", "sol.r1sw"], scale=0.45, billboard="fixed", yaw=90))
    # décor mobile : arbres et poteaux qui défilent
    import random
    rnd = random.Random(11)
    for i in range(22):
        side = 1 if i % 2 else -1
        z = side * (rnd.choice([7, 9, 12, 15]))
        x = OX - 45 + i * 4.3
        blk = rnd.choice(["spruce_leaves", "oak_leaves", "birch_leaves"]) if abs(z) > 7 else "spruce_fence"
        sc = "2f,4f,2f" if abs(z) > 7 else "0.3f,3f,0.3f"
        ent.append(f"summon block_display {x} {99 if abs(z) > 7 else 98} {z} {{Tags:[\"sol\",\"sol.r1\",\"sol.r1e\",\"sol.scen\"],"
                   f"teleport_duration:3,block_state:{{Name:\"minecraft:{blk}\"}},transformation:{{left_rotation:[0f,0f,0f,1f],"
                   f"right_rotation:[0f,0f,0f,1f],translation:[0f,0f,0f],scale:[{sc}]}}}}")
    dp.fn("r1/entities", ent)

    # --------------------------------------------------------------- départ, postes
    dp.fn("r1/start", [
        "function solstice:r1/entities",
        "kill @e[type=!player,tag=sol.r1mob]",
        f"scoreboard players set #errors {V} 0",
        f"scoreboard players set #step {V} 0",
        f"scoreboard players set #r1t {V} 0",
        "function solstice:r1/reset_run",
        f"scoreboard players set #dist {V} 0",
        f"scoreboard players set #ev {V} 0",
        "function solstice:roles/draw",
        "function solstice:r1/announce",
        "bossbar set solstice:train players @a", "bossbar set solstice:train visible true",
        obj("L’Express démarre : chacun à son poste !"),
        orel("Bienvenue à bord ! Le train ne s’arrête plus, alors on va le conduire en marche. Chacun son poste, "
             "et parlez-vous : c’est tout le secret des chemins de fer."),
    ])
    announce(dp, "r1/announce", ROLES, "aqua")
    dp.add("load", ["bossbar add solstice:train \"L’Express du Solstice\"", "bossbar set solstice:train color blue",
                    f"bossbar set solstice:train max {SEC * NSEC}", "bossbar set solstice:train visible false"])
    # remise à zéro d’un tronçon (début de partie, erreur, anéantissement)
    dp.fn("r1/reset_run", [
        f"scoreboard players set #press {V} 45", f"scoreboard players set #speed {V} 0",
        f"scoreboard players set #switch {V} 0", f"scoreboard players set #bopen {V} 0",
        f"scoreboard players set #crank {V} 0", f"scoreboard players set #lim {V} 0",
        f"scoreboard players set #over {V} 0", f"scoreboard players set #stall {V} 0",
        f"scoreboard players set #pause {V} 60",
        *[f"execute store result score #fside{k} {V} run random value 0..1" for k in FORKS],
        "kill @e[type=!player,tag=sol.r1mob]",
        "function solstice:r1/show_switch",
        "function solstice:r1/sign_free",
    ])
    for r, (x, y, z, yaw) in CP.items():
        dp.fn(f"r1/cp{r}", [f"tp @s {x} {y} {z} {yaw} 0", f"spawnpoint @s {int(x)} {y} {int(z)}"])
    dp.fn("r1/cp", [f"execute if score @s sol.role matches {r} run return run function solstice:r1/cp{r}" for r in (1, 2, 3)] +
          ["function solstice:r1/cp0"])
    dp.fn("r1/kit", [
        f"execute if entity @s[tag=sol.ro3] unless items entity @s container.* stick[custom_data~{{sol:{{broom:1b}}}}] run give @s {BROOM.give()}",
        f"execute if entity @s[tag=sol.ro3] unless items entity @s container.* written_book[custom_data~{{sol:{{route:1b}}}}] run give @s {ROUTE_BOOK.give()}",
        "effect give @s night_vision infinite 0 true",
        "effect give @s resistance infinite 4 true",
    ])
    dp.fn("r1/enter", [
        "execute unless score @s sol.role matches 1..3 run function solstice:roles/fill_vacant",
        "function solstice:r1/cp", "function solstice:r1/kit",
        "bossbar set solstice:train players @a",
    ])
    dp.fn("r1/respawn", ["function solstice:r1/cp", "function solstice:r1/kit"])
    dp.fn("r1/wipe", ["function solstice:r1/back"])
    dp.fn("r1/on_complete", ["bossbar set solstice:train visible false", "kill @e[type=!player,tag=sol.r1mob]",
                             f"execute if score #errors {V} matches 0 run function solstice:challenge/grant_voie_royale"])

    # --------------------------------------------------------------- panneaux et aiguillage
    dp.fn("r1/sign_free", [f"data modify entity @e[type=text_display,tag=sol.r1sign,limit=1] text set value {snbt_str(jdump(sign_text('free', None)))}"])
    for i, pos, typ, par, k in EV:
        if typ == "fork":
            dp.fn(f"r1/sign/{i}", [
                f"execute if score #fside{par} {V} matches 0 run data modify entity @e[type=text_display,tag=sol.r1sign,limit=1] text set value {snbt_str(jdump(sign_text(typ, par, 0)))}",
                f"execute if score #fside{par} {V} matches 1 run data modify entity @e[type=text_display,tag=sol.r1sign,limit=1] text set value {snbt_str(jdump(sign_text(typ, par, 1)))}",
                "execute as @a[tag=sol.ro1] at @s run playsound minecraft:block.note_block.pling master @s ~ ~ ~ 0.6 1.2",
            ])
        else:
            dp.fn(f"r1/sign/{i}", [
                f"data modify entity @e[type=text_display,tag=sol.r1sign,limit=1] text set value {snbt_str(jdump(sign_text(typ, par)))}",
                "execute as @a[tag=sol.ro1] at @s run playsound minecraft:block.note_block.pling master @s ~ ~ ~ 0.6 1.2"
                if typ != "board" else None,
                "execute as @a at @s run playsound minecraft:block.bell.use master @s ~ ~ ~ 0.5 1.6" if typ == "cross" else None,
            ])
    dp.fn("r1/show_switch", [
        f"execute if score #switch {V} matches 0 run data modify entity @e[type=text_display,tag=sol.r1sw,limit=1] text set value {snbt_str(jdump(['', T('Aiguillage : ◀ GAUCHE', 'aqua', bold=True)]))}",
        f"execute if score #switch {V} matches 1 run data modify entity @e[type=text_display,tag=sol.r1sw,limit=1] text set value {snbt_str(jdump(['', T('Aiguillage : DROITE ▶', 'aqua', bold=True)]))}",
    ])

    # --------------------------------------------------------------- résolution des évènements
    for i, pos, typ, par, k in EV:
        body = [f"scoreboard players add #ev {V} 1", f"scoreboard players set #signed {V} 0", f"scoreboard players set #ev_cross {V} 0",
                "function solstice:r1/sign_free"]
        if typ == "fork":
            body = [f"execute unless score #switch {V} = #fside{par} {V} run return run function solstice:r1/err_fork"] + body + [
                tellraw("@a", T("✔ Bonne voie : ", "green"), T(FORKS[par][0], "white")),
                "execute as @a at @s run playsound minecraft:block.piston.contract master @s ~ ~ ~ 0.6 1.4"]
        elif typ == "cross":
            body = [f"execute if score #bopen {V} matches 0 run return run function solstice:r1/err_cross"] + body + [
                f"scoreboard players set #bopen {V} 0", f"scoreboard players set #crank {V} 0",
                tellraw("@a", T("✔ Passage à niveau franchi.", "green"))]
        elif typ == "lim_on":
            body += [f"scoreboard players set #lim {V} 1", f"scoreboard players set #over {V} 0",
                     tellraw("@a[tag=sol.ro1]", T(f"⚠ {par} : à partir d’ici, on roule lentement !", "yellow"))]
        elif typ == "lim_off":
            body += [f"scoreboard players set #lim {V} 0", tellraw("@a", T("✔ Zone lente franchie.", "green"))]
        elif typ == "tunnel":
            body = [f"execute if score #press {V} matches ..59 run return run function solstice:r1/err_tunnel"] + body + [
                tellraw("@a", T("✔ Le train sort du tunnel dans un nuage de vapeur !", "green"))]
        elif typ == "board":
            body += [f"function solstice:r1/board{par}"]
        elif typ == "arrive":
            body += ["function solstice:r1/arrived"]
        dp.fn(f"r1/ev/{i}", body)
    for n in (2, 3, 4):
        dp.fn(f"r1/board{n}", [
            *[f"summon zombie {x} {y} {z} {{Tags:[\"sol\",\"sol.mob\",\"sol.r1mob\"],PersistenceRequired:1b,CanPickUpLoot:0b,"
              f"CustomName:'{{\"text\":\"Brumeux\",\"color\":\"gray\"}}',CustomNameVisible:1b,Silent:0b,"
              f"attributes:[{{id:\"minecraft:generic.attack_damage\",base:0d}},{{id:\"minecraft:generic.movement_speed\",base:0.2d}},"
              f"{{id:\"minecraft:generic.max_health\",base:40d}}],Health:40f,"
              f"ArmorItems:[{{}},{{}},{{}},{{id:\"minecraft:carved_pumpkin\",count:1}}],ArmorDropChances:[0f,0f,0f,0f]}}"
              for (x, y, z) in BOARD_SPAWN[:n]],
            tellraw("@a", T("⚠ Des Brumeux montent à bord par l’arrière ! Ils étouffent la chaudière !", "red")),
            "execute as @a at @s run playsound minecraft:entity.zombie.ambient master @s ~ ~ ~ 1 0.6",
        ])

    # erreurs → le train recule au début du tronçon
    errs = {"fork": "Mauvaise voie ! Le train freine et recule jusqu’au dernier aiguillage.",
            "cross": "BAM ! La barrière n’était pas ouverte. Le train recule au dernier tronçon.",
            "derail": "Trop vite dans la zone lente ! Le train patine et recule au dernier tronçon.",
            "tunnel": "Pas assez de pression : le train glisse en arrière dans la montée.",
            "stall": "La chaudière s’est éteinte… le train s’arrête et recule au dernier tronçon.",
            "over": "La soupape saute ! Surpression : le train freine d’urgence et recule au dernier tronçon."}
    for key, msg in errs.items():
        dp.fn(f"r1/err_{key}", [tellraw("@a", T("✖ " + msg, "red")), "function solstice:r1/back"])
    dp.fn("r1/back", [
        f"scoreboard players add #errors {V} 1",
        f"scoreboard players operation #dist {V} /= #cSEC {V}",
        f"scoreboard players operation #dist {V} *= #cSEC {V}",
        "function solstice:r1/ev_from_dist",
        "function solstice:r1/reset_run",
        *title("@a", "Le train recule…", "Retour au début du tronçon.", color="red", times=(5, 40, 10)),
        "execute as @a at @s run playsound minecraft:block.anvil.land master @s ~ ~ ~ 0.5 0.6",
        "effect give @a nausea 3 0 true",
    ])
    dp.add("load", [f"scoreboard players set #cSEC {V} {SEC}"])
    # index du premier évènement d’un tronçon (après recul)
    evd = []
    for k in range(1, NSEC + 1):
        first = min(i for i, pos, typ, par, kk in EV if kk == k)
        evd.append(f"execute if score #dist {V} matches {SEC * (k - 1)} run scoreboard players set #ev {V} {first}")
    dp.fn("r1/ev_from_dist", evd)
    dp.fn("r1/arrived", [
        f"scoreboard players set #dist {V} {SEC * NSEC}",
        *title("@a", "Terminus !", "Gare du Pic du Solstice", color="aqua"),
        orel("Bravo ! Pas un mort, et presque pas de charbon sur les banquettes. Descendez, la Tour vous attend."),
        "function solstice:flow/complete",
    ])

    # --------------------------------------------------------------- interactions (postes)
    kinds = ["left", "right", "fire", "valve", "coal", "hammer", "crank"]
    dp.fn("r1/clicked", [
        *[f"execute if entity @s[tag=sol.k1_{k}] if data entity @s interaction on target run function solstice:r1/c/{k}" for k in kinds],
        *[f"execute if entity @s[tag=sol.k1_{k}] if data entity @s attack on attacker run function solstice:r1/c/{k}" for k in kinds],
        "data remove entity @s interaction", "data remove entity @s attack",
    ])

    def role_fn(name, role, cmds, cool=6):
        dp.fn(f"r1/c/{name}", [
            "execute if score @s sol.cool matches 1.. run return 0", f"scoreboard players set @s sol.cool {cool}",
            f"execute unless entity @s[tag=sol.ro{role}] run return run " +
            actionbar("@s", f"Ce n’est pas votre poste : c’est celui du {ROLES[role - 1][0]}.", "red"),
            *cmds])
    role_fn("left", 1, [f"scoreboard players set #switch {V} 0", "function solstice:r1/show_switch",
                        "playsound minecraft:block.lever.click master @a ~ ~ ~ 1 0.8",
                        actionbar("@s", "Aiguillage : voie de GAUCHE", "aqua")])
    role_fn("right", 1, [f"scoreboard players set #switch {V} 1", "function solstice:r1/show_switch",
                         "playsound minecraft:block.lever.click master @a ~ ~ ~ 1 1.0",
                         actionbar("@s", "Aiguillage : voie de DROITE", "aqua")])
    role_fn("coal", 2, [
        f"execute if items entity @s container.* coal[custom_data~{{sol:{{coal:1b}}}}] run return run " +
        actionbar("@s", "Vous avez déjà une pelletée : à la chaudière !", "gold"),
        f"give @s {COAL_I.give()}", "playsound minecraft:block.gravel.break master @a ~ ~ ~ 1 0.8",
        actionbar("@s", "Une pelletée de charbon. Vite, à la chaudière !", "gold")], cool=10)
    role_fn("fire", 2, [
        f"execute unless items entity @s weapon.* coal[custom_data~{{sol:{{coal:1b}}}}] run return run " +
        actionbar("@s", "La chaudière réclame du charbon (tender, juste derrière).", "gold"),
        f"clear @s coal[custom_data~{{sol:{{coal:1b}}}}] 1", f"scoreboard players add #press {V} 15",
        "playsound minecraft:item.firecharge.use master @a ~ ~ ~ 0.8 0.8",
        "particle minecraft:flame 984 101.8 0.5 0.2 0.2 0.2 0.02 15"])
    role_fn("valve", 2, [
        f"scoreboard players remove #press {V} 20", f"execute if score #press {V} matches ..-1 run scoreboard players set #press {V} 0",
        "playsound minecraft:block.fire.extinguish master @a ~ ~ ~ 1 1.4",
        "particle minecraft:cloud 983.5 103.5 -1.5 0.3 0.4 0.3 0.05 25"])
    role_fn("crank", 3, [
        f"execute unless score #ev_cross {V} matches 1 run return run " + actionbar("@s", "Aucune barrière en vue… pour l’instant.", "yellow"),
        f"execute if score #bopen {V} matches 1 run return run " + actionbar("@s", "La barrière est déjà ouverte.", "green"),
        f"scoreboard players add #crank {V} 1", "playsound minecraft:block.chain.step master @a ~ ~ ~ 1 0.7",
        f"execute if score #crank {V} matches ..2 run " + actionbar("@s", ["", T("La manivelle tourne… ", "yellow"), SC("#crank"), T(" / 3", "gray")]),
        f"execute if score #crank {V} matches 3.. run function solstice:r1/barrier_open"], cool=8)
    dp.fn("r1/barrier_open", [f"scoreboard players set #bopen {V} 1",
                              tellraw("@a", T("✔ Barrière ouverte !", "yellow")),
                              "execute as @a at @s run playsound minecraft:block.fence_gate.open master @s ~ ~ ~ 1 0.8"])
    dp.fn("r1/c/hammer", [
        "execute if score @s sol.cool matches 1.. run return 0", "scoreboard players set @s sol.cool 10",
        narr("Un manche dépasse du charbon… Vous tirez : un marteau de forgeron gravé « B. » !", "@s"),
        "function solstice:story/found_marteau", "kill @e[type=!player,tag=sol.r1ham]"])

    # --------------------------------------------------------------- tick
    tick = [
        "execute as @e[type=interaction,tag=sol.r1i] at @s if data entity @s interaction run function solstice:r1/clicked",
        "execute as @e[type=interaction,tag=sol.r1i] at @s if data entity @s attack run function solstice:r1/clicked",
        f"scoreboard players add #r1t {V} 1",
        f"execute if score #step {V} matches 0 if score #r1t {V} matches 200.. run function solstice:r1/go",
        f"execute if score #step {V} matches 0 run return 0",
        f"execute if score #pause {V} matches 1.. run scoreboard players remove #pause {V} 1",
        # pression : baisse régulière, plus vite si des Brumeux sont à bord
        f"scoreboard players operation #m8 {V} = #r1t {V}", f"scoreboard players operation #m8 {V} %= #c8 {V}",
        f"execute if score #m8 {V} matches 0 run scoreboard players remove #press {V} 1",
        f"execute if score #m4 {V} matches 0 as @e[tag=sol.r1mob] at @s if entity @s[x=979,y=99,z=-4,dx=16,dy=6,dz=8] run scoreboard players remove #press {V} 1",
        f"execute if score #press {V} matches ..-1 run scoreboard players set #press {V} 0",
        # vitesse
        f"scoreboard players set #speed {V} 0",
        f"execute if score #press {V} matches 10..39 run scoreboard players set #speed {V} 1",
        f"execute if score #press {V} matches 40..74 run scoreboard players set #speed {V} 2",
        f"execute if score #press {V} matches 75.. run scoreboard players set #speed {V} 3",
        f"execute if score #pause {V} matches 1.. run scoreboard players set #speed {V} 0",
        f"execute if score #pause {V} matches 0 run scoreboard players operation #dist {V} += #speed {V}",
        f"execute store result bossbar solstice:train value run scoreboard players get #dist {V}",
        # erreurs continues
        f"execute if score #press {V} matches 101.. run return run function solstice:r1/err_over",
        f"execute if score #pause {V} matches 0 if score #press {V} matches ..9 run scoreboard players add #stall {V} 1",
        f"execute if score #press {V} matches 10.. run scoreboard players set #stall {V} 0",
        f"execute if score #stall {V} matches 120.. run return run function solstice:r1/err_stall",
        f"execute if score #lim {V} matches 1 if score #speed {V} matches 2.. run scoreboard players add #over {V} 1",
        f"execute if score #over {V} matches 40.. run return run function solstice:r1/err_derail",
        # évènements
        "function solstice:r1/events",
        # Brumeux tombés du train
        "execute as @e[tag=sol.r1mob] at @s if entity @s[y=-64,dy=158] run function solstice:r1/mob_fell",
        # décor, fumée, sons
        f"execute if score #m4 {V} matches 0 run function solstice:r1/scenery",
        f"execute if score #m20 {V} matches 0 run function solstice:r1/bars",
        f"execute if score #step {V} matches 1.. run function solstice:r1/section",
    ]
    dp.fn("r1/tick", tick)
    dp.add("load", [f"scoreboard players set #c8 {V} 8"])
    dp.fn("r1/go", [f"scoreboard players set #step {V} 1", "function solstice:hints/reset",
                    orel("Chauffeur : du charbon dans la chaudière ! Aiguilleur : les yeux sur les panneaux ! Garde : la feuille de route !"),
                    *title("@a", "Tchou-tchou !", "L’Express s’élance", color="aqua", times=(5, 40, 10))])
    evl = []
    for i, pos, typ, par, k in EV:
        sp = max(SEC * (k - 1), pos - SIGN_AHEAD) if typ != "board" else pos
        evl.append(f"execute if score #ev {V} matches {i} if score #signed {V} matches 0 if score #dist {V} matches {sp}.. "
                   f"run function solstice:r1/signon/{i}")
        dp.fn(f"r1/signon/{i}", [f"scoreboard players set #signed {V} 1", f"function solstice:r1/sign/{i}",
                                 f"scoreboard players set #ev_cross {V} {1 if typ == 'cross' else 0}"])
        evl.append(f"execute if score #ev {V} matches {i} if score #dist {V} matches {pos}.. run return run function solstice:r1/ev/{i}")
    dp.fn("r1/events", evl)
    # numéro de tronçon (étape pour les indices)
    sec = [f"scoreboard players operation #sec {V} = #dist {V}", f"scoreboard players operation #sec {V} /= #cSEC {V}",
           f"scoreboard players add #sec {V} 1",
           f"execute if score #sec {V} matches {NSEC + 1}.. run scoreboard players set #sec {V} {NSEC}",
           f"execute unless score #sec {V} = #step {V} run function solstice:r1/new_section"]
    dp.fn("r1/section", sec)
    dp.fn("r1/new_section", [f"scoreboard players operation #step {V} = #sec {V}", "function solstice:hints/reset",
                             "bossbar set solstice:obj name " + jdump(["", T("◆ ", "gold"), T("L’Express : tronçon ", "white"),
                                                                       SC("#step", color="aqua"), T(f" / {NSEC}", "gray")])])
    dp.fn("r1/mob_fell", ["tp @s ~ -100 ~", "kill @s",
                          tellraw("@a", T("Un Brumeux est passé par-dessus bord.", "gray"))])
    dp.fn("r1/bars", [
        "execute as @a[tag=sol.ro2] run " + actionbar("@s", ["", T("Pression ", "gold"), SC("#press", color="yellow"),
                                                           T("  (lent < 40 ≤ normal < 75 ≤ rapide · max 100)", "gray"),
                                                           T("   Vitesse ", "gold"), SC("#speed", color="yellow")]),
        "execute as @a[tag=sol.ro3,tag=!sol.ro2] run " + actionbar("@s", ["", T("Barrière : ", "yellow"), SC("#bopen", color="white"),
                                                                        T(" (1 = ouverte)   Tours de manivelle : ", "gray"), SC("#crank")]),
        "execute as @a[tag=sol.ro1,tag=!sol.ro2,tag=!sol.ro3] run " + actionbar("@s", ["", T("Vitesse : ", "aqua"), SC("#speed"),
                                                                                    T("   Aiguillage : ", "aqua"), SC("#switch"),
                                                                                    T(" (0 = gauche, 1 = droite)", "gray")]),
    ])
    scen = [
        # défilement du décor proportionnel à la vitesse (le train file vers l’ouest)
        f"execute if score #speed {V} matches 1 as @e[type=block_display,tag=sol.scen] at @s run tp @s ~0.6 ~ ~",
        f"execute if score #speed {V} matches 2 as @e[type=block_display,tag=sol.scen] at @s run tp @s ~1.2 ~ ~",
        f"execute if score #speed {V} matches 3 as @e[type=block_display,tag=sol.scen] at @s run tp @s ~1.9 ~ ~",
        f"execute as @e[type=block_display,tag=sol.scen] at @s if entity @s[x={OX + 46},y=80,z=-30,dx=20,dy=40,dz=60] run tp @s ~-94 ~ ~",
        f"execute if score #speed {V} matches 1.. run particle minecraft:campfire_cosy_smoke 982.5 108 0.5 0.3 0.3 0.3 0.02 3 force",
        f"execute if score #speed {V} matches 1.. as @a[tag=sol.ro1] at @s run playsound minecraft:entity.minecart.riding ambient @s ~ ~ ~ 0.15 0.8",
    ]
    dp.fn("r1/scenery", scen)
    dp.fn("r1/ptick", [
        f"execute if score @s sol.y matches ..95 run function solstice:r1/cp",
    ])

    hint_fn(dp, 1, {
        k: ("Parlez-vous ! L’Aiguilleur voit les panneaux, le Garde a la feuille de route, le Chauffeur la pression.",
            "Bifurcation : le Garde lit la feuille de route, l’Aiguilleur choisit le côté du bon nom. Passage à niveau : "
            "3 tours de manivelle avant d’arriver. Zones lentes : pression sous 40. Tunnel : 60 ou plus.")
        for k in range(1, NSEC + 1)})

    # tests structurels, registre, méta
    dp.test("express : 7 postes cliquables", "entity @e[type=interaction,tag=sol.k1_crank]")
    dp.test("express : panneau avant", "entity @e[type=text_display,tag=sol.r1sign]")
    dp.test("express : décor défilant", "entity @e[type=block_display,tag=sol.scen]")
    dp.test("express : marteau caché dans le tender", "entity @e[type=item_display,tag=sol.r1ham]")
    dp.puzzle(1, "route-choice", "route-choice", "Bifurcations : le Garde lit la feuille de route, l’Aiguilleur choisit la voie.")
    dp.puzzle(1, "gauge-keeping", "gauge-keeping", "Chauffeur : maintenir la pression dans la bonne plage (lente, tunnel).")
    dp.puzzle(1, "crank-deadline", "crank-deadline", "Garde : ouvrir la barrière (3 tours) avant le passage à niveau.")
    dp.puzzle(1, "repel-boarders", "repel-boarders", "Repousser les Brumeux qui montent à bord.")
    dp.meta.setdefault("rooms", {})["1"] = {
        "cp": CP[0], "cps": CP, "events": [(i, pos, typ, par, k) for i, pos, typ, par, k in EV], "sec": SEC,
        "k": {"left": BTN_L, "right": BTN_R, "fire": FIREBOX, "valve": VALVE, "coal": COAL, "hammer": HAMMER, "crank": CRANK}}
