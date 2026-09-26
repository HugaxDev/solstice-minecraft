"""Tirages au sort des rôles, sans @r ni limit=1.

Chaque candidat tire un nombre ; celui dont le rang est 0 (plus petit tirage) est choisi. Égalités re-tirées.
roles/draw : rôles 1, 2, 3 distribués aux présents (étiquettes sol.ro1..ro3 + score sol.role).
Rôles vacants (moins de 3 joueurs, mode debug) : l’étiquette est donnée à tous les présents (#vacN = 1).
Option : #noheal = 1 → le joueur étiqueté sol.prev ne peut pas recevoir le rôle 1 (Siège : le Guérisseur change).
"""
from .core import V, T, jdump, tellraw, title


def build(dp):
    dp.fn("roles/rank", [
        f"scoreboard players set #cnt {V} 0",
        f"scoreboard players operation #me {V} = @s sol.rnd",
        f"execute as @a[tag=sol.cand] if score @s sol.rnd < #me {V} run scoreboard players add #cnt {V} 1",
        f"scoreboard players operation @s sol.rank = #cnt {V}",
    ])
    dp.fn("roles/pick", [
        "tag @a remove sol.pick",
        "execute as @a[tag=sol.cand] store result score @s sol.rnd run random value 0..999999999",
        "execute as @a[tag=sol.cand] run function solstice:roles/rank",
        f"execute store result score #zero {V} if entity @a[tag=sol.cand,scores={{sol.rank=0}}]",
        f"scoreboard players add #tries {V} 1",
        f"execute if score #zero {V} matches 2.. if score #tries {V} matches ..20 run return run function solstice:roles/pick",
        "execute as @a[tag=sol.cand,scores={sol.rank=0}] run tag @s add sol.pick",
    ])
    draw = [
        "tag @a remove sol.ro1", "tag @a remove sol.ro2", "tag @a remove sol.ro3",
        "execute as @a run function solstice:player/clear_role",
        "tag @a add sol.cand",
    ]
    for r in (1, 2, 3):
        pre, post = [], []
        if r == 1:
            pre = [f"execute if score #noheal {V} matches 1 if entity @a[tag=sol.cand,tag=!sol.prev] run tag @a[tag=sol.prev] remove sol.cand"]
            post = [f"execute if score #noheal {V} matches 1 run tag @a[tag=sol.prev,scores={{sol.role=0}}] add sol.cand"]
        draw += pre + [
            f"scoreboard players set #tries {V} 0",
            "function solstice:roles/pick",
            f"execute as @a[tag=sol.pick] run function solstice:roles/give{r}",
        ] + post
        dp.fn(f"roles/give{r}", [f"scoreboard players set @s sol.role {r}", f"tag @s add sol.ro{r}",
                                 f"scoreboard players operation @s sol.rroom = #room {V}",
                                 "tag @s remove sol.cand", "tag @s remove sol.pick"])
    for r in (1, 2, 3):
        draw += [f"scoreboard players set #vac{r} {V} 0",
                 f"execute unless entity @a[scores={{sol.role={r}}}] run scoreboard players set #vac{r} {V} 1",
                 f"execute if score #vac{r} {V} matches 1 as @a run function solstice:roles/vac{r}"]
        dp.fn(f"roles/vac{r}", [f"tag @s add sol.ro{r}", f"scoreboard players operation @s sol.rroom = #room {V}"])
    draw += ["tag @a remove sol.cand", "tag @a remove sol.pick", f"scoreboard players add #draws {V} 1"]
    dp.fn("roles/draw", draw)
    revac = []
    for r in (1, 2, 3):
        revac += [f"scoreboard players set #vac{r} {V} 0",
                  f"execute unless entity @a[scores={{sol.role={r}}}] run scoreboard players set #vac{r} {V} 1",
                  f"execute if score #vac{r} {V} matches 1 as @a run function solstice:roles/vac{r}"]
    dp.fn("roles/revac", revac)
    # un joueur arrivé après le tirage prend le premier rôle vacant
    dp.fn("roles/fill_vacant", [
        f"execute if score #vac1 {V} matches 1 run return run function solstice:roles/take1",
        f"execute if score #vac2 {V} matches 1 run return run function solstice:roles/take2",
        f"execute if score #vac3 {V} matches 1 run return run function solstice:roles/take3",
        # aucun rôle vacant (4e joueur) : il peut aider partout
        "tag @s add sol.ro1", "tag @s add sol.ro2", "tag @s add sol.ro3",
        f"scoreboard players operation @s sol.rroom = #room {V}",
    ])
    for r in (1, 2, 3):
        dp.fn(f"roles/take{r}", [f"scoreboard players set #vac{r} {V} 0", f"function solstice:roles/give{r}",
                                 f"tag @a[scores={{sol.role=1..3}}] remove sol.r{r}", f"tag @s add sol.ro{r}"])


def announce(dp, name, roles, room_color="gold"):
    """Fonction d’annonce : title personnel + récapitulatif en chat. roles = [(nom, couleur, description)]."""
    body = []
    for r, (rname, color, desc) in enumerate(roles, 1):
        body += [f"execute as @a[scores={{sol.role={r}}}] run title @s times 10 70 20",
                 f"execute as @a[scores={{sol.role={r}}}] run title @s subtitle {jdump(T(desc, 'gray'))}",
                 f"execute as @a[scores={{sol.role={r}}}] run title @s title {jdump(T(rname, color, bold=True))}"]
    body.append(tellraw("@a", T("⚄ Tirage au sort", room_color, bold=True)))
    for r, (rname, color, desc) in enumerate(roles, 1):
        body.append(f"execute if score #vac{r} {V} matches 0 run " + tellraw(
            "@a", T("  • ", "dark_gray"), T(rname, color, bold=True), T(" : ", "gray"),
            {"selector": f"@a[scores={{sol.role={r}}}]", "color": "white"}))
        body.append(f"execute if score #vac{r} {V} matches 1 run " + tellraw(
            "@a", T("  • ", "dark_gray"), T(rname, color, bold=True), T(" : vacant (tout le monde peut le jouer)", "gray")))
    body.append("execute as @a at @s run playsound minecraft:block.note_block.chime master @s ~ ~ ~ 1 1.2")
    dp.fn(name, body)
