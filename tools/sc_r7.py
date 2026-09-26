"""Scénarios salle 7 — Le Cœur du Calendrier : vote (désaccord, unanimité), les DEUX branches de l’accusation,
machine-boss (3 systèmes, opérateur tournant), Lanterne, mort, anéantissement (verdict conservé), reconnexion, fin."""
from testlib import BOTS, V
from scenarios import ensure_room, no_way_back, SPAWN

LANT = "lantern[custom_data~{sol:{lantern:1b}}]"
FUSE = "lightning_rod[custom_data~{sol:{fuse:1b}}]"


def M(t):
    return t.meta["rooms"]["7"]


def vote(t, who, k):
    x, z = M(t)["suspects"][str(k)]
    for i, b in enumerate(BOTS):      # les autres s’écartent de la ligne de visée
        if b != who:
            t.tp(b, 6991.5 + 3 * i, 101, 31.5)
    t.rc(f"scoreboard players set {who} sol.cool 0")
    t.look_use(who, (x + 0.5, 101, z + 2.0), (x + 0.5, 102.2, z + 0.5), attack=True)


def op(t):
    return next((b for b in BOTS if t.score(b, "sol.role") == 1), None)


def shield(t, on=True):
    for b in BOTS:
        t.rc(f"effect give {b} resistance 100000 255 true" if on else f"effect clear {b} resistance")


def hold_item(t, who, pred):
    for i in range(9):
        if "passed" in t.rc(f"execute if items entity {who} hotbar.{i} {pred}"):
            t.rc(f"player {who} hotbar {i + 1}")
            t.wait(2)
            return True
    return False


def sc_r7_vote(t):
    t.section = "salle 7 : accusation"
    ensure_room(t, 7)
    t.wait(10)
    no_way_back(t, 7)
    found = sum(1 for c in ("encre", "minuit", "marteau", "graines", "mot", "plan", "gant", "registre", "veilleur", "lettre") if t.g(f"#clue_{c}") == 1)
    t.ok("le tableau d’enquête affiche un panneau par indice trouvé", t.count("@e[type=text_display,tag=sol.r7d]") == found + 1,
         f"{t.count('@e[type=text_display,tag=sol.r7d]')} vs {found}")
    vote(t, "Bot1", 2)
    vote(t, "Bot2", 2)
    t.ok("2 votes sur 3 : on attend le troisième", t.g("#step") == 1 and t.g("#votes") == 2,
         f"step={t.g('#step')} votes={t.g('#votes')} v1={t.score('Bot1', 'sol.vote')} ent={t.count('@e[type=interaction,tag=sol.k7_sus2]')} pos={t.pos('Bot1')}")
    vote(t, "Bot3", 3)
    t.ok("désaccord → votes remis à zéro, il faut se mettre d’accord", t.g("#step") == 1 and t.g("#votefail") == 1
         and all((t.score(b, "sol.vote") or 0) == 0 for b in BOTS))
    for b in BOTS:
        vote(t, b, 2)
    t.ok("vote unanime pour Bram → verdict (mauvais choix)", t.g("#accuse") == 2 and t.g("#good") == 0 and t.g("#step") == 2)
    t.sprint(220)
    t.wait(5)
    t.ok("branche « mauvais choix » : le combat commence, sans aide", t.g("#step") == 3 and t.count("@e[tag=sol.ysolde]") == 0)
    t.sprint(300)
    n_bad = t.count("@e[tag=sol.r7mob]")
    t.ok("branche « mauvais choix » : automates plus nombreux", n_bad >= 3, str(n_bad))
    # seconde partie de la salle : l’autre branche
    t.rc("function solstice:debug/reset_salle")
    t.wait(20)
    t.ok("salle rejouée (debug) : retour au vote", t.g("#step") == 1)
    for b in BOTS:
        vote(t, b, 1)
    t.ok("vote unanime pour Ysolde → bon choix", t.g("#accuse") == 1 and t.g("#good") == 1)
    t.ok("défi « Fin limier » (bon coupable du premier coup) accordé", all(t.adv(b, "challenge/fin_limier") for b in BOTS))
    t.sprint(260)
    t.wait(5)
    t.ok("branche « bon choix » : Ysolde rejoint le combat", t.g("#step") == 3 and t.count("@e[tag=sol.ysolde]") == 1)


def do_system(t):
    s = t.g("#sys")
    o = op(t)
    if s == 1:
        cx, cz = M(t)["crate"]
        for i, (sx, sz) in enumerate(M(t)["sockets"]):
            t.rc(f"scoreboard players set {o} sol.cool 0")
            t.look_use(o, (cx + 2.0, 101, cz + 0.5), (cx + 0.5, 101.6, cz + 0.5))
            hold_item(t, o, FUSE)
            t.rc(f"scoreboard players set {o} sol.cool 0")
            t.look_use(o, (sx - 1.2, 101, sz + 0.5), (sx + 0.5, 101.6, sz + 0.5))
    elif s == 2:
        px, pz = M(t)["platform"]
        for _ in range(8):           # les gardes du corps repoussent les automates (simulé)
            if t.g("#sys") != 2:
                break
            t.rc("kill @e[type=!player,tag=sol.r7mob]")
            t.tp(o, px + 0.5, 101, pz + 0.5)
            t.sprint(50)
            t.wait(2)
    else:
        holder = next((b for b in BOTS if t.has(b, LANT)), None)
        weak = t.g("#weak")
        gx, gz = M(t)["gears"][weak]
        if holder:
            hold_item(t, holder, LANT)
            t.tp(holder, gx + 3.5, 101, gz + 1.5)
            t.wait(12)
        t.ok("la Lanterne révèle le point faible", t.count("@e[type=text_display,tag=sol.weakink,tag=sol.shown]") == 1)
        wrong = (weak + 1) % 6
        wx, wz = M(t)["gears"][wrong]
        t.rc(f"scoreboard players set {o} sol.cool 0")
        t.look_use(o, (wx + 1.9, 101, wz + 0.5), (wx + 0.2, 102.4, wz + 0.5), attack=True)
        t.ok("mauvais engrenage → électrocution, compte remis à zéro", t.g("#hits") == 0)
        for _ in range(3):
            t.rc(f"scoreboard players set {o} sol.cool 0")
            t.look_use(o, (gx + 1.9, 101, gz + 0.5), (gx + 0.2, 102.4, gz + 0.5), attack=True)


def sc_r7_boss(t):
    t.section = "salle 7 : machine-boss"
    shield(t)
    ops = []
    systems = []
    for phase in (1, 2, 3):
        t.rc("kill @e[type=!player,tag=sol.r7mob]")
        t.ok(f"phase {phase} : un Opérateur tiré au sort", op(t) is not None)
        ops.append(op(t))
        systems.append(t.g("#sys"))
        if phase == 2:
            # mort, anéantissement, reconnexion pendant le combat
            victim = next(b for b in BOTS if b != op(t))
            shield(t, False)
            t.kill_respawn(victim, SPAWN)
            t.ok("mort pendant le combat → spectateur 10 s", t.gm(victim, "spectator"))
            t.sprint(220)
            t.wait(4)
            t.ok("…puis de retour dans l’arène", t.gm(victim, "adventure"))
            good = t.g("#good")
            w0 = t.g("#wipes") or 0
            for b in BOTS:
                t.kill_respawn(b, SPAWN)
            t.ok("les 3 à terre → le combat reprend du début, le verdict est conservé",
                 (t.g("#wipes") or 0) == w0 + 1 and t.g("#phase") == 1 and t.g("#good") == good)
            shield(t)
            o = op(t)
            t.leave(o)
            t.wait(30)
            t.join(o, SPAWN)
            t.wait(20)
            t.ok("l’Opérateur se reconnecte : il le reste", t.score(o, "sol.role") == 1 and t.score(o, "sol.room") == 7)
            ops, systems = [op(t)], [t.g("#sys")]
            do_system(t)
            ops.append(op(t))
            systems.append(t.g("#sys"))
        before = t.g("#phase")
        do_system(t)
        t.ok(f"système « {['', 'fusibles', 'balancier', 'point faible'][systems[-1]]} » désactivé", t.g("#phase") > before or t.g("#ended") == 1,
             f"phase={t.g('#phase')} sys={t.g('#sys')} fuses={t.g('#fuses')} hold={t.g('#hold')} hits={t.g('#hits')}")
    t.ok("trois systèmes différents", sorted(systems[-3:]) == [1, 2, 3], str(systems))
    t.ok("l’Opérateur change à chaque phase", len(set(ops[-3:])) == 3, str(ops))
    t.ok("le Verrou est brisé → fin de partie lancée", t.g("#ended") == 1)


SCENARIOS = [sc_r7_vote, sc_r7_boss]
