"""Systèmes transverses : objectifs, load/tick, cycle de vie du joueur (arrivée, mort, fantôme, reconnexion)."""
from .core import NS, V, T, jdump, tellraw, title, actionbar, orel, narr, sound, Item

OBJECTIVES = [
    ("sol.var", "dummy", "Variables"),
    ("sol.room", "dummy", "Salle"),
    ("sol.joined", "dummy", "Arrivé"),
    ("sol.role", "dummy", "Rôle"),
    ("sol.deaths", "deathCount", "Morts (à traiter)"),
    ("sol.dall", "dummy", "Morts"),
    ("sol.leave", "minecraft.custom:minecraft.leave_game", "Déconnexions"),
    ("sol.down", "dummy", "À terre"),
    ("sol.cool", "dummy", "Délai clic"),
    ("sol.rnd", "dummy", "Tirage"),
    ("sol.rank", "dummy", "Rang"),
    ("sol.use", "minecraft.used:minecraft.carrot_on_a_stick", "Objet utilisé"),
    ("sol.horn", "minecraft.used:minecraft.goat_horn", "Cor"),
    ("sol.t", "dummy", "Minuteur"),
    ("sol.k", "dummy", "Compteur"),
    ("sol.y", "dummy", "Altitude"),
    ("sol.track", "dummy", "Parcours"),
    ("sol.vote", "dummy", "Vote"),
    ("sol.cp", "dummy", "Checkpoint"),
    ("sol.test", "dummy", "Tests"),
    ("sol.sneak", "minecraft.custom:minecraft.sneak_time", "Accroupi"),
    ("sol.rroom", "dummy", "Salle du rôle"),
]

GAMERULES = {
    "doDaylightCycle": "false", "doWeatherCycle": "false", "doMobSpawning": "false",
    "keepInventory": "true", "fallDamage": "false", "doImmediateRespawn": "true",
    "announceAdvancements": "false", "commandBlockOutput": "false", "mobGriefing": "false",
    "doFireTick": "false", "spawnRadius": "0", "doInsomnia": "false", "doPatrolSpawning": "false",
    "doTraderSpawning": "false", "disableRaids": "true", "randomTickSpeed": "0",
    "doWardenSpawning": "false", "spectatorsGenerateChunks": "false", "logAdminCommands": "false",
    "maxCommandChainLength": "10000000", "showDeathMessages": "false", "doMobLoot": "false",
    "doTileDrops": "false", "doEntityDrops": "false", "drowningDamage": "true", "fireDamage": "true",
    "naturalRegeneration": "true", "sendCommandFeedback": "true", "playersSleepingPercentage": "101",
    "spawnChunkRadius": "0",
}

KEEP = "*[!custom_data~{sol:{keep:1b}}]"     # tout sauf les objets permanents (Lanterne, Carnet)
GHOST_TICKS = 200

# globales initialisées seulement si absentes (un rechargement ne perd rien)
GLOBALS = {"#room": 0, "#trans": 0, "#need": 3, "#started": 0, "#gtime": 0, "#rt": 0, "#ht": 0, "#hk": 0,
           "#step": 0, "#rdeaths": 0, "#np": 0, "#ended": 0, "#wipes": 0, "#combat": 0, "#win": 60,
           "#debug": 0, "#pstart": 0}
CONSTS = [2, 3, 4, 5, 8, 10, 16, 20, 40, 60, 100, 200, 1000, 1200, 3600, 72000]


def build(dp):
    load = [f"scoreboard objectives add {o} {c} {jdump(T(d))}" for o, c, d in OBJECTIVES]
    load += [f"gamerule {k} {v}" for k, v in GAMERULES.items()]
    load += ["weather clear 1000000",
             "execute store result score #diff sol.var run difficulty",
             "execute if score #diff sol.var matches 0 run function solstice:system/not_peaceful"]
    load += [f"scoreboard players set #c{c} {V} {c}" for c in CONSTS]
    for h, v in GLOBALS.items():
        load.append(f"execute unless score {h} {V} matches -2147483648..2147483647 run scoreboard players set {h} {V} {v}")
    load += ["bossbar add solstice:obj \"Solstice\"", "bossbar set solstice:obj style progress",
             "bossbar set solstice:obj max 100", "bossbar set solstice:obj value 100",
             "bossbar set solstice:obj visible true",
             "scoreboard players set #loaded sol.var 1",
             "function solstice:flow/refresh_obj"]
    dp.fn("load", load)
    dp.json(f"data/minecraft/tags/function/load.json", {"values": [f"{NS}:load"]})
    dp.json(f"data/minecraft/tags/function/tick.json", {"values": [f"{NS}:tick"]})
    dp.fn("system/not_peaceful", [
        "difficulty normal",
        tellraw("@a", T("[Solstice] ", "gold"), T("La difficulté Paisible supprime les monstres du Siège et du Cœur : "
                                                  "passage en Normal.", "gray")),
    ])

    dp.fn("tick", [
        f"scoreboard players add #tick {V} 1",
        f"scoreboard players operation #m20 {V} = #tick {V}",
        f"scoreboard players operation #m20 {V} %= #c20 {V}",
        f"scoreboard players operation #m4 {V} = #tick {V}",
        f"scoreboard players operation #m4 {V} %= #c4 {V}",
        f"execute as @a unless score @s sol.joined matches 1 run function solstice:player/first_join",
        "function solstice:flow/tick",
        "execute as @a at @s run function solstice:player/tick",
    ])

    # ------------------------------------------------------------------ joueur
    dp.fn("player/first_join", [
        "scoreboard players set @s sol.joined 1",
        "scoreboard players reset @s sol.room",
        "scoreboard players set @s sol.role 0",
        "scoreboard players set @s sol.deaths 0",
        "scoreboard players set @s sol.dall 0",
        "scoreboard players set @s sol.leave 0",
        "scoreboard players set @s sol.down 0",
        "scoreboard players set @s sol.use 0",
        "scoreboard players set @s sol.horn 0",
        "scoreboard players set @s sol.sneak 0",
        "scoreboard players set @s sol.vote 0",
        "function solstice:player/clear_tags",
        "clear @s",
        "effect clear @s",
        "gamemode adventure @s",
        "advancement grant @s only solstice:root",
    ])
    dp.fn("player/clear_tags", [f"tag @s remove {t}" for t in (
        "sol.dn", "sol.cand", "sol.pick", "sol.me", "sol.oob", "sol.prev", "sol.ok", "sol.here")] +
          ["function solstice:player/clear_role"])
    dp.fn("player/clear_role", ["scoreboard players set @s sol.role 0", "scoreboard players reset @s sol.rroom",
                                "tag @s remove sol.ro1", "tag @s remove sol.ro2", "tag @s remove sol.ro3"])

    dp.fn("player/tick", [
        "execute store result score @s sol.y run data get entity @s Pos[1]",
        "execute if score @s sol.leave matches 1.. run function solstice:player/rejoined",
        "execute if score @s sol.deaths matches 1.. run function solstice:player/on_death",
        "execute if score @s sol.down matches 1.. run function solstice:player/down_tick",
        f"execute if score #trans {V} matches 0 if score #pstart {V} matches 0 unless score @s sol.room = #room {V} run function solstice:flow/enter",
        f"execute if score #trans {V} matches 0 if score @s sol.room = #room {V} run function solstice:flow/ptick",
        "execute if score @s sol.cool matches 1.. run scoreboard players remove @s sol.cool 1",
        "scoreboard players set @s sol.use 0",
        "scoreboard players set @s sol.horn 0",
    ])

    # Mort : réapparition au checkpoint ; salles de combat : 10 s en spectateur d’un coéquipier.
    dp.fn("player/on_death", [
        "scoreboard players set @s sol.deaths 0",
        "scoreboard players add @s sol.dall 1",
        f"scoreboard players add #rdeaths {V} 1",
        f"execute unless score @s sol.room = #room {V} run return 0",
        f"execute if score #trans {V} matches 1.. run return 0",
        "tag @s add sol.dn",
        f"scoreboard players set @s sol.down {GHOST_TICKS}",
        "function solstice:rooms/respawn",
        f"execute if score #combat {V} matches 1 run function solstice:player/ghost_start",
        f"execute if score #combat {V} matches 0 run gamemode adventure @s",
        f"execute if score #combat {V} matches 0 run " + actionbar("@s", "Vous revoilà au dernier point de passage.", "gray"),
        "execute unless entity @a[tag=!sol.dn] run function solstice:flow/wipe",
    ])
    dp.fn("player/ghost_start", [
        "gamemode spectator @s",
        "spectate @a[tag=!sol.dn,gamemode=!spectator,sort=nearest,limit=1] @s",
        *title("@s", "À terre", "Vous observez un coéquipier… retour dans 10 secondes.", color="red", times=(5, 50, 10)),
        "playsound minecraft:entity.player.hurt master @s ~ ~ ~ 1 0.6",
    ])
    dp.fn("player/down_tick", [
        "scoreboard players remove @s sol.down 1",
        # le coéquipier observé est tombé à son tour : on en suit un autre
        "execute if entity @s[gamemode=spectator] if score #m20 sol.var matches 0 run "
        "spectate @a[tag=!sol.dn,gamemode=!spectator,sort=nearest,limit=1] @s",
        "execute if score @s sol.down matches 0 run function solstice:player/down_end",
    ])
    dp.fn("player/down_end", [
        "tag @s remove sol.dn",
        "execute if entity @s[gamemode=spectator] run function solstice:player/ghost_end",
    ])
    dp.fn("player/ghost_end", [
        "spectate",
        "gamemode adventure @s",
        "function solstice:rooms/respawn",
        actionbar("@s", "De retour dans la bataille !", "gold"),
    ])
    dp.fn("player/revive", [
        "tag @s remove sol.dn",
        "scoreboard players set @s sol.down 0",
        "execute if entity @s[gamemode=spectator] run spectate",
        "gamemode adventure @s",
        "effect clear @s",
        "effect give @s saturation infinite 0 true",
        "function solstice:rooms/respawn",
    ])
    # Reconnexion : remis dans la salle en cours, avec son rôle (rN/enter est idempotent).
    dp.fn("player/rejoined", [
        "scoreboard players set @s sol.leave 0",
        "execute if score @s sol.down matches 1.. run scoreboard players set @s sol.down 1",
        "execute unless entity @s[tag=sol.dn] run gamemode adventure @s",
        "function solstice:lantern/on_rejoin",
        "function solstice:story/sync_player",
        f"execute if score #trans {V} matches 0 if score @s sol.room = #room {V} run function solstice:rooms/enter",
        f"execute if score #room {V} matches 1.. run " + orel("Vous revoilà ! Le groupe ne vous a pas attendu, mais presque.", "@s"),
    ])

    # objets : tout sauf les permanents
    dp.fn("player/clear_items", [f"clear @s {KEEP}"])
    dp.fn("player/base_effects", [
        "effect give @s saturation infinite 0 true",
    ])
