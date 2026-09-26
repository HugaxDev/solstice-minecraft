"""Noyau des générateurs : écriture du datapack, textes JSON, objets custom, utilitaires."""
import json
import os
import shutil

NS = "solstice"
DATA_FORMAT = 48      # vérifié dans version.json du server.jar 1.21.1 (et par le lint)
RESOURCE_FORMAT = 34
FILL_LIMIT = 32768
V = "sol.var"         # objectif des variables globales (#…)


def jdump(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def snbt_str(s):
    """Chaîne SNBT entre apostrophes (échappe \\ et ')."""
    return "'" + s.replace("\\", "\\\\").replace("'", "\\'") + "'"


# ---------------------------------------------------------------- textes
def T(text, color=None, **style):
    d = {"text": text}
    if color:
        d["color"] = color
    d.update(style)
    return d


def SC(holder, obj=V, color="white"):
    return {"score": {"name": holder, "objective": obj}, "color": color}


def SEL(sel, color="white"):
    return {"selector": sel, "color": color}


OREL = [T("Maître Orel", "gold", bold=True), T(" » ", "dark_gray")]
PLAYERS = "@a"


def tellraw(sel, *parts):
    return f"tellraw {sel} {jdump(['', *parts])}"


def orel(line, sel=PLAYERS, color="yellow"):
    """Réplique de Maître Orel (voix dans les tuyaux, humour)."""
    return tellraw(sel, *OREL, T(line, color))


def say(name, name_color, line, sel=PLAYERS, color="white"):
    return tellraw(sel, T(name, name_color, bold=True), T(" » ", "dark_gray"), T(line, color))


def narr(line, sel=PLAYERS, color="gray"):
    return tellraw(sel, T(line, color, italic=True))


def title(sel, main, sub=None, color="gold", subcolor="gray", times=(10, 60, 20)):
    out = [f"title {sel} times {times[0]} {times[1]} {times[2]}"]
    if sub is not None:
        out.append(f"title {sel} subtitle {jdump(T(sub, subcolor))}")
    out.append(f"title {sel} title {jdump(T(main, color, bold=True))}")
    return out


def actionbar(sel, text, color="gray"):
    if isinstance(text, (list, dict)):
        return f"title {sel} actionbar {jdump(text)}"
    return f"title {sel} actionbar {jdump(T(text, color))}"


def sound(snd, sel=PLAYERS, vol=1, pitch=1, src="master"):
    """Son joué à la position de chaque joueur visé."""
    return f"execute as {sel} at @s run playsound {snd} {src} @s ~ ~ ~ {vol} {pitch}"


# ---------------------------------------------------------------- objets
class Item:
    def __init__(self, iid, name=None, color="white", lore=(), cmd=None, data=None, glint=False,
                 extra=None, rarity=None, stack=None, italic=False, hide=False):
        self.id = iid if ":" in iid else "minecraft:" + iid
        self.comps = {}
        if name:
            self.comps["custom_name"] = snbt_str(jdump(T(name, color, italic=italic)))
        if lore:
            self.comps["lore"] = "[" + ",".join(snbt_str(jdump(T(l, "gray", italic=True))) for l in lore) + "]"
        if cmd is not None:
            self.comps["custom_model_data"] = str(cmd)
        if data:
            self.comps["custom_data"] = data
        if glint:
            self.comps["enchantment_glint_override"] = "true"
        if rarity:
            self.comps["rarity"] = f'"{rarity}"'
        if stack:
            self.comps["max_stack_size"] = str(stack)
        if hide:
            self.comps["hide_additional_tooltip"] = "{}"
        for k, v in (extra or {}).items():
            self.comps[k] = v

    def give(self):
        if not self.comps:
            return self.id
        return self.id + "[" + ",".join(f"{k}={v}" for k, v in self.comps.items()) + "]"

    def nbt(self, count=1, slot=None):
        parts = [f'id:"{self.id}"', f"count:{count}"]
        if slot is not None:
            parts.insert(0, f"Slot:{slot}b")
        if self.comps:
            parts.append("components:{" + ",".join(f'"minecraft:{k}":{v}' for k, v in self.comps.items()) + "}")
        return "{" + ",".join(parts) + "}"


def pred(tag, base="*"):
    """Prédicat d’objet sur custom_data {sol:{tag:1b}}."""
    return f"{base}[custom_data~{{sol:{{{tag}:1b}}}}]"


def equip(slot, item):
    """Équipe sans écraser : emplacement occupé → l’objet est donné."""
    return [f"execute if items entity @s {slot} * run give @s {item.give()}",
            f"execute unless items entity @s {slot} * run item replace entity @s {slot} with {item.give()}"]


# ---------------------------------------------------------------- construction
def fill(x1, y1, z1, x2, y2, z2, block, mode=""):
    """fill découpé automatiquement sous la limite de 32768 blocs."""
    x1, x2 = sorted((x1, x2))
    y1, y2 = sorted((y1, y2))
    z1, z2 = sorted((z1, z2))
    vol = (x2 - x1 + 1) * (y2 - y1 + 1) * (z2 - z1 + 1)
    if vol <= FILL_LIMIT:
        return [f"fill {x1} {y1} {z1} {x2} {y2} {z2} {block}{(' ' + mode) if mode else ''}"]
    dx, dy, dz = x2 - x1, y2 - y1, z2 - z1
    if dx >= dy and dx >= dz:
        m = (x1 + x2) // 2
        return fill(x1, y1, z1, m, y2, z2, block, mode) + fill(m + 1, y1, z1, x2, y2, z2, block, mode)
    if dy >= dz:
        m = (y1 + y2) // 2
        return fill(x1, y1, z1, x2, m, z2, block, mode) + fill(x1, m + 1, z1, x2, y2, z2, block, mode)
    m = (z1 + z2) // 2
    return fill(x1, y1, z1, x2, y2, m, block, mode) + fill(x1, y1, m + 1, x2, y2, z2, block, mode)


def fillbiome(x1, y1, z1, x2, y2, z2, biome):
    """fillbiome a la même limite de volume que fill : découpage sur l’axe le plus long."""
    out = []
    for f in fill(x1, y1, z1, x2, y2, z2, "@@"):
        out.append(f.replace("fill ", "fillbiome ", 1).replace(" @@", " " + biome))
    return out


def setblock(x, y, z, block, mode=""):
    return f"setblock {x} {y} {z} {block}{(' ' + mode) if mode else ''}"


def zone(x1, y1, z1, x2, y2, z2):
    """Sélecteur de volume (bornes incluses)."""
    x1, x2 = sorted((x1, x2))
    y1, y2 = sorted((y1, y2))
    z1, z2 = sorted((z1, z2))
    return f"x={x1},y={y1},z={z1},dx={x2 - x1},dy={y2 - y1},dz={z2 - z1}"


def tags(*t):
    return "[" + ",".join(f'"{x}"' for x in t) + "]"


def text_display(x, y, z, text_json, tag_list=(), scale=1.0, billboard="vertical", bg=0x40000000,
                 extra="", line_width=200, hidden=False, yaw=None):
    """summon text_display. hidden=True : échelle 0 (révélée plus tard, ex. par la Lanterne)."""
    bg_signed = bg - (1 << 32) if bg >= (1 << 31) else bg
    s = 0 if hidden else scale
    rot = f"Rotation:[{yaw}f,0f]," if yaw is not None else ""
    return (f"summon text_display {x} {y} {z} {{Tags:{tags('sol', *tag_list)},{rot}billboard:\"{billboard}\","
            f"text:{snbt_str(jdump(text_json))},background:{bg_signed},shadow:1b,line_width:{line_width},"
            f"transformation:{{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],translation:[0f,0f,0f],"
            f"scale:[{s}f,{s}f,{s}f]}}{extra}}}")


def interaction(x, y, z, tag_list, w=1.0, h=1.0, response=True):
    return (f"summon interaction {x} {y} {z} {{Tags:{tags('sol', *tag_list)},width:{w}f,height:{h}f,"
            f"response:{'1b' if response else '0b'}}}")


def block_display(x, y, z, block, tag_list=(), scale=(1, 1, 1), extra="", translation=(0, 0, 0)):
    sx, sy, sz = scale
    tx, ty, tz = translation
    return (f"summon block_display {x} {y} {z} {{Tags:{tags('sol', *tag_list)},block_state:{{Name:\"{block}\"}},"
            f"transformation:{{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],"
            f"translation:[{tx}f,{ty}f,{tz}f],scale:[{sx}f,{sy}f,{sz}f]}}{extra}}}")


def item_display(x, y, z, item, tag_list=(), scale=1.0, extra="", billboard="fixed"):
    return (f"summon item_display {x} {y} {z} {{Tags:{tags('sol', *tag_list)},item:{item.nbt() if isinstance(item, Item) else item},"
            f"billboard:\"{billboard}\",transformation:{{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],"
            f"translation:[0f,0f,0f],scale:[{scale}f,{scale}f,{scale}f]}}{extra}}}")


def villager(x, y, z, name, color, tag_list=(), profession="none", vtype="plains", yaw=0, extra=""):
    return (f"summon villager {x} {y} {z} {{Tags:{tags('sol', *tag_list)},NoAI:1b,Silent:1b,Invulnerable:1b,"
            f"PersistenceRequired:1b,Rotation:[{yaw}f,0f],CustomNameVisible:1b,"
            f"CustomName:{snbt_str(jdump(T(name, color, bold=True)))},"
            f"VillagerData:{{profession:\"minecraft:{profession}\",level:5,type:\"minecraft:{vtype}\"}},"
            f"Offers:{{Recipes:[]}}{extra}}}")


def skinned_npc(x, y, z, name, color, tag_list=(), yaw=0, extra=""):
    """PNJ à skin joueur : noyé (drowned) retexturé par le resource pack. Immobile, muet, invulnérable, sans
    équipement (tableaux vides : pas de trident tiré au hasard). Il brûle au soleil : le poser sous un bloc plein."""
    return (f"summon drowned {x} {y} {z} {{Tags:{tags('sol', *tag_list)},NoAI:1b,Silent:1b,Invulnerable:1b,"
            f"PersistenceRequired:1b,CanPickUpLoot:0b,IsBaby:0b,CanBreakDoors:0b,Rotation:[{yaw}f,0f],"
            f"HandItems:[{{}},{{}}],ArmorItems:[{{}},{{}},{{}},{{}}],CustomNameVisible:1b,"
            f"CustomName:{snbt_str(jdump(T(name, color, bold=True)))}{extra}}}")


# ---------------------------------------------------------------- datapack
class Datapack:
    def __init__(self):
        self.functions = {}
        self.files = {}
        self.tests = []       # (nom, condition execute) pour test/all
        self.meta = {}        # infos exposées aux tests
        self.puzzles = []     # registre d’énigmes (salle, id, type, description)

    def fn(self, name, lines):
        if name in self.functions:
            raise ValueError("fonction dupliquée : " + name)
        self.functions[name] = []
        self.add(name, lines)
        return f"{NS}:{name}"

    def add(self, name, lines):
        self.functions.setdefault(name, [])
        for l in lines:
            if isinstance(l, (list, tuple)):
                self.add(name, l)
            elif l is not None:
                self.functions[name].append(l)

    def json(self, rel, obj):
        self.files[rel] = obj

    def adv(self, name, obj):
        self.json(f"data/{NS}/advancement/{name}.json", obj)

    def pred(self, name, obj):
        self.json(f"data/{NS}/predicate/{name}.json", obj)

    def loot(self, name, obj):
        self.json(f"data/{NS}/loot_table/{name}.json", obj)

    def test(self, name, cond):
        self.tests.append((name, cond))

    def puzzle(self, room, pid, ptype, desc):
        self.puzzles.append({"room": room, "id": pid, "type": ptype, "desc": desc})

    def write(self, root):
        base = os.path.join(root, NS)
        if os.path.exists(base):
            shutil.rmtree(base)
        os.makedirs(base)
        with open(os.path.join(base, "pack.mcmeta"), "w", encoding="utf-8") as f:
            f.write(json.dumps({"pack": {"pack_format": DATA_FORMAT,
                                         "description": "SOLSTICE — une aventure à trois"}},
                               ensure_ascii=False, indent=2))
        for name, lines in self.functions.items():
            p = os.path.join(base, "data", NS, "function", name + ".mcfunction")
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
        for rel, obj in self.files.items():
            p = os.path.join(base, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                json.dump(obj, f, ensure_ascii=False, indent=2)
        return base
