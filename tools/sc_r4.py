"""Scénarios salle 4 — Le Siège du Sanctuaire : rôles re-tirés à chaque sceau (Guérisseur toujours différent),
équipements, vagues, mécanismes réservés au Guérisseur, les 6 énigmes (erreurs comprises), butins, indices,
soin et provocation, mort (spectateur), anéantissement (le sceau en cours recommence), reconnexion."""
from testlib import BOTS, V
from scenarios import ensure_room, finish_transition, no_way_back, SPAWN

STAFF = "carrot_on_a_stick[custom_data~{sol:{staff:1b}}]"
SWORD = "iron_sword[custom_data~{sol:{gear:1b}}]"
HORN = "goat_horn[custom_data~{sol:{gear:1b}}]"


def M(t):
    return t.meta["rooms"]["4"]


def roles(t):
    return {t.score(b, "sol.role"): b for b in BOTS}


def shield_all(t, on=True):
    for b in BOTS:
        if on:
            t.rc(f"effect give {b} resistance 100000 255 true")
        else:
            t.rc(f"effect clear {b} resistance")


def click_side(t, who, x, z, h=1.0):
    """Clic depuis l’est (brasero entre deux piliers : on l’aborde par le côté)."""
    t.rc(f"kill @e[type=!player,tag=sol.r4mob,x={x - 4},y=95,z={z - 4},dx=8,dy=10,dz=8]")
    t.rc(f"scoreboard players set {who} sol.cool 0")
    t.look_use(who, (x + 2.4, 101, z + 0.5), (x + 0.5, 101 + h / 2, z + 0.5))


def click_braz(t, who, k, br):
    x, z = br[k]
    if k == 3:
        click_side(t, who, x, z)
    else:
        click_at(t, who, x, z, h=1.0)


def click_at(t, who, x, z, h=1.3, dz=1.9, y0=101):
    # les défenseurs tiennent les gardiens à distance (un gardien sur la ligne de visée prendrait le clic)
    t.rc(
        f"kill @e[type=!player,tag=sol.r4mob,x={x - 4},y=95,z={z - 4},dx=8,dy=10,dz=8]")
    t.rc(f"scoreboard players set {who} sol.cool 0")
    for b in BOTS:
        if b != who:
            p = t.pos(b)
            if p and abs(p[0] - (x + 0.5)) < 2.5 and abs(p[2] - (z + 0.5 + dz)) < 2.5:
                t.tp(b, x + 4.5, 101, z + 4.5)
    t.look_use(who, (x + 0.5, y0, z + 0.5 + dz), (x + 0.5, y0 + h / 2, z + 0.5))


def wait_step(t, k, max_ticks=500):
    t.sprint(20)
    ok = t.wait_until(lambda: t.g("#step") == k and t.g("#s4brk") == 0, max_ticks, 20)
    t.wait(5)
    shield_all(t)
    return ok


def sc_r4_start(t):
    t.section = "salle 4 : rôles et équipement"
    ensure_room(t, 4)
    shield_all(t)
    no_way_back(t, 4)
    t.ok("sceau I après l’introduction", wait_step(t, 1))
    r = roles(t)
    t.ok("tirage : Guérisseur, Chevalier, Tank distincts", sorted(r) == [1, 2, 3], str(r))
    t.ok("Guérisseur : bâton de soin", t.has(r[1], STAFF))
    t.ok("Chevalier : épée", t.has(r[2], SWORD))
    t.ok("Tank : cor de provocation et bouclier", t.has(r[3], HORN) and t.has(r[3], "shield", "weapon.offhand"))
    mh = t.rc(f"attribute {r[3]} minecraft:generic.max_health base get")
    t.ok("Tank : 30 points de vie", "30" in mh, mh)
    t.sprint(160)
    t.ok("vagues : des gardiens attaquent", t.count("@e[tag=sol.r4mob]") >= 1)
    rg = t.rc("gamerule naturalRegeneration")
    t.ok("régénération naturelle coupée (le soin compte)", "false" in rg, rg)
    # soin
    t.rc(f"effect clear {r[2]} resistance")
    t.rc(f"damage {r[2]} 8 minecraft:generic")
    t.wait(2)
    hp0 = t.rc(f"data get entity {r[2]} Health")
    t.tp(r[2], 4000.5, 101, 10.5)
    t.tp(r[1], 4001.5, 101, 10.5)
    for i in range(9):
        if "passed" in t.rc(f"execute if items entity {r[1]} hotbar.{i} {STAFF}"):
            t.rc(f"player {r[1]} hotbar {i + 1}")
    t.wait(2)
    t.rc(f"player {r[1]} use once")
    t.wait(10)
    hp1 = t.rc(f"data get entity {r[2]} Health")
    f = lambda s: float(s.split(":")[-1].strip().rstrip("f")) if ":" in s else 0
    t.ok("Guérisseur : le bâton soigne les alliés proches", f(hp1) > f(hp0), f"{hp0} → {hp1}")
    t.ok("…puis se recharge (10 s)", (t.score(r[1], "sol.t") or 0) > 100)
    shield_all(t)
    # provocation
    t.rc(f"player {r[3]} hotbar 1")
    for i in range(9):
        if "passed" in t.rc(f"execute if items entity {r[3]} hotbar.{i} {HORN}"):
            t.rc(f"player {r[3]} hotbar {i + 1}")
    t.tp(r[3], 4006.5, 101, 3.5)
    t.wait(2)
    t.rc(f"player {r[3]} look up")
    t.wait(2)
    t.rc(f"player {r[3]} use once")
    t.wait(6)
    t.ok("Tank : le cor le rend lumineux (provocation)", "passed" in t.rc(f"execute if entity @a[name={r[3]},nbt={{active_effects:[{{id:\"minecraft:glowing\"}}]}}]"))


def sc_r4_seals(t):
    t.section = "salle 4 : sceaux I à III"
    healers = []
    # --- I : glyphes
    r = roles(t)
    healers.append(r[1])
    p = M(t)["pillars"]
    click_at(t, r[2], *p[t.g("#s1a")], h=2.2)
    t.ok("mécanisme réservé : le Chevalier ne peut pas toucher les piliers", t.g("#s1i") == 0)
    wrong = (t.g("#s1a") + 1) % 5
    click_at(t, r[1], *p[wrong], h=2.2)
    t.ok("sceau I : mauvais pilier → l’ordre repart de zéro", t.g("#s1i") == 0)
    for slot in "abc":
        click_at(t, r[1], *p[t.g(f"#s1{slot}")], h=2.2)
    t.ok("sceau I : trois glyphes dans l’ordre lu par le Guérisseur → brisé", t.g("#s4brk") > 0)
    t.ok("les gardiens reculent (arène vidée)", t.count("@e[tag=sol.r4mob]") == 0)
    # --- II : dalles
    t.ok("sceau II commence", wait_step(t, 2))
    r = roles(t)
    healers.append(r[1])
    t.ok("nouveau tirage : le Guérisseur a changé de joueur", healers[-1] != healers[-2], str(healers))
    plates = M(t)["plates"]
    kx, kz = plates[t.g("#s2k")]
    tx, tz = plates[t.g("#s2t")]
    t.tp(r[2], kx + 0.5, 101, kz + 0.5)
    t.wait(50)
    t.ok("sceau II : le Chevalier seul sur sa dalle ne suffit pas", t.g("#s4brk") == 0)
    for _ in range(6):               # les gardiens repoussent : on tient la position (coéquipiers qui défendent)
        if t.g("#s4brk") > 0 or t.g("#step") == 3:
            break
        t.rc("kill @e[type=!player,tag=sol.r4mob]")
        t.tp(r[2], kx + 0.5, 101, kz + 0.5)
        t.tp(r[3], tx + 0.5, 101, tz + 0.5)
        t.wait(30)
    t.ok("sceau II : Chevalier et Tank sur les dalles annoncées 3 s → brisé", t.g("#s4brk") > 0 or t.g("#step") == 3,
         f"hold={t.g('#s2h')} k={t.g('#s2k')} t={t.g('#s2t')}")
    # --- III : devinette
    t.ok("sceau III commence", wait_step(t, 3))
    r = roles(t)
    healers.append(r[1])
    t.ok("le Guérisseur change encore", healers[-1] != healers[-2], str(healers))
    st = M(t)["statues"]
    ans = t.g("#s3")
    n0 = t.count("@e[tag=sol.r4mob]")
    click_at(t, r[1], *st[(ans + 1) % 4], h=3.2)
    t.ok("sceau III : mauvaise statue → des gardiens surgissent", t.g("#s4brk") == 0 and t.count("@e[tag=sol.r4mob]") > n0)
    t.rc("execute as @e[type=zombie,tag=sol.r4mob,name=\"Gardien des Jardins\"] run kill @s")
    t.wait(10)
    t.rc(f"tp {r[2]} @e[type=item,limit=1,nbt={{Item:{{components:{{\"minecraft:custom_data\":{{sol:{{gant:1b}}}}}}}}}}]")
    t.wait(30)
    t.ok("le Gardien des Jardins lâche un gant → indice « gant »", t.g("#clue_gant") == 1)
    click_at(t, r[1], *st[ans], h=3.2)
    t.ok("sceau III : la bonne statue → brisé", t.g("#s4brk") > 0)
    t.healers = healers


def sc_r4_deaths(t):
    t.section = "salle 4 : morts, anéantissement, reconnexion"
    t.ok("sceau IV commence", wait_step(t, 4))
    r = roles(t)
    knight = r[2]
    t.rc(f"effect clear {knight} resistance")
    t.kill_respawn(knight, SPAWN)
    t.ok("le Chevalier tombe → spectateur d’un coéquipier", t.gm(knight, "spectator") and t.tag(knight, "sol.dn"))
    t.sprint(220)
    t.wait(5)
    t.ok("10 s plus tard : de retour, avec son épée", t.gm(knight, "adventure") and t.has(knight, SWORD))
    tank = roles(t)[3]
    t.leave(tank)
    t.wait(30)
    t.join(tank, SPAWN)
    t.wait(20)
    mh = t.rc(f"attribute {tank} minecraft:generic.max_health base get")
    t.ok("le Tank se reconnecte : rôle, cor et 30 PV restaurés", t.score(tank, "sol.role") == 3 and t.has(tank, HORN) and "30" in mh, mh)
    step = t.g("#step")
    w0 = t.g("#wipes") or 0
    shield_all(t, False)
    for b in BOTS:
        t.kill_respawn(b, SPAWN)
    t.ok("les 3 à terre → arène vidée, groupe relevé", (t.g("#wipes") or 0) == w0 + 1 and t.count("@e[tag=sol.r4mob]") == 0)
    t.ok("le sceau en cours recommence (les sceaux brisés le restent)", wait_step(t, step), f"step={t.g('#step')}")
    t.ok("…avec un nouveau tirage des rôles", sorted(roles(t)) == [1, 2, 3])


def sc_r4_seals2(t):
    t.section = "salle 4 : sceaux IV à VI"
    shield_all(t)
    # --- IV : registre et braseros
    r = roles(t)
    lx, lz = M(t)["lectern"]
    click_at(t, r[1], lx, lz, h=1.3, dz=1.6)
    t.ok("sceau IV : le Guérisseur lit le Registre → indice « registre »", t.g("#clue_registre") == 1 and t.g("#s4read") == 1)
    a, b = M(t)["pairs"][t.g("#s4")]
    br = M(t)["braz"]
    wrong = next(k for k in range(6) if k not in (a, b))
    click_braz(t, r[1], a, br)
    t.ok("sceau IV : un brasero décrit s’allume", t.g("#s4n") == 1)
    click_braz(t, r[1], wrong, br)
    t.ok("sceau IV : mauvais brasero → tous s’éteignent", t.g("#s4n") == 0)
    click_braz(t, r[1], a, br)
    click_braz(t, r[1], b, br)
    t.ok("sceau IV : les deux braseros décrits → brisé", t.g("#s4brk") > 0)
    # --- V : plancher piégé
    t.ok("sceau V commence", wait_step(t, 5))
    r = roles(t)
    cells = M(t)["trap_cells"]
    sx = M(t)["trap_start"][0]
    path = M(t)["trap_paths"][t.g("#s5")]
    bad = next((c, rr) for c in range(5) for rr in range(5) if [c, rr] not in path)
    bx, bz = cells[f"{bad[0]},{bad[1]}"]
    t.tp(r[1], bx + 0.5, 101, bz + 0.5)
    t.wait(6)
    p = t.pos(r[1])
    t.ok("sceau V : dalle piégée → renvoyé à l’entrée de l’annexe", p and abs(p[0] - sx) < 1)
    zapped = 0
    for (c, rr) in path:
        cx, cz = cells[f"{c},{rr}"]
        t.tp(r[1], cx + 0.5, 101, cz + 0.5)
        t.wait(3)
        if abs(t.pos(r[1])[0] - sx) < 1:
            zapped += 1
    t.ok("sceau V : le chemin sûr (vu du seul Guérisseur) se traverse sans piège", zapped == 0)
    lvx, lvz = M(t)["lever"]
    t.rc("kill @e[type=!player,tag=sol.r4mob]")   # les coéquipiers ont nettoyé le passage (un gardien sur la ligne de visée prendrait le clic)
    t.rc(f"scoreboard players set {r[1]} sol.cool 0")
    t.look_use(r[1], (lvx + 1.9, 101, lvz + 0.5), (lvx + 0.5, 101.8, lvz + 0.5))
    t.ok("sceau V : levier atteint → brisé", t.g("#s4brk") > 0, f"step={t.g('#step')} pos={t.pos(r[1])} ro1={t.tag(r[1], 'sol.ro1')}")
    # --- VI : offrande
    t.ok("sceau VI commence", wait_step(t, 6))
    r = roles(t)
    t.rc("function solstice:r4/wave6")
    t.wait(2)
    t.rc("kill @e[type=skeleton,tag=sol.r4mob]")
    t.rc("kill @e[type=spider,tag=sol.r4mob]")
    t.rc("kill @e[type=zombie,tag=sol.r4mob]")
    t.wait(5)
    drops = t.count("@e[type=item,nbt={Item:{components:{\"minecraft:custom_data\":{sol:{}}}}}]")
    t.ok("sceau VI : les gardiens abattus lâchent os, fils et cendres", drops >= 1, str(drops))
    t.rc("kill @e[type=item]")
    click_at(t, r[1], 4000, 0, h=1.3, dz=1.9)
    t.ok("sceau VI : offrande incomplète → refus", t.g("#s4brk") == 0 and t.g("#step") == 6)
    for key, iid, n in (("os", "bone", t.g("#s6os")), ("fil", "string", t.g("#s6fil")), ("cendre", "gray_dye", t.g("#s6cen"))):
        if n:
            t.rc(f"give {r[1]} {iid}[custom_data={{sol:{{{key}:1b}}}}] {n}")
    click_at(t, r[1], 4000, 0, h=1.3, dz=1.9)
    t.ok("sceau VI : offrande complète → les six sceaux sont brisés", (t.g("#trans") or 0) > 0)
    t.ok("défi « Rempart » refusé (il y a eu des morts)", not t.adv("Bot1", "challenge/rempart"))
    t.ok("salle 4 → 5 : téléportation automatique", finish_transition(t, 5))
    t.ok("équipement de rôle retiré en quittant le Sanctuaire", not any(t.has(b, SWORD) or t.has(b, STAFF) for b in BOTS))


SCENARIOS = [sc_r4_start, sc_r4_seals, sc_r4_deaths, sc_r4_seals2]
