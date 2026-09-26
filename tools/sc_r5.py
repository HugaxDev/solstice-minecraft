"""Scénarios salle 5 (résultats affichés sous forme de compteurs uniquement)."""
from testlib import BOTS, V
from scenarios import ensure_room, finish_transition, SPAWN


def M(t):
    return t.meta["rooms"]["5"]


def sc_r5_a(t):
    t.section = "salle 5"
    t.secret = True
    ensure_room(t, 5)
    t.secret = True
    t.wait(20)
    t.ok("entrée", t.all_score("sol.room", 5))
    t.ok("a1", t.count("@e[type=item_display,tag=sol.w5it]") == 3)
    t.ok("a2", "passed" in t.rc("execute if entity @a[name=Bot1,nbt={active_effects:[{id:\"minecraft:darkness\"}]}]"))
    t.tp("Bot1", 0.5, 101, 0.5)
    t.wait(6)
    p = t.pos("Bot1")
    t.ok("a3", t.score("Bot1", "sol.room") == 5 and p and abs(p[0] - 5000) < 80)
    for k in range(3):
        pos = t.entity_pos("@e[type=interaction,tag=sol.k5_watch,limit=1]")
        if not pos:
            break
        x, y, z = pos
        t.rc("scoreboard players set Bot2 sol.cool 0")
        t.look_use("Bot2", (x, 101, z + 1.5), (x, y + 0.45, z))
    t.ok("a4", t.g("#w5n") == 3 and t.g("#step") == 2)
    t.ok("a5", "passed" in t.rc(f"execute if block 5000 102 {M(t)['A'][1] - 1} air"))


def sc_r5_b(t):
    t.section = "salle 5"
    t.secret = True
    bx1, bz1, bx2, bz2 = M(t)["B"]
    for i, b in enumerate(BOTS):
        t.tp(b, 4998.5 + 2 * i, 101, 6.5)
        t.rc(f"player {b} look at {4998.5 + 2 * i} 102 20")
    t.wait(4)
    z0 = t.entity_pos("@e[type=armor_stand,tag=sol.r5veil,limit=1]")[2]
    t.wait(40)
    z1 = t.entity_pos("@e[type=armor_stand,tag=sol.r5veil,limit=1]")[2]
    t.ok("b1", z1 > z0 + 1, f"{z0} → {z1}")
    vx, vy, vz = t.entity_pos("@e[type=armor_stand,tag=sol.r5veil,limit=1]")
    t.rc(f"player Bot1 look at {vx} {vy + 1.5} {vz}")
    t.wait(4)
    a = t.entity_pos("@e[type=armor_stand,tag=sol.r5veil,limit=1]")[2]
    t.wait(40)
    c = t.entity_pos("@e[type=armor_stand,tag=sol.r5veil,limit=1]")[2]
    t.ok("b2", abs(c - a) < 0.3, f"{a} → {c}")
    n0 = t.g("#r5caught")
    t.rc("tp @e[type=armor_stand,tag=sol.r5veil] 5002.5 101 6.5")
    t.wait(6)
    t.ok("b3", t.g("#r5caught") > n0)
    locks = M(t)["locks"]
    for i, (x, z) in enumerate(locks):
        stand = (x + 2.3, 101, z + 0.5) if x < 5000 else (x - 1.3, 101, z + 0.5)
        t.rc("scoreboard players set Bot3 sol.cool 0")
        t.rc("tp @e[type=armor_stand,tag=sol.r5veil] 5000.5 101 -30.5")
        t.look_use("Bot3", stand, (x + 0.5, 101.9, z + 0.5))
    t.ok("b4", t.g("#l5n") == 3 and t.g("#step") == 3, f"{t.g('#l5n')}")


def sc_r5_deaths(t):
    t.section = "salle 5"
    t.secret = True
    t.kill_respawn("Bot2", SPAWN)
    t.ok("d1", t.score("Bot2", "sol.room") == 5 and t.gm("Bot2", "adventure"))
    t.near("d2", "Bot2", M(t)["c_cp"][:3], 2.5)
    t.leave("Bot3")
    t.wait(30)
    t.join("Bot3", SPAWN)
    t.wait(20)
    t.ok("d3", t.score("Bot3", "sol.room") == 5)
    t.near("d4", "Bot3", M(t)["c_cp"][:3], 2.5)
    w0 = t.g("#wipes") or 0
    for b in BOTS:
        t.kill_respawn(b, SPAWN)
    t.ok("d5", (t.g("#wipes") or 0) == w0 + 1 and t.g("#step") == 3)


def sc_r5_c(t):
    t.section = "salle 5"
    t.secret = True
    t.setg("#r5freeze", 1)
    t.rc("tp @e[type=armor_stand,tag=sol.r5sh] 5000.5 101 -50.5 180 0")
    t.wait(3)
    n0 = t.g("#r5caught")
    t.tp("Bot1", 5000.5, 101, -60.5)
    t.wait(6)
    t.ok("c1", t.g("#r5caught") == n0 + 1)
    t.near("c2", "Bot1", M(t)["c_cp"][:3], 2.0)
    t.rc("player Bot2 sneak")
    t.wait(10)
    t.tp("Bot2", 5000.5, 101, -58.5)
    t.wait(6)
    t.ok("c3", t.g("#r5caught") == n0 + 1)
    t.rc("player Bot2 unsneak")
    t.tp("Bot2", 5000.5, 101, -44.5)
    t.tp("Bot3", 5000.5, 101, -48.5)
    t.wait(6)
    t.ok("c4", t.g("#r5caught") == n0 + 2)
    t.setg("#r5freeze", 0)
    p0 = t.entity_pos("@e[type=armor_stand,tag=sol.r5sh,limit=1]")
    t.rc("tp @e[type=armor_stand,tag=sol.r5sh] 4985.5 101 -44.5")
    t.wait(30)
    p1 = t.entity_pos("@e[type=armor_stand,tag=sol.r5sh,limit=1]")
    t.ok("c5", p1 and abs(p1[0] - 4985.5) > 0.5)
    t.setg("#r5freeze", 1)
    t.rc("tp @e[type=armor_stand,tag=sol.r5sh] 5000.5 101 -110.5")
    for i, (x, z) in enumerate(M(t)["lamps"]):
        t.rc("scoreboard players set Bot1 sol.cool 0")
        t.look_use("Bot1", (x + 0.5, 101, z + 2.0), (x + 0.5, 102.3, z + 0.5))
    t.ok("c6", t.g("#lamp5n") == 3 and t.g("#step") == 4,
         f"n={t.g('#lamp5n')} step={t.g('#step')} ent={t.count('@e[type=interaction,tag=sol.r5i]')} pos={t.pos('Bot1')} caught={t.g('#r5caught')}")
    lx, lz = M(t)["lodge"]
    t.rc("scoreboard players set Bot2 sol.cool 0")
    t.look_use("Bot2", (lx - 1.4, 101, lz + 0.5), (lx + 0.5, 101.6, lz + 0.5))
    t.ok("c7", t.g("#clue_veilleur") == 1)
    bx, bz = M(t)["bell"]
    t.tp("Bot1", bx + 0.5, 101, bz + 0.7)
    t.tp("Bot2", bx - 0.5, 101, bz - 0.5)
    t.wait(3)
    t.rc("scoreboard players set Bot1 sol.cool 0")
    t.rc(f"player Bot1 look at {bx + 0.5} 104.5 {bz + 0.5}")
    t.wait(3)
    t.rc("player Bot1 use once")
    t.wait(6)
    t.ok("c8", t.g("#r5done") == 0)
    t.tp("Bot3", bx + 1.5, 101, bz - 0.5)
    t.wait(3)
    t.rc("scoreboard players set Bot1 sol.cool 0")
    t.rc("player Bot1 use once")
    t.wait(8)
    t.ok("c9", t.g("#r5done") == 1)
    t.ok("c10", not t.adv("Bot1", "challenge/sang_froid"))
    t.ok("c11", finish_transition(t, 6))
    t.secret = False


SCENARIOS = [sc_r5_a, sc_r5_b, sc_r5_deaths, sc_r5_c]
