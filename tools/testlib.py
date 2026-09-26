"""Bibliothèque de tests E2E : serveur Fabric + Carpet (tests uniquement) sur une COPIE du monde, 3 joueurs factices.

Pièges connus (hérités de Fragments) :
- Carpet vise avec `player X look at`, pas avec la rotation d’un tp.
- Un joueur factice mort est déconnecté : la réapparition est simulée par une reconnexion.
- RCON : une réponse par paquet (géré par server.Rcon).
"""
import json
import os
import re
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from server import Server, mod_paths  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build")
BOTS = ["Bot1", "Bot2", "Bot3"]
V = "sol.var"


class Runner:
    def __init__(self, srv, manifest):
        self.srv = srv
        self.m = manifest
        self.meta = manifest["meta"]
        self.results = []   # (section, name, ok, detail, secret)
        self.section = "général"
        self.secret = False
        self._n5 = 0

    # ------------------------------------------------------------ primitives
    def rc(self, cmd):
        return self.srv.rcon(cmd)

    def wait(self, ticks):
        time.sleep(ticks / 20 + 0.15)

    def sprint(self, ticks):
        before = self.srv.console().count("Sprint completed")
        self.rc(f"tick sprint {ticks}")
        t0 = time.time()
        while time.time() - t0 < 180:
            if self.srv.console().count("Sprint completed") > before:
                return
            time.sleep(0.2)

    def ok(self, name, cond, detail=""):
        """Sortie console sans spoiler par défaut (numéro du test) ; noms complets avec SOLSTICE_SPOILERS=1.
        Les résultats détaillés sont toujours écrits dans design/SPOILERS_NE_PAS_LIRE/."""
        cond = bool(cond)
        self.results.append((self.section, name, cond, detail if not cond else "", self.secret))
        self._n = getattr(self, "_n", 0) + 1
        if self.secret:
            self._n5 += 1
            print(f"  {'PASS' if cond else 'FAIL'} [salle 5] test n°{self._n5}")
        elif os.environ.get("SOLSTICE_SPOILERS"):
            print(f"  {'PASS' if cond else 'FAIL'} [{self.section}] {name}{(' — ' + detail) if (detail and not cond) else ''}")
        else:
            print(f"  {'PASS' if cond else 'FAIL'} [{self.section}] test n°{self._n}")
        return cond

    def check(self, name, cond):
        r = self.rc(f"execute if {cond}")
        return self.ok(name, "passed" in r, f"{cond} → {r}")

    def score(self, holder, obj=V):
        r = self.rc(f"scoreboard players get {holder} {obj}")
        m = re.search(r"has (-?\d+)", r)
        return int(m.group(1)) if m else None

    def g(self, name):
        return self.score(name, V)

    def setg(self, name, value):
        self.rc(f"scoreboard players set {name} {V} {value}")

    def pos(self, who):
        r = self.rc(f"data get entity {who} Pos")
        nums = re.findall(r"(-?\d+(?:\.\d+)?(?:E-?\d+)?)d", r)
        return tuple(float(n) for n in nums[:3]) if len(nums) >= 3 else None

    def near(self, name, who, target, tol=2.0):
        p = self.pos(who)
        good = p is not None and all(abs(a - b) <= tol for a, b in zip(p, target))
        return self.ok(name, good, f"{who} en {p}, attendu ~{target}")

    def count(self, sel):
        self.rc(f"execute store result score #tcount sol.test if entity {sel}")
        return self.score("#tcount", "sol.test")

    def has(self, who, pred, slots="container.*"):
        return "passed" in self.rc(f"execute if items entity {who} {slots} {pred}")

    def all_score(self, obj, value, who=BOTS):
        return all(self.score(b, obj) == value for b in who)

    def tag(self, who, t):
        return "passed" in self.rc(f"execute if entity @a[name={who},tag={t}]")

    def gm(self, who, mode):
        return "passed" in self.rc(f"execute if entity @a[name={who},gamemode={mode}]")

    def adv(self, who, a):
        return "passed" in self.rc(f"execute if entity @a[name={who},advancements={{solstice:{a}=true}}]")

    # ------------------------------------------------------------ joueurs factices
    def join(self, who, at=(0.5, 101, 14.5)):
        """Connexion d’un joueur factice (asynchrone chez Carpet) : on attend qu’il soit réellement en ligne."""
        self.rc(f"player {who} spawn at {at[0]} {at[1]} {at[2]} facing 180 0 in minecraft:overworld")
        t0 = time.time()
        while time.time() - t0 < 20 and not self.online(who):
            time.sleep(0.25)
        self.wait(3)

    def leave(self, who):
        self.rc(f"player {who} kill")
        t0 = time.time()
        while time.time() - t0 < 10 and self.online(who):
            time.sleep(0.25)

    def online(self, who):
        return "passed" in self.rc(f"execute if entity @a[name={who}]")

    def tp(self, who, x, y, z):
        self.rc(f"tp {who} {x} {y} {z}")

    def look_use(self, who, stand, aim, attack=False):
        self.rc(f"tp {who} {stand[0]} {stand[1]} {stand[2]}")
        self.wait(2)
        self.rc(f"player {who} look at {aim[0]} {aim[1]} {aim[2]}")
        self.wait(2)
        self.rc(f"player {who} {'attack' if attack else 'use'} once")
        self.wait(3)

    def click_entity(self, who, tag, attack=False, dist=1.6):
        """Clic sur une entité interaction (par étiquette) : se place devant, la vise, clique."""
        p = self.entity_pos(f"@e[type=interaction,tag={tag},limit=1]")
        if p is None:
            return self.ok(f"entité {tag} trouvée pour le clic", False, "absente")
        x, y, z = p
        h = self.entity_h(tag)
        self.look_use(who, (x, y, z + dist), (x, y + h / 2, z), attack)
        return True

    def entity_pos(self, sel):
        r = self.rc(f"data get entity {sel} Pos")
        nums = re.findall(r"(-?\d+(?:\.\d+)?(?:E-?\d+)?)d", r)
        return tuple(float(n) for n in nums[:3]) if len(nums) >= 3 else None

    def entity_h(self, tag):
        r = self.rc(f"data get entity @e[type=interaction,tag={tag},limit=1] height")
        m = re.search(r"(-?\d+(?:\.\d+)?)f", r)
        return float(m.group(1)) if m else 1.0

    def kill_respawn(self, who, at=(0.5, 101, 14.5)):
        """Carpet déconnecte un factice mort : on simule la réapparition par une reconnexion."""
        self.rc(f"kill {who}")
        t0 = time.time()
        while time.time() - t0 < 10 and self.online(who):
            time.sleep(0.25)
        self.wait(4)
        self.join(who, at)
        self.wait(4)
        d = self.score(who, "sol.deaths")
        if not d and self.score(who, "sol.down") in (0, None):
            self.rc(f"scoreboard players set {who} sol.deaths 1")
        self.wait(6)

    def wait_until(self, fn, max_ticks=400, step=10):
        for _ in range(max_ticks // step):
            if fn():
                return True
            self.wait(step)
        return fn()

    def goto(self, n):
        self.rc(f"function solstice:debug/aller_salle_{n}")
        self.wait(10)


def run_server(name, scenarios, results_file):
    manifest = json.load(open(os.path.join(BUILD, "manifest.json")))
    wb = json.load(open(os.path.join(BUILD, "worldbuild.json")))
    if not wb.get("ok"):
        sys.exit("worldbuild en échec : tests annulés")
    sdir = os.path.join(BUILD, name)
    shutil.rmtree(sdir, ignore_errors=True)
    os.makedirs(sdir)
    shutil.copytree(os.path.join(BUILD, "world", "Solstice"), os.path.join(sdir, "Solstice"))
    srv = Server(sdir, world="Solstice", mods=mod_paths(["carpet"]))
    t = None
    from worldbuild import analyse_log
    t0 = time.time()
    try:
        srv.start()
        # les chunks forcés se chargent en arrière-plan : on attend qu’ils le soient tous
        from worldbuild import wait_loaded
        pts = {(cx * 16 + 8, 100, cz * 16 + 8) for (x1, z1, x2, z2) in manifest["meta"]["forceload"]
               for cx in range(x1 // 16, x2 // 16 + 1) for cz in range(z1 // 16, z2 // 16 + 1)}
        left = wait_loaded(srv, pts)
        t = Runner(srv, manifest)
        t.ok("serveur : toutes les zones de jeu chargées", not left, str(left[:3]))
        for sc in scenarios:
            t.secret = False
            try:
                sc(t)
            except Exception as e:  # un scénario qui plante = échec, on continue
                t.secret = False
                t.ok(f"scénario {sc.__name__} sans exception", False, repr(e)[:300])
        for b in BOTS:
            t.leave(b)
        t.wait(10)
    finally:
        srv.stop()
        srv.kill()
    bad = analyse_log(srv.console())
    res = t.results if t else []
    res.append(("serveur", "aucune erreur/avertissement lié au datapack dans les logs", not bad, "\n".join(bad[:20]), False))
    passed = sum(1 for r in res if r[2])
    print(f"\nRÉSULTAT {name} : {passed}/{len(res)} PASS ({time.time() - t0:.0f} s)")
    for r in res:
        if not r[2]:
            spoil_ok = os.environ.get("SOLSTICE_SPOILERS") and not r[4]
            print("  FAIL", f"{r[0]} · {r[1]} · {r[3][:400]}" if spoil_ok else f"[{'salle 5' if r[4] else r[0]}] (détail : design/SPOILERS_NE_PAS_LIRE/)")
    public = [r for r in res if not r[4]]
    secret = [r for r in res if r[4]]
    with open(os.path.join(BUILD, results_file), "w") as f:
        json.dump({"passed": passed, "total": len(res), "seconds": round(time.time() - t0),
                   "results": [r[:4] for r in public],
                   "secret5": {"passed": sum(1 for r in secret if r[2]), "total": len(secret)}},
                  f, ensure_ascii=False, indent=1)
    spoil = os.path.join(ROOT, "design", "SPOILERS_NE_PAS_LIRE", f"tests_{name}.json")
    with open(spoil, "w") as f:
        json.dump([r[:4] for r in secret], f, ensure_ascii=False, indent=1)
    with open(os.path.join(ROOT, "design", "SPOILERS_NE_PAS_LIRE", f"tests_{name}_complet.json"), "w") as f:
        json.dump([r[:4] for r in public], f, ensure_ascii=False, indent=1)
    return passed == len(res)
