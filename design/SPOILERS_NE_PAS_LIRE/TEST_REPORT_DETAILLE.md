# Rapport de tests DÉTAILLÉ (SPOILERS : solutions et enquête)

## Scénarios E2E

### général — 1/1

- ✅ serveur : toutes les zones de jeu chargées

### prologue — 22/22

- ✅ Bot1 arrive : dans le prologue (sol.room = 0)
- ✅ Bot1 au point d’apparition
- ✅ mode aventure
- ✅ Carnet d’enquête reçu
- ✅ advancement racine accordé
- ✅ 2 joueurs : le jeu attend toujours (#step = 0)
- ✅ bossbar : compteur de voyageurs
- ✅ 3 joueurs présents : la cinématique d’Orel démarre
- ✅ fin de la cinématique : exploration libre (#step = 2)
- ✅ clic réel sur Maître Orel → réplique
- ✅ Maître Orel : PNJ à skin présent (un seul noyé)
- ✅ Maître Orel en plein jour : ne brûle pas (auvent)
- ✅ mode Paisible : repassé en Normal, Maître Orel toujours là
- ✅ clic réel sur Lise → réplique
- ✅ horloge figée cliquée → indice « minuit »
- ✅ indice « minuit » : journal accordé aux 3
- ✅ indice « minuit » inscrit dans le Carnet de chacun
- ✅ flaque d’encre repérée → indice « encre »
- ✅ 2 joueurs sur le quai : le train attend
- ✅ le 3e monte : départ (transition)
- ✅ prologue → salle 1 : téléportation automatique des 3
- ✅ advancement « Brumeval » accordé aux 3

### tirages au sort — 4/4

- ✅ 30 tirages : chaque joueur a toujours un rôle unique (1, 2, 3)
- ✅ 30 tirages : chaque joueur obtient le rôle 1 au moins une fois (hasard réel)
- ✅ aucun rôle vacant à 3 joueurs
- ✅ 20 tirages avec exclusion : le rôle 1 change toujours de joueur

### salle 1 : rôles — 9/9

- ✅ tirage au sort : trois rôles distincts (Aiguilleur, Chauffeur, Garde)
- ✅ Bot1 (Garde) à son poste
- ✅ Bot2 (Chauffeur) à son poste
- ✅ Bot3 (Aiguilleur) à son poste
- ✅ le Garde reçoit le balai et la feuille de route
- ✅ les autres n’ont pas la feuille de route
- ✅ 4 nouveaux tirages : toujours 3 rôles distincts, kit du Garde suivi
- ✅ les rôles changent vraiment d’un tirage à l’autre
- ✅ salle 1 : retour au village impossible (renvoyé dans la salle 1)

### salle 1 : postes — 9/9

- ✅ fin de l’introduction : le train roule (tronçon 1)
- ✅ poste réservé : l’Aiguilleur ne peut pas charger la chaudière
- ✅ Chauffeur : une pelletée prise au tender
- ✅ Chauffeur : charbon dans la chaudière → pression +15
- ✅ Chauffeur : soupape → pression −20
- ✅ Aiguilleur : voie de droite
- ✅ Aiguilleur : voie de gauche
- ✅ poste réservé : le Garde ne touche pas à l’aiguillage
- ✅ indice « marteau » trouvé dans le tender

### salle 1 : départ naturel — 5/5

- ✅ le train démarre de lui-même
- ✅ départ : le panneau annonce le premier passage à niveau
- ✅ barrière restée fermée : le train recule
- ✅ après le recul, le panneau se réaffiche
- ✅ chaudière : la pelletée est acceptée même hors de la main

### salle 1 : évènements — 16/16

- ✅ passage à niveau sans barrière ouverte → erreur
- ✅ …le train recule au début du tronçon
- ✅ le panneau annonce le passage à niveau (manivelle active)
- ✅ Garde : 3 tours de manivelle → barrière ouverte
- ✅ passage à niveau franchi sans erreur
- ✅ bifurcation : mauvaise voie → erreur et recul
- ✅ bifurcation : l’Aiguilleur règle la bonne voie → passage
- ✅ zone lente franchie trop vite → déraillement (erreur)
- ✅ zone lente à pression basse → pas d’erreur
- ✅ tunnel en montée sans pression → erreur
- ✅ tunnel à pleine pression → passage
- ✅ 3 Brumeux montent à bord
- ✅ les Brumeux ne blessent pas (dégâts 0)
- ✅ Brumeux jetés par-dessus bord → disparus
- ✅ surpression (> 100) → erreur
- ✅ chaudière éteinte 6 s → erreur

### salle 1 : morts et reconnexion — 7/7

- ✅ le Chauffeur meurt → revient à son poste, avec son rôle
- ✅ …dans la cabine
- ✅ le Garde se reconnecte → rôle conservé
- ✅ …remis à l’arrière du train
- ✅ …avec son balai et sa feuille de route
- ✅ les 3 à terre → groupe relevé, train ramené au début du tronçon
- ✅ rôles conservés après l’anéantissement

### salle 1 : parcours complet — 24/24

- ✅ évènement 0 (cross) franchi sans erreur
- ✅ évènement 1 (board) franchi sans erreur
- ✅ évènement 2 (fork) franchi sans erreur
- ✅ évènement 3 (lim_on) franchi sans erreur
- ✅ évènement 4 (lim_off) franchi sans erreur
- ✅ évènement 5 (cross) franchi sans erreur
- ✅ évènement 6 (board) franchi sans erreur
- ✅ évènement 7 (fork) franchi sans erreur
- ✅ évènement 8 (board) franchi sans erreur
- ✅ évènement 9 (tunnel) franchi sans erreur
- ✅ évènement 10 (fork) franchi sans erreur
- ✅ évènement 11 (cross) franchi sans erreur
- ✅ évènement 12 (lim_on) franchi sans erreur
- ✅ évènement 13 (lim_off) franchi sans erreur
- ✅ évènement 14 (board) franchi sans erreur
- ✅ évènement 15 (fork) franchi sans erreur
- ✅ évènement 16 (cross) franchi sans erreur
- ✅ évènement 17 (fork) franchi sans erreur
- ✅ évènement 18 (arrive) franchi sans erreur
- ✅ parcours complet sans erreur
- ✅ terminus : transition vers la Tour
- ✅ défi « Voie royale » (aucune erreur) accordé
- ✅ salle 1 → 2 : téléportation automatique
- ✅ les objets du train ne suivent pas

### salle 2 : niveau 1 — 14/14

- ✅ tirage : chaque joueur a son puits (Cuivre, Laiton, Fer)
- ✅ Bot1 au pied de son puits (Fer)
- ✅ Bot2 au pied de son puits (Cuivre)
- ✅ Bot3 au pied de son puits (Laiton)
- ✅ toutes les grilles sont fermées au départ
- ✅ salle 2 : retour au village impossible (renvoyé dans la salle 2)
- ✅ mécanisme réservé : un joueur d’un autre puits ne peut pas l’actionner
- ✅ A1 (cadrans) : aiguilles réglées sur le motif affiché chez le Laiton → résolu
- ✅ …et c’est la grille du LAITON (niveau 1) qui s’ouvre
- ✅ B1 : mauvais nombre → rien
- ✅ B1 (compter 6 étoiles chez le Fer) → résolu, grille du FER ouverte
- ✅ C1 : mauvais gabarit → blocage de 5 s
- ✅ C1 (gabarit identique au modèle du Cuivre) → résolu, grille du CUIVRE ouverte
- ✅ niveau 1 terminé : étape 2

### salle 2 : niveau 2 — 7/7

- ✅ montée : checkpoint individuel au niveau 2
- ✅ A2 (vitrail : deux couleurs dans l’ordre) → résolu, grille du FER ouverte
- ✅ B2 : mauvais code recraché, bon code (inscription du Fer + table du Cuivre) → résolu
- ✅ …grille du CUIVRE (niveau 2) ouverte
- ✅ C2 (cuves 5 L / 3 L → 1 L) → résolu, grille du LAITON ouverte
- ✅ indice « graines » trouvé dans le puits du Fer
- ✅ niveau 2 terminé : étape 3

### salle 2 : morts et reconnexion — 4/4

- ✅ mort : le Laiton réapparaît à SON niveau (2), dans son puits
- ✅ reconnexion : le Fer garde son puits
- ✅ …et revient à son niveau (2)
- ✅ les 3 à terre : groupe relevé, énigmes résolues conservées

### salle 2 : niveau 3 et sommet — 10/10

- ✅ A3 : mauvaise combinaison → court-circuit, blocage
- ✅ A3 (leviers selon le schéma du Laiton) → résolu, grille du LAITON ouverte
- ✅ B3 : foncer dans un mur → retour au départ
- ✅ B3 (guidé par la fresque du Fer) → palet sur l’émeraude, grille du FER ouverte
- ✅ C3 (toutes les lampes rallumées) → résolu, grille du CUIVRE ouverte
- ✅ tous les mécanismes résolus : direction le sommet
- ✅ 2 joueurs sur 3 au sommet : on attend le troisième
- ✅ les 3 réunis au sommet → salle terminée
- ✅ défi « Horlogerie fine » (< 12 min) accordé
- ✅ salle 2 → 3 : téléportation automatique

### salle 3 : missions — 16/16

- ✅ tirage : une mission différente par joueur
- ✅ salle 3 : retour au village impossible (renvoyé dans la salle 3)
- ✅ porte réservée : un autre joueur ne peut pas entrer dans le Grenier
- ✅ le joueur du Grenier y est téléporté
- ✅ le joueur de la Cave y est téléporté
- ✅ le joueur du Cabinet y est téléporté
- ✅ Grenier : 8 poussées réelles, chaque caisse avance dans la direction du regard
- ✅ Grenier : les deux caisses sur les dalles d’or → vitrine ouverte
- ✅ Grenier : pièce « Cage de laiton » récupérée
- ✅ Cave : la boîte à musique joue la mélodie
- ✅ Cave : fausse note → on recommence la manche
- ✅ Cave : trois mélodies rejouées → vitrine ouverte
- ✅ Cave : pièce « Mèche éternelle » récupérée
- ✅ Cabinet : miroirs orientés → la lumière atteint la cible
- ✅ Cabinet : pièce « Verre de lune » récupérée
- ✅ trois pièces rapportées : étape « assemblage »

### salle 3 : morts et reconnexion — 4/4

- ✅ mort : retour à l’atelier, la pièce est conservée
- ✅ reconnexion : mission et pièce conservées
- ✅ …remis dans l’atelier
- ✅ les 3 à terre : relevés, les pièces restent en poche

### salle 3 : assemblage et Lanterne — 7/7

- ✅ pose d’une pièce sur l’établi (elle quitte l’inventaire)
- ✅ deux pièces seulement : elles retombent, rendues à leurs porteurs
- ✅ pas de Lanterne sans les trois
- ✅ les trois pièces posées ensemble → Lanterne des Saisons assemblée
- ✅ une seule Lanterne pour le groupe
- ✅ porteur déconnecté : la Lanterne passe à un coéquipier
- ✅ porteur revenu : toujours une seule Lanterne

### salle 3 : encre invisible — 10/10

- ✅ Lanterne en main : l’encre invisible apparaît près du porteur
- ✅ …et disparaît quand la Lanterne s’éloigne
- ✅ sous l’établi, à la Lanterne : indice « mot »
- ✅ passage secret révélé derrière les étagères
- ✅ dans l’alcôve, à la Lanterne : indice « plan »
- ✅ mauvaise lettre : le plancher grince, on recommence
- ✅ lettres TEMP : le mot se forme
- ✅ mot TEMPS épelé → la grande horloge s’ouvre, salle terminée
- ✅ salle 3 → 4 : téléportation automatique
- ✅ la Lanterne suit le groupe (objet permanent)

### salle 4 : rôles et équipement — 12/12

- ✅ salle 4 : retour au village impossible (renvoyé dans la salle 4)
- ✅ sceau I après l’introduction
- ✅ tirage : Guérisseur, Chevalier, Tank distincts
- ✅ Guérisseur : bâton de soin
- ✅ Chevalier : épée
- ✅ Tank : cor de provocation et bouclier
- ✅ Tank : 30 points de vie
- ✅ vagues : des gardiens attaquent
- ✅ régénération naturelle coupée (le soin compte)
- ✅ Guérisseur : le bâton soigne les alliés proches
- ✅ …puis se recharge (10 s)
- ✅ Tank : le cor le rend lumineux (provocation)

### salle 4 : sceaux I à III — 13/13

- ✅ mécanisme réservé : le Chevalier ne peut pas toucher les piliers
- ✅ sceau I : mauvais pilier → l’ordre repart de zéro
- ✅ sceau I : trois glyphes dans l’ordre lu par le Guérisseur → brisé
- ✅ les gardiens reculent (arène vidée)
- ✅ sceau II commence
- ✅ nouveau tirage : le Guérisseur a changé de joueur
- ✅ sceau II : le Chevalier seul sur sa dalle ne suffit pas
- ✅ sceau II : Chevalier et Tank sur les dalles annoncées 3 s → brisé
- ✅ sceau III commence
- ✅ le Guérisseur change encore
- ✅ sceau III : mauvaise statue → des gardiens surgissent
- ✅ le Gardien des Jardins lâche un gant → indice « gant »
- ✅ sceau III : la bonne statue → brisé

### salle 4 : morts, anéantissement, reconnexion — 7/7

- ✅ sceau IV commence
- ✅ le Chevalier tombe → spectateur d’un coéquipier
- ✅ 10 s plus tard : de retour, avec son épée
- ✅ le Tank se reconnecte : rôle, cor et 30 PV restaurés
- ✅ les 3 à terre → arène vidée, groupe relevé
- ✅ le sceau en cours recommence (les sceaux brisés le restent)
- ✅ …avec un nouveau tirage des rôles

### salle 4 : sceaux IV à VI — 15/15

- ✅ sceau IV : le Guérisseur lit le Registre → indice « registre »
- ✅ sceau IV : un brasero décrit s’allume
- ✅ sceau IV : mauvais brasero → tous s’éteignent
- ✅ sceau IV : les deux braseros décrits → brisé
- ✅ sceau V commence
- ✅ sceau V : dalle piégée → renvoyé à l’entrée de l’annexe
- ✅ sceau V : le chemin sûr (vu du seul Guérisseur) se traverse sans piège
- ✅ sceau V : levier atteint → brisé
- ✅ sceau VI commence
- ✅ sceau VI : les gardiens abattus lâchent os, fils et cendres
- ✅ sceau VI : offrande incomplète → refus
- ✅ sceau VI : offrande complète → les six sceaux sont brisés
- ✅ défi « Rempart » refusé (il y a eu des morts)
- ✅ salle 4 → 5 : téléportation automatique
- ✅ équipement de rôle retiré en quittant le Sanctuaire

### salle 6 : voyage — 13/13

- ✅ les 3 joueurs sont dans la salle 6
- ✅ Bot1 au point d’arrivée de la salle 6
- ✅ Bot2 au point d’arrivée de la salle 6
- ✅ Bot3 au point d’arrivée de la salle 6
- ✅ chacun reçoit un Cadran des Saisons
- ✅ vallée remise à zéro à l’entrée (aucun cristal rendu)
- ✅ Cadran + accroupi : Printemps → Été, même position (z + 200)
- ✅ saison du joueur mise à jour (Été)
- ✅ les autres joueurs restent au Printemps (groupe éclaté possible)
- ✅ Hiver → Printemps (cycle)
- ✅ sans le Cadran en main, s’accroupir ne fait rien
- ✅ salle 6 : retour au village impossible (renvoyé dans la salle 6)
- ✅ chute dans le ravin (Automne) → retour au Cercle de l’Automne

### salle 6 : anticipation — 15/15

- ✅ bourgeon cueilli au printemps → chacun en a une copie
- ✅ bourgeon déposé dans le Coffre du Temps (printemps), retiré des sacs
- ✅ propagation : en été, le coffre montre un bourgeon qui a grossi
- ✅ propagation : en automne, le bourgeon a mûri → Cristal du Printemps
- ✅ premier clic = avertissement, second = cristal du Printemps rendu
- ✅ le cristal quitte les sacs de tous
- ✅ gland trouvé en automne
- ✅ Printemps figé : impossible de planter
- ✅ impasse détectée et annoncée (le Sablier de Remontée est proposé)
- ✅ Sablier de Remontée : 1er clic = confirmation demandée
- ✅ 2e clic : toute la vallée revient au début
- ✅ remontée : objets de la vallée retirés des sacs
- ✅ remontée : coûteuse (joueurs figés)
- ✅ remontée comptée (le défi « sans sablier » est perdu)
- ✅ remontée : tout le monde au Cercle du Printemps

### salle 6 : propagations — 38/38

- ✅ gland planté au printemps
- ✅ printemps : pousse de chêne
- ✅ propagation : en été, un chêne adulte (tronc de 7 blocs)
- ✅ propagation : en automne, un vieux chêne
- ✅ pas encore de pont (automne)
- ✅ atterrissage sûr : on ne se retrouve jamais dans un tronc (posé au-dessus)
- ✅ hache trouvée en hiver (atelier de Lise)
- ✅ en été, le chêne est trop jeune pour être abattu
- ✅ 3 coups de hache en automne → le chêne tombe
- ✅ propagation : pont de bois au-dessus du ravin en automne
- ✅ propagation : le pont existe aussi en hiver (enneigé)
- ✅ …mais pas au printemps ni en été (le passé)
- ✅ la hache disparaît une fois utilisée
- ✅ on peut reprendre le bourgeon du coffre tant qu’il n’a pas mûri
- ✅ en été, le coffre ne rend rien (pas encore mûr)
- ✅ automne : Cristal du Printemps récupéré, pour tout le groupe
- ✅ avant la vanne : bassin vide en hiver
- ✅ vanne tournée 4 fois en été → ouverte
- ✅ propagation : en été, le bassin se remplit
- ✅ propagation : en automne, un étang
- ✅ propagation : en hiver, un lac gelé (on marche dessus)
- ✅ le printemps n’est pas touché (le passé)
- ✅ cristal du Printemps rendu (1/4)
- ✅ la Lanterne est bien dans le groupe
- ✅ brasero d’hiver sans braise : rien
- ✅ Flamme éternelle (été) : la Lanterne capture une braise
- ✅ braise portée en hiver → brasero allumé
- ✅ sans soufflet, la glace ne fond pas
- ✅ soufflet actionné en été PENDANT que le brasero brûle en hiver → la glace fond
- ✅ propagation : la grotte d’hiver est ouverte
- ✅ Cristal de l’Été récupéré dans la grotte
- ✅ cristal de l’Été rendu (2/4) — l’Été est figé
- ✅ Été figé : le soufflet ne fait plus rien
- ✅ Cristal de l’Automne récupéré sur le plateau (derrière le pont)
- ✅ cristal de l’Automne rendu (3/4)
- ✅ Cristal de l’Hiver récupéré sur l’îlot (lac gelé)
- ✅ cristal de l’Hiver rendu (4/4)
- ✅ étape finale : les cloches (#step = 4)

### salle 6 : morts et reconnexion — 8/8

- ✅ mort : le joueur reste dans la salle, progression intacte
- ✅ mort : pas de spectateur hors combat
- ✅ mort : le Cadran est rendu
- ✅ reconnexion : remis dans la salle 6
- ✅ reconnexion : dans une des vallées
- ✅ reconnexion : Cadran rendu
- ✅ les 3 à terre : le groupe est relevé
- ✅ …sans perdre les cristaux rendus

### salle 6 : cloches — 9/9

- ✅ 3 cloches sonnées (printemps, été, automne)…
- ✅ …mais sans l’hiver, l’accord n’est pas complet
- ✅ après la fenêtre, les cloches se taisent (à refaire ensemble)
- ✅ Sablier du Solstice retourné en hiver (30 s)
- ✅ les 3 cloches + le sablier sonnent ensemble → salle terminée
- ✅ défi « sans sablier » non accordé (on a remonté le temps)
- ✅ salle 6 → 7 : téléportation automatique
- ✅ advancement « Les Quatre Saisons » accordé
- ✅ les objets de la vallée ne suivent pas (Cadran retiré)

### salle 7 : accusation — 11/11

- ✅ salle 7 : retour au village impossible (renvoyé dans la salle 7)
- ✅ le tableau d’enquête affiche un panneau par indice trouvé
- ✅ 2 votes sur 3 : on attend le troisième
- ✅ désaccord → votes remis à zéro, il faut se mettre d’accord
- ✅ vote unanime pour Bram → verdict (mauvais choix)
- ✅ branche « mauvais choix » : le combat commence, sans aide
- ✅ branche « mauvais choix » : automates plus nombreux
- ✅ salle rejouée (debug) : retour au vote
- ✅ vote unanime pour Ysolde → bon choix
- ✅ défi « Fin limier » (bon coupable du premier coup) accordé
- ✅ branche « bon choix » : Ysolde rejoint le combat

### salle 7 : machine-boss — 17/17

- ✅ phase 1 : un Opérateur tiré au sort
- ✅ la Lanterne révèle le point faible
- ✅ mauvais engrenage → électrocution, compte remis à zéro
- ✅ système « point faible » désactivé
- ✅ phase 2 : un Opérateur tiré au sort
- ✅ mort pendant le combat → spectateur 10 s
- ✅ …puis de retour dans l’arène
- ✅ les 3 à terre → le combat reprend du début, le verdict est conservé
- ✅ l’Opérateur se reconnecte : il le reste
- ✅ système « balancier » désactivé
- ✅ phase 3 : un Opérateur tiré au sort
- ✅ la Lanterne révèle le point faible
- ✅ mauvais engrenage → électrocution, compte remis à zéro
- ✅ système « point faible » désactivé
- ✅ trois systèmes différents
- ✅ l’Opérateur change à chaque phase
- ✅ le Verrou est brisé → fin de partie lancée

### fin de partie — 5/5

- ✅ fin déclenchée (#ended = 1)
- ✅ crédits : advancement final accordé aux 3
- ✅ épilogue : retour à Brumeval (#room = 8)
- ✅ épilogue : les 3 joueurs au village
- ✅ temps de partie compté (#gtime > 0)

### serveur — 1/1

- ✅ aucune erreur/avertissement lié au datapack dans les logs

## Parcours complet et modes spéciaux

### général — 1/1

- ✅ serveur : toutes les zones de jeu chargées

### parcours complet — 19/19

- ✅ 3 joueurs au prologue, la cinématique démarre
- ✅ salle 0 → salle 1 : téléportation automatique des 3
- ✅ salle 1 : impossible de revenir dans les 1 salle(s) précédente(s)
- ✅ salle 1 → salle 2 : téléportation automatique des 3
- ✅ salle 2 : impossible de revenir dans les 2 salle(s) précédente(s)
- ✅ salle 2 → salle 3 : téléportation automatique des 3
- ✅ salle 3 : impossible de revenir dans les 3 salle(s) précédente(s)
- ✅ salle 3 → salle 4 : téléportation automatique des 3
- ✅ salle 4 : impossible de revenir dans les 4 salle(s) précédente(s)
- ✅ salle 4 → salle 5 : téléportation automatique des 3
- ✅ salle 5 : impossible de revenir dans les 5 salle(s) précédente(s)
- ✅ salle 5 → salle 6 : téléportation automatique des 3
- ✅ salle 6 : impossible de revenir dans les 6 salle(s) précédente(s)
- ✅ salle 6 → salle 7 : téléportation automatique des 3
- ✅ salle 7 : impossible de revenir dans les 7 salle(s) précédente(s)
- ✅ ordre des salles strictement croissant 0 → 7
- ✅ crédits : advancement final pour les 3
- ✅ épilogue : retour au village (#room = 8)
- ✅ journal : les 8 salles sont validées

### indices progressifs — 3/3

- ✅ 5 minutes bloqués sur une étape → premier indice
- ✅ 8 minutes → second indice
- ✅ changement d’étape → compteur d’indices remis à zéro

### mode debug à 1 joueur — 4/4

- ✅ à 1 joueur (debug), le prologue démarre seul
- ✅ salle 1 : le joueur seul cumule les trois rôles vacants
- ✅ salle 2 : l’automate d’Orel résout les puits vacants
- ✅ retour au réglage à 3 joueurs

### serveur — 1/1

- ✅ aucune erreur/avertissement lié au datapack dans les logs

(Salle 5 : voir tests_server-test.json dans ce dossier.)
