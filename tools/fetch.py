#!/usr/bin/env python3
"""Téléchargements vérifiés depuis les sources officielles uniquement.

- Mojang  : piston-meta (manifest) -> piston-data (server.jar, sha1 vérifié)
- Fabric  : meta.fabricmc.net (server launcher)
- Modrinth: api.modrinth.com (versions, hashes) -> cdn.modrinth.com (jars, sha512 vérifié)

Écrit cache/mods.lock.json (versions figées). Relancer avec --update pour re-résoudre.
"""
import hashlib
import json
import os
import sys
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "cache")
MC = "1.21.1"
ALLOWED_HOSTS = {
    "piston-meta.mojang.com", "piston-data.mojang.com", "launchermeta.mojang.com",
    "meta.fabricmc.net", "api.modrinth.com", "cdn.modrinth.com",
}
# Mods livrés dans le modpack (+ dépendances requises résolues automatiquement)
PACK_MODS = ["fabric-api", "sodium", "lithium", "modmenu"]
# Mods du serveur de test uniquement (jamais livrés)
TEST_ONLY_MODS = ["carpet"]
SERVER_MODS = ["fabric-api", "lithium"]


def _check(url):
    host = urllib.parse.urlparse(url).hostname
    if host not in ALLOWED_HOSTS:
        raise SystemExit(f"Hôte non autorisé : {host} ({url})")


def get(url):
    _check(url)
    req = urllib.request.Request(url, headers={"User-Agent": "solstice-build/1.0 (local map build)"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def get_json(url):
    return json.loads(get(url))


def download(url, dest, algo=None, digest=None):
    if os.path.exists(dest) and algo and _hash(dest, algo) == digest:
        return dest
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    data = get(url)
    if algo:
        h = hashlib.new(algo, data).hexdigest()
        if h != digest:
            raise SystemExit(f"Hash invalide pour {url}: {h} != {digest}")
    with open(dest + ".part", "wb") as f:
        f.write(data)
    os.replace(dest + ".part", dest)
    if len(data) > 1_000_000:
        print(f"  téléchargé {os.path.basename(dest)} ({len(data)} o)")
    return dest


def _hash(path, algo):
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_mod(slug_or_id):
    q = urllib.parse.urlencode({"loaders": '["fabric"]', "game_versions": f'["{MC}"]'})
    versions = get_json(f"https://api.modrinth.com/v2/project/{slug_or_id}/version?{q}")
    rel = [v for v in versions if v["version_type"] == "release"] or versions
    if not rel:
        raise SystemExit(f"Aucune version {MC} Fabric pour {slug_or_id}")
    v = rel[0]
    files = [f for f in v["files"] if f["primary"]] or v["files"]
    f = files[0]
    proj = get_json(f"https://api.modrinth.com/v2/project/{v['project_id']}")
    return {
        "slug": proj["slug"], "title": proj["title"], "project_id": v["project_id"],
        "version_id": v["id"], "version_number": v["version_number"],
        "game_versions": v["game_versions"], "loaders": v["loaders"],
        "filename": f["filename"], "url": f["url"], "size": f["size"],
        "sha1": f["hashes"]["sha1"], "sha512": f["hashes"]["sha512"],
        "client_side": proj["client_side"], "server_side": proj["server_side"],
        "required_deps": [d["project_id"] for d in v["dependencies"]
                          if d["dependency_type"] == "required" and d.get("project_id")],
    }


def build_lock():
    print("Résolution des versions (Mojang / Fabric / Modrinth)…")
    manifest = get_json("https://piston-meta.mojang.com/mc/game/version_manifest_v2.json")
    ver = next(v for v in manifest["versions"] if v["id"] == MC)
    vjson = get_json(ver["url"])
    server = vjson["downloads"]["server"]
    loaders = get_json(f"https://meta.fabricmc.net/v2/versions/loader/{MC}")
    loader = next(l["loader"]["version"] for l in loaders if l["loader"]["stable"])
    installers = get_json("https://meta.fabricmc.net/v2/versions/installer")
    installer = next(i["version"] for i in installers if i["stable"])

    mods, seen, queue = {}, set(), [(m, "pack") for m in PACK_MODS] + [(m, "test") for m in TEST_ONLY_MODS]
    while queue:
        slug, role = queue.pop(0)
        info = resolve_mod(slug)
        key = info["project_id"]
        if key in seen:
            if role == "pack":
                mods[key]["role"] = "pack"
            continue
        seen.add(key)
        info["role"] = role
        mods[key] = info
        for dep in info["required_deps"]:
            queue.append((dep, role))
    for m in mods.values():
        if MC not in m["game_versions"] or "fabric" not in m["loaders"]:
            raise SystemExit(f"{m['slug']} n’est pas compatible {MC} fabric")
    lock = {
        "minecraft": MC, "java": vjson["javaVersion"]["majorVersion"],
        "server_jar": {"url": server["url"], "sha1": server["sha1"], "size": server["size"]},
        "client_jar": {k: vjson["downloads"]["client"][k] for k in ("url", "sha1", "size")},
        "fabric_loader": loader, "fabric_installer": installer,
        "mods": sorted(mods.values(), key=lambda m: m["slug"]),
    }
    with open(os.path.join(CACHE, "mods.lock.json"), "w") as f:
        json.dump(lock, f, indent=2)
    return lock


def add_missing(lock, lock_path):
    """Ajoute au verrou les mods de PACK_MODS absents (et leurs dépendances), sans toucher aux autres versions."""
    have = {m["slug"] for m in lock["mods"]} | {m["project_id"] for m in lock["mods"]}
    queue = [s for s in PACK_MODS if s not in have]
    if not queue:
        return
    while queue:
        slug = queue.pop(0)
        info = resolve_mod(slug)
        if info["project_id"] in have:
            continue
        if MC not in info["game_versions"] or "fabric" not in info["loaders"]:
            raise SystemExit(f"{info['slug']} n’est pas compatible {MC} fabric")
        info["role"] = "pack"
        lock["mods"].append(info)
        have |= {info["slug"], info["project_id"]}
        print(f"  ajouté au verrou : {info['slug']} {info['version_number']}")
        queue += [d for d in info["required_deps"] if d not in have]
    lock["mods"].sort(key=lambda m: m["slug"])
    with open(lock_path, "w") as f:
        json.dump(lock, f, indent=2)


JAVA_RUNTIMES = "https://piston-meta.mojang.com/v1/products/java-runtime/2ec0cc96c44e5a76b9c8b7c39df7210883d12871/all.json"


def java_bin():
    """Java 21 à utiliser : $JAVA_HOME, sinon runtime Mojang local dans cache/java."""
    jh = os.environ.get("JAVA_HOME")
    if jh and os.path.exists(os.path.join(jh, "bin", "java")):
        return os.path.join(jh, "bin", "java")
    return os.path.join(CACHE, "java", "jre.bundle", "Contents", "Home", "bin", "java")


def fetch_java():
    """Runtime Java 21 officiel de Mojang (java-runtime-delta), installé localement dans cache/java."""
    if os.path.exists(java_bin()):
        return java_bin()
    import platform
    plat = "mac-os-arm64" if platform.machine() == "arm64" else "mac-os"
    entry = get_json(JAVA_RUNTIMES)[plat]["java-runtime-delta"][0]
    man = get_json(entry["manifest"]["url"])
    base = os.path.join(CACHE, "java")
    print(f"Installation du runtime Java Mojang {entry['version']['name']} ({plat}) dans cache/java…")
    links = []
    for path, info in sorted(man["files"].items()):
        dest = os.path.join(base, path)
        if info["type"] == "directory":
            os.makedirs(dest, exist_ok=True)
        elif info["type"] == "file":
            raw = info["downloads"]["raw"]
            download(raw["url"], dest, "sha1", raw["sha1"])
            if info.get("executable"):
                os.chmod(dest, 0o755)
        elif info["type"] == "link":
            links.append((dest, info["target"]))
    for dest, target in links:
        if not os.path.lexists(dest):
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            os.symlink(target, dest)
    return java_bin()


def main():
    os.makedirs(CACHE, exist_ok=True)
    print("Java :", fetch_java())
    lock_path = os.path.join(CACHE, "mods.lock.json")
    if "--update" in sys.argv or not os.path.exists(lock_path):
        lock = build_lock()
    else:
        lock = json.load(open(lock_path))
        add_missing(lock, lock_path)
    print(f"MC {lock['minecraft']} · Fabric loader {lock['fabric_loader']} · installer {lock['fabric_installer']}")
    for m in lock["mods"]:
        print(f"  {m['role']:4} {m['slug']:16} {m['version_number']}")
    if "client_jar" not in lock:
        manifest = get_json("https://piston-meta.mojang.com/mc/game/version_manifest_v2.json")
        vjson = get_json(next(v for v in manifest["versions"] if v["id"] == MC)["url"])
        lock["client_jar"] = {k: vjson["downloads"]["client"][k] for k in ("url", "sha1", "size")}
        json.dump(lock, open(lock_path, "w"), indent=2)
    # client.jar : uniquement lu (modèles vanilla) par le lint, jamais lancé
    cj = lock["client_jar"]
    download(cj["url"], os.path.join(CACHE, "client", "client.jar"), "sha1", cj["sha1"])
    sj = lock["server_jar"]
    download(sj["url"], os.path.join(CACHE, "server", "server.jar"), "sha1", sj["sha1"])
    launcher = os.path.join(CACHE, "server", "fabric-server-launch.jar")
    if not os.path.exists(launcher):
        download(f"https://meta.fabricmc.net/v2/versions/loader/{MC}/{lock['fabric_loader']}/"
                 f"{lock['fabric_installer']}/server/jar", launcher)
    for m in lock["mods"]:
        if m["slug"] in SERVER_MODS or m["role"] == "test":
            download(m["url"], os.path.join(CACHE, "mods", m["filename"]), "sha512", m["sha512"])
    gen_reports()
    print("fetch OK")


def gen_reports():
    """Rapports officiels du jeu (blocs, états, registres), extraits du server.jar : utilisés par le lint."""
    out = os.path.join(CACHE, "reports")
    if os.path.exists(os.path.join(out, "reports", "blocks.json")):
        return
    import shutil
    import subprocess
    work = os.path.join(CACHE, "reports-gen")
    os.makedirs(work, exist_ok=True)
    shutil.copy(os.path.join(CACHE, "server", "server.jar"), os.path.join(work, "server.jar"))
    subprocess.run([java_bin(), "-DbundlerMainClass=net.minecraft.data.Main", "-jar", "server.jar", "--reports",
                    "--output", out], cwd=work, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("rapports du jeu générés :", out)


if __name__ == "__main__":
    main()
