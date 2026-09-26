# SOLSTICE

*Le village de Brumeval vit sous la protection du Grand Calendrier, la machine qui fait tourner les saisons.
Une nuit, quelqu’un l’a sabotée. Maître Orel, l’horloger, appelle trois voyageurs pour la réparer… et découvrir
qui a fait le coup.*

Aventure **Minecraft Java 1.21.1**, **vanilla** (aucun mod), pour **exactement 3 joueurs** en réseau local.
Durée : **environ 1 h 55**. Difficulté conseillée : **Normale** (pas Paisible).
Un chat vocal est indispensable : presque tout se joue en se parlant.

## Contenu

| Fichier | À quoi il sert |
|---|---|
| `Solstice-world.zip` | Le monde. **C’est le seul fichier indispensable** (pour l’hôte). |
| `Solstice-resourcepack.zip` | Les textures. À installer par **chacun des 3 joueurs** (optionnel mais conseillé). |
| `Solstice-1.0.mrpack` | Optionnel, pour Prism Launcher (mods de confort). Inutile avec le launcher officiel. |

## 1. Installation du monde (hôte, launcher officiel)

1. Launcher Minecraft › **Installations** › **Nouvelle installation** › Version **release 1.21.1** › Créer.
2. Dézippez `Solstice-world.zip` dans le dossier des mondes :
   `~/Library/Application Support/minecraft/saves/`
   (Finder › menu **Aller** › **Aller au dossier…** puis collez ce chemin.)
3. **Vérifiez** : vous devez obtenir `saves/Solstice/level.dat`. Si vous voyez `saves/Solstice/Solstice/level.dat`,
   remontez le dossier intérieur d’un niveau.
4. Lancez l’installation 1.21.1 : le monde « Solstice » apparaît dans **Solo**.

## 2. Resource pack (les 3 joueurs)

En réseau local, le jeu n’envoie **pas** le resource pack aux autres joueurs : chacun l’installe chez lui.

1. Copiez `Solstice-resourcepack.zip` (sans le dézipper) dans `~/Library/Application Support/minecraft/resourcepacks/`.
2. En jeu : **Options › Packs de ressources**, cliquez sur la flèche du pack « Solstice » pour l’activer, puis **Terminé**.

Sans lui, le jeu reste entièrement compréhensible : seules certaines textures sont moins jolies.

## 3. Jouer à trois en LAN (même wifi)

**L’hôte** :
1. Ouvre le monde Solstice en Solo.
2. **Échap › Ouvrir au réseau local**. Mode de jeu des autres joueurs : **Aventure**. Autoriser les commandes :
   **Activé** (utile pour les commandes de secours ci-dessous). Numéro de port : **25565** (conseillé, plus simple).
3. Clique **Démarrer le monde en réseau local**.
4. Trouve son adresse IP locale : **Réglages Système › Wi-Fi › Détails…** (à côté du réseau connecté) › **Adresse IP**
   (par exemple `192.168.1.23`).

**Les deux autres** :
1. **Multijoueur › Connexion directe**.
2. Tapent `IP:port`, par exemple `192.168.1.23:25565`, puis **Rejoindre le serveur**.
   (Le monde apparaît parfois tout seul dans la liste « Parties en réseau local » : on peut cliquer dessus.)

**Si la connexion échoue** :
- Au premier lancement, macOS demande d’**autoriser les connexions entrantes pour « java »** : répondez **Autoriser**.
- Sinon : **Réglages Système › Réseau › Pare-feu › Options…** : ajoutez/autorisez **java** (ou désactivez le pare-feu
  le temps de la partie).
- Vérifiez que les trois ordinateurs sont sur **le même** wifi (pas un réseau « invité » qui isole les appareils).
- Tous les joueurs doivent être en **1.21.1**.

Le jeu démarre quand les trois voyageurs sont arrivés.

## 4. Conseils

- Journal de quête : touche **L** (Progrès) › onglet **Solstice**. Le **Carnet d’enquête** se remplit tout seul.
- Activez les **sous-titres** : Options › Paramètres d’accessibilité › Sous-titres.
- Clic droit (ou gauche) sur les objets et personnages pour interagir : visez bien leur centre.
- Si vous restez bloqués longtemps sur une étape, des **indices** arrivent tout seuls (après 5 puis 8 minutes).

## 5. Commandes de secours (hôte, commandes activées)

À taper dans le chat (touche T) :

| Commande | Effet |
|---|---|
| `/function solstice:debug/reset_salle` | Réinitialise la salle en cours (en cas de blocage). |
| `/function solstice:debug/salle_suivante` | Passe à la salle suivante. |
| `/function solstice:debug/joueurs_1` | Lancer / jouer à 1 joueur (test). |
| `/function solstice:debug/joueurs_2` | Lancer / jouer à 2 joueurs (test). |
| `/function solstice:debug/joueurs_3` | Revenir au réglage normal à 3 joueurs. |
| `/function solstice:debug/aller_salle_0` … `aller_salle_7` | Aller directement à une salle. |
| `/function solstice:debug/nouvelle_partie` | Tout recommencer depuis le prologue. |

Le mode 1 ou 2 joueurs sert à tester : certaines épreuves sont pensées pour trois.

## 6. Prism Launcher (optionnel)

`Solstice-1.0.mrpack` : Prism › **Ajouter une instance › Importer** › choisissez le fichier. Il contient Fabric,
Sodium, Lithium et Mod Menu (confort uniquement), le monde et le resource pack. Les autres joueurs peuvent rester
sur le launcher officiel en vanilla.

Bonne partie, et méfiez-vous du temps qui passe.
