"""Scénarios salle 1 — L’Express du Solstice : rôles (tirages répétés), postes réservés, chaque évènement
(bifurcation, passage à niveau, zone lente, tunnel, Brumeux, surpression, panne) en réussite et en erreur,
parcours nominal complet, mort, anéantissement, reconnexion."""
from testlib import BOTS, V
from scenarios import ensure_room, finish_transition, no_way_back, SPAWN

ROLE_NAMES = {1: "Aiguilleur", 2: "Chauffeur", 3: "Garde"}
BROOM = "stick[custom_data~{sol:{broom:1b}}]"
BOOK = "written_book[custom_data~{sol:{route:1b}}]"
COAL = "coal[custom_data~{sol:{coal:1b}}]"


def who_has(t, role):
    return next((b for b in BOTS if t.score(b, "sol.role") == role), None)


def click1(t, who, key, attack=False):
    x, y, z = t.meta["rooms"]["1"]["k"][key]
    # on se place côté couloir (z vers 0) ou devant (x+1.4) selon l’élément
    if key in ("left", "right", "fire"):
        stand = (x + 1.6, 101, z)
    else:
        stand = (x, 101, z + 1.9 if z < 0.5 else z - 1.9)
    for b in BOTS:
        if b != who:
            p = t.pos(b)
            if p and abs(p[0] - stand[0]) < 2.5 and abs(p[2] - stand[2]) < 2.5:
                t.tp(b, stand[0] + 5, 101, 0.5)
    t.rc(f"scoreboard players set {who} sol.cool 0")
    t.look_use(who, stand, (x, y + 0.5, z), attack)


def ev_index(t, typ, par=None):
    for i, pos, ty, pa, k in t.meta["rooms"]["1"]["events"]:
        if ty == typ and (par is None or pa == par):
            return i, pos, k
    raise KeyError(typ)


def jump(t, i, dist, press=50):
    """Place le train juste avant un évènement (test ciblé)."""
    t.setg("#ev", i)
    t.setg("#signed", 0)
    t.setg("#dist", dist)
    t.setg("#press", press)
    t.setg("#pause", 0)
    t.setg("#lim", 0)
    t.setg("#over", 0)
    t.setg("#stall", 0)
    t.wait(3)


def roles_ok(t):
    roles = sorted(t.score(b, "sol.role") or 0 for b in BOTS)
    return roles == [1, 2, 3]


def sc_r1_roles(t):
    t.section = "salle 1 : rôles"
    ensure_room(t, 1)
    t.wait(10)
    t.ok("tirage au sort : trois rôles distincts (Aiguilleur, Chauffeur, Garde)", roles_ok(t),
         str([t.score(b, "sol.role") for b in BOTS]))
    cps = t.meta["rooms"]["1"]["cps"]
    for b in BOTS:
        r = t.score(b, "sol.role")
        t.near(f"{b} ({ROLE_NAMES.get(r)}) à son poste", b, cps[str(r)][:3], 2.5)
    g = who_has(t, 3)
    t.ok("le Garde reçoit le balai et la feuille de route", g and t.has(g, BROOM) and t.has(g, BOOK))
    t.ok("les autres n’ont pas la feuille de route", not any(t.has(b, BOOK) for b in BOTS if b != g))
    seen = {b: set() for b in BOTS}
    bad = 0
    for i in range(4):
        t.rc("function solstice:debug/reset_salle")
        t.wait(12)
        if not roles_ok(t):
            bad += 1
        for b in BOTS:
            seen[b].add(t.score(b, "sol.role"))
        g = who_has(t, 3)
        if not (g and t.has(g, BOOK)):
            bad += 1
    t.ok("4 nouveaux tirages : toujours 3 rôles distincts, kit du Garde suivi", bad == 0, f"{bad} anomalies")
    t.ok("les rôles changent vraiment d’un tirage à l’autre", sum(len(v) for v in seen.values()) > 3, str(seen))
    no_way_back(t, 1)


def sc_r1_posts(t):
    t.section = "salle 1 : postes"
    t.setg("#r1t", 300)
    t.wait(3)
    t.ok("fin de l’introduction : le train roule (tronçon 1)", t.g("#step") >= 1)
    a, c, g = who_has(t, 1), who_has(t, 2), who_has(t, 3)
    t.setg("#press", 50)
    p0 = t.g("#press")
    click1(t, a, "fire")
    t.ok("poste réservé : l’Aiguilleur ne peut pas charger la chaudière", t.g("#press") <= p0)
    click1(t, c, "coal")
    t.ok("Chauffeur : une pelletée prise au tender", t.has(c, COAL))
    t.rc(f"player {c} hotbar 1")
    for i in range(9):
        if "passed" in t.rc(f"execute if items entity {c} hotbar.{i} {COAL}"):
            t.rc(f"player {c} hotbar {i + 1}")
    t.setg("#press", 50)
    click1(t, c, "fire")
    t.ok("Chauffeur : charbon dans la chaudière → pression +15", (t.g("#press") or 0) >= 60 and not t.has(c, COAL),
         f"press={t.g('#press')}")
    t.setg("#press", 60)
    click1(t, c, "valve")
    t.ok("Chauffeur : soupape → pression −20", (t.g("#press") or 99) <= 42)
    click1(t, a, "right")
    t.ok("Aiguilleur : voie de droite", t.g("#switch") == 1)
    click1(t, a, "left")
    t.ok("Aiguilleur : voie de gauche", t.g("#switch") == 0)
    click1(t, g, "right")
    t.ok("poste réservé : le Garde ne touche pas à l’aiguillage", t.g("#switch") == 0)
    click1(t, a, "hammer")
    t.ok("indice « marteau » trouvé dans le tender", t.g("#clue_marteau") == 1)


def sc_r1_natural(t):
    """Départ réel, compteurs jamais initialisés (monde neuf) : le panneau doit s’armer tout seul."""
    t.section = "salle 1 : départ naturel"
    for s in ("#signed", "#ev_cross"):
        t.rc(f"scoreboard players reset {s} {V}")
    t.rc("function solstice:debug/reset_salle")
    t.wait(12)
    t.setg("#r1t", 199)
    t.wait(5)
    t.ok("le train démarre de lui-même", (t.g("#step") or 0) >= 1)

    def run_to_first_sign():
        t.setg("#pause", 0)
        t.setg("#stall", 0)
        t.setg("#press", 50)
        t.setg("#dist", 450)
        t.wait(5)
        return t.rc("data get entity @e[type=text_display,tag=sol.r1sign,limit=1] text")
    sign = run_to_first_sign()
    t.ok("départ : le panneau annonce le premier passage à niveau", "PASSAGE" in sign and t.g("#ev_cross") == 1, sign[:100])
    e0 = t.g("#errors") or 0
    t.setg("#dist", 1100)
    t.wait(5)
    t.ok("barrière restée fermée : le train recule", (t.g("#errors") or 0) == e0 + 1 and t.g("#dist") == 0)
    sign = run_to_first_sign()
    t.ok("après le recul, le panneau se réaffiche", "PASSAGE" in sign and t.g("#ev_cross") == 1, sign[:100])
    # pelletée rangée dans l’inventaire (pas en main) : la chaudière l’accepte quand même
    c = who_has(t, 2)
    t.rc(f"clear {c} {COAL}")
    t.rc(f"item replace entity {c} inventory.5 with minecraft:coal[minecraft:custom_data={{sol:{{coal:1b}}}}]")
    t.setg("#press", 30)
    click1(t, c, "fire")
    t.wait(4)
    t.ok("chaudière : la pelletée est acceptée même hors de la main", (t.g("#press") or 0) >= 40 and not t.has(c, COAL),
         f"press={t.g('#press')}")


def sc_r1_events(t):
    t.section = "salle 1 : évènements"
    a, c, g = who_has(t, 1), who_has(t, 2), who_has(t, 3)
    sec = t.meta["rooms"]["1"]["sec"]
    # passage à niveau
    i, pos, k = ev_index(t, "cross", 1)
    e0 = t.g("#errors")
    jump(t, i, pos - 30)
    t.wait(30)
    t.ok("passage à niveau sans barrière ouverte → erreur", t.g("#errors") == e0 + 1)
    t.ok("…le train recule au début du tronçon", t.g("#dist") == sec * (k - 1) and t.g("#ev") == i)
    jump(t, i, pos - 400)
    t.wait(4)
    t.ok("le panneau annonce le passage à niveau (manivelle active)", t.g("#ev_cross") == 1)
    for _ in range(3):
        click1(t, g, "crank")
    t.ok("Garde : 3 tours de manivelle → barrière ouverte", t.g("#bopen") == 1)
    t.setg("#dist", pos - 10)
    t.wait(20)
    t.ok("passage à niveau franchi sans erreur", t.g("#ev") == i + 1 and t.g("#errors") == e0 + 1)
    # bifurcation
    i, pos, k = ev_index(t, "fork", 1)
    side = t.g("#fside1")
    jump(t, i, pos - 30)
    t.setg("#switch", 1 - side)
    t.wait(30)
    t.ok("bifurcation : mauvaise voie → erreur et recul", t.g("#errors") == e0 + 2 and t.g("#dist") == sec * (k - 1))
    side = t.g("#fside1")
    jump(t, i, pos - 40)
    click1(t, a, "left" if side == 0 else "right")
    t.setg("#dist", pos - 5)
    t.wait(20)
    t.ok("bifurcation : l’Aiguilleur règle la bonne voie → passage", t.g("#ev") == i + 1 and t.g("#errors") == e0 + 2)
    # zone lente
    i, pos, k = ev_index(t, "lim_on", "Virage du Ravin")
    jump(t, i, pos - 5, press=85)
    t.wait(70)
    t.ok("zone lente franchie trop vite → déraillement (erreur)", t.g("#errors") == e0 + 3)
    jump(t, i, pos - 5, press=30)
    t.wait(60)
    t.ok("zone lente à pression basse → pas d’erreur", t.g("#errors") == e0 + 3 and t.g("#lim") == 1)
    # tunnel
    i, pos, k = ev_index(t, "tunnel")
    jump(t, i, pos - 5, press=40)
    t.wait(20)
    t.ok("tunnel en montée sans pression → erreur", t.g("#errors") == e0 + 4)
    jump(t, i, pos - 5, press=70)
    t.wait(20)
    t.ok("tunnel à pleine pression → passage", t.g("#ev") == i + 1 and t.g("#errors") == e0 + 4)
    # Brumeux
    i, pos, k = ev_index(t, "board", 3)
    jump(t, i, pos - 3)
    t.wait(15)
    n = t.count("@e[type=zombie,tag=sol.r1mob]")
    t.ok("3 Brumeux montent à bord", n == 3, str(n))
    r = t.rc("attribute @e[type=zombie,tag=sol.r1mob,limit=1] minecraft:generic.attack_damage get")
    t.ok("les Brumeux ne blessent pas (dégâts 0)", "0.0" in r or " 0 " in r, r)
    t.rc(f"tp @e[type=zombie,tag=sol.r1mob] {g}")
    t.rc("tp @e[type=zombie,tag=sol.r1mob] ~ 80 ~")
    t.wait(20)
    t.ok("Brumeux jetés par-dessus bord → disparus", t.count("@e[type=zombie,tag=sol.r1mob]") == 0)
    # surpression, panne
    t.setg("#press", 105)
    t.wait(5)
    t.ok("surpression (> 100) → erreur", t.g("#errors") == e0 + 5)
    t.setg("#pause", 0)
    t.setg("#press", 3)
    t.sprint(140)
    t.wait(4)
    t.ok("chaudière éteinte 6 s → erreur", t.g("#errors") == e0 + 6)


def sc_r1_deaths(t):
    t.section = "salle 1 : morts et reconnexion"
    c = who_has(t, 2)
    cps = t.meta["rooms"]["1"]["cps"]
    t.kill_respawn(c, SPAWN)
    t.ok("le Chauffeur meurt → revient à son poste, avec son rôle", t.score(c, "sol.role") == 2)
    t.near("…dans la cabine", c, cps["2"][:3], 2.5)
    g = who_has(t, 3)
    t.leave(g)
    t.wait(30)
    t.join(g, SPAWN)
    t.wait(20)
    t.ok("le Garde se reconnecte → rôle conservé", t.score(g, "sol.role") == 3 and t.score(g, "sol.room") == 1)
    t.near("…remis à l’arrière du train", g, cps["3"][:3], 2.5)
    t.ok("…avec son balai et sa feuille de route", t.has(g, BROOM) and t.has(g, BOOK))
    w0 = t.g("#wipes") or 0
    d0 = t.g("#dist")
    for b in BOTS:
        t.kill_respawn(b, SPAWN)
    t.ok("les 3 à terre → groupe relevé, train ramené au début du tronçon", (t.g("#wipes") or 0) == w0 + 1
         and t.g("#room") == 1 and t.g("#dist") % t.meta["rooms"]["1"]["sec"] == 0)
    t.ok("rôles conservés après l’anéantissement", roles_ok(t))


def sc_r1_full(t):
    t.section = "salle 1 : parcours complet"
    a, c, g = who_has(t, 1), who_has(t, 2), who_has(t, 3)
    t.setg("#errors", 0)
    t.setg("#ev", 0)
    t.setg("#dist", 0)
    t.setg("#pause", 0)
    t.setg("#signed", 0)
    evs = t.meta["rooms"]["1"]["events"]
    for i, pos, typ, par, k in evs:
        if t.g("#room") != 1 or t.g("#trans"):
            break
        t.setg("#dist", max(t.g("#dist"), pos - 350))
        t.setg("#press", 30 if typ in ("lim_on", "lim_off") else 65)
        t.wait(3)
        if typ == "fork":
            click1(t, a, "left" if t.g(f"#fside{par}") == 0 else "right")
        if typ == "cross":
            for _ in range(3):
                click1(t, g, "crank")
        t.setg("#press", 30 if typ in ("lim_on", "lim_off") else 65)
        t.setg("#dist", pos - 20)
        t.wait(25)
        if typ == "board":   # le Garde les jette dehors (simulé : ils gêneraient les clics suivants)
            t.rc("tp @e[type=zombie,tag=sol.r1mob] ~ 80 ~")
        t.ok(f"évènement {i} ({typ}) franchi sans erreur", (t.g("#ev") >= i + 1 or t.g("#trans") > 0 or t.g("#room") == 2)
             and t.g("#errors") == 0,
             f"ev={t.g('#ev')} err={t.g('#errors')} dist={t.g('#dist')}")
    t.ok("parcours complet sans erreur", t.g("#errors") == 0)
    t.ok("terminus : transition vers la Tour", (t.g("#trans") or 0) > 0 or t.g("#room") == 2)
    t.ok("défi « Voie royale » (aucune erreur) accordé", all(t.adv(b, "challenge/voie_royale") for b in BOTS))
    t.ok("salle 1 → 2 : téléportation automatique", finish_transition(t, 2))
    t.ok("les objets du train ne suivent pas", not any(t.has(b, BOOK) or t.has(b, BROOM) for b in BOTS))


SCENARIOS = [sc_r1_roles, sc_r1_posts, sc_r1_natural, sc_r1_events, sc_r1_deaths, sc_r1_full]
