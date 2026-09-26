# Salle 6 — Les Quatre Saisons (document de conception, contient les solutions)

La même vallée existe en 4 exemplaires (z = 0, 200, 400, 600) : Printemps, Été, Automne, Hiver. Biomes
(`fillbiome`) : cherry_grove, plains, wooded_badlands (feuillage roux), snowy_plains.

**Voyager** : Cadran des Saisons (horloge) en main + s’accroupir ~½ s → saison suivante, même position
(atterrissage sûr : on remonte jusqu’à 12 blocs, sinon Cercle d’arrivée). Chacun voyage seul : le groupe peut
être éclaté entre les saisons.

**But** : rendre les 4 cristaux à leurs autels (centre de la vallée), **dans l’ordre des saisons**, puis faire
sonner les 4 cloches ensemble (3 joueurs + le Sablier du Solstice qui sonne tout seul après 30 s).

**Règle d’anticipation** : rendre un cristal **fige sa saison** (plus aucune action n’y est possible). Il faut donc
avoir tout fait dans une saison avant d’y rendre son cristal. Erreur → Sablier de Remontée (reset complet de la
vallée, 30 s d’immobilité) : on n’est jamais bloqué.

## Chaînes de propagation (le datapack régénère les structures dépendantes)
| cristal | chaîne | saisons |
|---|---|---|
| Printemps | Bourgeon de cristal (verger, printemps) déposé dans le Coffre du Temps au printemps → il grossit dans le coffre d’été → mûr (= cristal) dans le coffre d’automne | P → É → A |
| Automne | Gland d’horloge (tas de feuilles, automne) planté dans la terre fertile au printemps → arbre adulte en été → vieil arbre en automne, abattu à la Hache de Lise (atelier de Lise, hiver) → tronc couché = pont au-dessus du ravin (automne et hiver) → cristal sur le plateau nord | A → P → É → A (+H) |
| Hiver | Vanne tournée (4 tours) en été → le canal remplit le bassin (été), étang (automne), **lac gelé** en hiver → on marche jusqu’à l’îlot | É → A → H |
| Été | Braise prise à la Flamme éternelle d’été **dans la Lanterne** (60 s) → brasero devant la grotte gelée en hiver ; pendant qu’il brûle, un coéquipier actionne le **soufflet** de la forge d’été (action simultanée dans 2 saisons) → la glace fond → cristal dans la grotte | É + H |

Pièges d’anticipation : rendre le cristal du Printemps avant d’avoir planté le gland ; rendre celui de l’Été avant
d’avoir tourné la vanne. Les inscriptions du Cercle le laissent deviner (« Ce que le Printemps n’a pas semé,
l’Automne ne l’abattra pas »…) ; les indices progressifs le disent plus clairement.

Indice d’enquête : la **lettre de Lise**, dans son atelier, en été.

## Énigmes (registre)
- `season-plant-propagation` — planter au printemps, abattre en automne pour faire un pont.
- `season-aging-chest` — déposer un objet dans le passé, le récupérer vieilli dans le futur.
- `season-water-freeze` — détourner l’eau en été pour marcher sur la glace en hiver.
- `season-heat-bellows` — transporter une braise d’une saison à l’autre, avec action simultanée dans deux saisons.
- `season-order-lock` — ordre de restitution qui fige les saisons (anticipation).
- `season-chord-hourglass` — sonner 4 cloches ensemble dans 4 saisons avec 3 joueurs et un sablier.
