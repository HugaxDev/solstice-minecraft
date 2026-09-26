"""Fonctions de debug (README) : utilisables avec /function en mode triche (hôte)."""
from .core import V, T, tellraw
from .layout import ROOMS, LAST_ROOM


def build(dp):
    dp.fn("debug/reset_salle", [
        "kill @e[type=!player,tag=sol.mob]",
        f"scoreboard players set #trans {V} 0",
        "execute as @a run function solstice:player/clear_role",
        "function solstice:flow/room_setup",
        "scoreboard players reset @a sol.room",
        "function solstice:flow/start_room",
        "execute as @a run function solstice:player/revive",
        tellraw("@a", T("[debug] Salle en cours réinitialisée.", "red")),
    ])
    dp.fn("debug/salle_suivante", [
        tellraw("@a", T("[debug] Salle passée.", "red")),
        f"execute if score #room {V} matches ..{LAST_ROOM - 1} run function solstice:flow/complete",
        f"execute if score #room {V} matches {LAST_ROOM} run function solstice:end/start",
    ])
    for n in (1, 2, 3):
        dp.fn(f"debug/joueurs_{n}", [
            f"scoreboard players set #need {V} {n}",
            f"scoreboard players set #debug {V} {1 if n < 3 else 0}",
            f"scoreboard players set #win {V} {60 if n == 3 else 1200}",
            "function solstice:roles/revac",
            tellraw("@a", T(f"[debug] Partie réglée pour {n} joueur(s).", "red"),
                    T(" Rôles vacants : joués par tout le monde ou par l’automate d’Orel." if n < 3 else "", "gray")),
        ])
    for n in range(0, LAST_ROOM + 1):
        dp.fn(f"debug/aller_salle_{n}", [
            "kill @e[type=!player,tag=sol.mob]",
            f"scoreboard players set #trans {V} 0",
            f"scoreboard players set #ended {V} 0",
            f"scoreboard players set #room {V} {n}",
            f"scoreboard players set #started {V} 1" if n > 0 else f"scoreboard players set #started {V} 0",
            "execute as @a run function solstice:player/clear_role",
            "function solstice:flow/room_setup",
            "scoreboard players reset @a sol.room",
            "function solstice:flow/start_room",
            "execute as @a run function solstice:player/revive",
            tellraw("@a", T(f"[debug] Aller à la salle {n} : {ROOMS[n]['name']}.", "red")),
        ])
    dp.fn("debug/nouvelle_partie", [
        "function solstice:flow/new_game",
        tellraw("@a", T("[debug] Nouvelle partie.", "red")),
    ])
