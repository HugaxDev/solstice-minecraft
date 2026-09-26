#!/usr/bin/env python3
"""Construit le monde `Solstice` sur un serveur **vanilla** headless (aucune trace de mod) :
monde vide → datapack → forceload → fonctions de build (RCON) → test/all → post-traitement level.dat.
Sortie : build/world/Solstice (propre, sans joueur) + build/worldbuild.json (résultats)."""
import json
import os
import re
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from server import Server  # noqa: E402
import nbt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build")
SDIR = os.path.join(BUILD, "server-build")
WORLD = "Solstice"
VANILLA_ADV = 1399   # advancements vanilla 1.21.1 (mesuré sur un serveur vanilla vide)
SPAWN = (0, 101, 14)

LOG_BAD = re.compile(r"(solstice|Failed to load function|Couldn.t load|Unknown function|Couldn.t parse|"
                     r"Failed to parse|Invalid|Parsing error|Unknown or incomplete|Couldn.t find)", re.I)


def analyse_log(text):
    """Lignes WARN/ERROR liées au datapack."""
    bad = []
    for line in text.splitlines():
        if ("/WARN]" in line or "/ERROR]" in line) and LOG_BAD.search(line):
            bad.append(line.strip())
        elif "Exception" in line and "solstice" in line:
            bad.append(line.strip())
    return bad


def parse_tests(console, start_marker="TEST_BEGIN"):
    i = console.rfind(start_marker)
    seg = console[i:] if i >= 0 else ""
    return [(m.group(1), m.group(2).strip()) for m in re.finditer(r"\] (PASS|FAIL) (.+)$", seg, re.M)]


def wait_loaded(srv, points, timeout=300):
    t0 = time.time()
    pending = list(points)
    while pending and time.time() - t0 < timeout:
        pending = [p for p in pending if "passed" not in srv.rcon(f"execute if loaded {p[0]} {p[1]} {p[2]}")]
        if pending:
            time.sleep(0.5)
    return pending


def main():
    manifest = json.load(open(os.path.join(BUILD, "manifest.json")))
    shutil.rmtree(SDIR, ignore_errors=True)
    wdir = os.path.join(SDIR, WORLD)
    os.makedirs(os.path.join(wdir, "datapacks"))
    shutil.copytree(os.path.join(BUILD, "datapack", "solstice"), os.path.join(wdir, "datapacks", "solstice"))
    result = {"ok": False}
    srv = Server(SDIR, world=WORLD, vanilla=True)
    t_start = time.time()
    try:
        srv.start()
        out = {"datapack_list": srv.rcon("datapack list")}
        if "file/solstice" not in out["datapack_list"].split("available")[0]:
            raise RuntimeError("datapack solstice non activé : " + out["datapack_list"])
        srv.rcon("function solstice:build/forceload")
        pts = set()
        for (x1, z1, x2, z2) in manifest["meta"]["forceload"]:
            for cxk in range(x1 // 16, x2 // 16 + 1):
                for czk in range(z1 // 16, z2 // 16 + 1):
                    pts.add((cxk * 16 + 8, 100, czk * 16 + 8))
        pending = wait_loaded(srv, pts)
        if pending:
            raise RuntimeError(f"chunks non chargés après forceload : {pending[:5]}")
        srv.rcon(f"setworldspawn {SPAWN[0]} {SPAWN[1]} {SPAWN[2]} 180")
        builds = {}
        biome_err = []
        for cmd in manifest["meta"].get("biomes", []):
            for attempt in range(5):
                r = srv.rcon(cmd)
                if "biome" in r.lower() and "set" in r.lower():
                    break
                time.sleep(1)
            else:
                biome_err.append(f"{cmd} → {r}")
        builds["biomes"] = f"{len(manifest['meta'].get('biomes', []))} commandes, {len(biome_err)} échec(s)"
        if biome_err:
            print("  ÉCHEC fillbiome :", biome_err[:3])
        for f in manifest["builds"]:
            r = srv.rcon(f"function solstice:{f}")
            builds[f] = r
            print(f"  {f}: {r[:120]}")
        time.sleep(2)
        srv.rcon("kill @e[type=item]")
        srv.rcon("function solstice:test/all")
        time.sleep(1.5)
        tests = parse_tests(srv.console())
        fails = [n for s, n in tests if s == "FAIL"]
        srv.rcon("save-all flush")
        time.sleep(1)
        srv.stop()
        console = srv.console()
        adv = re.findall(r"Loaded (\d+) advancements", console)
        bad = analyse_log(console)
        bad_builds = {k: v for k, v in builds.items() if "Unknown" in v or "Incorrect" in v or "error" in v.lower()}
        if biome_err:
            bad_builds["biomes"] = biome_err[:5]
        _, lvl = nbt.load(os.path.join(wdir, "level.dat"))
        ld = lvl.value["Data"].value
        spawn = (ld["SpawnX"].value, ld["SpawnY"].value, ld["SpawnZ"].value)
        result = {
            "ok": bool(not fails and not bad and not bad_builds and len(tests) == manifest["tests"] and adv
                       and int(adv[-1]) == VANILLA_ADV + manifest["advancements"] and spawn == SPAWN),
            "spawn": spawn, "tests_pass": sum(1 for s, _ in tests if s == "PASS"), "tests_total": len(tests),
            "tests_expected": manifest["tests"], "fails": fails, "log_problems": bad, "bad_builds": bad_builds,
            "advancements_loaded": int(adv[-1]) if adv else None,
            "advancements_expected": VANILLA_ADV + manifest["advancements"],
            "functions_expected": manifest["functions"], "build_seconds": round(time.time() - t_start),
            "datapack_list": out["datapack_list"],
        }
    finally:
        srv.stop()
        srv.kill()
    print(json.dumps(result, ensure_ascii=False, indent=1))
    if result["ok"]:
        finalize(wdir)
    with open(os.path.join(BUILD, "worldbuild.json"), "w") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    if not result["ok"]:
        sys.exit(1)


def finalize(wdir):
    """Copie propre du monde : level.dat ajusté, sans joueurs ni verrou."""
    dst = os.path.join(BUILD, "world", WORLD)
    shutil.rmtree(dst, ignore_errors=True)
    shutil.copytree(wdir, dst)
    for sub in ("playerdata", "advancements", "stats"):
        shutil.rmtree(os.path.join(dst, sub), ignore_errors=True)
    for f in ("session.lock", "level.dat_old"):
        if os.path.exists(os.path.join(dst, f)):
            os.remove(os.path.join(dst, f))
    name, root = nbt.load(os.path.join(dst, "level.dat"))
    d = root.value["Data"].value
    d["allowCommands"] = nbt.Tag(nbt.BYTE, 1)
    d["LevelName"] = nbt.Tag(nbt.STRING, "Solstice")
    d["GameType"] = nbt.Tag(nbt.INT, 2)
    d["Difficulty"] = nbt.Tag(nbt.BYTE, 2)
    d["DifficultyLocked"] = nbt.Tag(nbt.BYTE, 0)
    d["hardcore"] = nbt.Tag(nbt.BYTE, 0)
    d.pop("Player", None)
    enabled = d["DataPacks"].value["Enabled"].value
    d["DataPacks"].value["Enabled"].value = [t for t in enabled if t.value in ("vanilla", "file/solstice")]
    nbt.save(os.path.join(dst, "level.dat"), name, root)
    shutil.copy(os.path.join(BUILD, "resourcepack", "world_icon.png"), os.path.join(dst, "icon.png"))
    print(f"  monde finalisé : {dst}")


if __name__ == "__main__":
    main()
