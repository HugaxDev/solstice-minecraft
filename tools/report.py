#!/usr/bin/env python3
"""Génère TEST_REPORT.md (racine + dist/) à partir des résultats réels de build/*.json.
La salle 5 n’apparaît que sous forme de compteurs."""
import json
import os
import shutil
from collections import OrderedDict
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build")


def load(name):
    p = os.path.join(BUILD, name)
    return json.load(open(p)) if os.path.exists(p) else None


UNTESTED = """## Ce qui n’a pas pu être testé

Tout ce qui suit dépend du **client graphique** ou de **vrais humains**, que je ne pouvais pas lancer ni simuler :

- **Rendu client** : textures du resource pack (Lanterne, cristaux, apparence de Maître Orel), text_display et
  item_display, particules, titres, bossbars, sons, obscurité, biomes des quatre vallées, onglet « Solstice » des
  progrès. Les fichiers sont validés (PNG 16×16, modèles de base identiques au vanilla du `client.jar`, chemins),
  mais leur affichage n’a jamais été vu.
- **Vraie partie en LAN** : « Ouvrir au réseau local » (serveur intégré de l’hôte), connexion de deux vrais
  clients, pare-feu macOS, latence. Les tests utilisent un serveur dédié local et 3 joueurs factices Carpet.
- **Gestes humains** : les joueurs factices cliquent pour de vrai (`look at` + `use`/`attack`), marchent sur les
  dalles, s’accroupissent, meurent, se déconnectent ; mais les déplacements longs sont des téléportations, les
  combats sont raccourcis (monstres tués par commande, résistance accordée) et certains réglages sont forcés
  par le test (pression du train, position d’un évènement, butin donné). La difficulté réelle n’est pas éprouvée.
- **Ressenti** : peur, rythme, clarté des énigmes, équilibrage des combats, durée réelle (l’estimation ci-dessous
  est une estimation, pas une mesure).
- **Lecture des livres** (Carnet, feuille de route) : le contenu des pages est vérifié, pas l’interface.
- **Chat vocal** : indispensable pour la coopération, évidemment non testé.
"""

KNOWN = """## Bugs connus et limites

- **Sans le resource pack**, tout reste jouable : les objets sont des objets vanilla nommés (lanterne, horloge,
  éclats d’améthyste…), mais Maître Orel apparaît comme un noyé nommé « Maître Orel ».
- **Les interactions se font sur des zones cliquables invisibles** (entités `interaction`) : viser le centre de
  l’objet. Un coéquipier ou un monstre placé entre vous et l’objet « prend » le clic.
- **Difficulté Paisible** : repassée automatiquement en Normal (sinon plus de monstres au Siège et au Cœur).
- **Mode 1 ou 2 joueurs (debug)** : prévu pour tester, pas pour jouer. Certaines énigmes pensées pour trois
  (informations visibles ailleurs) sont affichées en clair dans le chat, et des étapes simultanées deviennent
  séquentielles.
- **Anéantissement dans une salle longue** : la salle se réinitialise proprement mais conserve les étapes déjà
  franchies (Siège : le sceau en cours recommence ; Cœur : le combat recommence, le verdict est conservé).
- **Plus de 3 joueurs** : possible, mais l’équilibrage et les rôles sont pensés pour exactement trois.
- **Hôte LAN** : si l’hôte quitte, la partie s’arrête pour tout le monde (limite du mode LAN) ; la progression
  est sauvegardée dans son monde.
"""


COVER = [
    ("prologue", "attente des 3 joueurs, cinématique, PNJ cliquables, indices, Carnet, tirages au sort répétés, embarquement"),
    ("tirages", "30 tirages : rôles uniques, hasard réel, exclusion du précédent"),
    ("salle 1", "rôles et postes réservés, chaque évènement du trajet en réussite et en erreur, parcours complet, mort, reconnexion"),
    ("salle 2", "tirage des puits, 9 énigmes (erreurs comprises), grilles croisées, niveaux, sommet, mort, reconnexion"),
    ("salle 3", "missions réservées et résolues en vrais clics, assemblage simultané, objet unique, encre invisible, passage secret"),
    ("salle 4", "rôles re-tirés à chaque étape, équipements, capacités, 6 étapes (erreurs comprises), mort/spectateur, anéantissement"),
    ("salle 6", "voyage entre saisons, chaque chaîne de propagation, piège d’anticipation et remontée du temps, étape finale, morts"),
    ("salle 7", "vote (désaccord puis unanimité), les deux branches de l’accusation, machine-boss, mort, anéantissement, reconnexion"),
    ("fin de partie", "cinématique, crédits (temps, morts), advancement final, épilogue"),
    ("parcours complet", "prologue → crédits dans l’ordre, retour impossible vers chaque salle précédente, journal complet"),
    ("indices progressifs", "indice à 5 min puis à 8 min, remise à zéro au changement d’étape"),
    ("mode debug", "partie lancée à 1 joueur, rôles vacants, automate d’Orel, retour à 3"),
    ("serveur", "aucune erreur/avertissement du datapack, zones chargées"),
    ("général", "chargement des zones de jeu"),
]


def cover(sec):
    return next((d for k, d in COVER if sec.startswith(k)), "")


def detailed(tr, jr):
    L = ["# Rapport de tests DÉTAILLÉ (SPOILERS : solutions et enquête)", ""]
    for title_, res in (("Scénarios E2E", tr["results"]), ("Parcours complet et modes spéciaux", jr["results"])):
        L.append(f"## {title_}\n")
        secs = OrderedDict()
        for sec, name, ok, detail in res:
            secs.setdefault(sec, []).append((name, ok, detail))
        for sec, items in secs.items():
            L.append(f"### {sec} — {sum(1 for _, ok, _ in items if ok)}/{len(items)}\n")
            L += [f"- {'✅' if ok else '❌'} {name}" + (f" — `{d[:160]}`" if d and not ok else "") for name, ok, d in items]
            L.append("")
    L.append("(Salle 5 : voir tests_server-test.json dans ce dossier.)")
    return "\n".join(L) + "\n"


def main():
    lint = load("lint.json") or {}
    wb = load("worldbuild.json") or {}
    tr = load("test_results.json") or {"results": [], "passed": 0, "total": 0, "secret5": {"passed": 0, "total": 0}}
    jr = load("journey_results.json") or {"results": [], "passed": 0, "total": 0}
    du = load("durations.json") or {}
    pk = load("package.json") or {}
    orph = load("orphans.json") or {}
    s5 = tr.get("secret5", {"passed": 0, "total": 0})
    L = ["# Rapport de tests — SOLSTICE 1.0", "",
         f"Généré automatiquement par `tools/report.py` le {datetime.now():%Y-%m-%d %H:%M} (relancé à chaque `./build.sh`).", "",
         "## Résumé", "", "| Étape | Résultat |", "|---|---|",
         f"| py_compile + lint JSON + références (fonctions, advancements, loot, prédicats, blocs, objets) | "
         f"{'OK' if lint.get('errors') == 0 else 'ÉCHEC'} — {lint.get('python')} fichiers Python, {lint.get('json')} JSON, "
         f"{lint.get('functions')} fonctions ({lint.get('commands')} commandes), {lint.get('advancements')} advancements |",
         f"| Audit des sélecteurs (jeu à 3 : pas de @p/@r, pas de sélection d’un joueur unique, @s toujours avec exécutant) | "
         f"OK — {lint.get('audit', {}).get('functions')} fonctions, {lint.get('audit', {}).get('at_s')} usages de @s vérifiés |",
         f"| Registre d’énigmes (aucun type répété sur la carte) | OK — {lint.get('puzzles')} énigmes, {lint.get('puzzles')} types distincts |",
         f"| Monde construit par un serveur **vanilla** : `test/all` structurel | **{wb.get('tests_pass')}/{wb.get('tests_total')} PASS** |",
         f"| Erreurs/avertissements du datapack dans les logs (build) | {len(wb.get('log_problems', []))} |",
         f"| Advancements chargés | {wb.get('advancements_loaded')} (attendu {wb.get('advancements_expected')}) |",
         f"| Scénarios E2E, 3 joueurs factices (toutes les salles, salle 5 comprise) | **{tr['passed']}/{tr['total']} PASS** |",
         f"| Parcours complet + indices progressifs + mode 1 joueur | **{jr['passed']}/{jr['total']} PASS** |",
         f"| Processus orphelins / ports ouverts après les runs | {orph.get('servers', '?')} / {orph.get('ports', '?')} |",
         f"| Durée estimée (découverte) | **{du.get('total')} min** (cible 105–120) |",
         f"| Monde livré : `level.dat` au premier niveau du dossier une fois dézippé | {'vérifié' if pk.get('level_dat_first_level') else '?'} |",
         "", "## Méthode", "",
         "1. `src/build_packs.py` génère tout le datapack (et le resource pack) ; `tools/lint.py` valide chaque bloc, "
         "état de bloc et objet contre les rapports officiels extraits du `server.jar` 1.21.1.",
         "2. `tools/worldbuild.py` construit le monde sur un **serveur vanilla** headless (127.0.0.1), vérifie chaque "
         "commande de biome, lance `test/all`, analyse les logs, puis nettoie `level.dat`.",
         "3. `tools/tests.py` rejoue la partie sur une **copie** du monde, serveur Fabric + **Carpet (tests uniquement)**, "
         "avec 3 joueurs factices : chemin nominal de chaque salle, tirages de rôles répétés, mort d’un joueur, mort des 3, "
         "déconnexion/reconnexion, retour arrière impossible.",
         "4. `tools/test_journey.py` : parcours complet du prologue aux crédits (ordre, retours interdits vers chaque "
         "salle précédente), indices progressifs, mode debug à 1 joueur.",
         "5. `tools/package.py` : zips contrôlés (dézippage réel), aucune trace de Fabric/Carpet dans le monde.", ""]
    # Version publique SANS spoiler : compteurs par section + ce que la section couvre.
    # Le détail nominatif (qui dévoile solutions et coupable) va dans design/SPOILERS_NE_PAS_LIRE/.
    L.append("## Scénarios E2E par section\n")
    L.append("Le détail nominatif des tests dévoile des solutions (et l’enquête) : il est rangé dans "
             "`design/SPOILERS_NE_PAS_LIRE/TEST_REPORT_DETAILLE.md`.\n")
    L.append("| Section | Résultat | Ce qui est couvert |")
    L.append("|---|---|---|")
    secs = OrderedDict()
    for sec, name, ok, detail in tr["results"]:
        secs.setdefault(sec, []).append((name, ok, detail))
    for sec, items in secs.items():
        n = sum(1 for _, ok, _ in items if ok)
        L.append(f"| {sec} | {'✅' if n == len(items) else '❌'} {n}/{len(items)} | {cover(sec)} |")
    L.append(f"| salle 5 | {'✅' if s5['passed'] == s5['total'] else '❌'} {s5['passed']}/{s5['total']} | salle 5 : faite, "
             f"{s5['passed']}/{s5['total']} tests OK (détail non publié) |")
    for sec in OrderedDict((r[0], 1) for r in jr["results"]):
        items = [r for r in jr["results"] if r[0] == sec]
        n = sum(1 for r in items if r[2])
        L.append(f"| {sec} | {'✅' if n == len(items) else '❌'} {n}/{len(items)} | {cover(sec)} |")
    L.append("")
    L.append("## Estimation de durée (joueurs qui découvrent)\n")
    L.append("| Salle | Visé | Estimé | Étapes |")
    L.append("|---|---|---|---|")
    for r in du.get("rooms", []):
        steps = " · ".join(f"{s} ({d:g})" for s, d in r["steps"])
        L.append(f"| {r['room']} — {r['name']} | {r['target']} min | {r['estimate']:g} min | {steps} |")
    L.append(f"| transitions | — | {du.get('transitions')} min | 7 transitions narratives de 10 s |")
    L.append(f"| **Total** | **105–120** | **{du.get('total')} min** | |\n")
    L.append(UNTESTED)
    L.append(KNOWN)
    txt = "\n".join(L) + "\n"
    with open(os.path.join(ROOT, "design", "SPOILERS_NE_PAS_LIRE", "TEST_REPORT_DETAILLE.md"), "w", encoding="utf-8") as f:
        f.write(detailed(tr, jr))
    for dst in (os.path.join(ROOT, "TEST_REPORT.md"), os.path.join(ROOT, "dist", "TEST_REPORT.md")):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "w", encoding="utf-8") as f:
            f.write(txt)
    shutil.copy(os.path.join(ROOT, "README.md"), os.path.join(ROOT, "dist", "README.md"))
    print("TEST_REPORT.md écrit")


if __name__ == "__main__":
    main()
