"""Enchaînement linéaire des salles : entrée, transitions narratives, anéantissement, bornes, bossbar d’objectif.

États globaux : #room (salle courante 0..8), #trans (0 = en jeu, >0 = transition en cours, en ticks),
#rt (ticks dans la salle), #step (étape de la salle), #combat (salle de combat), #gtime (temps de partie).
"""
from .core import V, T, jdump, tellraw, title, actionbar, orel, narr, sound
from .layout import ROOMS, LAST_ROOM
from .system import KEEP

HOOKS = ["start", "enter", "tick", "ptick", "cp", "respawn", "wipe", "hint", "on_complete"]
TRANS_TICKS = 200

# Transitions narratives : texte affiché entre la salle n et la salle n+1
TRANSITIONS = {
    0: ["L’Express du Solstice siffle dans la brume…",
        "« Montez, montez ! Il ne s’arrête plus depuis que le temps s’est détraqué. »"],
    1: ["Le train freine enfin au pied du Pic du Solstice.",
        "Devant vous, la Tour des Engrenages grince comme une vieille horloge."],
    2: ["Au sommet de la tour, une porte ronde s’ouvre sur une odeur d’huile et de laiton.",
        "« Bienvenue dans mon vieil atelier. Ne touchez à rien. Enfin, touchez à tout, mais avec respect. »"],
    3: ["La Lanterne des Saisons s’allume au creux de vos mains.",
        "Plus bas, les cloches du Sanctuaire sonnent l’alarme : les gardiens se sont réveillés."],
    4: ["Le dernier sceau cède. Le silence retombe sur le Sanctuaire.",
        "Un escalier descend vers l’obscurité. Il y fait… nuit."],
    5: ["Enfin, l’aube.",
        "Au-delà de la nuit, une vallée où les saisons se sont mélangées."],
    6: ["Les quatre cristaux brillent à nouveau. Le Calendrier respire.",
        "Il ne reste qu’une porte : celle du Cœur."],
}


def room_dispatch(dp, hook):
    dp.fn(f"rooms/{hook}", [f"execute if score #room {V} matches {n} run function solstice:r{n}/{hook}"
                            for n in sorted(ROOMS)])


def build(dp):
    for hook in HOOKS:
        room_dispatch(dp, hook)

    # ------------------------------------------------------------- tick global
    dp.fn("flow/tick", [
        f"execute store result score #np {V} if entity @a",
        # Paisible supprime tous les monstres (Express, Siège, Cœur…) : repassé en Normal, dans toutes les salles
        f"execute if score #m20 {V} matches 13 store result score #diff {V} run difficulty",
        f"execute if score #m20 {V} matches 13 if score #diff {V} matches 0 run function solstice:system/not_peaceful",
        f"execute if score #started {V} matches 1 if score #ended {V} matches 0 run scoreboard players add #gtime {V} 1",
        f"execute if score #trans {V} matches 1.. run return run function solstice:flow/trans_tick",
        f"execute if score #pstart {V} matches 1 run return run function solstice:flow/start_room",
        f"scoreboard players add #rt {V} 1",
        "function solstice:hints/tick",
        "function solstice:rooms/tick",
        "function solstice:lantern/tick",
    ])
    # tick joueur dans la salle courante : bornes + logique de salle
    dp.fn("flow/ptick", [
        "execute if entity @s[gamemode=!spectator] run function solstice:flow/bounds",
        "function solstice:rooms/ptick",
    ])
    b = ["tag @s add sol.oob"]
    for n, r in ROOMS.items():
        for (x1, y1, z1, x2, y2, z2) in r["boxes"]:
            b.append(f"execute if score #room {V} matches {n} if entity @s[x={x1},y={y1},z={z1},dx={x2 - x1},"
                     f"dy={y2 - y1},dz={z2 - z1}] run tag @s remove sol.oob")
    b += ["execute if entity @s[tag=sol.oob] run function solstice:flow/oob", "tag @s remove sol.oob"]
    dp.fn("flow/bounds", b)
    dp.fn("flow/oob", [
        "function solstice:rooms/cp",
        actionbar("@s", "Le temps vous ramène en arrière…", "dark_aqua"),
        "playsound minecraft:block.respawn_anchor.deplete master @s ~ ~ ~ 0.5 1.4",
    ])

    # ------------------------------------------------------------- entrée dans la salle courante
    dp.fn("flow/enter", [
        f"scoreboard players operation @s sol.room = #room {V}",
        "function solstice:player/clear_items",
        *[f"tag @s remove {t}" for t in ("sol.dn", "sol.cand", "sol.pick", "sol.me", "sol.oob", "sol.ok", "sol.here")],
        # un rôle ne vaut que pour la salle où il a été tiré (joueur absent pendant le tirage, salle précédente…)
        f"execute unless score @s sol.rroom = #room {V} run function solstice:player/clear_role",
        "scoreboard players set @s sol.down 0",
        "execute if entity @s[gamemode=spectator] run spectate",
        "gamemode adventure @s",
        "effect clear @s",
        "function solstice:player/base_effects",
        "attribute @s minecraft:generic.max_health base set 20",
        "attribute @s minecraft:generic.movement_speed base set 0.1",
        "attribute @s minecraft:generic.attack_damage base set 1",
        "attribute @s minecraft:generic.knockback_resistance base set 0",
        "attribute @s minecraft:generic.armor base set 0",
        "effect give @s instant_health 1 5 true",
        "function solstice:story/sync_player",
        "function solstice:rooms/enter",
    ])

    # ------------------------------------------------------------- fin de salle → transition
    dp.fn("flow/complete", [
        f"execute if score #trans {V} matches 1.. run return 0",
        f"execute if score #room {V} matches {LAST_ROOM + 1}.. run return 0",
        f"scoreboard players set #trans {V} 1",
        *[f"execute if score #room {V} matches {n} run advancement grant @a only solstice:room/r{n}"
          for n in range(0, LAST_ROOM + 1)],
        "function solstice:rooms/on_complete",
        "kill @e[type=!player,tag=sol.mob]",
        "execute as @a run function solstice:flow/trans_player",
    ])
    dp.fn("flow/trans_player", [
        "tag @s remove sol.dn",
        "scoreboard players set @s sol.down 0",
        "execute if entity @s[gamemode=spectator] run spectate",
        "gamemode adventure @s",
        "effect give @s resistance 12 255 true",
        "effect give @s slowness 12 6 true",
        "playsound minecraft:block.bell.resonate master @s ~ ~ ~ 1 0.7",
        "playsound minecraft:ui.toast.challenge_complete master @s ~ ~ ~ 0.8 1",
    ])
    tt = [f"scoreboard players add #trans {V} 1"]
    for n in range(0, LAST_ROOM):
        lines = TRANSITIONS.get(n, [])
        nxt = ROOMS[n + 1]
        done = ROOMS[n]
        sub = dp.fn(f"flow/trans/r{n}_a", [
            *title("@a", "Salle terminée", done["name"], color=done["color"], subcolor="gray", times=(10, 50, 10)),
        ])
        tt.append(f"execute if score #room {V} matches {n} if score #trans {V} matches 5 run function {sub}")
        for i, line in enumerate(lines):
            sub = dp.fn(f"flow/trans/r{n}_l{i}", [narr(line, "@a", "white"),
                                                  "execute as @a at @s run playsound minecraft:block.amethyst_block.chime master @s ~ ~ ~ 0.8 0.9"])
            tt.append(f"execute if score #room {V} matches {n} if score #trans {V} matches {60 + 50 * i} run function {sub}")
        sub = dp.fn(f"flow/trans/r{n}_z", [
            "execute as @a run effect give @s blindness 3 0 true",
            *title("@a", nxt["name"], f"Salle {n + 1}", color=nxt["color"], subcolor="gray", times=(20, 60, 20)),
        ])
        tt.append(f"execute if score #room {V} matches {n} if score #trans {V} matches {TRANS_TICKS - 40} run function {sub}")
    tt.append(f"execute if score #trans {V} matches {TRANS_TICKS}.. run function solstice:flow/next_room")
    dp.fn("flow/trans_tick", tt)

    dp.fn("flow/next_room", [
        f"scoreboard players set #trans {V} 0",
        f"scoreboard players add #room {V} 1",
        "execute as @a run function solstice:player/clear_role",
        "function solstice:flow/room_setup",
        "function solstice:flow/start_room",
        "function solstice:flow/refresh_obj",
    ])
    # démarrage d’une salle seulement quand sa zone est chargée (entités créées dans un chunk non chargé = perdues) :
    # sinon on réessaie à chaque tick (#pstart), les joueurs attendent en transition.
    chk = [f"scoreboard players set #zl {V} 1"]
    for n, r in ROOMS.items():
        for (x1, y1, z1, x2, y2, z2) in r["boxes"]:
            cxm, czm = (x1 + x2) // 2, (z1 + z2) // 2
            chk.append(f"execute if score #room {V} matches {n} unless loaded {cxm} 100 {czm} run scoreboard players set #zl {V} 0")
    dp.fn("flow/zone_loaded", chk)
    dp.fn("flow/start_room", [
        "function solstice:flow/zone_loaded",
        f"execute if score #zl {V} matches 0 run return run scoreboard players set #pstart {V} 1",
        f"scoreboard players set #pstart {V} 0",
        "function solstice:rooms/start",
    ])
    # réglages communs d’une salle (heure, combat, compteurs)
    rs = [f"scoreboard players set #rt {V} 0", f"scoreboard players set #rdeaths {V} 0",
          f"scoreboard players set #step {V} 0", "function solstice:hints/reset",
          "kill @e[type=!player,tag=sol.mob]"]
    for n, r in ROOMS.items():
        rs.append(f"execute if score #room {V} matches {n} run time set {r['time']}")
        rs.append(f"execute if score #room {V} matches {n} run scoreboard players set #combat {V} {1 if r['combat'] else 0}")
        rs.append(f"execute if score #room {V} matches {n} run bossbar set solstice:obj color {r['bar']}")
        rs.append(f"execute if score #room {V} matches {n} run gamerule naturalRegeneration {'false' if r['combat'] else 'true'}")
    dp.fn("flow/room_setup", rs)

    # ------------------------------------------------------------- anéantissement du groupe
    dp.fn("flow/wipe", [
        f"scoreboard players add #wipes {V} 1",
        *title("@a", "Le groupe est tombé", "La salle se réinitialise…", color="dark_red", times=(10, 60, 20)),
        "execute as @a at @s run playsound minecraft:entity.wither.spawn master @s ~ ~ ~ 0.4 1.6",
        "kill @e[type=!player,tag=sol.mob]",
        "function solstice:rooms/wipe",
        "execute as @a run function solstice:player/revive",
        "function solstice:hints/reset",
    ])

    # ------------------------------------------------------------- bossbar d’objectif
    dp.fn("flow/refresh_obj", [
        "bossbar set solstice:obj players @a",
    ])

    # ------------------------------------------------------------- reset complet de la partie (debug)
    dp.fn("flow/new_game", [
        f"scoreboard players set #room {V} 0",
        f"scoreboard players set #trans {V} 0",
        f"scoreboard players set #started {V} 0",
        f"scoreboard players set #ended {V} 0",
        f"scoreboard players set #gtime {V} 0",
        f"scoreboard players set #wipes {V} 0",
        "function solstice:story/reset",
        "function solstice:lantern/reset",
        "function solstice:flow/room_setup",
        "function solstice:flow/start_room",
        "execute as @a run function solstice:flow/new_game_player",
    ])
    dp.fn("flow/new_game_player", [
        "scoreboard players reset @s sol.room",
        "scoreboard players set @s sol.dall 0",
        "advancement revoke @s from solstice:root",
        "advancement grant @s only solstice:root",
        "clear @s",
    ])


def obj(text, color="white", sub=None):
    """Commande : titre de la bossbar d’objectif (objectif court, sans solution)."""
    parts = ["", T("◆ ", "gold"), T(text, color)]
    if sub:
        parts.append(T("  " + sub, "gray"))
    return f"bossbar set solstice:obj name {jdump(parts)}"


def stub_missing(dp):
    """Crée les crochets absents (vides) pour chaque salle."""
    for n in ROOMS:
        for hook in HOOKS:
            name = f"r{n}/{hook}"
            if name not in dp.functions:
                dp.fn(name, [])
