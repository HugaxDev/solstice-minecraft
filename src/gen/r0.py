"""Salle 0 — Prologue : Brumeval. Attente des 3 joueurs, cinématique de Maître Orel, premiers indices, embarquement.

#step 0 : attente des voyageurs (#np < #need) · 1 : cinématique d’Orel · 2 : libre, rejoindre le quai.
"""
from .core import V, T, jdump, tellraw, title, orel, narr, actionbar, fill, setblock, text_display, interaction, sound, SC
from .flow import obj
from .hints import hint_fn
from . import village

SPAWN = (0.5, 101, 14.5, 180)


def build(dp):
    village.build(dp)
    P = village.PLATFORM
    dp.fn("r0/start", [
        f"scoreboard players set #step {V} 0",
        f"scoreboard players set #r0t {V} 0",
        "function solstice:r0/obj_wait",
    ])
    dp.fn("r0/obj_wait", [
        "bossbar set solstice:obj name " + jdump(["", T("◆ ", "gold"), T("En attente des voyageurs : ", "white"),
                                                  SC("#np"), T(" / ", "gray"), SC("#need")]),
    ])
    dp.fn("r0/cp", [f"tp @s {SPAWN[0]} {SPAWN[1]} {SPAWN[2]} {SPAWN[3]} 0",
                    f"spawnpoint @s {int(SPAWN[0])} {SPAWN[1]} {int(SPAWN[2])}"])
    dp.fn("r0/welcome", [
        *title("@s", "SOLSTICE", "Brumeval, la veille du dernier jour", color="gold", times=(20, 80, 30)),
        narr("Trois voyageurs sont attendus à Brumeval. L’aventure commence quand vous êtes tous là.", "@s"),
        "playsound minecraft:block.bell.resonate master @s ~ ~ ~ 0.8 0.8",
    ])
    dp.fn("r0/enter", [
        "function solstice:r0/cp",
        f"execute if score #step {V} matches 0 run function solstice:r0/welcome",
        "effect give @s night_vision infinite 0 true",
    ])
    dp.fn("r0/respawn", ["function solstice:r0/cp"])

    intro = [
        (20, [*title("@a", "SOLSTICE", "Les trois voyageurs sont arrivés", color="gold", times=(20, 70, 20)),
              sound("minecraft:block.bell.use", "@a", 1, 0.6)]),
        (100, [orel("Ah ! Vous voilà enfin. Trois voyageurs, comme dans ma lettre. Parfait, je déteste les nombres impairs… "
                    "enfin, sauf trois.")]),
        (220, [orel("Je suis Maître Orel, horloger de Brumeval et gardien du Grand Calendrier. C’est la machine qui fait "
                    "tourner les saisons, là-haut, dans le Pic du Solstice.")]),
        (360, [orel("Il y a trois nuits, quelqu’un l’a sabotée. Les saisons se sont brisées : il neige sur les cerisiers "
                    "et les citrouilles poussent en juillet.")]),
        (500, [orel("Trois personnes pouvaient approcher la machine : Madame Ysolde, la bibliothécaire, Bram, le "
                    "forgeron, et Lise, la jardinière. Je ne soupçonne personne. Enfin, je soupçonne tout le monde.")]),
        (640, [orel("Ouvrez l’œil en chemin : le coupable a forcément laissé des traces. Notez tout dans votre Carnet d’enquête.")]),
        (760, [orel("L’Express du Solstice vous attend au quai, au nord de la place. Il ne s’arrête plus, alors sautez "
                    "dedans ensemble ! Moi, je vous guiderai par les tuyaux acoustiques. Ils passent partout."),
               narr("Promenez-vous dans le village si vous le souhaitez, puis rejoignez tous les trois le quai de la gare.")]),
        (770, ["function solstice:r0/free"]),
    ]
    tl = [f"scoreboard players add #r0t {V} 1"]
    for t, cmds in intro:
        sub = dp.fn(f"r0/intro/t{t}", cmds)
        tl.append(f"execute if score #r0t {V} matches {t} run function {sub}")
    dp.fn("r0/intro_tick", tl)
    dp.fn("r0/begin", [
        f"scoreboard players set #step {V} 1",
        f"scoreboard players set #started {V} 1",
        f"scoreboard players set #gtime {V} 0",
        f"scoreboard players set #r0t {V} 0",
        obj("Écoutez Maître Orel"),
        "function solstice:hints/reset",
    ])
    dp.fn("r0/free", [
        f"scoreboard players set #step {V} 2",
        obj("Rejoignez tous le quai de la gare, au nord", sub="(observez le village en chemin)"),
        "function solstice:hints/reset",
    ])
    px1, py1, pz1, px2, py2, pz2 = P
    dp.fn("r0/tick", [
        f"execute if score #step {V} matches 0 if score #m20 {V} matches 0 run function solstice:r0/obj_wait",
        f"execute if score #step {V} matches 0 if score #np {V} >= #need {V} run function solstice:r0/begin",
        f"execute if score #step {V} matches 1 run function solstice:r0/intro_tick",
        f"execute if score #step {V} matches 2 run function solstice:r0/board_check",
        "function solstice:village/tick",
    ])
    dp.fn("r0/board_check", [
        f"execute store result score #onb {V} if entity @a[x={px1},y={py1},z={pz1},dx={px2 - px1},dy={py2 - py1},dz={pz2 - pz1},gamemode=!spectator]",
        f"execute if score #onb {V} >= #need {V} if score #onb {V} >= #np {V} run function solstice:flow/complete",
        f"execute if score #m20 {V} matches 0 if score #onb {V} matches 1.. as @a[x={px1},y={py1},z={pz1},dx={px2 - px1},dy={py2 - py1},dz={pz2 - pz1}] run "
        + actionbar("@s", ["", T("Sur le quai : ", "gray"), SC("#onb"), T(" / ", "gray"), SC("#np"),
                           T(" — l’Express part quand tout le groupe est là.", "gray")]),
    ])
    dp.fn("r0/ptick", ["function solstice:village/ptick"])
    hint_fn(dp, 0, {
        2: ("Le quai de la gare est au nord de la place, derrière la grande horloge. Tout le groupe doit s’y tenir.",
            "Suivez la rue pavée vers le nord : le train fume au bout. Montez tous les trois sur le quai."),
    })
    dp.meta.setdefault("rooms", {})["0"] = {"spawn": SPAWN, "platform": P}
