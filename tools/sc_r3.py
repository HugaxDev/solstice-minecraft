"""Scénarios salle 3 — L’Atelier d’Orel : missions tirées au sort et réservées, caisses (solution complète en vrais
clics), cloches (fausse note + 3 manches), miroirs, assemblage simultané (échec puis réussite), Lanterne unique
(gardien : déconnexion du porteur), encre invisible, passage secret, indices, mot épelé, morts, reconnexion."""
from testlib import BOTS, V
from scenarios import ensure_room, finish_transition, no_way_back, SPAWN

LANT = "lantern[custom_data~{sol:{lantern:1b}}]"


def M(t):
    return t.meta["rooms"]["3"]


def comp(k):
    return {1: "iron_bars", 2: "string", 3: "glass_pane"}[k] + f"[custom_data~{{sol:{{comp{k}:1b}}}}]"


def by_role(t):
    return {t.score(b, "sol.role"): b for b in BOTS}


def click_tag(t, who, tag, stand, attack=False):
    p = t.entity_pos(f"@e[type=interaction,tag={tag},limit=1]")
    h = t.entity_h(tag)
    t.rc(f"scoreboard players set {who} sol.cool 0")
    t.look_use(who, stand, (p[0], p[1] + h / 2, p[2]), attack)


def go_mission(t, who, k):
    x, z = M(t)["pads"][str(k)]
    t.rc(f"scoreboard players set {who} sol.cool 0")
    t.tp(who, x + 0.5, 101, z + 0.5)
    t.wait(6)


def hold(t, who, pred):
    for i in range(9):
        if "passed" in t.rc(f"execute if items entity {who} hotbar.{i} {pred}"):
            t.rc(f"player {who} hotbar {i + 1}")
            t.wait(2)
            return True
    return False


def sc_r3_missions(t):
    t.section = "salle 3 : missions"
    ensure_room(t, 3)
    t.wait(10)
    ro = by_role(t)
    t.ok("tirage : une mission différente par joueur", sorted(ro) == [1, 2, 3], str(ro))
    no_way_back(t, 3)
    # porte réservée
    other = ro[2]
    go_mission(t, other, 1)
    p = t.pos(other)
    t.ok("porte réservée : un autre joueur ne peut pas entrer dans le Grenier", p and p[2] > -20)
    for k in (1, 2, 3):
        go_mission(t, ro[k], k)
    t.near("le joueur du Grenier y est téléporté", ro[1], M(t)["m1_entry"][:3], 2.0)
    t.near("le joueur de la Cave y est téléporté", ro[2], M(t)["m2_entry"][:3], 2.0)
    t.near("le joueur du Cabinet y est téléporté", ro[3], M(t)["m3_entry"][:3], 2.0)
    # ---- Grenier : solution complète, en vrais clics
    gx, gz = M(t)["m1"]
    A = ro[1]
    ok_moves = True
    for (cx, cy), (dx, dy) in M(t)["sk_solution"]:
        i = next(n for n in (1, 2) if t.g(f"#cr{n}x") == cx and t.g(f"#cr{n}z") == cy)
        stand = (gx + cx + 0.5 - dx * 1.45, 101, gz + cy + 0.5 - dy * 1.45)
        t.rc(f"scoreboard players set {A} sol.cool 0")
        t.look_use(A, stand, (gx + cx + 0.5, 101.5, gz + cy + 0.5))
        if not (t.g(f"#cr{i}x") == cx + dx and t.g(f"#cr{i}z") == cy + dy):
            ok_moves = False
    t.ok(f"Grenier : {len(M(t)['sk_solution'])} poussées réelles, chaque caisse avance dans la direction du regard", ok_moves)
    t.ok("Grenier : les deux caisses sur les dalles d’or → vitrine ouverte", t.g("#m1done") == 1)
    click_tag(t, A, "sol.k3_m1_ped", (gx + 1.5, 101, gz + 8.0))
    t.ok("Grenier : pièce « Cage de laiton » récupérée", t.has(A, comp(1)))
    # ---- Cave : fausse note puis trois manches
    C2 = ro[2]
    bells = M(t)["bells"]

    def ring(i):
        x, z = bells[i]
        t.rc(f"scoreboard players set {C2} sol.cool 0")
        t.look_use(C2, (x + 0.5, 101, z - 1.3), (x + 0.5, 102.4, z + 0.3))

    click_tag(t, C2, "sol.k3_m2_box", (3000.5, 101, 38.6))
    t.ok("Cave : la boîte à musique joue la mélodie", t.g("#m2play") == 1)
    t.sprint(110)
    first = t.g("#mel0")
    ring((first + 1) % 5)
    t.ok("Cave : fausse note → on recommence la manche", t.g("#m2in") == 0 and t.g("#m2round") == 1)
    t.sprint(130)
    for rnd in (1, 2, 3):
        for n in range(rnd + 2):
            ring(t.g(f"#mel{n}"))
        t.sprint(130)
    t.ok("Cave : trois mélodies rejouées → vitrine ouverte", t.g("#m2done") == 1, f"round={t.g('#m2round')} in={t.g('#m2in')}")
    click_tag(t, C2, "sol.k3_m2_ped", (2996.5, 101, 35.8))
    t.ok("Cave : pièce « Mèche éternelle » récupérée", t.has(C2, comp(2)))
    # ---- Cabinet : miroirs
    B3 = ro[3]
    ox, oz = M(t)["m3"]
    goal = M(t)["good"][0]
    for i, (mx, mz) in enumerate(M(t)["mirrors"]):
        if (goal >> i) & 1:
            t.rc(f"scoreboard players set {B3} sol.cool 0")
            t.look_use(B3, (ox + mx + 0.5, 101, oz + mz + 1.8), (ox + mx + 0.5, 101.6, oz + mz + 0.5))
    t.ok("Cabinet : miroirs orientés → la lumière atteint la cible", t.g("#m3done") == 1, f"cfg={t.g('#m3cfg')}")
    click_tag(t, B3, "sol.k3_m3_ped", (ox + 1.5, 101, oz + 6.6))
    t.ok("Cabinet : pièce « Verre de lune » récupérée", t.has(B3, comp(3)))
    t.ok("trois pièces rapportées : étape « assemblage »", t.g("#step") == 2)


def sc_r3_deaths(t):
    t.section = "salle 3 : morts et reconnexion"
    ro = by_role(t)
    t.kill_respawn(ro[1], SPAWN)
    t.ok("mort : retour à l’atelier, la pièce est conservée", t.score(ro[1], "sol.room") == 3 and t.has(ro[1], comp(1)))
    t.leave(ro[2])
    t.wait(30)
    t.join(ro[2], SPAWN)
    t.wait(20)
    t.ok("reconnexion : mission et pièce conservées", t.score(ro[2], "sol.role") == 2 and t.has(ro[2], comp(2)))
    t.near("…remis dans l’atelier", ro[2], M(t)["cp"][:3], 2.5)
    w0 = t.g("#wipes") or 0
    for b in BOTS:
        t.kill_respawn(b, SPAWN)
    t.ok("les 3 à terre : relevés, les pièces restent en poche", (t.g("#wipes") or 0) == w0 + 1
         and all(t.has(ro[k], comp(k)) for k in (1, 2, 3)))


def place(t, who, k):
    hold(t, who, comp(k))
    x, z = M(t)["bench"][k - 1]
    t.rc(f"scoreboard players set {who} sol.cool 0")
    t.look_use(who, (x + 0.5, 101, z + 1.9), (x + 0.5, 102.3, z + 0.5))


def sc_r3_assembly(t):
    t.section = "salle 3 : assemblage et Lanterne"
    ro = by_role(t)
    place(t, ro[1], 1)
    place(t, ro[2], 2)
    t.ok("pose d’une pièce sur l’établi (elle quitte l’inventaire)", t.g("#slot1") == 1 and t.g("#slot2") == 1 and not t.has(ro[1], comp(1)))
    t.sprint(80)
    t.wait(4)
    t.ok("deux pièces seulement : elles retombent, rendues à leurs porteurs", t.g("#slot1") == 0 and t.has(ro[1], comp(1)) and t.has(ro[2], comp(2)))
    t.ok("pas de Lanterne sans les trois", t.g("#lantern") == 0)
    for k in (1, 2, 3):
        hold(t, ro[k], comp(k))
    for k in (1, 2, 3):          # trois poses en moins de 3 s
        x, z = M(t)["bench"][k - 1]
        t.rc(f"scoreboard players set {ro[k]} sol.cool 0")
        t.rc(f"tp {ro[k]} {x + 0.5} 101 {z + 1.9}")
        t.rc(f"player {ro[k]} look at {x + 0.5} 102.3 {z + 0.5}")
    t.wait(2)
    for k in (1, 2, 3):
        x, z = M(t)["bench"][k - 1]
        t.rc(f"player {ro[k]} look at {x + 0.5} 102.3 {z + 0.5}")
        t.rc(f"player {ro[k]} use once")
        t.wait(3)
    t.wait(10)
    t.ok("les trois pièces posées ensemble → Lanterne des Saisons assemblée", t.g("#lantern") == 1 and t.g("#step") == 3,
         f"slots={[t.g(f'#slot{k}') for k in (1, 2, 3)]} asm={t.g('#asm')} held={[t.rc(f'data get entity {ro[k]} SelectedItem.id') for k in (1, 2, 3)]}")
    t.wait(30)
    holders = [b for b in BOTS if t.has(b, LANT)]
    t.ok("une seule Lanterne pour le groupe", len(holders) == 1, str(holders))
    if not holders:
        return
    h = holders[0]
    # gardien : le porteur se déconnecte → elle passe à un coéquipier, sans doublon au retour
    t.leave(h)
    t.wait(40)
    others = [b for b in BOTS if b != h and t.has(b, LANT)]
    t.ok("porteur déconnecté : la Lanterne passe à un coéquipier", len(others) == 1)
    t.join(h, SPAWN)
    t.wait(40)
    n = sum(1 for b in BOTS if t.has(b, LANT))
    t.ok("porteur revenu : toujours une seule Lanterne", n == 1, str(n))


def sc_r3_lantern(t):
    t.section = "salle 3 : encre invisible"
    h = next(b for b in BOTS if t.has(b, LANT))
    hold(t, h, LANT)
    shown = 0
    for (x, y, z, yaw) in M(t)["ink"]:
        t.tp(h, x + (1.5 if x < 3000 else -1.5), 101, z + (1.5 if z < 0 else -1.5))
        t.wait(12)
        shown = max(shown, t.count("@e[type=text_display,tag=sol.ink,tag=sol.shown]"))
    t.ok("Lanterne en main : l’encre invisible apparaît près du porteur", shown >= 1)
    t.tp(h, 3000.5, 101, 5.5)
    t.wait(20)
    t.tp(h, 3012.5, 101, 7.5)
    t.wait(25)
    t.ok("…et disparaît quand la Lanterne s’éloigne", t.count("@e[type=text_display,tag=sol.ink,tag=sol.i_mot,tag=sol.shown]") == 0)
    t.tp(h, 3000.5, 101, -2.4)
    t.wait(15)
    t.ok("sous l’établi, à la Lanterne : indice « mot »", t.g("#clue_mot") == 1)
    t.tp(h, 2986.5, 101, 5.5)
    t.wait(15)
    t.ok("passage secret révélé derrière les étagères", "passed" in t.rc("execute if block 2985 102 5 air"))
    t.tp(h, 2982.5, 101, 5.5)
    t.wait(15)
    t.ok("dans l’alcôve, à la Lanterne : indice « plan »", t.g("#clue_plan") == 1)
    # épeler TEMPS en marchant sur les dalles
    tiles, word = M(t)["tiles"], M(t)["word"]
    w = next(b for b in BOTS if b != h)

    def step(letter):
        idx = tiles.index(letter)
        c, r = idx % 4, idx // 4
        t.tp(w, 2995 + 3 * c + 1.0, 101, 3 + 3 * r + 1.0)
        t.wait(4)
        t.tp(w, 3000.5, 101, 1.5)
        t.wait(3)
    step("T")
    step("A")
    t.ok("mauvaise lettre : le plancher grince, on recommence", t.g("#spell") == 0)
    for letter in word[:-1]:
        step(letter)
    t.ok(f"lettres {word[:-1]} : le mot se forme", t.g("#spell") == len(word) - 1)
    step(word[-1])
    t.ok("mot TEMPS épelé → la grande horloge s’ouvre, salle terminée", (t.g("#trans") or 0) > 0)
    t.ok("salle 3 → 4 : téléportation automatique", finish_transition(t, 4))
    t.ok("la Lanterne suit le groupe (objet permanent)", sum(1 for b in BOTS if t.has(b, LANT)) == 1)


SCENARIOS = [sc_r3_missions, sc_r3_deaths, sc_r3_assembly, sc_r3_lantern]
