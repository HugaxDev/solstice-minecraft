"""Resource pack `solstice_rp` (optionnel) : textures 16x16 des objets clés via custom_model_data, et apparence de
Maître Orel (skin joueur porté par un noyé, voir skin.py).
Le jeu reste lisible sans lui (objets vanilla nommés). Modèles de base = copies exactes du vanilla (vérifié par le lint)."""
import json
import math
import os
import shutil

from .core import RESOURCE_FORMAT
from .png import Canvas, shade
from . import skin

GOLD = (230, 180, 60, 255)
DARK = (70, 45, 20, 255)


def tex_lantern():
    c = Canvas(16, 16)
    for x in range(5, 11):
        c.set(x, 2, DARK)
    c.set(7, 1, DARK); c.set(8, 1, DARK); c.set(7, 0, GOLD); c.set(8, 0, GOLD)
    for y in range(3, 14):
        for x in range(4, 12):
            edge = x in (4, 11) or y in (3, 13)
            c.set(x, y, GOLD if edge else (255, 230, 150, 200))
    seasons = [(255, 170, 200, 255), (255, 220, 70, 255), (230, 110, 40, 255), (170, 220, 255, 255)]
    for i, col in enumerate(seasons):
        x0, y0 = 5 + (i % 2) * 3, 5 + (i // 2) * 4
        for dx in range(2):
            for dy in range(3):
                c.set(x0 + dx, y0 + dy, col)
    for x in range(4, 12):
        c.set(x, 14, DARK)
    return c


def tex_dial():
    c = Canvas(16, 16)
    cols = [(255, 170, 200, 255), (255, 220, 70, 255), (230, 110, 40, 255), (170, 220, 255, 255)]
    for y in range(16):
        for x in range(16):
            dx, dy = x - 7.5, y - 7.5
            d = math.hypot(dx, dy)
            if d <= 7.2:
                a = (math.degrees(math.atan2(dy, dx)) + 360 + 45) % 360
                c.set(x, y, shade(cols[int(a // 90)], 1.0 if d < 6.2 else 0.6))
    for k in range(0, 5):
        c.set(8, 8 - k, (40, 30, 20, 255))
    c.set(8, 8, (255, 255, 255, 255))
    return c


# item vanilla -> modèle vanilla d’origine, et nos surcharges (custom_model_data, nom, parent, peintre)
VANILLA = {
    "lantern": {"parent": "minecraft:item/generated", "textures": {"layer0": "minecraft:item/lantern"}},
    "clock": None,   # le modèle vanilla de l’horloge est animé (overrides "time") : pas de surcharge
}
OVERRIDES = {
    "lantern": [(3001, "lanterne_des_saisons", "minecraft:item/generated", tex_lantern)],
}


def compose_icon(size):
    c = Canvas(size, size)
    cols = [(255, 170, 200, 255), (120, 200, 90, 255), (230, 110, 40, 255), (170, 220, 255, 255)]
    for y in range(size):
        for x in range(size):
            dx, dy = x - size / 2 + 0.5, y - size / 2 + 0.5
            d = math.hypot(dx, dy) / (size / 2)
            a = (math.degrees(math.atan2(dy, dx)) + 360 + 45) % 360
            if d <= 0.95:
                base = cols[int(a // 90)]
                c.set(x, y, shade(base, 1.1 - d * 0.5))
            else:
                c.set(x, y, (35, 25, 45, 255))
    # aiguilles
    for k in range(int(size * 0.38)):
        c.set(size // 2, size // 2 - k, (40, 25, 15, 255))
        c.set(size // 2 - 1, size // 2 - k, (40, 25, 15, 255))
    for k in range(int(size * 0.25)):
        c.set(size // 2 + k, size // 2, (40, 25, 15, 255))
        c.set(size // 2 + k, size // 2 - 1, (40, 25, 15, 255))
    return c


def build(out_root):
    base = os.path.join(out_root, "solstice_rp")
    if os.path.exists(base):
        shutil.rmtree(base)
    tex = os.path.join(base, "assets", "solstice", "textures", "item")
    mdl = os.path.join(base, "assets", "solstice", "models", "item")
    van = os.path.join(base, "assets", "minecraft", "models", "item")
    for d in (tex, mdl, van):
        os.makedirs(d)
    for item, ovs in OVERRIDES.items():
        m = dict(VANILLA[item])
        m["overrides"] = [{"predicate": {"custom_model_data": cmd}, "model": f"solstice:item/{name}"}
                          for cmd, name, _, _ in ovs]
        with open(os.path.join(van, f"{item}.json"), "w") as f:
            json.dump(m, f, indent=2)
        for cmd, name, parent, painter in ovs:
            painter().save(os.path.join(tex, f"{name}.png"))
            with open(os.path.join(mdl, f"{name}.json"), "w") as f:
                json.dump({"parent": parent, "textures": {"layer0": f"solstice:item/{name}"}}, f, indent=2)
    skin.write(os.path.join(base, "assets", "minecraft", "textures", "entity", "zombie"))
    with open(os.path.join(base, "pack.mcmeta"), "w", encoding="utf-8") as f:
        json.dump({"pack": {"pack_format": RESOURCE_FORMAT, "description": "SOLSTICE — objets et Maître Orel"}},
                  f, ensure_ascii=False, indent=2)
    compose_icon(128).save(os.path.join(base, "pack.png"))
    compose_icon(64).save(os.path.join(out_root, "world_icon.png"))
    return base


def register(item, vanilla_model, cmd, name, painter, parent="minecraft:item/generated"):
    """Ajout d’une surcharge par une salle."""
    if item not in VANILLA or VANILLA[item] is None:
        VANILLA[item] = vanilla_model
    OVERRIDES.setdefault(item, []).append((cmd, name, parent, painter))
