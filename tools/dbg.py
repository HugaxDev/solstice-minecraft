#!/usr/bin/env python3
"""Débogage : démarre le serveur de test (copie du monde) et exécute une liste de commandes RCON.
Usage : python3 tools/dbg.py "cmd1" "cmd2" ... (« wait:N » attend N ticks, « sprint:N »)."""
import os, sys, shutil, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from server import Server, mod_paths
from testlib import Runner, BUILD
sdir = os.path.join(BUILD, "server-dbg")
shutil.rmtree(sdir, ignore_errors=True); os.makedirs(sdir)
shutil.copytree(os.path.join(BUILD, "world", "Solstice"), os.path.join(sdir, "Solstice"))
srv = Server(sdir, world="Solstice", mods=mod_paths(["carpet"]))
try:
    srv.start()
    man = json.load(open(os.path.join(BUILD, "manifest.json")))
    from worldbuild import wait_loaded
    left = wait_loaded(srv, {(cx * 16 + 8, 100, cz * 16 + 8) for (x1, z1, x2, z2) in man["meta"]["forceload"]
                             for cx in range(x1 // 16, x2 // 16 + 1) for cz in range(z1 // 16, z2 // 16 + 1)})
    print("chunks non chargés :", left[:3])
    t = Runner(srv, man)
    for c in sys.argv[1:]:
        if c.startswith("wait:"):
            t.wait(int(c[5:])); continue
        if c.startswith("sprint:"):
            t.sprint(int(c[7:])); continue
        print(">", c, "\n ", t.rc(c)[:1500])
finally:
    srv.stop(); srv.kill()
print("---- console (solstice/erreurs) ----")
for l in srv.console().splitlines():
    if "ERROR" in l or "WARN" in l and "solstice" in l.lower():
        print(l[:300])
