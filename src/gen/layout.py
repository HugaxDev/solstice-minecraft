"""Coordonnées et métadonnées des salles. Sol en y=100 (le joueur se tient en y=101)."""

Y = 100

# id -> nom, couleur, origine, boîtes de sécurité (x1,y1,z1,x2,y2,z2), heure, combat, bossbar
ROOMS = {
    0: {"name": "Prologue : Brumeval", "short": "Brumeval", "color": "gold", "origin": (0, Y, 0),
        "boxes": [(-60, 80, -60, 60, 140, 60)], "time": 13000, "combat": False, "bar": "yellow"},
    1: {"name": "L’Express du Solstice", "short": "L’Express", "color": "aqua", "origin": (1000, Y, 0),
        "boxes": [(940, 80, -30, 1060, 140, 30)], "time": 18000, "combat": False, "bar": "blue"},
    2: {"name": "La Tour des Engrenages", "short": "La Tour", "color": "gold", "origin": (2000, Y, 0),
        "boxes": [(1960, 80, -40, 2040, 160, 40)], "time": 1000, "combat": False, "bar": "yellow"},
    3: {"name": "L’Atelier d’Orel", "short": "L’Atelier", "color": "yellow", "origin": (3000, Y, 0),
        "boxes": [(2950, 80, -50, 3050, 140, 50)], "time": 16000, "combat": False, "bar": "yellow"},
    4: {"name": "Le Siège du Sanctuaire", "short": "Le Sanctuaire", "color": "red", "origin": (4000, Y, 0),
        "boxes": [(3950, 80, -50, 4050, 140, 50)], "time": 13500, "combat": True, "bar": "red"},
    5: {"name": "La Nuit la plus longue", "short": "La Nuit", "color": "dark_purple", "origin": (5000, Y, 0),
        "boxes": [(4940, 60, -90, 5060, 140, 60)], "time": 18000, "combat": False, "bar": "purple"},
    6: {"name": "Les Quatre Saisons", "short": "Les Saisons", "color": "green", "origin": (6000, Y, 0),
        "boxes": [(5955, 80, -45 + z, 6045, 150, 45 + z) for z in (0, 200, 400, 600)], "time": 6000, "combat": False, "bar": "green"},
    7: {"name": "Le Cœur du Calendrier", "short": "Le Cœur", "color": "light_purple", "origin": (7000, Y, 0),
        "boxes": [(6950, 80, -50, 7050, 150, 50)], "time": 18000, "combat": True, "bar": "pink"},
    8: {"name": "Épilogue", "short": "Brumeval", "color": "green", "origin": (0, Y, 0),
        "boxes": [(-60, 80, -60, 60, 140, 60)], "time": 1000, "combat": False, "bar": "green"},
}
LAST_ROOM = 7
