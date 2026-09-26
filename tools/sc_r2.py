"""Scénarios salle 2 — La Tour des Engrenages : tirage des puits, mécanismes réservés, les 9 énigmes (erreurs
comprises), ouverture croisée des grilles, montée, sommet, mort, anéantissement, reconnexion."""
import itertools
from collections import deque

from testlib import BOTS, V
from scenarios import ensure_room, finish_transition, no_way_back, SPAWN


def M(t):
    return t.meta["rooms"]["2"]


def by_track(t):
    return {t.score(b, "sol.role"): b for b in BOTS}


def ent_click(t, who, key, stand_dz=-1.4, dx=0.0, attack=False):
    """Clique l’interaction sol.k2_<key> en se plaçant devant (côté intérieur du puits)."""
    p = t.entity_pos(f"@e[type=interaction,tag=sol.k2_{key},limit=1]")
    if p is None:
        return t.ok(f"élément {key} présent", False)
    x, y, z = p
    h = t.entity_h(f"sol.k2_{key}")
    if x > 2014:                      # mur est du puits du Fer
        stand = (x - 1.6, y if y > 100 else 101, z)
    elif z < -3:                      # mur nord
        stand = (x, y, z + 1.6)
    else:
        stand = (x + dx, int(y) if y % 1 < 0.9 else int(y) + 1, z + stand_dz)
    floor = max(k for k in (101, 111, 121, 131) if k <= y + 0.5)
    stand = (stand[0], floor, stand[2])
    for b in BOTS:
        if b != who:
            q = t.pos(b)
            if q and abs(q[0] - stand[0]) < 2 and abs(q[2] - stand[2]) < 2 and abs(q[1] - stand[1]) < 3:
                t.tp(b, stand[0], stand[1], stand[2] - 2.5)
    t.rc(f"scoreboard players set {who} sol.cool 0")
    t.look_use(who, stand, (x, y + h / 2, z), attack)


def door_open(t, track, k):
    x, z = M(t)["door_cells"][f"{track}{k}"][2]
    F = M(t)["fl"][str(k)]
    return "passed" in t.rc(f"execute if block {x} {F + 2} {z} air")


def to_level(t, who, track, k):
    cxx = M(t)["cx"][str(track)]
    F = M(t)["fl"][str(k)]
    t.tp(who, cxx + 0.5, F + 1, 1.5)
    t.wait(4)


def sc_r2_level1(t):
    t.section = "salle 2 : niveau 1"
    ensure_room(t, 2)
    t.wait(10)
    tr = by_track(t)
    t.ok("tirage : chaque joueur a son puits (Cuivre, Laiton, Fer)", sorted(tr) == [1, 2, 3], str(tr))
    for k, b in tr.items():
        cxx = M(t)["cx"][str(k)]
        t.near(f"{b} au pied de son puits ({['Cuivre', 'Laiton', 'Fer'][k - 1]})", b, (cxx + 0.5, 101, 1.5), 2.0)
    t.ok("toutes les grilles sont fermées au départ", not any(door_open(t, k, 1) for k in (1, 2, 3)))
    no_way_back(t, 2)
    A, B, C = tr[1], tr[2], tr[3]
    to_level(t, A, 1, 1)
    # accès réservé
    ent_click(t, B, "a1_1") if False else None
    before = t.g("#a1_1")
    t.tp(B, 1990.5, 101, 3.0)       # B ne peut pas entrer chez A : on force la position pour tester le contrôle
    ent_click(t, B, "a1_1")
    t.ok("mécanisme réservé : un joueur d’un autre puits ne peut pas l’actionner", t.g("#a1_1") == before)
    to_level(t, B, 2, 1)
    # A1 : cadrans
    for i in (1, 2, 3):
        need = (t.g(f"#a1t_{i}") - t.g(f"#a1_{i}")) % 4
        for _ in range(need):
            ent_click(t, A, f"a1_{i}")
    t.ok("A1 (cadrans) : aiguilles réglées sur le motif affiché chez le Laiton → résolu", t.g("#s_a1") == 1)
    t.ok("…et c’est la grille du LAITON (niveau 1) qui s’ouvre", door_open(t, 2, 1) and not door_open(t, 1, 1))
    # B1 : étoiles
    ent_click(t, B, "b1_ok")
    t.ok("B1 : mauvais nombre → rien", t.g("#s_b1") == 0 or t.g("#b1n") == 0)
    n = t.g("#b1n")
    for _ in range(n):
        ent_click(t, B, "b1_plus")
    ent_click(t, B, "b1_ok")
    t.ok(f"B1 (compter {n} étoiles chez le Fer) → résolu, grille du FER ouverte", t.g("#s_b1") == 1 and door_open(t, 3, 1))
    # C1 : gabarits
    to_level(t, C, 3, 1)
    target = t.g("#c1t")
    wrong = 1 if target != 1 else 2
    ent_click(t, C, f"c1_{wrong}")
    t.ok("C1 : mauvais gabarit → blocage de 5 s", t.g("#s_c1") == 0 and t.g("#c1lock") > 0)
    t.setg("#c1lock", 0)
    ent_click(t, C, f"c1_{target}")
    t.ok("C1 (gabarit identique au modèle du Cuivre) → résolu, grille du CUIVRE ouverte", t.g("#s_c1") == 1 and door_open(t, 1, 1))
    t.ok("niveau 1 terminé : étape 2", t.g("#step") == 2)


def sc_r2_level2(t):
    t.section = "salle 2 : niveau 2"
    tr = by_track(t)
    A, B, C = tr[1], tr[2], tr[3]
    for k, b in tr.items():
        to_level(t, b, k, 2)
    t.ok("montée : checkpoint individuel au niveau 2", all(t.score(b, "sol.cp") == 2 for b in BOTS))
    # A2 : couleurs
    for tgt in (t.g("#a2t1"), t.g("#a2t2")):
        cur = t.g("#a2m")
        for i, bit in ((1, 1), (2, 2), (3, 4)):
            if (cur ^ tgt) & bit:
                ent_click(t, A, f"a2_{i}", stand_dz=-1.6)
    t.ok("A2 (vitrail : deux couleurs dans l’ordre) → résolu, grille du FER ouverte", t.g("#s_a2") == 1 and door_open(t, 3, 2))
    # B2 : signes → code
    for d in (1, 1, 1, 1):
        ent_click(t, B, f"b2_{d}")
    ok_wrong = t.g("#s_b2") == 0 or t.g("#b2code") == 1111
    code = str(t.g("#b2code"))
    for d in code:
        ent_click(t, B, f"b2_{d}")
    t.ok("B2 : mauvais code recraché, bon code (inscription du Fer + table du Cuivre) → résolu", ok_wrong and t.g("#s_b2") == 1)
    t.ok("…grille du CUIVRE (niveau 2) ouverte", door_open(t, 1, 2))
    # C2 : cuves
    seq = ["fill_b", "b2s", "empty_s", "b2s", "fill_b", "b2s"] if t.g("#c2t") == 4 else ["fill_s", "s2b", "fill_s", "s2b", "empty_b", "s2b"]
    for op in seq:
        ent_click(t, C, f"c2_{op}")
    t.ok(f"C2 (cuves 5 L / 3 L → {t.g('#c2t')} L) → résolu, grille du LAITON ouverte", t.g("#s_c2") == 1 and door_open(t, 2, 2),
         f"b={t.g('#c2b')} s={t.g('#c2s')}")
    ent_click(t, C, "seeds", stand_dz=1.6)
    t.ok("indice « graines » trouvé dans le puits du Fer", t.g("#clue_graines") == 1)
    t.ok("niveau 2 terminé : étape 3", t.g("#step") == 3)


def sc_r2_deaths(t):
    t.section = "salle 2 : morts et reconnexion"
    tr = by_track(t)
    B, C = tr[2], tr[3]
    t.kill_respawn(B, SPAWN)
    t.near("mort : le Laiton réapparaît à SON niveau (2), dans son puits", B, (M(t)["cx"]["2"] + 0.5, 111, 1.5), 2.0)
    t.leave(C)
    t.wait(30)
    t.join(C, SPAWN)
    t.wait(20)
    t.ok("reconnexion : le Fer garde son puits", t.score(C, "sol.role") == 3 and t.score(C, "sol.room") == 2)
    t.near("…et revient à son niveau (2)", C, (M(t)["cx"]["3"] + 0.5, 111, 1.5), 2.0)
    solved = [t.g(f"#s_{p}") for p in ("a1", "b1", "c1", "a2", "b2", "c2")]
    w0 = t.g("#wipes") or 0
    for b in BOTS:
        t.kill_respawn(b, SPAWN)
    t.ok("les 3 à terre : groupe relevé, énigmes résolues conservées", (t.g("#wipes") or 0) == w0 + 1
         and [t.g(f"#s_{p}") for p in ("a1", "b1", "c1", "a2", "b2", "c2")] == solved)


def lights_solution(state):
    for combo in itertools.product((0, 1), repeat=9):
        s = list(state)
        for q, on in enumerate(combo):
            if on:
                r, c = divmod(q, 3)
                for rr, cc in ((r, c), (r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if 0 <= rr < 3 and 0 <= cc < 3:
                        s[rr * 3 + cc] ^= 1
        if all(s):
            return [q for q, on in enumerate(combo) if on]
    return None


def maze_path(edges):
    E = {frozenset(map(tuple, e)) for e in edges}
    start, goal = (0, 3), (3, 0)
    prev = {start: None}
    dq = deque([start])
    while dq:
        c = dq.popleft()
        if c == goal:
            break
        for d, (dc, dr) in zip("nswe", ((0, -1), (0, 1), (-1, 0), (1, 0))):
            n = (c[0] + dc, c[1] + dr)
            if frozenset((c, n)) in E and n not in prev:
                prev[n] = (c, d)
                dq.append(n)
    path, c = [], goal
    while prev[c]:
        c, d = prev[c]
        path.append(d)
    return path[::-1]


def sc_r2_level3(t):
    t.section = "salle 2 : niveau 3 et sommet"
    tr = by_track(t)
    A, B, C = tr[1], tr[2], tr[3]
    for k, b in tr.items():
        to_level(t, b, k, 3)
    # A3 : circuit logique (erreur = blocage 20 s)
    ent_click(t, A, "a3_ok", stand_dz=-1.6)
    t.ok("A3 : mauvaise combinaison → court-circuit, blocage", t.g("#a3lock") > 0 and t.g("#s_a3") == 0)
    t.setg("#a3lock", 0)
    sol = M(t)["circuits"][t.g("#a3c")]
    cxa = M(t)["cx"]["1"]
    for i, on in enumerate(sol, 1):
        if on:
            x = cxa - 4 + 2 * i
            t.look_use(A, (x + 0.5, 121, 2.6), (x + 0.5, 122.4, 4.85))
    ent_click(t, A, "a3_ok", stand_dz=-1.6)
    t.ok("A3 (leviers selon le schéma du Laiton) → résolu, grille du LAITON ouverte", t.g("#s_a3") == 1 and door_open(t, 2, 3))
    # B3 : labyrinthe
    ent_click(t, B, "b3_s")
    t.ok("B3 : foncer dans un mur → retour au départ", t.g("#mx") == 0 and t.g("#my") == 3)
    for d in maze_path(M(t)["mazes"][t.g("#b3m")]):
        ent_click(t, B, f"b3_{d}")
    t.ok("B3 (guidé par la fresque du Fer) → palet sur l’émeraude, grille du FER ouverte", t.g("#s_b3") == 1 and door_open(t, 3, 3),
         f"mx={t.g('#mx')} my={t.g('#my')}")
    # C3 : lumières
    state = [t.g(f"#c3_{q}") for q in range(9)]
    presses = lights_solution(state)
    for q in presses or []:
        ent_click(t, C, f"c3_{q}")
    t.ok("C3 (toutes les lampes rallumées) → résolu, grille du CUIVRE ouverte", t.g("#s_c3") == 1 and door_open(t, 1, 3), str(state))
    t.ok("tous les mécanismes résolus : direction le sommet", t.g("#step") == 4)
    for b in (A, B):
        t.tp(b, 2000.5, 131, 0.5)
    t.wait(10)
    t.ok("2 joueurs sur 3 au sommet : on attend le troisième", t.g("#trans") == 0 and t.g("#room") == 2)
    t.tp(C, 2001.5, 131, 1.5)
    t.wait(8)
    t.ok("les 3 réunis au sommet → salle terminée", (t.g("#trans") or 0) > 0)
    t.ok("défi « Horlogerie fine » (< 12 min) accordé", all(t.adv(b, "challenge/horlogerie_fine") for b in BOTS))
    t.ok("salle 2 → 3 : téléportation automatique", finish_transition(t, 3))


SCENARIOS = [sc_r2_level1, sc_r2_level2, sc_r2_deaths, sc_r2_level3]
