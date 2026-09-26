#!/usr/bin/env python3
"""Lint statique : py_compile, JSON, références de fonctions/advancements/tags, resource pack."""
import glob
import json
import os
import py_compile
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from gen.png import read_png_size  # noqa: E402

DP = os.path.join(ROOT, "build", "datapack", "solstice")
RP = os.path.join(ROOT, "build", "resourcepack", "solstice_rp")
errors = []


def err(msg):
    errors.append(msg)


SEL_AS = re.compile(r"(?:^|\s)(as|on)\s+(\S+)")


def _kind(sel):
    """Type d’exécutant produit par « as <sel> » / « on <relation> »."""
    if sel in ("target", "attacker", "controller", "leasher", "owner", "origin"):
        return "P"   # nos interactions : la cible/l’attaquant est un joueur
    if sel.startswith("@s"):
        return None  # inchangé
    if sel.startswith("@a") or sel.startswith("@p") or sel.startswith("@r") or "type=player" in sel:
        return "P"
    if sel.startswith("@e"):
        return "E"
    return "P"       # nom de joueur explicite


def selector_audit(fdir, funcs):
    """Propage le contexte d’exécution dans le graphe d’appels et vérifie chaque sélecteur.

    G = aucun exécutant (tick, load, build, test, schedule) · P = joueur · E = autre entité.
    Règles : pas de @p ni de @r ; pas de @a[…limit=1] ; tout @s doit être atteint avec un exécutant."""
    code = {}
    for f in funcs:
        with open(os.path.join(fdir, f + ".mcfunction"), encoding="utf-8") as fh:
            code[f] = [l for l in fh.read().split("\n") if l.strip() and not l.startswith("#")]
    ctx = {f: set() for f in funcs}
    work = []

    def push(f, c):
        if f in ctx and c not in ctx[f]:
            ctx[f].add(c)
            work.append((f, c))

    for f in funcs:
        if f in ("tick", "load", "test/all") or f.startswith("build/"):
            push(f, "G")
        if f.startswith("debug/"):
            push(f, "P")
        if f.startswith("test/"):
            push(f, "G")
    at_s = 0
    problems = set()
    while work:
        f, c0 = work.pop()
        for i, line in enumerate(code[f], 1):
            where = f"solstice:{f}:{i}"
            for bad in ("@p", "@r"):
                if re.search(bad + r"(?![a-z])", line):
                    problems.add(f"{where} utilise {bad} (logique mono-joueur interdite)")
            for m in re.finditer(r"@[ae]\[([^\]]*)\]", line):
                inner = m.group(1)
                if "limit=1" in inner and (m.group(0).startswith("@a") or "type=player" in inner):
                    if "tag=sol.me" in inner:     # l’exécutant, étiqueté juste avant : un seul joueur par construction
                        continue
                    if "sort=nearest" in inner and "facing entity" in line:   # orientation d’une entité vers le joueur le plus proche
                        continue
                    if not (line.startswith("spectate ") or " run spectate " in line) or "sort=nearest" not in inner:
                        problems.add(f"{where} sélection d’un seul joueur ({m.group(0)}) : logique mono-joueur interdite")
            # contexte au fil de la ligne
            events = [(m.start(), "as", m.group(2)) for m in SEL_AS.finditer(line)]
            events += [(m.start(), "s", None) for m in re.finditer(r"@s(?![a-z])", line)]
            events += [(m.start(), "fn", m.group(1)) for m in re.finditer(r"(?<!schedule )function solstice:([a-z0-9_/.\-]+)", line)]
            events += [(m.start(), "sched", m.group(1)) for m in re.finditer(r"schedule function solstice:([a-z0-9_/.\-]+)", line)]
            c = c0
            for _, kind, arg in sorted(events):
                if kind == "as":
                    k = _kind(arg)
                    if k:
                        c = k
                elif kind == "s":
                    at_s += 1
                    if c == "G":
                        problems.add(f"{where} @s sans exécutant (appelée en contexte global)")
                elif kind == "fn":
                    push(arg, c)
                elif kind == "sched":
                    push(arg, "G")
    for p in sorted(problems):
        err("audit " + p)
    return {"functions": len(funcs), "global": sum(1 for v in ctx.values() if "G" in v),
            "player": sum(1 for v in ctx.values() if "P" in v), "entity": sum(1 for v in ctx.values() if "E" in v),
            "at_s": at_s, "unreached": sorted(f for f, v in ctx.items() if not v)}


REPORTS = os.path.join(ROOT, "cache", "reports", "reports")
_BLOCKS = None
_ITEMS = None


def blocks_db():
    global _BLOCKS, _ITEMS
    if _BLOCKS is None:
        raw = json.load(open(os.path.join(REPORTS, "blocks.json")))
        _BLOCKS = {k: v.get("properties", {}) for k, v in raw.items()}
        reg = json.load(open(os.path.join(REPORTS, "registries.json")))
        _ITEMS = set(reg["minecraft:item"]["entries"])
    return _BLOCKS, _ITEMS


def check_block(tok, where):
    """tok : minecraft:x[a=b,…]{…} ou x[…]. Vérifie nom et propriétés contre blocks.json."""
    blocks, _ = blocks_db()
    if tok.startswith("#"):
        return
    m = re.match(r"([a-z0-9_:]+)(\[[^\]]*\])?", tok)
    if not m:
        err(f"{where} bloc illisible : {tok}")
        return
    name = m.group(1) if ":" in m.group(1) else "minecraft:" + m.group(1)
    if name not in blocks:
        err(f"{where} bloc inconnu : {name}")
        return
    if m.group(2):
        props = blocks[name]
        for kv in m.group(2)[1:-1].split(","):
            if not kv.strip():
                continue
            k, _, v = kv.partition("=")
            if k not in props:
                err(f"{where} propriété inconnue {k} pour {name}")
            elif v not in props[k]:
                err(f"{where} valeur {k}={v} invalide pour {name} ({props[k]})")


BLOCK_RES = [re.compile(r"(?:^|\s)fill (?:\S+ ){6}(\S+)"), re.compile(r"(?:^|\s)setblock (?:\S+ ){3}(\S+)"),
             re.compile(r"(?:if|unless) block (?:\S+ ){3}(\S+)")]
ITEM_RES = [re.compile(r"(?:^|(?<=\s))(?<!effect )(?<!loot )give \S+ ([a-z0-9_:]+)"), re.compile(r"replace (?:entity|block) .* with ([a-z0-9_:]+)"),
            re.compile(r'id:\\?"(minecraft:[a-z0-9_]+)\\?"'), re.compile(r"(?:^|\s)clear \S+ ([a-z0-9_:]+)\["),
            re.compile(r"items entity \S+ \S+ ([a-z0-9_:]+)\[")]


def check_ids(line, where):
    _, items = blocks_db()
    for rx in BLOCK_RES:
        for m in rx.finditer(line):
            tok = m.group(1)
            # retire le NBT éventuel
            check_block(tok.split("{")[0] if "{" in tok and "[" not in tok.split("{")[0][-1:] else tok.split("{")[0], where)
    for m in re.finditer(r'block_state:\{Name:\\?"([a-z0-9_:]+)\\?"', line):
        check_block(m.group(1), where)
    for rx in ITEM_RES:
        for m in rx.finditer(line):
            iid = m.group(1) if ":" in m.group(1) else "minecraft:" + m.group(1)
            if iid not in items:
                err(f"{where} objet inconnu : {iid}")


def main():
    # 1. py_compile
    pys = glob.glob(os.path.join(ROOT, "src", "**", "*.py"), recursive=True) + glob.glob(os.path.join(ROOT, "tools", "*.py"))
    import tempfile
    tmpc = os.path.join(tempfile.mkdtemp(), "x.pyc")
    for p in pys:
        try:
            py_compile.compile(p, doraise=True, cfile=tmpc)
        except py_compile.PyCompileError as e:
            err(f"py_compile : {e}")
    # 2. JSON
    jsons = [p for base in (DP, RP) for p in glob.glob(os.path.join(base, "**", "*"), recursive=True)
             if p.endswith((".json", ".mcmeta"))]
    parsed = {}
    for p in jsons:
        try:
            with open(p, encoding="utf-8") as f:
                parsed[p] = json.load(f)
        except (ValueError, UnicodeDecodeError) as e:
            err(f"JSON invalide {os.path.relpath(p, ROOT)} : {e}")
    # 3. pack_format vérifié contre le jar serveur
    with zipfile.ZipFile(os.path.join(ROOT, "cache", "server", "server.jar")) as z:
        pv = json.loads(z.read("version.json"))["pack_version"]
    if parsed.get(os.path.join(DP, "pack.mcmeta"), {}).get("pack", {}).get("pack_format") != pv["data"]:
        err(f"pack_format datapack != {pv['data']}")
    if parsed.get(os.path.join(RP, "pack.mcmeta"), {}).get("pack", {}).get("pack_format") != pv["resource"]:
        err(f"pack_format resource pack != {pv['resource']}")
    # 4. fonctions et références
    fdir = os.path.join(DP, "data", "solstice", "function")
    funcs = {os.path.relpath(p, fdir)[:-len(".mcfunction")] for p in
             glob.glob(os.path.join(fdir, "**", "*.mcfunction"), recursive=True)}
    advdir = os.path.join(DP, "data", "solstice", "advancement")
    advs = {os.path.relpath(p, advdir)[:-5] for p in glob.glob(os.path.join(advdir, "**", "*.json"), recursive=True)}
    btags = {os.path.relpath(p, os.path.join(DP, "data", "solstice", "tags", "block"))[:-5]
             for p in glob.glob(os.path.join(DP, "data", "solstice", "tags", "block", "*.json"))}
    n_lines = 0
    for f in funcs:
        path = os.path.join(fdir, f + ".mcfunction")
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().split("\n")
        for i, line in enumerate(lines, 1):
            if not line.strip() or line.startswith("#"):
                continue
            n_lines += 1
            where = f"solstice:{f}:{i}"
            if line.startswith("/"):
                err(f"{where} commence par /")
            check_ids(line, where)
            if re.search(r"scoreboard players (add|remove) \S+ \S+ -\d", line):
                err(f"{where} add/remove avec un nombre négatif (refusé par le jeu)")
            if re.search(r"kill @e\[(?![^\]]*type=)", line):
                err(f"{where} kill @e sans type= (risque de tuer un joueur)")
            for ref in re.findall(r"function solstice:([a-z0-9_/.\-]+)", line):
                if ref not in funcs:
                    err(f"{where} fonction inconnue solstice:{ref}")
            for ref in re.findall(r"advancement (?:grant|revoke) @\S+ (?:only|from|until|through) solstice:([a-z0-9_/]+)", line):
                if ref not in advs:
                    err(f"{where} advancement inconnu solstice:{ref}")
            for ref in re.findall(r"solstice:([a-z0-9_/]+)=(?:true|false)", line):
                if ref not in advs:
                    err(f"{where} advancement inconnu (sélecteur) solstice:{ref}")
            for ref in re.findall(r"#solstice:([a-z0-9_/]+)", line):
                if ref not in btags:
                    err(f"{where} tag inconnu #solstice:{ref}")
            for a, b in (("{", "}"), ("[", "]")):
                if line.count(a) != line.count(b):
                    err(f"{where} {a}{b} déséquilibrés")
            for m in re.finditer(r"score (\S+) (\S+) (=|<|<=|>|>=) (\S+) (\S+)", line):
                if m.group(5) in ("run", "if", "unless", "as", "at", "store"):
                    err(f"{where} comparaison de score sans objectif : {m.group(0)}")
            for ref in re.findall(r"loot (?:give|replace|spawn|insert) .* loot solstice:([a-z0-9_/]+)", line):
                if not os.path.exists(os.path.join(DP, "data", "solstice", "loot_table", ref + ".json")):
                    err(f"{where} table de loot inconnue solstice:{ref}")
            for ref in re.findall(r"predicate solstice:([a-z0-9_/]+)", line):
                if not os.path.exists(os.path.join(DP, "data", "solstice", "predicate", ref + ".json")):
                    err(f"{where} prédicat inconnu solstice:{ref}")
            mj = re.search(r"(?:^|run )(tellraw \S+ |title \S+ (?:title|subtitle|actionbar) |bossbar set \S+ name )(.*)$", line)
            if mj:
                try:
                    json.loads(mj.group(2))
                except ValueError as e:
                    err(f"{where} texte JSON invalide : {e}")
            if line.count('"') % 2:
                err(f"{where} guillemets impairs")
            if "'" in line and "’" not in line and "\\'" not in line:
                # apostrophes droites autorisées uniquement comme délimiteurs SNBT (par paires)
                if line.count("'") % 2:
                    err(f"{where} apostrophes droites impaires")
    audit = selector_audit(fdir, funcs)
    # chaque zone construite (forceload) doit être couverte par la boîte de sécurité d’une salle
    sys.path.insert(0, os.path.join(ROOT, "src"))
    from gen.layout import ROOMS
    man0 = json.load(open(os.path.join(ROOT, "build", "manifest.json")))
    for (fx1, fz1, fx2, fz2) in man0["meta"]["forceload"]:
        ok = any(bx1 <= fx1 and fx2 <= bx2 and bz1 <= fz1 and fz2 <= bz2
                 for r in ROOMS.values() for (bx1, _, bz1, bx2, _, bz2) in r["boxes"])
        if not ok:
            err(f"zone construite {(fx1, fz1, fx2, fz2)} hors de toute boîte de sécurité (joueurs renvoyés au checkpoint)")
    # registre d’énigmes : aucun type ne se répète sur toute la carte
    man = json.load(open(os.path.join(ROOT, "build", "manifest.json")))
    seen = {}
    for pz in man.get("puzzles", []):
        if pz["type"] in seen:
            err(f"registre : énigme {pz['id']} (salle {pz['room']}) du même type « {pz['type']} » que {seen[pz['type']]}")
        seen[pz["type"]] = f"{pz['id']} (salle {pz['room']})"
    for name, obj in parsed.items():
        if "/advancement/" in name:
            par = obj.get("parent")
            if par and par.split(":", 1)[1] not in advs:
                err(f"parent inconnu {par} dans {os.path.relpath(name, ROOT)}")
    # tags de fonctions minecraft:load / tick
    for t in ("load", "tick"):
        tp = os.path.join(DP, "data", "minecraft", "tags", "function", t + ".json")
        vals = parsed.get(tp, {}).get("values", [])
        if not vals or any(v.split(":", 1)[1] not in funcs for v in vals):
            err(f"tag minecraft:{t} invalide")
    # 5. resource pack
    with zipfile.ZipFile(os.path.join(ROOT, "cache", "client", "client.jar")) as z:
        for p in glob.glob(os.path.join(RP, "assets", "minecraft", "models", "item", "*.json")):
            item = os.path.basename(p)
            vanilla = json.loads(z.read(f"assets/minecraft/models/item/{item}"))
            ours = dict(parsed[p])
            ours.pop("overrides", None)
            if ours != vanilla:
                err(f"modèle {item} diverge du vanilla : {ours} != {vanilla}")
            for ov in parsed[p].get("overrides", []):
                ns, path = ov["model"].split(":")
                mp = os.path.join(RP, "assets", ns, "models", path + ".json")
                if not os.path.exists(mp):
                    err(f"modèle manquant {ov['model']}")
                    continue
                with open(mp) as fh:
                    m = json.load(fh)
                for tex in m.get("textures", {}).values():
                    tns, tpath = tex.split(":")
                    tp = os.path.join(RP, "assets", tns, "textures", tpath + ".png")
                    if tns != "minecraft":
                        if not os.path.exists(tp):
                            err(f"texture manquante {tex}")
                        elif read_png_size(tp) != (16, 16):
                            err(f"texture {tex} n’est pas 16x16")
    print(f"audit sélecteurs : {audit['functions']} fonctions analysées — {audit['global']} en contexte global, "
          f"{audit['player']} en contexte joueur, {audit['entity']} en contexte entité ; "
          f"{audit['at_s']} usages de @s vérifiés, 0 @p/@r autorisé")
    print(f"registre d’énigmes : {len(seen)} énigmes, {len(seen)} types distincts")
    print(f"lint : {len(pys)} fichiers Python, {len(jsons)} JSON, {len(funcs)} fonctions ({n_lines} commandes), "
          f"{len(advs)} advancements")
    with open(os.path.join(ROOT, "build", "lint.json"), "w") as fh:
        json.dump({"python": len(pys), "json": len(jsons), "functions": len(funcs), "commands": n_lines, "advancements": len(advs),
                   "audit": {k: v for k, v in audit.items() if k != "unreached"}, "puzzles": len(seen), "errors": len(errors)}, fh)
    if errors:
        for e in errors[:80]:
            print("  ERREUR", e)
        print(f"lint : {len(errors)} erreur(s)")
        sys.exit(1)
    print("lint OK")


if __name__ == "__main__":
    main()
