#!/usr/bin/env python3
"""Vérifie qu’aucun serveur de test ne tourne encore et qu’aucun port de test n’est ouvert.
Ne regarde QUE les serveurs headless du projet (jamais le client du joueur)."""
import subprocess
import sys

import time

for _ in range(15):   # un JVM qui s’arrête peut mettre quelques secondes à disparaître
    out = subprocess.run(["ps", "-axo", "pid=,command="], capture_output=True, text=True).stdout
    mine = [l.split()[0] for l in out.splitlines() if "--nogui" in l and ("server.jar" in l or "fabric-server-launch.jar" in l)]
    ports = subprocess.run(["lsof", "-nP", "-iTCP:25575", "-iTCP:25585", "-sTCP:LISTEN"], capture_output=True, text=True).stdout.strip()
    if not mine and not ports:
        break
    time.sleep(1)
print(f"serveurs de test encore actifs : {len(mine)} · ports de test ouverts : {'oui' if ports else 'aucun'}")
import json
import os
with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "build", "orphans.json"), "w") as f:
    json.dump({"servers": len(mine), "ports": "oui" if ports else "aucun"}, f)
sys.exit(1 if mine or ports else 0)
