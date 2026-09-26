# Décisions (choix pris en autonomie)

1. **Outillage** copié depuis Fragments (fetch, server, RCON, lint, NBT, PNG pur Python, package, report),
   puis adapté. Fragments n’est pas modifié. Le cache (Java Mojang 21, server.jar, Fabric, Carpet) est copié
   par `ditto` dans `cache/` : aucun téléchargement nécessaire, aucune installation système.
2. **pack_format** relus dans `version.json` du server.jar 1.21.1 : données 48, ressources 34. Le lint le revérifie.
3. **Monde livré construit par un serveur vanilla** (server.jar seul, sans Fabric) : `level.dat` et les données du
   monde ne contiennent aucune trace de mod. Les tests tournent sur une **copie** du monde, sur un serveur
   Fabric + Carpet (3 joueurs factices). Carpet ne dépend que du loader Fabric : pas de Fabric API, pas de Lithium
   dans les tests, pour rester au plus près du vanilla.
4. **Monde vide** (superflat « the_void »), salles espacées de 1000 blocs : on ne peut physiquement pas revenir
   en arrière. Chaque salle a une boîte de sécurité ; tout joueur hors de la boîte est ramené au checkpoint.
5. **Progression = un seul compteur global `#room`**. Un joueur dont la salle diffère de `#room` est
   automatiquement remis dans la salle courante (retardataire, reconnexion, mort). Aucune porte de retour n’existe.
6. **Tirages au sort sans `@r` ni `limit=1`** : chaque joueur tire un nombre aléatoire (`random value`), son rang
   parmi les présents donne son rôle. Égalités re-tirées. Audit du lint conservé et durci.
7. **Mode debug 1 ou 2 joueurs** (`#need`) : les rôles vacants sont donnés à tous les présents (étiquettes de rôle
   cumulables) ou joués par « l’automate d’Orel » quand la salle l’exige physiquement (parcours séparés de la tour).
   Les actions « simultanées » ont une fenêtre de 60 s au lieu de 3 s en mode debug.
8. **Pas de resource pack dans le monde** (`resources.zip`) : en LAN il n’est pas transmis ; il est livré à part et
   chaque joueur l’installe. Tout reste lisible sans lui (objets vanilla nommés : lanterne, horloge, papier…).
9. **Mode aventure partout** : les actions sur le monde passent par des entités `interaction` (clic droit/gauche),
   des boutons et des leviers. Fiable, et simulable par les joueurs factices Carpet (`look at` + `use`/`attack`).
10. **Dégâts de chute désactivés** ; seules les salles de combat (4 et 7) peuvent tuer. Faim neutralisée
    (saturation). Dans les salles de combat, la régénération naturelle est coupée : le Guérisseur compte.
11. **Morts** : réapparition immédiate au checkpoint ; dans les salles de combat, 10 s en spectateur d’un
    coéquipier. « Groupe anéanti » = tous les présents à terre en même temps → réinitialisation de la salle.
12. **Checkpoints d’étape dans les salles longues** : un anéantissement réinitialise proprement la salle
    (monstres, mécanismes, rôles re-tirés) mais conserve les étapes déjà franchies (Siège : l’étape en cours
    recommence ; Cœur : le combat recommence, le vote est conservé). Refaire 18 minutes de siège à cause d’un
    seul anéantissement serait punitif ; les salles terminées ne sont jamais perdues.
13. **Assemblage de la Lanterne par datapack** plutôt que par recette vanilla : une recette ne peut ni exiger
    3 joueurs simultanés, ni vérifier les composants custom d’un ingrédient (1.21.1 : ingrédients = types/tags).
14. **Une seule Lanterne** pour le groupe (objet unique). Le datapack garantit qu’il en existe exactement une parmi
    les présents : si son porteur se déconnecte, elle passe à un coéquipier ; au retour, pas de doublon.
15. **Carnet d’enquête** = livre écrit régénéré par une table de loot conditionnelle (une page par indice trouvé).
16. **Difficulté** : si le monde est en Paisible, le datapack passe en Normal (sinon le Siège et le Cœur n’ont
    plus de monstres) et le signale.
17. **Apparence de Maître Orel = skin joueur porté par un noyé (drowned) retexturé** par le resource pack
    (`skin.png` 64x64 à la racine → `src/gen/skin.py`, Python pur). Vanilla 1.21.1 sans mod : pas d’entité
    mannequin, pas de CIT ; une tête de joueur exigerait une texture hébergée par Mojang. Choix du mob :
    zombie et husk sont des ennemis (Express, Siège, Cœur) et leurs membres gauches sont le miroir des droits ;
    le **noyé** n’apparaît nulle part et son modèle suit exactement un skin joueur 64x64 (bras et jambe gauches
    distincts en 32,48 / 16,48, bras de 4 px, chapeau gonflé de 0,5). Les calques veste / manches / pantalon vont
    dans `drowned_outer_layer.png` (même modèle gonflé de 0,25, comme chez le joueur) ; les zones de base sont
    rendues opaques comme le fait le client pour un skin ; un skin « fin » (bras de 3 px) est élargi à 4 px.
    PNJ : `NoAI`, `Silent`, `Invulnerable`, `PersistenceRequired`, mains et armure vides explicites (pas de trident
    tiré au hasard), mêmes étiquettes, même zone cliquable et mêmes répliques qu’avant.
    **Soleil** : vérifié sur serveur vanilla, un noyé `NoAI` brûle en plein jour (épilogue). Une barrière au-dessus
    ne suffit pas, l’éteindre à chaque tick laisse passer des flammes ; un bloc plein qui coupe le ciel supprime
    toute combustion → **auvent de l’horloger** (planches d’épicéa sur un poteau, lanterne suspendue) au-dessus de lui.
    **Paisible** supprime tout monstre, même persistant : toutes les secondes au village (et à l’épilogue), le datapack
    repasse en Normal (décision 16) et fait réapparaître Orel si sa zone cliquable est là mais lui absent.
    Limites : sans le resource pack on voit un noyé nommé « Maître Orel » ; posture de zombie (bras tendus devant),
    propre au modèle et non modifiable sans mod.
18. **Un rôle ne vaut que pour la salle où il a été tiré** (`sol.rroom`) : un joueur absent au tirage ou revenant
    d’une salle précédente ne garde jamais un rôle périmé ; à son arrivée, il prend un rôle vacant s’il y en a.
19. **Zones cliquables** : largeur ≥ 1,25 et base légèrement sous le bloc quand elles couvrent un bloc plein (à
    distance égale, le jeu vise le bloc). Posées *sur* le plateau quand plusieurs zones sont côte à côte (établi).
20. **Démarrage d’une salle différé tant que sa zone n’est pas chargée** : sur une machine lente, créer les entités
    d’une salle dans un chunk non chargé les perdrait. Les joueurs attendent la fin du chargement en transition.
21. **Express du Solstice** : le train est un décor fixe ; le mouvement est simulé (décor qui défile, fumée, sons,
    distance en bossbar). Les évènements (bifurcations, barrières, zones lentes, tunnel, Brumeux) sont placés sur
    9 tronçons ; une erreur ramène au début du tronçon. Les Brumeux ne font aucun dégât.
22. **Quatre Saisons** : l’anticipation est imposée par une règle annoncée en jeu (détail :
    `design/SPOILERS_NE_PAS_LIRE/SALLE6_SAISONS.md`). Un moyen de remonter le temps, coûteux, remet toute la vallée à
    zéro : on n’est jamais bloqué. Les objets trouvés dans la vallée sont « de groupe » (une copie par joueur).
23. **Biomes des vallées** appliqués par RCON au build, réponse vérifiée (et non dans une fonction où un échec
    passerait inaperçu). Le test structurel lit un point éloigné du bord : le jeu lisse les biomes avec un décalage
    aléatoire dépendant de la graine.
24. **Siège** : les zones à éviter testent le bloc exactement sous les pieds du joueur (et non sa boîte de collision,
    qui déborde sur les cases voisines). Les gardiens ne lâchent de butin que lorsque c’est utile à une étape.
25. **Finale** : un bon choix ajoute une aide pendant le combat et un épilogue plus complet ; un mauvais choix rend le
    combat plus dur (plus d’adversaires, plus rapides). La vérité est révélée dans les deux cas. Un anéantissement
    relance le combat, jamais le vote. (Histoire complète : `design/SPOILERS_NE_PAS_LIRE/HISTOIRE.md`.)
26. **`.mrpack` optionnel** : il référence le loader Fabric et des mods de confort téléchargés depuis Modrinth (c’est
    ce que demande Prism) ; il ne contient ni Carpet ni outil de test, et le monde qu’il embarque est le même monde
    vanilla que `Solstice-world.zip`. Le livrable principal reste le monde vanilla.
27. **Journal : tous les indices sont des advancements cachés** (ils apparaissent quand on les trouve) ; titres et
    descriptions neutres pour tout ce qui touche à la salle 5.
