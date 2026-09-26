"""Apparence de Maître Orel : le skin joueur `skin.png` (64x64, racine du projet) porté par un noyé (drowned)
retexturé par le resource pack. Python pur.

Le modèle du noyé suit la disposition d’un skin joueur 64x64 : tête (0,0), chapeau (32,0, gonflé de 0,5),
corps (16,16), bras droit (40,16), jambe droite (0,16), bras gauche (32,48), jambe gauche (16,48), bras de 4 px.
Il n’a pas de calques veste / manches / pantalon : ils passent dans `drowned_outer_layer.png`, rendu sur le même
modèle gonflé de 0,25 (exactement comme les calques du joueur). Un skin « fin » (bras de 3 px) est élargi à 4 px."""
import os

from .png import Canvas, read_png

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SKIN = os.path.join(ROOT, "skin.png")

# (x, y, largeur, hauteur) des zones d’un skin joueur 64x64
HEAD, HAT = (0, 0, 32, 16), (32, 0, 32, 16)
R_LEG, BODY, R_ARM = (0, 16, 16, 16), (16, 16, 24, 16), (40, 16, 16, 16)
L_LEG, L_ARM = (16, 48, 16, 16), (32, 48, 16, 16)
# calque de superposition joueur → emplacement de la même pièce dans la texture du noyé (calque extérieur)
OVERLAYS = {"pantalon droit": ((0, 32), (0, 16)), "veste": ((16, 32), (16, 16)), "manche droite": ((40, 32), (40, 16)),
            "pantalon gauche": ((0, 48), (16, 48)), "manche gauche": ((48, 48), (32, 48))}
OVERLAY_SIZE = {"veste": (24, 16)}
# zones rendues opaques par le jeu pour un skin joueur (setNoAlpha du client) : on reproduit le même rendu
OPAQUE = [(0, 0, 32, 16), (0, 16, 64, 16), (16, 48, 32, 16)]
ARMS = [(40, 16), (32, 48), (40, 32), (48, 48)]   # bras et manches (origine de chaque patron)


def _blit(dst, src, sx, sy, w, h, dx, dy):
    for y in range(h):
        for x in range(w):
            dst.set(dx + x, dy + y, src.get(sx + x, sy + y))


def _alpha(c, x, y, w, h):
    return [c.get(i, j)[3] for j in range(y, y + h) for i in range(x, x + w)]


def is_slim(c):
    """Skin « Alex » : colonnes 54-55 du bras droit vides alors que la face avant (44-46) est peinte."""
    return not any(_alpha(c, 54, 20, 2, 12)) and all(_alpha(c, 44, 20, 3, 12))


def _widen_arm(c, u, v):
    """Patron de bras 3x12x4 → 4x12x4 : la colonne centrale de chaque face large est dupliquée."""
    src = Canvas(16, 16)
    _blit(src, c, u, v, 16, 16, 0, 0)
    out = Canvas(16, 16)
    _blit(out, src, 0, 4, 4, 12, 0, 4)                        # côté extérieur (profondeur 4, inchangé)
    for sx, dx, h, y0 in ((4, 4, 4, 0), (7, 8, 4, 0),         # dessus, dessous
                          (4, 4, 12, 4), (11, 12, 12, 4)):    # avant, arrière
        for k, col in enumerate((0, 1, 1, 2)):
            _blit(out, src, sx + col, y0, 1, h, dx + k, y0)
    _blit(out, src, 7, 4, 4, 12, 8, 4)                        # côté intérieur (profondeur 4, décalé)
    for y in range(16):
        for x in range(16):
            c.set(u + x, v + y, out.get(x, y))


def load(path=SKIN):
    assert os.path.exists(path), f"skin introuvable : {path}"
    c = read_png(path)
    assert (c.w, c.h) == (64, 64), f"{path} : {c.w}x{c.h}, un skin joueur 64x64 est attendu"
    if is_slim(c):
        for u, v in ARMS:
            _widen_arm(c, u, v)
    return c


def drowned_textures(skin):
    """→ (drowned.png, drowned_outer_layer.png) sous forme de Canvas 64x64."""
    base = Canvas(64, 64)
    for x, y, w, h in (HEAD, HAT, R_LEG, BODY, R_ARM, L_LEG, L_ARM):
        _blit(base, skin, x, y, w, h, x, y)
    for x, y, w, h in OPAQUE:
        for j in range(y, y + h):
            for i in range(x, x + w):
                r, g, b, _ = base.get(i, j)
                base.set(i, j, (r, g, b, 255))
    outer = Canvas(64, 64)
    for name, ((sx, sy), (dx, dy)) in OVERLAYS.items():
        w, h = OVERLAY_SIZE.get(name, (16, 16))
        _blit(outer, skin, sx, sy, w, h, dx, dy)
    return base, outer


def check(base, outer):
    """Garde-fous : membres entièrement peints, tête du calque extérieur vide (le chapeau est dans la base)."""
    for x, y, w, h in (HEAD, R_LEG, BODY, R_ARM, L_LEG, L_ARM):
        assert min(_alpha(base, x, y, w, h)) == 255, f"texture du noyé : zone {(x, y)} non opaque"
    assert not any(_alpha(outer, *HEAD)) and not any(_alpha(outer, *HAT)), "calque extérieur : tête non vide"


def write(tex_dir, path=SKIN):
    base, outer = drowned_textures(load(path))
    check(base, outer)
    os.makedirs(tex_dir, exist_ok=True)
    base.save(os.path.join(tex_dir, "drowned.png"))
    outer.save(os.path.join(tex_dir, "drowned_outer_layer.png"))
