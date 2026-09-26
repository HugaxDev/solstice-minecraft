"""Journal de quête : onglet « Solstice ». Une entrée par salle, les indices (cachés jusqu’à leur découverte),
des défis cachés, et l’advancement final. Tout est accordé par commande (critère impossible)."""
from .core import T
from .layout import ROOMS
from .story import CLUES

ROOM_ADV = {
    0: ("Brumeval", "Répondre à l’appel de Maître Orel.", "bell"),
    1: ("L’Express du Solstice", "Mener le train jusqu’au pied du Calendrier.", "minecart"),
    2: ("La Tour des Engrenages", "Se retrouver au sommet de la tour.", "piston"),
    3: ("L’Atelier d’Orel", "Allumer la Lanterne des Saisons.", "lantern"),
    4: ("Le Siège du Sanctuaire", "Briser les six sceaux du Sanctuaire.", "shield"),
    5: ("La Nuit la plus longue", "Voir le jour se lever.", "black_candle"),
    6: ("Les Quatre Saisons", "Rendre ses quatre cristaux au Calendrier.", "amethyst_cluster"),
    7: ("Le Cœur du Calendrier", "Remettre le temps en marche.", "clock"),
}
CHALLENGES = {
    "voie_royale": ("Voie royale", "Mener l’Express sans une seule erreur.", "rail"),
    "horlogerie_fine": ("Horlogerie fine", "Gravir la Tour des Engrenages en moins de 12 minutes.", "clock"),
    "rempart": ("Rempart", "Traverser le Siège du Sanctuaire sans aucune mort.", "shield"),
    "sang_froid": ("Sang-froid", "Un défi caché, quelque part dans l’aventure.", "snowball"),
    "premier_sablier": ("Le temps d’un sablier", "Réussir les Quatre Saisons sans remonter le temps.", "sand"),
    "fin_limier": ("Fin limier", "Désigner le bon coupable du premier coup.", "spyglass"),
    "enqueteur": ("Rien ne m’échappe", "Trouver tous les indices de l’enquête.", "writable_book"),
    "maitre_horloger": ("Maître horloger", "Relever tous les autres défis.", "nether_star"),
}


def _adv(icon, title_txt, desc, parent=None, frame="task", hidden=False, color="gold", toast=True, bg=None):
    d = {"display": {"icon": {"id": f"minecraft:{icon}"}, "title": T(title_txt, color), "description": T(desc, "gray"),
                     "frame": frame, "show_toast": toast, "announce_to_chat": False, "hidden": hidden},
         "criteria": {"done": {"trigger": "minecraft:impossible"}}}
    if bg:
        d["display"]["background"] = bg
    if parent:
        d["parent"] = f"solstice:{parent}"
    return d


def build(dp):
    dp.adv("root", _adv("clock", "Solstice", "Réparer le Grand Calendrier de Brumeval… et découvrir qui l’a saboté.",
                        frame="challenge", toast=False, bg="minecraft:textures/block/stripped_spruce_log.png"))
    prev = "root"
    for n in range(0, 8):
        t, d, icon = ROOM_ADV[n]
        dp.adv(f"room/r{n}", _adv(icon, t, d, parent=prev, frame="goal" if n in (3, 6, 7) else "task",
                                  color=ROOMS[n]["color"]))
        prev = f"room/r{n}"
    dp.adv("fin", _adv("nether_star", "Le temps reprend son cours", "Terminer Solstice.", parent="room/r7",
                       frame="challenge", color="light_purple"))
    dp.adv("clue/root", _adv("writable_book", "Carnet d’enquête", "Les indices apparaissent ici quand vous les trouvez.",
                             parent="root", toast=False))
    for cid, room, t, text, icon in CLUES:
        dp.adv(f"clue/{cid}", _adv(icon, t, text, parent="clue/root", hidden=True, color="yellow"))
    dp.adv("challenge/root", _adv("gold_nugget", "Défis cachés", "Il y en a plusieurs. Ils se révèlent quand on les relève.",
                                  parent="root", toast=False))
    for cid, (t, d, icon) in CHALLENGES.items():
        dp.adv(f"challenge/{cid}", _adv(icon, t, d, parent="challenge/root", hidden=True, frame="challenge",
                                        color="aqua"))
    others = [c for c in CHALLENGES if c != "maitre_horloger"]
    dp.fn("challenge/check_all", [
        "execute if entity @s[advancements={" + ",".join(f"solstice:challenge/{c}=true" for c in others)
        + "}] run advancement grant @s only solstice:challenge/maitre_horloger"])
    for cid, (t, d, icon) in CHALLENGES.items():
        if cid == "maitre_horloger":
            continue
        dp.fn(f"challenge/grant_{cid}", [
            f"advancement grant @a only solstice:challenge/{cid}",
            f"tellraw @a [\"\",{{\"text\":\"★ Défi caché relevé : \",\"color\":\"aqua\",\"bold\":true}},"
            f"{{\"text\":\"{t}\",\"color\":\"white\"}}]",
            "execute as @a run function solstice:challenge/check_all",
        ])
    dp.meta["advancements"] = 1 + 8 + 1 + 1 + len(CLUES) + 1 + len(CHALLENGES)
