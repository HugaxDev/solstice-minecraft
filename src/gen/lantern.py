"""La Lanterne des Saisons : objet unique du groupe (à partir de la salle 3).

- Gardien : il existe exactement une Lanterne parmi les joueurs présents (#lantern = 1 une fois fabriquée).
  Lâchée → rendue à celui qui l’a jetée ; porteur déconnecté → elle passe à un coéquipier ; pas de doublon.
- Révélation : tenue en main (principale ou secondaire), elle révèle à ≤ 5 blocs les text_display « sol.ink »
  (encre invisible, échelle 0 → 1) tant qu’elle est proche, et déclenche une seule fois les secrets « sol.secret »
  (≤ 3 blocs) : chaque secret porte l’étiquette sol.s_<clé> et appelle lantern/secret/<clé>.
"""
from .core import V, T, Item, tellraw, actionbar

LANTERN = Item("lantern", "Lanterne des Saisons", "gold",
               lore=["Tenez-la en main : elle révèle l’encre invisible,", "les inscriptions cachées et les passages secrets."],
               cmd=3001, data="{sol:{keep:1b,lantern:1b}}", glint=True, rarity="epic", stack=1)
LPRED = "lantern[custom_data~{sol:{lantern:1b}}]"
SECRETS = {}   # clé -> commandes (enregistrées par les salles)


def secret(key, cmds):
    SECRETS[key] = cmds


def build(dp):
    dp.fn("lantern/give", [f"give @s {LANTERN.give()}"])
    dp.fn("lantern/count", [
        f"scoreboard players set #lc {V} 0",
        f"execute as @a if items entity @s container.* {LPRED} run scoreboard players add #lc {V} 1",
        f"execute as @a if items entity @s weapon.offhand {LPRED} run scoreboard players add #lc {V} 1",
    ])
    dp.fn("lantern/keeper", [
        # lâchée par terre : rendue au lanceur
        f"execute as @e[type=item] if items entity @s contents {LPRED} on origin run tag @s add sol.lgive",
        f"execute as @e[type=item] if items entity @s contents {LPRED} run kill @s",
        "function solstice:lantern/count",
        f"execute if score #lc {V} matches 0 as @a[tag=sol.lgive] run function solstice:lantern/give",
        "tag @a remove sol.lgive",
        "function solstice:lantern/count",
        f"execute if score #lc {V} matches 2.. as @a run clear @s {LPRED}",
        f"execute if score #lc {V} matches 2.. run scoreboard players set #lc {V} 0",
        f"execute if score #lc {V} matches 0 if entity @a run function solstice:lantern/regive",
    ])
    dp.fn("lantern/regive", [
        "tag @a add sol.cand",
        f"scoreboard players set #tries {V} 0",
        "function solstice:roles/pick",
        "execute as @a[tag=sol.pick] run function solstice:lantern/give",
        tellraw("@a", T("✦ La Lanterne des Saisons passe entre les mains de ", "gold"), {"selector": "@a[tag=sol.pick]", "color": "white"},
                T(".", "gold")),
        "tag @a remove sol.cand", "tag @a remove sol.pick",
    ])
    dp.fn("lantern/on_rejoin", [
        f"execute unless score #lantern {V} matches 1 run return 0",
        "tag @s add sol.me",
        f"scoreboard players set #lo {V} 0",
        f"execute as @a[tag=!sol.me] if items entity @s container.* {LPRED} run scoreboard players add #lo {V} 1",
        f"execute as @a[tag=!sol.me] if items entity @s weapon.offhand {LPRED} run scoreboard players add #lo {V} 1",
        "tag @s remove sol.me",
        f"execute if score #lo {V} matches 1.. run clear @s {LPRED}",
    ])
    dp.fn("lantern/reset", [f"scoreboard players set #lantern {V} 0",
                            f"execute as @a run clear @s {LPRED}"])
    dp.add("load", [f"execute unless score #lantern {V} matches 0.. run scoreboard players set #lantern {V} 0"])

    dp.fn("lantern/tick", [
        f"execute if score #lantern {V} matches 1 if score #m20 {V} matches 7 run function solstice:lantern/keeper",
        f"execute if score #m4 {V} matches 0 run function solstice:lantern/reveal",
    ])
    dp.fn("lantern/reveal", [
        f"execute as @a[gamemode=!spectator] if items entity @s weapon.* {LPRED} at @s run function solstice:lantern/holder",
        "execute as @e[type=text_display,tag=sol.ink,scores={sol.t=1..}] run function solstice:lantern/ink_tick",
    ])
    dp.fn("lantern/holder", [
        "execute as @e[type=text_display,tag=sol.ink,distance=..5] run scoreboard players set @s sol.t 3",
        "execute as @e[type=marker,tag=sol.secret,distance=..3] run function solstice:lantern/secret_found",
        "particle minecraft:end_rod ~ ~1.2 ~ 0.4 0.4 0.4 0.01 2",
    ])
    dp.fn("lantern/ink_tick", [
        "scoreboard players remove @s sol.t 1",
        "execute if score @s sol.t matches 1.. unless entity @s[tag=sol.shown] run function solstice:lantern/ink_show",
        "execute if score @s sol.t matches 0 if entity @s[tag=sol.shown] run function solstice:lantern/ink_hide",
    ])
    dp.fn("lantern/ink_show", [
        "tag @s add sol.shown",
        "data merge entity @s {start_interpolation:0,interpolation_duration:8,transformation:{scale:[1f,1f,1f]}}",
        "execute at @s run particle minecraft:enchant ~ ~ ~ 0.5 0.3 0.5 0.5 20",
        "execute at @s run playsound minecraft:block.amethyst_block.chime master @a[distance=..8] ~ ~ ~ 0.5 1.8",
        "execute if entity @s[tag=sol.once] run function solstice:lantern/ink_once",
    ])
    dp.fn("lantern/ink_hide", [
        "tag @s remove sol.shown",
        "data merge entity @s {start_interpolation:0,interpolation_duration:8,transformation:{scale:[0f,0f,0f]}}",
    ])


INK_ONCE = {}   # tag -> commandes : première révélation d’une encre marquée sol.once + sol.i_<tag>


def ink_once(key, cmds):
    INK_ONCE[key] = cmds


def build_late(dp):
    """Appelé après les salles : dispatch des premières révélations et des secrets."""
    dp.fn("lantern/ink_once", ["tag @s remove sol.once"] +
          [f"execute if entity @s[tag=sol.i_{k}] run function solstice:lantern/once/{k}" for k in sorted(INK_ONCE)])
    for k, cmds in INK_ONCE.items():
        dp.fn(f"lantern/once/{k}", cmds)
    dp.fn("lantern/secret_found", [
        "tag @s remove sol.secret",
        "execute at @s run particle minecraft:end_rod ~ ~0.5 ~ 0.6 0.6 0.6 0.05 40",
        "execute at @s run playsound minecraft:block.beacon.activate master @a[distance=..16] ~ ~ ~ 0.8 1.6",
        *[f"execute if entity @s[tag=sol.s_{k}] run function solstice:lantern/secret/{k}" for k in sorted(SECRETS)],
    ])
    for k, cmds in SECRETS.items():
        dp.fn(f"lantern/secret/{k}", cmds)
