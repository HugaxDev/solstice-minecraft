"""Fin de partie : cinématique commune, crédits (temps total, morts par joueur), advancement final, épilogue (#room 8)."""
from .core import V, T, jdump, tellraw, title, orel, narr, SC
from .layout import ROOMS

EPI = (0.5, 101, 6.5, 180)


def build(dp, cine_steps):
    """cine_steps : liste (tick, [commandes]) fournie par la finale (révélation, saisons, feux d’artifice)."""
    dp.fn("end/start", [
        f"execute if score #ended {V} matches 1 run return 0",
        f"scoreboard players set #ended {V} 1",
        f"scoreboard players set #endt {V} 0",
        "advancement grant @a only solstice:room/r7",
        "kill @e[type=!player,tag=sol.mob]",
        "execute as @a run function solstice:flow/trans_player",
        "effect give @a resistance 1000000 255 true",
    ])
    tick = [f"scoreboard players add #endt {V} 1"]
    last = 0
    for t, cmds in cine_steps:
        sub = dp.fn(f"end/cine/t{t}", cmds)
        tick.append(f"execute if score #endt {V} matches {t} run function {sub}")
        last = max(last, t)
    credits_t = last + 60
    tick.append(f"execute if score #endt {V} matches {credits_t} run function solstice:end/credits")
    tick.append(f"execute if score #endt {V} matches {credits_t + 200} run function solstice:end/epilogue")
    dp.fn("end/tick", tick)

    # crédits : temps total et morts par joueur
    dp.fn("end/credits", [
        f"scoreboard players operation #s {V} = #gtime {V}",
        f"scoreboard players operation #s {V} /= #c20 {V}",
        f"scoreboard players operation #h {V} = #s {V}",
        f"scoreboard players operation #h {V} /= #c3600 {V}",
        f"scoreboard players operation #mn {V} = #s {V}",
        f"scoreboard players operation #mn {V} %= #c3600 {V}",
        f"scoreboard players operation #mn {V} /= #c60 {V}",
        f"scoreboard players operation #sec {V} = #s {V}",
        f"scoreboard players operation #sec {V} %= #c60 {V}",
        tellraw("@a", T("\n══════════  S O L S T I C E  ══════════", "gold", bold=True)),
        tellraw("@a", T("      Une aventure pour trois voyageurs", "yellow", italic=True)),
        tellraw("@a", T("\nTemps de partie : ", "gray"), SC("#h"), T(" h ", "gray"), SC("#mn"), T(" min ", "gray"),
                SC("#sec"), T(" s", "gray")),
        tellraw("@a", T("Indices trouvés : ", "gray"), SC("#clues"), T(" / 10", "gray")),
        tellraw("@a", T("Morts :", "gray")),
        "execute as @a run function solstice:end/credit_line",
        tellraw("@a", T("\nMaître Orel", "gold"), T(" — l’horloger qui voulait arrêter le temps", "gray")),
        tellraw("@a", T("Madame Ysolde", "dark_purple"), T(" — la bibliothécaire", "gray")),
        tellraw("@a", T("Bram", "dark_red"), T(" — le forgeron", "gray"), T("   ·   ", "dark_gray"),
                T("Lise", "dark_green"), T(" — la jardinière", "gray")),
        tellraw("@a", T("\nConception, construction et tests : générés pour vous trois.", "dark_gray", italic=True)),
        tellraw("@a", T("Merci d’avoir joué.  ✦", "gold")),
        tellraw("@a", T("═══════════════════════════════════════\n", "gold", bold=True)),
        "advancement grant @a only solstice:fin",
        "execute as @a at @s run playsound minecraft:ui.toast.challenge_complete master @s ~ ~ ~ 1 1",
    ])
    dp.fn("end/credit_line", [
        tellraw("@a", T("   • ", "dark_gray"), {"selector": "@s", "color": "white"}, T(" : ", "gray"),
                {"score": {"name": "@s", "objective": "sol.dall"}, "color": "red"}),
    ])
    dp.fn("end/epilogue", [
        f"scoreboard players set #room {V} 8",
        f"scoreboard players set #step {V} 0",
        "function solstice:flow/room_setup",
        "function solstice:village/npc_guard",
        "effect clear @a resistance",
        "bossbar set solstice:obj name " + jdump(["", T("✦ ", "gold"), T("Brumeval — le printemps est revenu", "green")]),
    ])
    # salle 8 : épilogue libre au village
    dp.fn("r8/cp", [f"tp @s {EPI[0]} {EPI[1]} {EPI[2]} {EPI[3]} 0", f"spawnpoint @s {int(EPI[0])} {EPI[1]} {int(EPI[2])}"])
    dp.fn("r8/enter", ["function solstice:r8/cp",
                       narr("Brumeval au printemps. Prenez le temps de flâner : l’aventure est terminée.", "@s")])
    dp.fn("r8/respawn", ["function solstice:r8/cp"])
