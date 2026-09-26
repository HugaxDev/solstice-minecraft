"""Indices progressifs : #ht compte les ticks passés sur l’étape courante (#step).
5 min → indice 1 (#hk=1), 8 min → indice 2 (#hk=2). Chaque salle fournit rN/hint qui lit #step et #hk.
Les salles appellent hints/reset à chaque changement d’étape."""
from .core import V, T, tellraw

HINT1 = 6000
HINT2 = 9600


def build(dp):
    dp.fn("hints/reset", [f"scoreboard players set #ht {V} 0", f"scoreboard players set #hk {V} 0"])
    dp.fn("hints/tick", [
        f"scoreboard players add #ht {V} 1",
        f"execute if score #ht {V} matches {HINT1} run function solstice:hints/give1",
        f"execute if score #ht {V} matches {HINT2} run function solstice:hints/give2",
    ])
    for k in (1, 2):
        dp.fn(f"hints/give{k}", [
            f"scoreboard players set #hk {V} {k}",
            f"scoreboard players add #hints {V} 1",
            tellraw("@a", T("✦ Indice " + ("(1/2)" if k == 1 else "(2/2)"), "aqua", bold=True),
                    T(" — vous bloquez depuis un moment…", "gray", italic=True)),
            "function solstice:rooms/hint",
            "execute as @a at @s run playsound minecraft:block.amethyst_block.chime master @s ~ ~ ~ 1 1.5",
        ])


def hint_fn(dp, room, hints):
    """hints = {step: (texte indice 1, texte indice 2)} ; génère rN/hint."""
    body = []
    for step, (h1, h2) in hints.items():
        body.append(f"execute if score #step {V} matches {step} if score #hk {V} matches 1 run " +
                    tellraw("@a", T("  " + h1, "aqua")))
        body.append(f"execute if score #step {V} matches {step} if score #hk {V} matches 2 run " +
                    tellraw("@a", T("  " + h2, "aqua")))
    dp.fn(f"r{room}/hint", body)
