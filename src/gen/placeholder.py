"""Salle factice (squelette) : plateforme + 3 dalles ; terminée quand #need joueurs se tiennent sur les dalles.
Sert à valider la chaîne complète avant les vraies salles, puis est remplacée salle par salle."""
from .core import V, fill, setblock, text_display, T
from .flow import obj
from .layout import ROOMS


def build(dp, n, done="function solstice:flow/complete"):
    ox, oy, oz = ROOMS[n]["origin"]
    cp = (ox + 0.5, oy + 1, oz + 8.5, 180)
    plates = [(ox - 3, oz - 6), (ox, oz - 6), (ox + 3, oz - 6)]
    b = [f"kill @e[type=!player,tag=sol.r{n}]"]
    b += fill(ox - 12, oy - 2, oz - 12, ox + 12, oy + 8, oz + 12, "air")
    b += fill(ox - 10, oy, oz - 10, ox + 10, oy, oz + 10, "smooth_stone")
    for (x, z) in plates:
        b.append(setblock(x, oy + 1, z, "heavy_weighted_pressure_plate"))
    b.append(text_display(ox + 0.5, oy + 3, oz - 6.5, ["", T(ROOMS[n]["name"], ROOMS[n]["color"], bold=True),
                                                       T("\n(salle en construction)", "gray")], [f"sol.r{n}"]))
    dp.fn(f"build/r{n}", b)
    dp.fn(f"r{n}/start", [obj(f"{ROOMS[n]['short']} : tenez-vous tous sur les dalles")])
    dp.fn(f"r{n}/cp", [f"tp @s {cp[0]} {cp[1]} {cp[2]} {cp[3]} 0", f"spawnpoint @s {int(cp[0])} {cp[1]} {int(cp[2])}"])
    dp.fn(f"r{n}/enter", [f"function solstice:r{n}/cp"])
    dp.fn(f"r{n}/respawn", [f"function solstice:r{n}/cp"])
    dp.fn(f"r{n}/wipe", [])
    on = " ".join(f"@a[x={x},y={oy + 1},z={z},dx=0,dy=1,dz=0]" for x, z in plates)
    dp.fn(f"r{n}/tick", [
        f"scoreboard players set #on {V} 0",
        *[f"execute if entity @a[x={x},y={oy + 1},z={z},dx=0,dy=1,dz=0,tag=!sol.dn] run scoreboard players add #on {V} 1"
          for x, z in plates],
        f"execute if score #on {V} >= #need {V} run {done}",
    ])
    dp.meta.setdefault("forceload", []).append((ox - 12, oz - 12, ox + 12, oz + 12))
    dp.meta.setdefault("rooms", {})[str(n)] = {"cp": cp, "plates": plates, "placeholder": True}
    dp.meta.setdefault("builds", []).append(f"build/r{n}")
    dp.test(f"salle {n} (factice) : dalles posées", f"block {plates[0][0]} {oy + 1} {plates[0][1]} heavy_weighted_pressure_plate")
