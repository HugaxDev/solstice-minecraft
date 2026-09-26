Tu vas installer la map d’aventure Minecraft **SOLSTICE** sur mon serveur dédié. Fais-le de bout en bout, en vérifiant chaque étape.

## Contexte
- Map d’aventure **Minecraft Java 1.21.1**, **vanilla** : tout le jeu est un datapack déjà inclus dans le monde. Aucun mod ni plugin n’est nécessaire.
- Elle est prévue pour **exactement 3 joueurs**.
- Repo : https://github.com/HugaxDev/solstice-minecraft
- Monde : https://github.com/HugaxDev/solstice-minecraft/raw/main/dist/Solstice-world.zip
- Resource pack : https://github.com/HugaxDev/solstice-minecraft/raw/main/dist/Solstice-resourcepack.zip
  (SHA-1 : `f2b3287d7362a10a07cf695129f6d2ec8dfe3441`)

## ⚠️ Anti-spoiler (important)
Je vais jouer à cette map.
- N’ouvre pas et ne résume pas le code du datapack, les fichiers `src/`, `design/` ou `TEST_REPORT.md` du repo.
- N’affiche jamais le contenu des fonctions `.mcfunction` dans le chat.
- Contente-toi d’installer et de vérifier que tout se charge. Si tu dois diagnostiquer une erreur, cite uniquement la ligne d’erreur du log.

## Étapes
1. **Version du serveur.** Il doit tourner en **1.21.1 exactement** (le datapack est en pack_format 48 ; une autre version refusera de le charger).
   - Recommandé : le `server.jar` vanilla officiel de Mojang. Fabric sans mods marche aussi.
   - Paper/Spigot/Purpur **n’ont pas été testés** : ils modifient certains comportements vanilla. En cas de problème, repasser en vanilla.
   - Java 21 est requis.
2. **Arrêt et sauvegarde.** Arrête le serveur. Sauvegarde le monde actuel s’il y en a un : ne supprime rien sans me demander.
3. **Installation du monde.** Télécharge `Solstice-world.zip` et dézippe-le à la racine du serveur.
   - Le résultat doit être exactement `<serveur>/Solstice/level.dat`.
   - Si tu obtiens `Solstice/Solstice/level.dat`, remonte le dossier d’un niveau.
   - Vérifie aussi que `<serveur>/Solstice/datapacks/solstice/pack.mcmeta` existe.
4. **`server.properties`.** Modifie uniquement ces clés et laisse les autres telles quelles :
   ```properties
   level-name=Solstice
   gamemode=adventure
   force-gamemode=true
   difficulty=normal
   spawn-protection=0
   function-permission-level=2
   spawn-monsters=true
   generate-structures=false
   max-players=3
   view-distance=8
   simulation-distance=6
   resource-pack=https://github.com/HugaxDev/solstice-minecraft/raw/main/dist/Solstice-resourcepack.zip
   resource-pack-sha1=f2b3287d7362a10a07cf695129f6d2ec8dfe3441
   require-resource-pack=false
   resource-pack-prompt={"text":"Textures de SOLSTICE (conseillé)"}
   ```
   Points critiques :
   - `spawn-protection=0` : sinon les joueurs non-op ne peuvent pas utiliser boutons et leviers près du spawn, et la map est bloquée.
   - `difficulty=normal` : jamais `peaceful`, sinon il n’y a plus de monstres dans certaines épreuves.
   - Ne mets pas `level-type` : le monde existant garde son propre générateur (monde vide).
5. **Op de l’hôte.** Donne l’op (niveau 4) à mon pseudo : ___________ (demande-le-moi s’il n’est pas renseigné). Ça sert aux commandes de secours.
6. **Démarrage et vérifications.** Démarre le serveur, puis vérifie :
   - les logs : aucune ligne `Failed to load function`, `Couldn't load data packs` ou erreur de parsing liée à `solstice`. Si tu en vois, montre-moi uniquement ces lignes ;
   - en console, `datapack list enabled` doit contenir `file/solstice` ;
   - en console, `difficulty` doit renvoyer Normal.
7. **Accès.** Donne-moi l’adresse et le port de connexion. Vérifie que le port est ouvert (pare-feu / redirection) si le serveur est hébergé chez moi.

## Commandes de secours (pour info, à taper en jeu par un op)
- `/function solstice:debug/reset_salle` : réinitialise la salle en cours.
- `/function solstice:debug/salle_suivante` : passe à la salle suivante.
- `/function solstice:debug/nouvelle_partie` : tout recommencer depuis le début.
- `/function solstice:debug/joueurs_3` : réglage normal à 3 joueurs (`joueurs_1` / `joueurs_2` pour tester à moins).

Ne lance aucune de ces commandes toi-même : la partie doit démarrer vierge quand les 3 joueurs se connectent.

À la fin, résume en 5 lignes max : version du serveur, chemin du monde, propriétés modifiées, résultat des vérifications, adresse de connexion.
