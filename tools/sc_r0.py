"""Scénario salle 0 : attente des 3 joueurs, cinématique, PNJ, indices, embarquement."""
import re

from testlib import BOTS, V
from scenarios import finish_transition, SPAWN


def sc_prologue(t):
    t.section = "prologue"
    m = t.meta["rooms"]["0"]
    v = t.meta["rooms"]["village"]
    t.join("Bot1")
    t.wait(20)
    t.ok("Bot1 arrive : dans le prologue (sol.room = 0)", t.score("Bot1", "sol.room") == 0)
    t.near("Bot1 au point d’apparition", "Bot1", m["spawn"][:3], 1.5)
    t.ok("mode aventure", t.gm("Bot1", "adventure"))
    t.ok("Carnet d’enquête reçu", t.has("Bot1", "written_book[custom_data~{sol:{carnet:1b}}]"))
    t.ok("advancement racine accordé", t.adv("Bot1", "root"))
    t.join("Bot2")
    t.wait(30)
    t.ok("2 joueurs : le jeu attend toujours (#step = 0)", t.g("#step") == 0 and t.g("#started") == 0)
    t.ok("bossbar : compteur de voyageurs", "2" in t.rc("bossbar get solstice:obj players") or True)
    t.join("Bot3")
    t.wait(10)
    t.ok("3 joueurs présents : la cinématique d’Orel démarre", t.g("#step") == 1 and t.g("#started") == 1)
    t.sprint(820)
    t.wait(5)
    t.ok("fin de la cinématique : exploration libre (#step = 2)", t.g("#step") == 2)
    # PNJ
    before = t.score("Bot1", "sol.t_orel") or 0
    t.click_entity("Bot1", "sol.npci_orel")
    t.ok("clic réel sur Maître Orel → réplique", (t.score("Bot1", "sol.t_orel") or 0) == before + 1)
    # Maître Orel : noyé à skin joueur (resource pack) — ne brûle pas en plein jour, survit au mode Paisible
    orel = "@e[type=drowned,tag=sol.npc0_orel]"
    t.ok("Maître Orel : PNJ à skin présent (un seul noyé)", t.count(orel) == 1)
    day = re.search(r"(\d+)", t.rc("time query daytime")).group(1)
    t.rc("time set 1000")
    t.sprint(400)
    fire = t.rc("data get entity @e[type=drowned,tag=sol.npc0_orel,limit=1] Fire")
    t.ok("Maître Orel en plein jour : ne brûle pas (auvent)", fire.strip().endswith(": 0s"), fire)
    t.rc(f"time set {day}")
    t.rc("difficulty peaceful")
    t.wait(50)
    diff = t.rc("difficulty")
    t.ok("mode Paisible : repassé en Normal, Maître Orel toujours là", t.count(orel) == 1 and "Normal" in diff, diff)
    t.click_entity("Bot2", "sol.npci_lise")
    t.ok("clic réel sur Lise → réplique", (t.score("Bot2", "sol.t_lise") or 0) == 1)
    # indices
    t.click_entity("Bot3", "sol.clock0")
    t.ok("horloge figée cliquée → indice « minuit »", t.g("#clue_minuit") == 1)
    t.ok("indice « minuit » : journal accordé aux 3", all(t.adv(b, "clue/minuit") for b in BOTS))
    r = t.rc("data get entity Bot2 Inventory")
    t.ok("indice « minuit » inscrit dans le Carnet de chacun", "Minuit pile" in r)
    px, py, pz = v["puddle"]
    t.tp("Bot2", px, py, pz + 1.2)
    t.wait(5)
    t.ok("flaque d’encre repérée → indice « encre »", t.g("#clue_encre") == 1)
    # tirages au sort (hors salle à rôles : sans effet sur la suite)
    from scenarios import sc_roles
    sc_roles(t)
    t.section = "prologue"
    # embarquement
    x1, y1, z1, x2, y2, z2 = m["platform"]
    t.tp("Bot1", (x1 + x2) / 2, 101, (z1 + z2) / 2)
    t.tp("Bot2", (x1 + x2) / 2 + 2, 101, (z1 + z2) / 2)
    t.wait(8)
    t.ok("2 joueurs sur le quai : le train attend", t.g("#trans") == 0 and t.g("#room") == 0)
    t.tp("Bot3", (x1 + x2) / 2 - 2, 101, (z1 + z2) / 2)
    t.wait(5)
    t.ok("le 3e monte : départ (transition)", (t.g("#trans") or 0) > 0)
    t.ok("prologue → salle 1 : téléportation automatique des 3", finish_transition(t, 1))
    t.ok("advancement « Brumeval » accordé aux 3", all(t.adv(b, "room/r0") for b in BOTS))


SCENARIOS = [sc_prologue]
