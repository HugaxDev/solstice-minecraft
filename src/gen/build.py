"""Primitives de construction (maisons, toits, arbres, lampadaires…) → listes de commandes fill/setblock."""
import math
import random

from .core import fill, setblock


def box(x1, y1, z1, x2, y2, z2, wall, floor=None, ceil=None, hollow=True):
    out = fill(x1, y1, z1, x2, y2, z2, wall)
    if hollow:
        out += fill(x1 + 1, y1 + 1, z1 + 1, x2 - 1, y2 - 1, z2 - 1, "air")
    if floor:
        out += fill(x1 + 1, y1, z1 + 1, x2 - 1, y1, z2 - 1, floor)
    if ceil:
        out += fill(x1 + 1, y2, z1 + 1, x2 - 1, y2, z2 - 1, ceil)
    return out


def gable_roof(x1, z1, x2, z2, y, mat, axis="x", overhang=1, cap=None):
    """Toit à deux pans en escaliers. axis = direction du faîtage."""
    out = []
    x1 -= overhang; x2 += overhang; z1 -= overhang; z2 += overhang
    if axis == "x":
        lo, hi = z1, z2
        k = 0
        while lo <= hi:
            out += fill(x1, y + k, lo, x2, y + k, lo, f"{mat}_stairs[facing=south]")
            out += fill(x1, y + k, hi, x2, y + k, hi, f"{mat}_stairs[facing=north]")
            if lo == hi:
                out += fill(x1, y + k, lo, x2, y + k, lo, cap or f"{mat}_slab[type=bottom]")
            elif hi - lo == 1:
                pass
            lo += 1; hi -= 1; k += 1
        if (z2 - z1) % 2 == 1:
            mid = (z1 + z2) // 2
            out += fill(x1, y + k, mid, x2, y + k, mid + 1, cap or f"{mat}_slab[type=bottom]")
    else:
        lo, hi = x1, x2
        k = 0
        while lo <= hi:
            out += fill(lo, y + k, z1, lo, y + k, z2, f"{mat}_stairs[facing=east]")
            out += fill(hi, y + k, z1, hi, y + k, z2, f"{mat}_stairs[facing=west]")
            if lo == hi:
                out += fill(lo, y + k, z1, lo, y + k, z2, cap or f"{mat}_slab[type=bottom]")
            lo += 1; hi -= 1; k += 1
        if (x2 - x1) % 2 == 1:
            mid = (x1 + x2) // 2
            out += fill(mid, y + k, z1, mid + 1, y + k, z2, cap or f"{mat}_slab[type=bottom]")
    return out


def gable_fill(x1, z1, x2, z2, y, mat, axis="x"):
    """Remplit les pignons sous un toit gable_roof (sans débord)."""
    out = []
    if axis == "x":
        lo, hi, k = z1 + 1, z2 - 1, 0
        while lo <= hi:
            out += fill(x1, y + k, lo, x1, y + k, hi, mat) + fill(x2, y + k, lo, x2, y + k, hi, mat)
            lo += 1; hi -= 1; k += 1
    else:
        lo, hi, k = x1 + 1, x2 - 1, 0
        while lo <= hi:
            out += fill(lo, y + k, z1, hi, y + k, z1, mat) + fill(lo, y + k, z2, hi, y + k, z2, mat)
            lo += 1; hi -= 1; k += 1
    return out


def house(x1, z1, x2, z2, y, h, wall="spruce_planks", frame="spruce_log", floor="spruce_planks",
          roof="dark_oak", axis="x", door=None, windows="glass_pane", light=True, ceil=None):
    """Maison simple : murs, poteaux d’angle, fenêtres, porte (côté, position), toit, lanterne intérieure."""
    out = box(x1, y, z1, x2, y + h, z2, wall, floor=floor, ceil=None)
    out += fill(x1 + 1, y + h, z1 + 1, x2 - 1, y + h, z2 - 1, "air")
    for (x, z) in ((x1, z1), (x1, z2), (x2, z1), (x2, z2)):
        out += fill(x, y, z, x, y + h, z, frame)
    # fenêtres
    for x in range(x1 + 2, x2 - 1, 3):
        for z in (z1, z2):
            out += fill(x, y + 2, z, x, y + 3, z, windows)
    for z in range(z1 + 2, z2 - 1, 3):
        for x in (x1, x2):
            out += fill(x, y + 2, z, x, y + 3, z, windows)
    woods = ("oak", "spruce", "birch", "jungle", "acacia", "dark_oak", "mangrove", "cherry", "bamboo", "crimson", "warped")
    out += fill(x1 + 1, y + h, z1 + 1, x2 - 1, y + h, z2 - 1, ceil or (f"{roof}_planks" if roof in woods else "spruce_planks"))
    out += gable_roof(x1, z1, x2, z2, y + h + 1, roof, axis=axis)
    out += gable_fill(x1, z1, x2, z2, y + h + 1, wall, axis=axis)
    if door:
        dx, dz, facing = door
        out += [setblock(dx, y + 1, dz, "air"), setblock(dx, y + 2, dz, "air"),
                setblock(dx, y + 1, dz, f"spruce_door[facing={facing},half=lower]"),
                setblock(dx, y + 2, dz, f"spruce_door[facing={facing},half=upper]")]
    if light:
        out.append(setblock((x1 + x2) // 2, y + h - 1, (z1 + z2) // 2, "lantern[hanging=true]"))
    return out


def tree(x, y, z, log="oak_log", leaves="oak_leaves", h=5, r=2, seed=0):
    rnd = random.Random(seed * 7919 + x * 31 + z)
    out = fill(x, y, z, x, y + h - 1, z, log)
    for dy in range(h - 2, h + 2):
        rr = r if dy < h else r - 1
        for dx in range(-rr, rr + 1):
            for dz in range(-rr, rr + 1):
                if dx * dx + dz * dz <= rr * rr + 1 and not (dx == 0 and dz == 0 and dy < h):
                    if rnd.random() < 0.9:
                        out.append(setblock(x + dx, y + dy, z + dz, f"{leaves}[persistent=true]", "keep"))
    return out


def lamp_post(x, y, z, h=3, post="dark_oak_fence", lamp="lantern"):
    return fill(x, y, z, x, y + h - 1, z, post) + [setblock(x, y + h, z, lamp)]


def disc(cx, cy, cz, r, block, mode=""):
    out = []
    for dx in range(-r, r + 1):
        w = int(math.sqrt(max(0, r * r - dx * dx)))
        out += fill(cx + dx, cy, cz - w, cx + dx, cy, cz + w, block, mode)
    return out


def ring(cx, cy, cz, r, block):
    out = []
    seen = set()
    for a in range(0, 360, 3):
        x = cx + int(round(r * math.cos(math.radians(a))))
        z = cz + int(round(r * math.sin(math.radians(a))))
        if (x, z) not in seen:
            seen.add((x, z))
            out.append(setblock(x, cy, z, block))
    return out
