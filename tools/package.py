#!/usr/bin/env python3
"""Packaging des livrables dans dist/ :
- Solstice-world.zip          : le monde vanilla 1.21.1 (dossier « Solstice » contenant directement level.dat)
- Solstice-resourcepack.zip   : le resource pack seul (pack.mcmeta à la racine), à installer par chaque joueur
- Solstice-1.0.mrpack         : optionnel (Prism) — mods de confort, hashes Modrinth re-vérifiés
Aucune trace de Fabric ni de Carpet dans le monde : vérifié ici (level.dat, fichiers du monde)."""
import hashlib
import io
import json
import os
import shutil
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch import CACHE, download  # noqa: E402
import nbt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build")
DIST = os.path.join(ROOT, "dist")
VERSION = "1.0"
FIXED_TIME = (2026, 9, 26, 12, 0, 0)
MRPACK_MODS = ["fabric-api", "sodium", "lithium", "modmenu", "placeholder-api"]
OPTIONS = """version:3955
lang:fr_fr
resourcePacks:["vanilla","fabric","file/Solstice-resourcepack.zip"]
incompatibleResourcePacks:[]
onboardAccessibility:false
tutorialStep:none
skipMultiplayerWarning:true
joinedFirstServer:true
"""


def zinfo(arc):
    zi = zipfile.ZipInfo(arc, FIXED_TIME)
    zi.compress_type = zipfile.ZIP_DEFLATED
    return zi


def zip_dir(zf, src, prefix, skip=()):
    for base, dirs, files in os.walk(src):
        dirs.sort()
        for f in sorted(files):
            if f in skip:
                continue
            p = os.path.join(base, f)
            arc = os.path.join(prefix, os.path.relpath(p, src)).replace(os.sep, "/").lstrip("/")
            with open(p, "rb") as fh:
                zf.writestr(zinfo(arc), fh.read())


def rp_bytes():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zip_dir(zf, os.path.join(BUILD, "resourcepack", "solstice_rp"), "")
    return buf.getvalue()


def main():
    wb = json.load(open(os.path.join(BUILD, "worldbuild.json")))
    if not wb.get("ok"):
        sys.exit("worldbuild en échec : packaging refusé")
    for name in ("test_results.json", "journey_results.json"):
        p = os.path.join(BUILD, name)
        if not os.path.exists(p):
            sys.exit(f"{name} absent : packaging refusé")
        r = json.load(open(p))
        if r["passed"] != r["total"]:
            sys.exit(f"{name} : {r['passed']}/{r['total']} — packaging refusé (100 % exigé)")
    os.makedirs(DIST, exist_ok=True)
    world = os.path.join(BUILD, "world", "Solstice")
    # --- monde vanilla : contrôle d’absence de toute trace de mod
    name, root = nbt.load(os.path.join(world, "level.dat"))
    d = root.value["Data"].value
    enabled = [t.value for t in d["DataPacks"].value["Enabled"].value]
    assert enabled == ["vanilla", "file/solstice"] or sorted(enabled) == ["file/solstice", "vanilla"], enabled
    blob = json.dumps(str(root.value)).lower()
    for bad in ("fabric", "carpet"):
        assert bad not in blob, f"trace « {bad} » dans level.dat"
    for base, dirs, files in os.walk(world):
        for f in files + dirs:
            assert "fabric" not in f.lower() and "carpet" not in f.lower(), f"fichier suspect {f}"
    wzip = os.path.join(DIST, "Solstice-world.zip")
    with zipfile.ZipFile(wzip, "w") as zf:
        zip_dir(zf, world, "Solstice", skip=("session.lock",))
    rzip = os.path.join(DIST, "Solstice-resourcepack.zip")
    with open(rzip, "wb") as f:
        f.write(rp_bytes())
    # --- .mrpack (optionnel, Prism) : mods de confort, hashes re-vérifiés
    lock = json.load(open(os.path.join(CACHE, "mods.lock.json")))
    files = []
    for m in lock["mods"]:
        if m["slug"] not in MRPACK_MODS:
            continue
        dest = os.path.join(CACHE, "mods", m["filename"])
        download(m["url"], dest, "sha512", m["sha512"])
        data = open(dest, "rb").read()
        assert hashlib.sha1(data).hexdigest() == m["sha1"] and hashlib.sha512(data).hexdigest() == m["sha512"]
        files.append({"path": f"mods/{m['filename']}", "hashes": {"sha1": m["sha1"], "sha512": m["sha512"]},
                      "env": {"client": "required", "server": "optional"}, "downloads": [m["url"]], "fileSize": m["size"]})
    index = {"formatVersion": 1, "game": "minecraft", "versionId": VERSION, "name": "SOLSTICE",
             "summary": "Aventure coop à trois (Minecraft 1.21.1). Le monde fonctionne aussi en vanilla pur.",
             "files": files, "dependencies": {"minecraft": lock["minecraft"], "fabric-loader": lock["fabric_loader"]}}
    mrpack = os.path.join(DIST, f"Solstice-{VERSION}.mrpack")
    with zipfile.ZipFile(mrpack, "w") as zf:
        zf.writestr(zinfo("modrinth.index.json"), json.dumps(index, ensure_ascii=False, indent=2).encode())
        zip_dir(zf, world, "overrides/saves/Solstice", skip=("session.lock",))
        zf.writestr(zinfo("overrides/resourcepacks/Solstice-resourcepack.zip"), rp_bytes())
        zf.writestr(zinfo("overrides/options.txt"), OPTIONS.encode())
    # --- contrôles des archives
    with zipfile.ZipFile(wzip) as z:
        names = z.namelist()
        assert "Solstice/level.dat" in names, "level.dat doit être au premier niveau du dossier Solstice/"
        assert "Solstice/datapacks/solstice/pack.mcmeta" in names
        assert all(n.startswith("Solstice/") for n in names)
        assert not any("session.lock" in n for n in names)
        assert z.testzip() is None
    with zipfile.ZipFile(rzip) as z:
        assert "pack.mcmeta" in z.namelist() and "pack.png" in z.namelist()
        assert json.loads(z.read("pack.mcmeta"))["pack"]["pack_format"] == 34
        assert z.testzip() is None
    with zipfile.ZipFile(mrpack) as z:
        assert "modrinth.index.json" in z.namelist() and "overrides/saves/Solstice/level.dat" in z.namelist()
        assert z.testzip() is None
    # dézippage réel : le dossier obtenu contient directement level.dat
    tmp = os.path.join(BUILD, "unzip-check")
    shutil.rmtree(tmp, ignore_errors=True)
    with zipfile.ZipFile(wzip) as z:
        z.extractall(tmp)
    assert os.listdir(tmp) == ["Solstice"] and os.path.isfile(os.path.join(tmp, "Solstice", "level.dat"))
    shutil.rmtree(tmp)
    info = {"world_zip": wzip, "world_zip_size": os.path.getsize(wzip), "rp_zip": rzip, "rp_zip_size": os.path.getsize(rzip),
            "mrpack": mrpack, "mrpack_size": os.path.getsize(mrpack), "mrpack_mods": [f["path"] for f in files],
            "level_dat_first_level": True}
    with open(os.path.join(BUILD, "package.json"), "w") as f:
        json.dump(info, f, ensure_ascii=False, indent=1)
    for k in ("world_zip", "rp_zip", "mrpack"):
        print(f"  {info[k]} ({info[k + '_size'] // 1024} Kio)")


if __name__ == "__main__":
    main()
