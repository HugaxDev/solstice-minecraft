"""Enquête : indices (drapeaux #clue_<id>), annonces, journal (advancements) et Carnet d’enquête (livre régénéré)."""
from .core import V, T, jdump, tellraw, snbt_str, Item, title
from . import secret5

# (id, salle, titre, texte, icône)
CLUES = [
    ("encre", 0, "L’encre bleue", "Des gouttes d’encre bleue, encore fraîches, mènent de la bibliothèque jusqu’à la gare.", "blue_dye"),
    ("minuit", 0, "Minuit pile", "L’horloge de la place s’est arrêtée à minuit pile, la nuit du sabotage.", "clock"),
    ("marteau", 1, "Le marteau gravé « B. »", "Un marteau de forgeron gravé « B. », caché dans le tender. Une étiquette jaunie pend au manche : "
     "« Collection de la bibliothèque — objet n°12 ».", "iron_axe"),
    ("graines", 2, "Le sachet de graines", "« Tournesol géant de Lise ». Le sachet porte le tampon « Herbier de la bibliothèque », "
     "et l’étiquette est écrite à l’encre bleue.", "sunflower"),
    ("mot", 3, "Le mot invisible", "« Orel, je sais ce que tu caches sous l’établi. Arrête avant le solstice, ou je le ferai à ta place. — Y. »",
     "paper"),
    ("plan", 3, "Le plan déchiré", "Un plan de la main d’Orel, déchiré. On ne lit plus que : « VERROU … DERNIER JOUR … à minuit du solstice ».",
     "map"),
    ("gant", 4, "Le gant de jardinière", "Un gant de jardinage taché de terre, lâché par un gardien. Il est brodé d’un « L ».", "leather"),
    ("registre", 4, "Le registre du Sanctuaire", "« Dernier passage autorisé au Cœur : Maître Orel, trois jours avant la panne. »",
     "writable_book"),
    (secret5.CLUE_ID, 5, secret5.CLUE_TITLE, secret5.CLUE_TEXT, secret5.CLUE_ICON),
    ("lettre", 6, "La lettre de Lise", "« Bram, merci pour la soupe de minuit. Sans toi, j’aurais veillé la serre toute seule. — Lise »",
     "white_tulip"),
]
CARNET = Item("written_book", data="{sol:{keep:1b,carnet:1b}}")
CARNET_PRED = "written_book[custom_data~{sol:{carnet:1b}}]"


def build(dp):
    for cid, room, t, text, icon in CLUES:
        dp.fn(f"story/found_{cid}", [
            f"execute if score #clue_{cid} {V} matches 1 run return 0",
            f"scoreboard players set #clue_{cid} {V} 1",
            f"scoreboard players add #clues {V} 1",
            tellraw("@a", T("🔍 Indice découvert : ", "gold", bold=True), T(t, "yellow", bold=True)),
            tellraw("@a", T("   " + text, "white", italic=True)),
            tellraw("@a", T("   (ajouté au Carnet d’enquête et au journal, touche L)", "dark_gray")),
            "execute as @a at @s run playsound minecraft:item.book.page_turn master @s ~ ~ ~ 1 0.8",
            "execute as @a at @s run playsound minecraft:block.note_block.bell master @s ~ ~ ~ 0.6 1.6",
            f"advancement grant @a only solstice:clue/{cid}",
            "execute as @a run function solstice:story/refresh_carnet",
            f"execute if score #clues {V} matches {len(CLUES)}.. run function solstice:challenge/grant_enqueteur",
        ])
    sync = []
    for cid, *_ in CLUES:
        sync.append(f"execute if score #clue_{cid} {V} matches 1 run advancement grant @s only solstice:clue/{cid}")
    sync += [f"execute if score #room {V} matches {n + 1}.. run advancement grant @s only solstice:room/r{n}" for n in range(0, 8)]
    sync.append(f"execute unless items entity @s container.* {CARNET_PRED} unless items entity @s weapon.offhand {CARNET_PRED} "
                f"run loot give @s loot solstice:carnet")
    dp.fn("story/sync_player", sync)
    dp.fn("story/refresh_carnet", [f"clear @s {CARNET_PRED}", "loot give @s loot solstice:carnet"])
    dp.fn("story/reset", [f"scoreboard players set #clue_{cid} {V} 0" for cid, *_ in CLUES] +
          [f"scoreboard players set #clues {V} 0"])
    dp.fn("story/init", [f"execute unless score #clue_{cid} {V} matches 0.. run scoreboard players set #clue_{cid} {V} 0"
                         for cid, *_ in CLUES] +
          [f"execute unless score #clues {V} matches 0.. run scoreboard players set #clues {V} 0"])
    dp.add("load", ["function solstice:story/init"])

    # Carnet : livre écrit, une page d’introduction + une page par indice trouvé (table de loot conditionnelle)
    intro = ["", T("Carnet d’enquête\n\n", "dark_blue", bold=True),
             T("Quelqu’un a saboté le Grand Calendrier.\n\nTrois personnes y avaient accès :\n", "black"),
             T("• Ysolde", "dark_purple"), T(", la bibliothécaire\n", "black"),
             T("• Bram", "dark_red"), T(", le forgeron\n", "black"),
             T("• Lise", "dark_green"), T(", la jardinière\n\n", "black"),
             T("Chaque indice trouvé s’inscrit ici. Certains mentent.", "dark_gray", italic=True)]
    funcs = [
        {"function": "minecraft:set_book_cover", "title": "Carnet d’enquête", "author": "Les trois voyageurs"},
        {"function": "minecraft:set_written_book_pages", "mode": "replace_all", "pages": [intro]},
        {"function": "minecraft:set_custom_data", "tag": "{sol:{keep:1b,carnet:1b}}"},
        {"function": "minecraft:set_name", "target": "item_name", "name": T("Carnet d’enquête", "gold")},
    ]
    for cid, room, t, text, icon in CLUES:
        page = ["", T(f"Salle {room}\n", "dark_gray"), T(t + "\n\n", "dark_blue", bold=True), T(text, "black")]
        funcs.append({"function": "minecraft:set_written_book_pages", "mode": "append", "pages": [page],
                      "conditions": [{"condition": "minecraft:value_check",
                                      "value": {"type": "minecraft:score", "target": {"type": "minecraft:fixed", "name": f"#clue_{cid}"},
                                                "score": "sol.var"},
                                      "range": 1}]})
    dp.loot("carnet", {"type": "minecraft:command", "pools": [{"rolls": 1, "entries": [
        {"type": "minecraft:item", "name": "minecraft:written_book", "functions": funcs}]}]})

    for cid, *_ in CLUES:
        dp.test(f"enquête : indice « {cid} » initialisé", f"score #clue_{cid} {V} matches 0..1")
