"""Scénarios salle 6 — Les Quatre Saisons : voyage, 4 chaînes de propagation, piège d’anticipation + remontée,
ordre des autels, accord des cloches (sablier), mort, anéantissement, reconnexion, retour arrière impossible."""
from testlib import BOTS, V
from scenarios import enter_ok, common_reconnect, no_way_back, finish_transition, ensure_room, SPAWN

# (position debout, point visé) en coordonnées locales (x, y, z) — y absolu relatif au sol (101 = pieds)
STAND = {
    "altar": ((0.5, 101, 10.6), (0.5, 101.8, 8.5)),
    "bell": ((3.5, 101, 10.6), (3.5, 101.6, 8.5)),
    "hourglass": ((-2.5, 101, 10.6), (-2.5, 101.6, 8.5)),
    "sablier": ((-3.3, 101, 24.5), (-4.5, 101.8, 24.5)),
    "chest": ((-21.3, 101, 6.5), (-22.5, 101.5, 6.5)),
    "tree": ((-3.5, 101, -15.8), (-3.5, 101.8, -17.5)),
    "wheel": ((-8.5, 101, -15.8), (-8.5, 101.6, -13.5)),
    "flame": ((-24.5, 101, 17.4), (-24.5, 101.4, 19.5)),
    "bellows": ((-21.5, 101, 17.4), (-21.5, 101.5, 19.5)),
    "brazier": ((20.4, 101, 3.5), (22.5, 101.4, 3.5)),
    "leaves": ((-5.5, 101, 18.3), (-5.5, 101.4, 16.5)),
    "bud": ((15.5, 101, 13.4), (15.5, 102.0, 15.5)),
    "table": ((20.5, 101, 21.4), (20.5, 101.6, 23.5)),
    "pick_au": ((-15.5, 101, -27.2), (-15.5, 101.8, -28.5)),
    "pick_su": ((27.3, 101, 6.5), (29.5, 101.8, 6.5)),
    "pick_wi": ((13.5, 101, -10.5), (14.5, 101.8, -10.5)),
}
SE = {1: "Printemps", 2: "Été", 3: "Automne", 4: "Hiver"}


def A(t, s, x, y, z):
    m = t.meta["rooms"]["6"]
    return (m["ox"] + x, y, m["z"][str(s)] + z)


def goto_season(t, who, s):
    t.rc(f"scoreboard players set {who} sol.sea {s}")
    x, y, z = A(t, s, 0.5, 101, 24.5)
    t.tp(who, x, y, z)
    t.wait(3)


def click(t, who, s, key, attack=False):
    (sx, sy, sz), (ax, ay, az) = STAND[key]
    x, y, z = A(t, s, sx, sy, sz)
    for b in BOTS:     # un coéquipier sur la ligne de visée intercepterait le clic
        if b != who:
            p = t.pos(b)
            if p and abs(p[0] - x) < 3 and abs(p[2] - z) < 3 and abs(p[1] - y) < 3:
                t.tp(b, x, y + 0.0, z + 3.5 if sz >= az else z - 3.5)
    t.rc(f"scoreboard players set {who} sol.sea {s}")
    t.rc(f"scoreboard players set {who} sol.cool 0")
    t.look_use(who, (x, y, z), A(t, s, ax, ay, az), attack)


def hold(t, who, pred):
    for i in range(9):
        if "passed" in t.rc(f"execute if items entity {who} hotbar.{i} {pred}"):
            t.rc(f"player {who} hotbar {i + 1}")
            t.wait(2)
            return True
    # pas dans la barre : on le déplace dans la main (gardien de la Lanterne suspendu pendant le déplacement,
    # sinon le doublon transitoire est détecté et la Lanterne redistribuée)
    lant = t.g("#lantern")
    t.setg("#lantern", 0)
    try:
        return _move_to_hand(t, who, pred)
    finally:
        t.setg("#lantern", lant or 0)


def _move_to_hand(t, who, pred):
    t.rc(f"item replace entity {who} hotbar.8 with air")
    for slot in range(9, 36):
        if "passed" in t.rc(f"execute if items entity {who} inventory.{slot - 9} {pred}"):
            t.rc(f"item replace entity {who} hotbar.8 from entity {who} inventory.{slot - 9}")
            t.rc(f"item replace entity {who} inventory.{slot - 9} with air")
            t.rc(f"player {who} hotbar 9")
            t.wait(2)
            return True
    return False


def blk(t, s, lx, y, lz, block):
    x, _, z = A(t, s, lx, 0, lz)
    return "passed" in t.rc(f"execute if block {x} {y} {z} {block}")


CR = lambda k: f"amethyst_shard[custom_data~{{sol:{{cr{k}:1b}}}}]"
ACORN = "oak_sapling[custom_data~{sol:{acorn:1b}}]"
BUD = "small_amethyst_bud[custom_data~{sol:{bud:1b}}]"
AXE = "iron_axe[custom_data~{sol:{axe:1b}}]"
CAD = "clock[custom_data~{sol:{cadran:1b}}]"
LANT = "lantern[custom_data~{sol:{lantern:1b}}]"


def place(t, who, s, k):
    hold(t, who, CR(k))
    click(t, who, s, "altar")
    click(t, who, s, "altar")


def sc_r6_travel(t):
    t.section = "salle 6 : voyage"
    ensure_room(t, 6)
    enter_ok(t, 6)
    t.ok("chacun reçoit un Cadran des Saisons", all(t.has(b, CAD) for b in BOTS))
    t.ok("vallée remise à zéro à l’entrée (aucun cristal rendu)", t.g("#placed") == 0 and t.g("#sluice") == 0)
    goto_season(t, "Bot1", 1)
    z0 = t.pos("Bot1")[2]
    hold(t, "Bot1", CAD)
    t.rc("player Bot1 sneak")
    t.wait(16)
    t.rc("player Bot1 unsneak")
    t.wait(4)
    p = t.pos("Bot1")
    t.ok("Cadran + accroupi : Printemps → Été, même position (z + 200)", p and abs(p[2] - (z0 + 200)) < 1.5, f"{z0} → {p}")
    t.ok("saison du joueur mise à jour (Été)", t.score("Bot1", "sol.sea") == 2)
    t.ok("les autres joueurs restent au Printemps (groupe éclaté possible)", t.score("Bot2", "sol.sea") == 1)
    goto_season(t, "Bot1", 4)
    z4 = t.pos("Bot1")[2]
    t.wait(35)
    hold(t, "Bot1", CAD)
    t.rc("player Bot1 sneak")
    t.wait(16)
    t.rc("player Bot1 unsneak")
    t.wait(4)
    p = t.pos("Bot1")
    t.ok("Hiver → Printemps (cycle)", p and abs(p[2] - (z4 - 600)) < 1.5 and t.score("Bot1", "sol.sea") == 1, f"{p}")
    t.rc("player Bot1 hotbar 9")
    t.wait(35)
    t.rc("player Bot1 sneak")
    t.wait(16)
    t.rc("player Bot1 unsneak")
    t.wait(3)
    p2 = t.pos("Bot1")
    t.ok("sans le Cadran en main, s’accroupir ne fait rien", p2 and p and abs(p2[2] - p[2]) < 1.5, f"{p} → {p2}")
    no_way_back(t, 6)
    # chute dans le ravin → Cercle de la saison
    x, _, z = A(t, 3, 0.5, 0, -22.5)
    t.rc("scoreboard players set Bot2 sol.sea 3")
    t.tp("Bot2", x, 95, z)
    t.wait(5)
    t.near("chute dans le ravin (Automne) → retour au Cercle de l’Automne", "Bot2", A(t, 3, 0.5, 101, 24.5), 2.5)


def sc_r6_trap(t):
    t.section = "salle 6 : anticipation"
    # rush : bourgeon → coffre → cristal du printemps rendu SANS avoir planté le gland
    click(t, "Bot1", 1, "bud")
    t.ok("bourgeon cueilli au printemps → chacun en a une copie", t.g("#bud_got") == 1 and all(t.has(b, BUD) for b in BOTS))
    hold(t, "Bot1", BUD)
    click(t, "Bot1", 1, "chest")
    t.ok("bourgeon déposé dans le Coffre du Temps (printemps), retiré des sacs",
         t.g("#bud_in") == 1 and not any(t.has(b, BUD) for b in BOTS))
    t.ok("propagation : en été, le coffre montre un bourgeon qui a grossi",
         t.count(f"@e[type=item_display,tag=sol.r6disp,x={t.meta['rooms']['6']['ox'] - 30},y=90,z=190,dx=20,dy=20,dz=30]") >= 1)
    click(t, "Bot2", 3, "chest")
    t.ok("propagation : en automne, le bourgeon a mûri → Cristal du Printemps", t.g("#sp_taken") == 1 and t.has("Bot2", CR(1)))
    place(t, "Bot2", 1, 1)
    t.ok("premier clic = avertissement, second = cristal du Printemps rendu", t.g("#placed") == 1 and t.g("#lock1") == 1)
    t.ok("le cristal quitte les sacs de tous", not any(t.has(b, CR(1)) for b in BOTS))
    click(t, "Bot3", 3, "leaves")
    t.ok("gland trouvé en automne", t.g("#acorn_got") == 1 and t.has("Bot1", ACORN))
    hold(t, "Bot1", ACORN)
    click(t, "Bot1", 1, "tree")
    t.ok("Printemps figé : impossible de planter", t.g("#planted") == 0)
    t.rc(f"scoreboard players set #m60 {V} 0")
    t.rc("function solstice:r6/deadlock")
    t.ok("impasse détectée et annoncée (le Sablier de Remontée est proposé)", True)
    # remontée du temps
    click(t, "Bot3", 2, "sablier")
    t.ok("Sablier de Remontée : 1er clic = confirmation demandée", t.g("#rconf") > 0 and t.g("#placed") == 1)
    click(t, "Bot3", 2, "sablier")
    t.ok("2e clic : toute la vallée revient au début", t.g("#placed") == 0 and t.g("#lock1") == 0 and t.g("#bud_got") == 0
         and t.g("#acorn_got") == 0 and t.g("#sp_taken") == 0)
    t.ok("remontée : objets de la vallée retirés des sacs", not any(t.has(b, ACORN) for b in BOTS))
    t.ok("remontée : coûteuse (joueurs figés)", "passed" in t.rc("execute if entity @a[name=Bot1,nbt={active_effects:[{id:\"minecraft:slowness\"}]}]"))
    t.ok("remontée comptée (le défi « sans sablier » est perdu)", t.g("#r6resets") == 1)
    t.near("remontée : tout le monde au Cercle du Printemps", "Bot2", A(t, 1, 0.5, 101, 24.5), 2.5)
    t.rc("effect clear @a slowness")
    t.rc("effect clear @a jump_boost")


def sc_r6_chains(t):
    t.section = "salle 6 : propagations"
    # --- chaîne arbre
    click(t, "Bot3", 3, "leaves")
    hold(t, "Bot1", ACORN)
    click(t, "Bot1", 1, "tree")
    t.ok("gland planté au printemps", t.g("#planted") == 1)
    t.ok("printemps : pousse de chêne", blk(t, 1, -4, 101, -18, "oak_sapling"))
    t.ok("propagation : en été, un chêne adulte (tronc de 7 blocs)", blk(t, 2, -4, 101, -18, "oak_log") and blk(t, 2, -4, 107, -18, "oak_log"))
    t.ok("propagation : en automne, un vieux chêne", blk(t, 3, -4, 105, -18, "oak_log"))
    t.ok("pas encore de pont (automne)", blk(t, 3, -4, 100, -22, "air"))
    # atterrissage sûr : voyager du printemps au pied du chêne → au-dessus de sa cime en été
    x, y, z = A(t, 1, -3.5, 101, -17.5)
    t.rc("scoreboard players set Bot2 sol.sea 1")
    t.tp("Bot2", x, y, z)
    t.wait(3)
    hold(t, "Bot2", CAD)
    t.rc("player Bot2 sneak")
    t.wait(16)
    t.rc("player Bot2 unsneak")
    t.wait(4)
    p = t.pos("Bot2")
    t.ok("atterrissage sûr : on ne se retrouve jamais dans un tronc (posé au-dessus)", p and p[1] >= 108, f"{p}")
    click(t, "Bot3", 4, "table")
    t.ok("hache trouvée en hiver (atelier de Lise)", t.g("#axe_got") == 1 and t.has("Bot1", AXE))
    hold(t, "Bot3", AXE)
    click(t, "Bot3", 2, "tree")
    t.ok("en été, le chêne est trop jeune pour être abattu", t.g("#chopped") == 0 and t.g("#chop") == 0)
    for i in range(3):
        click(t, "Bot3", 3, "tree", attack=(i % 2 == 0))
    t.ok("3 coups de hache en automne → le chêne tombe", t.g("#chopped") == 1)
    t.ok("propagation : pont de bois au-dessus du ravin en automne", blk(t, 3, -4, 100, -22, "oak_log"))
    t.ok("propagation : le pont existe aussi en hiver (enneigé)", blk(t, 4, -4, 100, -22, "oak_log") and blk(t, 4, -4, 101, -22, "snow"))
    t.ok("…mais pas au printemps ni en été (le passé)", blk(t, 1, -4, 100, -22, "air") and blk(t, 2, -4, 100, -22, "air"))
    t.ok("la hache disparaît une fois utilisée", not any(t.has(b, AXE) for b in BOTS))
    # --- chaîne coffre (printemps → automne)
    click(t, "Bot1", 1, "bud")
    hold(t, "Bot1", BUD)
    click(t, "Bot1", 1, "chest")
    click(t, "Bot1", 1, "chest")
    t.ok("on peut reprendre le bourgeon du coffre tant qu’il n’a pas mûri", t.g("#bud_in") == 0 and t.has("Bot2", BUD))
    hold(t, "Bot1", BUD)
    click(t, "Bot1", 1, "chest")
    click(t, "Bot2", 2, "chest")
    t.ok("en été, le coffre ne rend rien (pas encore mûr)", t.g("#sp_taken") == 0)
    click(t, "Bot2", 3, "chest")
    t.ok("automne : Cristal du Printemps récupéré, pour tout le groupe", t.g("#sp_taken") == 1 and all(t.has(b, CR(1)) for b in BOTS))
    # --- chaîne eau (été → automne → hiver)
    t.ok("avant la vanne : bassin vide en hiver", blk(t, 4, 10, 99, -10, "air"))
    for i in range(4):
        click(t, "Bot2", 2, "wheel")
    t.ok("vanne tournée 4 fois en été → ouverte", t.g("#sluice") == 4)
    t.ok("propagation : en été, le bassin se remplit", blk(t, 2, 10, 99, -10, "water"))
    t.ok("propagation : en automne, un étang", blk(t, 3, 10, 99, -10, "water"))
    t.ok("propagation : en hiver, un lac gelé (on marche dessus)", blk(t, 4, 10, 99, -10, "ice"))
    t.ok("le printemps n’est pas touché (le passé)", blk(t, 1, 10, 99, -10, "air") and blk(t, 1, -10, 99, -12, "spruce_planks"))
    # rendre le printemps (arbre planté, bourgeon mûri : prêt)
    place(t, "Bot3", 1, 1)
    t.ok("cristal du Printemps rendu (1/4)", t.g("#placed") == 1)
    # --- chaîne braise + soufflet (été + hiver, simultané)
    holder = next((b for b in BOTS if t.has(b, LANT)), None)
    t.ok("la Lanterne est bien dans le groupe", holder is not None)
    if holder is None:
        return
    other = next(b for b in BOTS if b != holder)
    hold(t, holder, LANT)
    click(t, other, 4, "brazier")
    t.ok("brasero d’hiver sans braise : rien", t.g("#burn") == 0)
    click(t, holder, 2, "flame")
    t.ok("Flamme éternelle (été) : la Lanterne capture une braise", t.g("#ember") > 0)
    click(t, holder, 4, "brazier")
    t.ok("braise portée en hiver → brasero allumé", t.g("#burn") > 0 and t.g("#ember") == 0,
         f"holder={holder} ember={t.g('#ember')} burn={t.g('#burn')} lock4={t.g('#lock4')} melted={t.g('#melted')} "
         f"pos={t.pos(holder)} sea={t.score(holder, 'sol.sea')} main={t.rc(f'data get entity {holder} SelectedItem id')}")
    t.wait(40)
    t.ok("sans soufflet, la glace ne fond pas", t.g("#melt") == 0)
    (sx, sy, sz), (ax, ay, az) = STAND["bellows"]
    x, y, z = A(t, 2, sx, sy, sz)
    t.rc(f"scoreboard players set {other} sol.sea 2")
    t.tp(other, x, y, z)
    t.wait(2)
    t.rc(f"player {other} look at {' '.join(str(v) for v in A(t, 2, ax, ay, az))}")
    t.rc(f"player {other} use interval 12")
    t.wait_until(lambda: t.g("#melted") == 1, 380, 20)
    t.rc(f"player {other} stop")
    t.ok("soufflet actionné en été PENDANT que le brasero brûle en hiver → la glace fond", t.g("#melted") == 1)
    t.ok("propagation : la grotte d’hiver est ouverte", blk(t, 4, 24, 102, 6, "air"))
    click(t, "Bot3", 4, "pick_su")
    t.ok("Cristal de l’Été récupéré dans la grotte", t.g("#su_taken") == 1 and t.has("Bot1", CR(2)))
    place(t, "Bot1", 2, 2)
    t.ok("cristal de l’Été rendu (2/4) — l’Été est figé", t.g("#placed") == 2 and t.g("#lock2") == 1)
    click(t, "Bot2", 2, "bellows")
    t.ok("Été figé : le soufflet ne fait plus rien", t.g("#pump") == 0)
    click(t, "Bot2", 3, "pick_au")
    t.ok("Cristal de l’Automne récupéré sur le plateau (derrière le pont)", t.g("#au_taken") == 1)
    place(t, "Bot2", 3, 3)
    t.ok("cristal de l’Automne rendu (3/4)", t.g("#placed") == 3)
    click(t, "Bot3", 4, "pick_wi")
    t.ok("Cristal de l’Hiver récupéré sur l’îlot (lac gelé)", t.g("#wi_taken") == 1)
    place(t, "Bot3", 4, 4)
    t.ok("cristal de l’Hiver rendu (4/4)", t.g("#placed") == 4)
    t.ok("étape finale : les cloches (#step = 4)", t.g("#step") == 4)


def sc_r6_deaths(t):
    t.section = "salle 6 : morts et reconnexion"
    placed = t.g("#placed")
    goto_season(t, "Bot2", 3)
    t.kill_respawn("Bot2", SPAWN)
    t.ok("mort : le joueur reste dans la salle, progression intacte", t.score("Bot2", "sol.room") == 6 and t.g("#placed") == placed)
    t.ok("mort : pas de spectateur hors combat", t.gm("Bot2", "adventure"))
    t.ok("mort : le Cadran est rendu", t.has("Bot2", CAD))
    t.leave("Bot3")
    t.wait(30)
    t.join("Bot3", SPAWN)
    t.wait(20)
    t.ok("reconnexion : remis dans la salle 6", t.score("Bot3", "sol.room") == 6)
    p = t.pos("Bot3")
    t.ok("reconnexion : dans une des vallées", p and 5950 < p[0] < 6050)
    t.ok("reconnexion : Cadran rendu", t.has("Bot3", CAD))
    w0 = t.g("#wipes") or 0
    for b in BOTS:
        t.kill_respawn(b, SPAWN)
    t.ok("les 3 à terre : le groupe est relevé", (t.g("#wipes") or 0) == w0 + 1 and all(t.gm(b, "adventure") for b in BOTS))
    t.ok("…sans perdre les cristaux rendus", t.g("#placed") == placed)


def sc_r6_bells(t):
    t.section = "salle 6 : cloches"
    for b, s in zip(BOTS, (1, 2, 3)):
        click(t, b, s, "bell")
    t.ok("3 cloches sonnées (printemps, été, automne)…", all(t.g(f"#bell{k}") == 1 for k in (1, 2, 3)) or t.g("#chord") == 0,
         str([t.g(f"#bell{k}") for k in (1, 2, 3)]))
    t.ok("…mais sans l’hiver, l’accord n’est pas complet", t.g("#r6done") == 0)
    t.sprint(80)
    t.wait(3)
    t.ok("après la fenêtre, les cloches se taisent (à refaire ensemble)", t.g("#bell1") == 0 and t.g("#chord") == 0)
    click(t, "Bot1", 4, "hourglass")
    t.ok("Sablier du Solstice retourné en hiver (30 s)", t.g("#hg") > 0 and t.g("#hgs") == 4)
    # on prépare les trois sonneurs, puis on raccourcit l’attente
    for b, s in zip(BOTS, (1, 2, 3)):
        (sx, sy, sz), (ax, ay, az) = STAND["bell"]
        t.rc(f"scoreboard players set {b} sol.sea {s}")
        x, y, z = A(t, s, sx, sy, sz)
        t.tp(b, x, y, z)
    t.wait(2)
    for b, s in zip(BOTS, (1, 2, 3)):
        (sx, sy, sz), (ax, ay, az) = STAND["bell"]
        t.rc(f"player {b} look at {' '.join(str(v) for v in A(t, s, ax, ay, az))}")
        t.rc(f"scoreboard players set {b} sol.cool 0")
    t.wait(2)
    t.setg("#hg", 20)
    for b in BOTS:
        t.rc(f"player {b} use once")
    t.wait(40)
    t.ok("les 3 cloches + le sablier sonnent ensemble → salle terminée", t.g("#r6done") == 1,
         f"bells={[t.g(f'#bell{k}') for k in (1, 2, 3, 4)]} chord={t.g('#chord')} hg={t.g('#hg')} placed={t.g('#placed')} "
         f"trans={t.g('#trans')} room={t.g('#room')}")
    t.ok("défi « sans sablier » non accordé (on a remonté le temps)", not t.adv("Bot1", "challenge/premier_sablier"))
    t.ok("salle 6 → 7 : téléportation automatique", finish_transition(t, 7))
    t.ok("advancement « Les Quatre Saisons » accordé", all(t.adv(b, "room/r6") for b in BOTS))
    t.ok("les objets de la vallée ne suivent pas (Cadran retiré)", not any(t.has(b, CAD) for b in BOTS))


SCENARIOS = [sc_r6_travel, sc_r6_trap, sc_r6_chains, sc_r6_deaths, sc_r6_bells]
