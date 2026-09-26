"""Scénarios E2E. Chaque salle a son module sc_rN (quand elle est réelle) ; les salles factices utilisent
sc_placeholder. Les scénarios s’enchaînent dans l’ordre de la partie (le monde est partagé)."""
import importlib

from testlib import BOTS, V

SPAWN = (0.5, 101, 14.5)


def room_meta(t, n):
    return t.meta["rooms"][str(n)]


# ------------------------------------------------------------------ communs
def ensure_room(t, n):
    """Pour lancer une salle isolément (python3 tools/tests.py r6) : connecte les 3 joueurs et saute à la salle n."""
    for b in BOTS:
        if not t.online(b):
            t.join(b)
    if t.g("#room") != n:
        t.goto(n)
        t.wait_until(lambda: t.all_score("sol.room", n), 200)



def enter_ok(t, n):
    t.ok(f"les 3 joueurs sont dans la salle {n}", t.all_score("sol.room", n))
    cp = room_meta(t, n).get("cp")
    if cp:
        for b in BOTS:
            t.near(f"{b} au point d’arrivée de la salle {n}", b, cp[:3], 3.0)


def finish_transition(t, n_next):
    """Attend la fin d’une transition (200 ticks) et l’entrée dans la salle suivante."""
    t.sprint(230)
    t.wait(10)
    return t.wait_until(lambda: t.g("#room") == n_next and t.all_score("sol.room", n_next), 200)


def common_death_one(t, n, who="Bot2", combat=False):
    cp = room_meta(t, n)["cp"]
    t.kill_respawn(who, cp[:3])
    t.ok(f"salle {n} : {who} meurt → reste dans la salle", t.score(who, "sol.room") == n and t.g("#room") == n)
    if combat:
        t.ok(f"salle {n} : {who} observe un coéquipier (spectateur)", t.gm(who, "spectator") and t.tag(who, "sol.dn"))
        t.sprint(220)
        t.wait(5)
        t.ok(f"salle {n} : après 10 s, {who} revient en aventure", t.gm(who, "adventure") and not t.tag(who, "sol.dn"))
    else:
        t.ok(f"salle {n} : {who} réapparaît en aventure (pas de spectateur hors combat)", t.gm(who, "adventure"))
        t.sprint(220)
    t.ok(f"salle {n} : les autres n’ont pas été affectés", t.all_score("sol.room", n))


def common_wipe(t, n):
    cp = room_meta(t, n)["cp"]
    w0 = t.g("#wipes") or 0
    for b in BOTS:
        t.kill_respawn(b, cp[:3])
    t.ok(f"salle {n} : les 3 à terre → salle réinitialisée (#wipes +1)", (t.g("#wipes") or 0) == w0 + 1, f"{w0} → {t.g('#wipes')}")
    t.ok(f"salle {n} : tout le monde relevé, en aventure", all(t.gm(b, "adventure") for b in BOTS)
         and not any(t.tag(b, "sol.dn") for b in BOTS))
    t.ok(f"salle {n} : toujours dans la salle {n} (aucune progression perdue)", t.g("#room") == n and t.all_score("sol.room", n))


def common_reconnect(t, n, who="Bot3"):
    t.leave(who)
    t.wait(40)
    t.ok(f"salle {n} : {who} déconnecté, la partie continue", t.g("#room") == n and not t.online(who))
    t.join(who, SPAWN)
    t.wait(20)
    t.ok(f"salle {n} : {who} revient → remis dans la salle en cours", t.score(who, "sol.room") == n)
    cp = room_meta(t, n).get("cp")
    if cp:
        t.near(f"salle {n} : {who} replacé au checkpoint", who, cp[:3], 3.5)


def no_way_back(t, n):
    t.tp("Bot1", 0.5, 101, 0.5)
    t.wait(6)
    t.ok(f"salle {n} : retour au village impossible (renvoyé dans la salle {n})",
         t.score("Bot1", "sol.room") == n and t.pos("Bot1") and abs(t.pos("Bot1")[0] - 1000 * n) < 100)


# ------------------------------------------------------------------ salles factices
def sc_placeholder(t, n):
    t.section = f"salle {n} (factice)"
    enter_ok(t, n)
    no_way_back(t, n)
    combat = t.meta["room_combat"][str(n)]
    common_death_one(t, n, combat=combat)
    common_reconnect(t, n)
    common_wipe(t, n)
    plates = room_meta(t, n)["plates"]
    for b, (x, z) in zip(BOTS[:2], plates):
        t.tp(b, x + 0.5, 101, z + 0.5)
    t.wait(5)
    t.ok(f"salle {n} : 2 joueurs sur 3 ne suffisent pas", t.g("#trans") == 0)
    x, z = plates[2]
    t.tp("Bot3", x + 0.5, 101, z + 0.5)
    t.wait(5)
    if n < 7:
        t.ok(f"salle {n} : les 3 ensemble → transition", (t.g("#trans") or 0) > 0)
        t.ok(f"salle {n} → {n + 1} : téléportation automatique du groupe", finish_transition(t, n + 1))
        t.ok(f"salle {n} : advancement accordé aux 3", all(t.adv(b, f"room/r{n}") for b in BOTS))


def sc_roles(t):
    t.section = "tirages au sort"
    bad = 0
    heal = {b: 0 for b in BOTS}
    for i in range(30):
        t.rc("function solstice:roles/draw")
        roles = [t.score(b, "sol.role") for b in BOTS]
        if sorted(roles) != [1, 2, 3]:
            bad += 1
        for b, r in zip(BOTS, roles):
            if r == 1:
                heal[b] += 1
    t.ok("30 tirages : chaque joueur a toujours un rôle unique (1, 2, 3)", bad == 0, f"{bad} tirages invalides")
    t.ok("30 tirages : chaque joueur obtient le rôle 1 au moins une fois (hasard réel)", all(v > 0 for v in heal.values()), str(heal))
    t.ok("aucun rôle vacant à 3 joueurs", all(t.g(f"#vac{r}") == 0 for r in (1, 2, 3)))
    # exclusion du précédent (Siège : le Guérisseur change à chaque étape)
    t.setg("#noheal", 1)
    same = 0
    for i in range(20):
        t.rc("tag @a remove sol.prev")
        t.rc("tag @a[scores={sol.role=1}] add sol.prev")
        prev = [b for b in BOTS if t.score(b, "sol.role") == 1]
        t.rc("function solstice:roles/draw")
        now = [b for b in BOTS if t.score(b, "sol.role") == 1]
        if prev == now or len(now) != 1:
            same += 1
    t.setg("#noheal", 0)
    t.rc("tag @a remove sol.prev")
    t.ok("20 tirages avec exclusion : le rôle 1 change toujours de joueur", same == 0, f"{same} répétitions")


def sc_end(t):
    t.section = "fin de partie"
    t.ok("le groupe est dans la dernière salle", t.g("#room") == 7)


# ------------------------------------------------------------------ ordre
def all_scenarios():
    from sc_r0 import sc_prologue
    out = [sc_prologue]
    for n in range(1, 8):
        try:
            mod = importlib.import_module(f"sc_r{n}")
            out += mod.SCENARIOS
        except ModuleNotFoundError:
            out.append(_ph(n))
    out.append(sc_ending)
    return out


def _ph(n):
    def f(t):
        sc_placeholder(t, n)
    f.__name__ = f"sc_placeholder_r{n}"
    return f


def sc_ending(t):
    t.section = "fin de partie"
    if t.g("#ended") != 1:
        t.rc("function solstice:debug/salle_suivante")
    t.wait(5)
    t.ok("fin déclenchée (#ended = 1)", t.g("#ended") == 1)
    t.sprint(2000)
    t.wait(10)
    t.ok("crédits : advancement final accordé aux 3", all(t.adv(b, "fin") for b in BOTS))
    t.ok("épilogue : retour à Brumeval (#room = 8)", t.g("#room") == 8)
    t.wait(10)
    t.ok("épilogue : les 3 joueurs au village", all(abs((t.pos(b) or (999,))[0]) < 60 for b in BOTS))
    t.ok("temps de partie compté (#gtime > 0)", (t.g("#gtime") or 0) > 0)
