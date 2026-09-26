"""Salle 4 — Le Siège du Sanctuaire. Six sceaux, six énigmes différentes, sous des vagues de gardiens.
Rôles re-tirés à chaque étape (le Guérisseur change toujours de joueur) : ro1 Guérisseur (seul à lire les
inscriptions et à toucher les mécanismes, bâton de soin), ro2 Chevalier (dégâts), ro3 Tank (encaisse, cor de provocation).
#step 1..6 : sceau en cours · #s4brk > 0 : pause entre deux sceaux · #step 0 : introduction."""
import math

from .core import (V, T, jdump, tellraw, title, orel, narr, actionbar, fill, setblock, text_display, interaction,
                   Item, SC, snbt_str, item_display, sound)
from .flow import obj
from .hints import hint_fn
from .roles import announce
from .build import disc, ring

OX, Y = 4000, 100
CP = (4000.5, 101, 12.5, 180)
R = 17
GATES = [(round(OX + 15 * math.cos(math.radians(a))), round(15 * math.sin(math.radians(a)))) for a in range(0, 360, 60)]
GLYPHS = ["☀", "☾", "✦", "❄", "✹"]
PILLARS = [(round(OX + 9 * math.cos(math.radians(-90 + 72 * k))), round(9 * math.sin(math.radians(-90 + 72 * k)))) for k in range(5)]
PLATES = [("rouge", "red", (OX - 8, -8)), ("verte", "lime", (OX + 8, -8)), ("bleue", "blue", (OX - 8, 8)), ("jaune", "yellow", (OX + 8, 8))]
STATUES = [("bell", (OX, -5)), ("lantern", (OX + 5, 0)), ("clock", (OX, 5)), ("compass", (OX - 5, 0))]
RIDDLES = ["Je n’ai pas de bouche, et pourtant je réveille tout le village.",
           "Plus la nuit est noire, plus je suis utile ; en plein jour, on m’oublie.",
           "J’ai deux aiguilles mais pas de fil, un visage mais pas d’yeux, et je ne m’arrête jamais… sauf la nuit du sabotage.",
           "Je ne marche jamais, et pourtant je montre toujours le même chemin."]
BRAZ = [(round(OX + 13 * math.cos(math.radians(30 + 60 * k))), round(13 * math.sin(math.radians(30 + 60 * k)))) for k in range(6)]
BRAZ_DESC = ["sous la bannière bleue", "sous la bannière rouge", "au bord du bassin", "entre les deux piliers fendus",
             "coiffé d’un crâne", "près du pot de fleurs"]
PAIRS = [(a, b) for a in range(6) for b in range(a + 1, 6)]
LECTERN = (OX + 4, -15)
# plancher piégé 5×5 dans une annexe à l’ouest : case (c, r) → x = OX-20-c, z = -2+r ; entrée côté arène, levier au fond
TRAP_START = (OX - 18.5, 101, 0.5, 90)


def trap_cell(c, r):
    return (OX - 20 - c, -2 + r)
TRAP_PATHS = [[(0, 2), (1, 2), (1, 1), (2, 1), (3, 1), (3, 2), (3, 3), (4, 3)],
              [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (2, 3), (3, 3), (4, 3)],
              [(0, 4), (1, 4), (1, 3), (1, 2), (2, 2), (3, 2), (3, 1), (4, 1)],
              [(0, 1), (1, 1), (2, 1), (2, 2), (2, 3), (2, 4), (3, 4), (4, 4)]]
TRAP_LEVER = (OX - 26, 0)
ROLES = [("Guérisseur", "green", "Vous seul lisez les inscriptions et touchez les mécanismes. Lisez à voix haute !"),
         ("Chevalier", "red", "Frappez ! Protégez le Guérisseur."),
         ("Tank", "blue", "Encaissez. Soufflez dans le cor : les gardiens s’en prennent à vous.")]

GEAR = "*[custom_data~{sol:{gear:1b}}]"


def gear(iid, name, color, lore, extra=None, data="gear:1b"):
    ex = {"unbreakable": "{show_in_tooltip:false}"}
    ex.update(extra or {})
    return Item(iid, name, color, lore=lore, data=f"{{sol:{{{data}}}}}", extra=ex)


STAFF = gear("carrot_on_a_stick", "Bâton de soin", "green", ["Clic droit : soigne les alliés proches.", "Recharge : 10 secondes."],
             data="gear:1b,staff:1b")
SWORD = gear("iron_sword", "Épée du Chevalier", "red", ["Tranchante."], {"enchantments": "{levels:{\"minecraft:sharpness\":2}}"})
SHIELD = gear("shield", "Bouclier du Tank", "blue", ["Clic droit : se protéger."])
HORN = gear("goat_horn", "Cor de provocation", "blue", ["Clic droit : tous les gardiens proches vous prennent pour cible."],
            {"instrument": "\"minecraft:seek_goat_horn\""})
ARMOR = {1: [("armor.chest", gear("leather_chestplate", "Robe du Guérisseur", "green", ["Légère."], {"dyed_color": "{rgb:6536538}"}))],
         2: [("armor.chest", gear("iron_chestplate", "Cuirasse du Chevalier", "red", ["Solide."])),
             ("armor.head", gear("iron_helmet", "Heaume du Chevalier", "red", ["Solide."]))],
         3: [("armor.chest", gear("diamond_chestplate", "Plastron du Tank", "blue", ["Très solide."])),
             ("armor.legs", gear("iron_leggings", "Jambières du Tank", "blue", ["Solides."])),
             ("armor.head", gear("iron_helmet", "Casque du Tank", "blue", ["Solide."]))]}
DROPS = {"os": ("bone", "Os consacré", "white"), "fil": ("string", "Fil d’argent", "gray"), "cendre": ("gray_dye", "Cendre d’ombre", "dark_gray")}
GANT = ("leather", "Gant de jardinière", "yellow")

# étape -> (période, plafond, lot, types)
WAVES = {1: (200, 4, 2, ["zombie"]), 2: (180, 6, 2, ["zombie", "skeleton"]), 3: (160, 7, 3, ["zombie", "skeleton", "spider"]),
         4: (150, 8, 3, ["zombie", "skeleton", "spider", "husk"]), 5: (140, 9, 3, ["zombie", "stray", "spider", "husk"]),
         6: (120, 10, 3, ["zombie", "skeleton", "spider"])}
LOOT_OF = {"zombie": "cendre", "skeleton": "os", "spider": "fil"}


def mob(typ, x, z, step, loot=None, name=None, extra=""):
    lt = f"solstice:siege/{loot}" if loot else "minecraft:empty"
    nm = f"CustomName:'{jdump(T(name, 'yellow'))}',CustomNameVisible:1b," if name else ""
    hp = {"zombie": 20, "skeleton": 20, "spider": 16, "husk": 22, "stray": 20}[typ] + 2 * step
    if typ in ("skeleton", "stray") and "HandItems" not in extra:
        extra += ",HandItems:[{id:\"minecraft:bow\",count:1},{}],HandDropChances:[0f,0f]"
    if typ in ("zombie", "husk"):
        extra += ",IsBaby:0b"
    return (f"summon {typ} {x + 0.5} {Y + 1} {z + 0.5} {{Tags:[\"sol\",\"sol.mob\",\"sol.r4mob\"],PersistenceRequired:1b,"
            f"DeathLootTable:\"{lt}\",{nm}CanPickUpLoot:0b,attributes:[{{id:\"minecraft:generic.follow_range\",base:40d}},"
            f"{{id:\"minecraft:generic.max_health\",base:{hp}d}}],Health:{hp}f{extra}}}")


def build(dp):
    b = ["kill @e[type=!player,tag=sol.r4]"]
    b += fill(OX - 30, 90, -30, OX + 30, 125, 30, "air")
    b += disc(OX, Y - 1, 0, R + 2, "deepslate_bricks")
    b += disc(OX, Y, 0, R, "polished_deepslate")
    b += disc(OX, Y, 0, 4, "chiseled_deepslate")
    b += ring(OX, Y, 0, 7, "deepslate_tiles")
    b += ring(OX, Y, 0, 12, "deepslate_tiles")
    for h in range(1, 12):
        b += ring(OX, Y + h, 0, R + 1, "deepslate_bricks" if h < 11 else "polished_blackstone_brick_wall")
    for (gx, gz) in GATES:     # arches des portes des gardiens
        dx = 1 if gx > OX else (-1 if gx < OX else 0)
        dz = 1 if gz > 0 else (-1 if gz < 0 else 0)
        ex, ez = OX + round(17.5 * (gx - OX) / 15), round(17.5 * gz / 15)
        b += fill(ex - 1, Y + 1, ez - 1, ex + 1, Y + 3, ez + 1, "air")
        b.append(setblock(gx, Y, gz, "crying_obsidian"))
    # piliers-glyphes (étape 1)
    for k, (x, z) in enumerate(PILLARS):
        b += fill(x, Y + 1, z, x, Y + 2, z, "chiseled_stone_bricks")
    # dalles de couleur (étape 2)
    for name, col, (x, z) in PLATES:
        b += fill(x - 1, Y, z - 1, x + 1, Y, z + 1, f"{col}_concrete")
    # statues (étape 3)
    for item, (x, z) in STATUES:
        b.append(setblock(x, Y + 1, z, "polished_andesite"))
    # braseros (étape 4) et leurs détails
    for k, (x, z) in enumerate(BRAZ):
        b.append(setblock(x, Y + 1, z, "campfire[lit=false]"))
        if k == 0:
            b += [setblock(x, Y + 2, z, "polished_blackstone_wall"), setblock(x, Y + 3, z, "blue_banner")]
        elif k == 1:
            b += [setblock(x, Y + 2, z, "polished_blackstone_wall"), setblock(x, Y + 3, z, "red_banner")]
        elif k == 2:
            b += [setblock(x + (1 if x < OX else -1), Y, z, "water"), setblock(x + (1 if x < OX else -1), Y, z + 1, "water")]
        elif k == 3:
            b += [setblock(x, Y + 1, z - 1, "cracked_stone_bricks"), setblock(x, Y + 2, z - 1, "cracked_stone_bricks"),
                  setblock(x, Y + 1, z + 1, "cracked_stone_bricks"), setblock(x, Y + 2, z + 1, "cracked_stone_bricks")]
        elif k == 4:
            b.append(setblock(x, Y + 2, z, "skeleton_skull"))
        elif k == 5:
            b.append(setblock(x + (1 if x < OX else -1), Y + 1, z, "potted_red_tulip"))
    # lutrin du registre
    lx, lz = LECTERN
    b.append(setblock(lx, Y + 1, lz, "lectern[facing=south]"))
    # plancher piégé (étape 5) : annexe ouest (x OX-28..OX-17), ouverture dans le mur de l’arène
    b += fill(OX - 28, Y - 1, -4, OX - 17, Y + 5, 4, "deepslate_bricks")
    b += fill(OX - 27, Y + 1, -3, OX - 17, Y + 4, 3, "air")
    b += fill(OX - 27, Y, -3, OX - 17, Y, 3, "polished_deepslate")
    b += fill(OX - 24, Y, -2, OX - 20, Y, 2, "polished_tuff")
    b += fill(OX - 19, Y + 1, -2, OX - 16, Y + 3, 2, "air")
    b.append(setblock(TRAP_LEVER[0], Y + 1, TRAP_LEVER[1], "polished_blackstone_bricks"))
    b.append(setblock(OX - 22, Y + 4, 0, "soul_lantern[hanging=true]"))
    # autel central
    b.append(setblock(OX, Y + 1, 0, "enchanting_table"))
    b += [setblock(OX + x, Y + 1, z, "lantern") for x, z in ((3, 3), (-3, 3), (3, -3), (-3, -3))]
    dp.meta.setdefault("builds", []).append("build/r4")
    dp.meta.setdefault("forceload", []).append((OX - 30, -30, OX + 30, 30))

    # ------------------------------------------------------------ entités
    e = ["kill @e[type=!player,tag=sol.r4d]"]

    def it(x, y, z, key, w=1.3, h=1.3):
        e.append(interaction(x, y, z, ["sol.r4", "sol.r4d", "sol.r4i", f"sol.k4_{key}"], w, h))
    for k, (x, z) in enumerate(PILLARS):
        it(x + 0.5, Y + 0.95, z + 0.5, f"g{k}", 1.3, 2.2)
        e.append(text_display(x + 0.5, Y + 3.2, z + 0.5, ["", T(GLYPHS[k], "aqua", bold=True)], ["sol.r4", "sol.r4d"], scale=2.0))
    for k, (item, (x, z)) in enumerate(STATUES):
        e.append(f"summon armor_stand {x + 0.5} {Y + 2} {z + 0.5} {{Tags:[\"sol\",\"sol.r4\",\"sol.r4d\"],NoGravity:1b,Invulnerable:1b,"
                 f"ShowArms:1b,NoBasePlate:1b,DisabledSlots:4144959,Rotation:[{[180, 90, 0, -90][k]}f,0f],"
                 f"HandItems:[{{id:\"minecraft:{item}\",count:1}},{{}}],ArmorItems:[{{}},{{}},{{}},{{id:\"minecraft:carved_pumpkin\",count:1}}]}}")
        it(x + 0.5, Y + 0.95, z + 0.5, f"st{k}", 1.3, 3.2)
    for k, (x, z) in enumerate(BRAZ):
        it(x + 0.5, Y + 0.95, z + 0.5, f"b{k}", 1.3, 1.0)
    it(LECTERN[0] + 0.5, Y + 0.95, LECTERN[1] + 0.5, "reg", 1.3, 1.3)
    it(TRAP_LEVER[0] + 0.5, Y + 0.95, TRAP_LEVER[1] + 0.5, "lever", 1.3, 1.6)
    it(OX + 0.5, Y + 0.95, 0.5, "altar", 1.3, 1.3)
    for k in range(6):
        a = math.radians(60 * k)
        e.append(text_display(OX + 0.5 + 2.2 * math.cos(a), Y + 5, 0.5 + 2.2 * math.sin(a), ["", T(["I", "II", "III", "IV", "V", "VI"][k], "gold", bold=True)],
                              ["sol.r4", "sol.r4d", f"sol.seal{k + 1}"], scale=1.4))
    e.append(text_display(lx + 0.5, Y + 2.6, lz + 0.5, ["", T("Registre du Sanctuaire", "gray")], ["sol.r4", "sol.r4d"], scale=0.5))
    dp.fn("r4/entities", e)
    dp.fn("build/r4", b + ["function solstice:r4/entities"])

    # ------------------------------------------------------------ équipement
    for r in (1, 2, 3):
        body = []
        for slot, itm in ARMOR[r]:
            body.append(f"item replace entity @s {slot} with {itm.give()}")
        if r == 1:
            body += [f"give @s {STAFF.give()}", "effect give @s weakness infinite 0 true"]
        elif r == 2:
            body += [f"give @s {SWORD.give()}", "effect give @s strength infinite 0 true"]
        else:
            body += [f"execute unless items entity @s weapon.offhand * run item replace entity @s weapon.offhand with {SHIELD.give()}",
                     f"execute if items entity @s weapon.offhand * unless items entity @s weapon.offhand {SHIELD.id}[custom_data~{{sol:{{gear:1b}}}}] run give @s {SHIELD.give()}",
                     f"give @s {HORN.give()}",
                     "attribute @s minecraft:generic.max_health base set 30", "attribute @s minecraft:generic.knockback_resistance base set 0.6",
                     "effect give @s resistance infinite 0 true"]
        dp.fn(f"r4/gear{r}", body)
    dp.fn("r4/gear", [
        f"clear @s {GEAR}",
        "effect clear @s weakness", "effect clear @s strength", "effect clear @s resistance",
        "attribute @s minecraft:generic.max_health base set 20", "attribute @s minecraft:generic.knockback_resistance base set 0",
        *[f"execute if entity @s[tag=sol.ro{r}] run function solstice:r4/gear{r}" for r in (1, 2, 3)],
        "effect give @s instant_health 1 3 true", "effect give @s saturation infinite 0 true",
    ])

    # ------------------------------------------------------------ butins (étape 6) et gant (indice)
    for key, (iid, name, col) in DROPS.items():
        dp.loot(f"siege/{key}", {"type": "minecraft:entity", "pools": [{"rolls": 1, "entries": [
            {"type": "minecraft:item", "name": f"minecraft:{iid}", "functions": [
                {"function": "minecraft:set_custom_data", "tag": f"{{sol:{{{key}:1b}}}}"},
                {"function": "minecraft:set_name", "target": "item_name", "name": T(name, col)}]}]}]})
    dp.loot("siege/gant", {"type": "minecraft:entity", "pools": [{"rolls": 1, "entries": [
        {"type": "minecraft:item", "name": f"minecraft:{GANT[0]}", "functions": [
            {"function": "minecraft:set_custom_data", "tag": "{sol:{gant:1b}}"},
            {"function": "minecraft:set_name", "target": "item_name", "name": T(GANT[1], GANT[2])}]}]}]})
    dp.json("data/solstice/loot_table/siege/none.json", {"type": "minecraft:entity", "pools": []})

    # ------------------------------------------------------------ vagues
    for step, (per, cap, lot, types) in WAVES.items():
        body = [f"execute store result score #mobs {V} if entity @e[tag=sol.r4mob]",
                f"execute if score #mobs {V} matches {cap}.. run return 0"]
        for n in range(lot):
            body.append(f"execute store result score #g {V} run random value 0..{len(GATES) - 1}")
            body.append(f"execute store result score #ty {V} run random value 0..{len(types) - 1}")
            for gi, (gx, gz) in enumerate(GATES):
                for ti, ty in enumerate(types):
                    loot = LOOT_OF.get(ty) if step == 6 else None
                    body.append(f"execute if score #g {V} matches {gi} if score #ty {V} matches {ti} run " + mob(ty, gx, gz, step, loot))
        body.append(f"execute as @a[tag=sol.ro3] at @s run particle minecraft:angry_villager ~ ~2.3 ~ 0.2 0.1 0.2 0 1")
        dp.fn(f"r4/wave{step}", body)
    dp.fn("r4/wave_tick", [
        f"scoreboard players add #wt {V} 1",
        *[f"execute if score #step {V} matches {s} if score #wt {V} matches {WAVES[s][0]}.. run function solstice:r4/wave_go" for s in WAVES],
    ])
    dp.fn("r4/wave_go", [f"scoreboard players set #wt {V} 0",
                         *[f"execute if score #step {V} matches {s} run function solstice:r4/wave{s}" for s in WAVES],
                         "execute as @a at @s run playsound minecraft:event.raid.horn master @s ~ ~ ~ 0.3 1.4"])
    dp.fn("r4/penalty", [*[mob("zombie", gx, gz, 3) for gx, gz in GATES[:2]],
                         tellraw("@a", T("Le sceau rugit : des gardiens surgissent !", "red"))])

    # ------------------------------------------------------------ déroulé des étapes
    dp.fn("r4/start", [
        "function solstice:r4/entities",
        f"scoreboard players set #step {V} 0", f"scoreboard players set #s4brk {V} 200", f"scoreboard players set #wt {V} 0",
        f"scoreboard players set #r4done {V} 0", "gamerule doMobLoot true",
        "execute as @a run function solstice:player/clear_role",
        "tag @a remove sol.prev",
        obj("Le Sanctuaire s’éveille… préparez-vous"),
        orel("Le Sanctuaire du Calendrier ! Six sceaux gardent le passage, et leurs gardiens n’aiment pas les visiteurs. "
             "Un Guérisseur, un Chevalier, un Tank : seul le Guérisseur sait lire les sceaux. Et les rôles tournent !"),
    ])
    dp.fn("r4/begin", [
        f"scoreboard players add #step {V} 1",
        "tag @a remove sol.prev", "tag @a[tag=sol.ro1,scores={sol.role=1}] add sol.prev",
        f"execute if score #step {V} matches 2.. run scoreboard players set #noheal {V} 1",
        "function solstice:roles/draw", f"scoreboard players set #noheal {V} 0",
        "execute as @a run function solstice:r4/gear",
        "function solstice:r4/announce",
        f"scoreboard players set #wt {V} 100",
        *[f"execute if score #step {V} matches {s} run function solstice:r4/setup{s}" for s in range(1, 7)],
        "function solstice:hints/reset", "function solstice:r4/obj",
        "function solstice:r4/read",
    ])
    announce(dp, "r4/announce", ROLES, "red")
    dp.fn("r4/obj", [f"bossbar set solstice:obj name " + jdump(["", T("◆ ", "gold"), T("Sceau ", "white"), SC("#step", color="gold"),
                                                                T(" / 6 : le Guérisseur lit l’inscription, les autres le protègent", "white")])])
    dp.fn("r4/solved", [
        "kill @e[type=!player,tag=sol.r4mob]",
        *[f"execute if score #step {V} matches {k} run kill @e[type=!player,tag=sol.seal{k}]" for k in range(1, 7)],
        *title("@a", "Sceau brisé !", "Les gardiens reculent…", color="gold", times=(5, 40, 10)),
        sound("minecraft:block.end_portal_frame.fill", "@a", 1, 0.8),
        "particle minecraft:end_rod 4000.5 105 0.5 1.5 1 1.5 0.05 80 force",
        f"scoreboard players set #s4brk {V} 200",
        f"execute if score #step {V} matches 6 run function solstice:r4/finish",
    ])
    dp.fn("r4/finish", [f"scoreboard players set #s4brk {V} 0", f"scoreboard players set #r4done {V} 1",
                        f"execute if score #rdeaths {V} matches 0 run function solstice:challenge/grant_rempart",
                        orel("Six sceaux ! Et je vous entends encore respirer. C’est un excellent signe."),
                        "function solstice:flow/complete"])
    dp.fn("r4/on_complete", ["gamerule doMobLoot false", "kill @e[type=item]",
                             "execute as @a run function solstice:r4/ungear"])
    dp.fn("r4/ungear", [f"clear @s {GEAR}", "attribute @s minecraft:generic.max_health base set 20"])
    # relire l’inscription (Guérisseur) : texte privé
    rd = [tellraw("@a[tag=!sol.ro1]", T("Seul le Guérisseur peut lire l’inscription du sceau. Écoutez-le !", "gray", italic=True))]
    for s in range(1, 7):
        rd.append(f"execute if score #step {V} matches {s} run function solstice:r4/instr{s}")
    dp.fn("r4/read", rd)
    H = "@a[tag=sol.ro1]"
    hdr = lambda s: tellraw(H, T(f"✦ Inscription du sceau {['I', 'II', 'III', 'IV', 'V', 'VI'][s - 1]} ", "green", bold=True),
                            T("(vous seul la voyez — lisez-la à voix haute)", "gray", italic=True))

    # --- étape 1 : glyphes dans l’ordre
    SEQS = [(a, b, c) for a in range(5) for b in range(5) for c in range(5) if len({a, b, c}) == 3][::5]
    dp.fn("r4/setup1", [f"execute store result score #s1q {V} run random value 0..{len(SEQS) - 1}", f"scoreboard players set #s1i {V} 0"] +
          [f"execute if score #s1q {V} matches {i} run function solstice:r4/s1set{i}" for i in range(len(SEQS))])
    for i, sq in enumerate(SEQS):
        dp.fn(f"r4/s1set{i}", [f"scoreboard players set #s1a {V} {sq[0]}", f"scoreboard players set #s1b {V} {sq[1]}", f"scoreboard players set #s1c {V} {sq[2]}"])
    ins1 = [hdr(1)]
    for g in range(5):
        for pos, slot in enumerate("abc"):
            ins1.append(f"execute if score #s1{slot} {V} matches {g} run " + tellraw(H, T(f"   {pos + 1}. touchez le pilier du signe ", "white"), T(GLYPHS[g], "aqua", bold=True)))
    dp.fn("r4/instr1", ins1)
    for g in range(5):
        dp.fn(f"r4/c/g{g}", [
            f"execute unless score #step {V} matches 1 run return 0",
            f"scoreboard players set #want {V} -1",
            f"execute if score #s1i {V} matches 0 run scoreboard players operation #want {V} = #s1a {V}",
            f"execute if score #s1i {V} matches 1 run scoreboard players operation #want {V} = #s1b {V}",
            f"execute if score #s1i {V} matches 2 run scoreboard players operation #want {V} = #s1c {V}",
            f"execute unless score #want {V} matches {g} run return run function solstice:r4/s1_bad",
            f"scoreboard players add #s1i {V} 1", "playsound minecraft:block.amethyst_block.chime master @a ~ ~ ~ 1 1.3",
            "particle minecraft:end_rod ~ ~2 ~ 0.3 0.6 0.3 0.05 20",
            f"execute if score #s1i {V} matches 3 run function solstice:r4/solved"])
    dp.fn("r4/s1_bad", [f"scoreboard players set #s1i {V} 0", "playsound minecraft:block.note_block.bass master @a ~ ~ ~ 1 0.5",
                        tellraw(H, T("Mauvais ordre : le sceau se referme. Recommencez depuis le premier signe.", "red")),
                        "function solstice:r4/penalty"])
    # --- étape 2 : placer les coéquipiers sur des dalles
    dp.fn("r4/setup2", [f"execute store result score #s2k {V} run random value 0..3", f"execute store result score #s2t {V} run random value 0..2",
                        f"execute if score #s2t {V} >= #s2k {V} run scoreboard players add #s2t {V} 1", f"scoreboard players set #s2h {V} 0"])
    ins2 = [hdr(2)]
    for p, (pn, col, _) in enumerate(PLATES):
        ins2.append(f"execute if score #s2k {V} matches {p} run " + tellraw(H, T("   Le Chevalier doit se tenir sur la dalle ", "white"), T(pn.upper(), "gold", bold=True)))
        ins2.append(f"execute if score #s2t {V} matches {p} run " + tellraw(H, T("   Le Tank doit se tenir sur la dalle ", "white"), T(pn.upper(), "gold", bold=True)))
    ins2.append(tellraw(H, T("   …ensemble, pendant 3 secondes.", "white")))
    dp.fn("r4/instr2", ins2)
    chk2 = [f"scoreboard players set #okk {V} 0", f"scoreboard players set #okt {V} 0"]
    for p, (pn, col, (x, z)) in enumerate(PLATES):
        area = f"x={x - 1},y={Y + 1},z={z - 1},dx=2,dy=1,dz=2"
        chk2.append(f"execute if score #s2k {V} matches {p} if entity @a[tag=sol.ro2,tag=!sol.dn,{area}] run scoreboard players set #okk {V} 1")
        chk2.append(f"execute if score #s2t {V} matches {p} if entity @a[tag=sol.ro3,tag=!sol.dn,{area}] run scoreboard players set #okt {V} 1")
    chk2 += [f"execute if score #need {V} matches 1 run scoreboard players set #okt {V} 1",
             f"execute if score #okk {V} matches 1 if score #okt {V} matches 1 run scoreboard players add #s2h {V} 1",
             f"execute unless score #okk {V} matches 1 run scoreboard players set #s2h {V} 0",
             f"execute unless score #okt {V} matches 1 run scoreboard players set #s2h {V} 0",
             f"execute if score #s2h {V} matches 1.. run " + actionbar("@a", ["", T("Le sceau vibre… ", "gold"), SC("#s2h"), T(" / 3", "gray")]),
             f"execute if score #s2h {V} matches 3.. run function solstice:r4/solved"]
    dp.fn("r4/s2_check", chk2)
    # --- étape 3 : devinette → statue
    dp.fn("r4/setup3", [f"execute store result score #s3 {V} run random value 0..3",
                        mob("zombie", GATES[2][0], GATES[2][1], 3, loot="gant", name="Gardien des Jardins",
                            extra=",HandItems:[{id:\"minecraft:iron_hoe\",count:1},{}],HandDropChances:[0f,0f]")])
    ins3 = [hdr(3), tellraw(H, T("   Désignez la statue qui répond à l’énigme :", "white"))]
    for i, rid in enumerate(RIDDLES):
        ins3.append(f"execute if score #s3 {V} matches {i} run " + tellraw(H, T(f"   « {rid} »", "yellow", italic=True)))
    dp.fn("r4/instr3", ins3)
    for k in range(4):
        dp.fn(f"r4/c/st{k}", [f"execute unless score #step {V} matches 3 run return 0",
                              f"execute if score #s3 {V} matches {k} run return run function solstice:r4/solved",
                              tellraw(H, T("La statue reste de pierre. Ce n’était pas la bonne réponse.", "red")),
                              "function solstice:r4/penalty"])
    # --- étape 4 : registre → deux braseros décrits
    dp.fn("r4/setup4", [f"execute store result score #s4 {V} run random value 0..{len(PAIRS) - 1}", f"scoreboard players set #s4n {V} 0",
                        f"scoreboard players set #s4read {V} 0",
                        *[setblock(x, Y + 1, z, "campfire[lit=false]") for x, z in BRAZ]])
    dp.fn("r4/instr4", [hdr(4), tellraw(H, T("   Lisez le Registre du Sanctuaire, sur le lutrin au nord (clic).", "white"))])
    reg = [f"scoreboard players set #s4read {V} 1",
           tellraw("@s", T("Registre du Sanctuaire", "gold", bold=True), T(" — ", "gray"),
                   T("« Dernier passage autorisé au Cœur : Maître Orel, trois jours avant la panne. »", "white", italic=True)),
           "function solstice:story/found_registre",
           tellraw("@s", T("   Pour briser le quatrième sceau, allumez deux braseros :", "white"))]
    for i, (a, bb) in enumerate(PAIRS):
        reg.append(f"execute if score #s4 {V} matches {i} run " + tellraw("@s", T(f"   • le brasero {BRAZ_DESC[a]}\n   • le brasero {BRAZ_DESC[bb]}", "yellow")))
    dp.fn("r4/reg_read", reg)
    dp.fn("r4/c/reg", [f"execute unless score #step {V} matches 4 run return run " + actionbar("@s", "Un vieux registre. Les pages sont collées.", "gray"),
                       "function solstice:r4/reg_read"])
    for k, (x, z) in enumerate(BRAZ):
        targets = [i for i, (a, bb) in enumerate(PAIRS) if k in (a, bb)]
        dp.fn(f"r4/c/b{k}", [f"execute unless score #step {V} matches 4 run return 0",
                             f"execute if block {x} {Y + 1} {z} campfire[lit=true] run return 0",
                             f"scoreboard players set #okb {V} 0",
                             *[f"execute if score #s4 {V} matches {i} run scoreboard players set #okb {V} 1" for i in targets],
                             f"execute if score #okb {V} matches 0 run return run function solstice:r4/s4_bad",
                             setblock(x, Y + 1, z, "campfire[lit=true]"), "playsound minecraft:item.firecharge.use master @a ~ ~ ~ 1 1",
                             f"scoreboard players add #s4n {V} 1", f"execute if score #s4n {V} matches 2 run function solstice:r4/solved"])
    dp.fn("r4/s4_bad", [*[setblock(x, Y + 1, z, "campfire[lit=false]") for x, z in BRAZ], f"scoreboard players set #s4n {V} 0",
                        "playsound minecraft:block.fire.extinguish master @a ~ ~ ~ 1 0.8",
                        tellraw(H, T("Mauvais brasero : tous s’éteignent.", "red")), "function solstice:r4/penalty"])
    # --- étape 5 : plancher piégé (cases sûres visibles du seul Guérisseur)
    dp.fn("r4/setup5", [f"execute store result score #s5 {V} run random value 0..{len(TRAP_PATHS) - 1}"])
    dp.fn("r4/instr5", [hdr(5), tellraw(H, T("   Traversez le plancher piégé de l’annexe ouest, jusqu’au levier du sceau, au fond.", "white")),
                        tellraw(H, T("   Les dalles sûres scintillent… pour vous seul.", "white"))])
    show5 = []
    for pi, path in enumerate(TRAP_PATHS):
        show5 += [f"execute if score #s5 {V} matches {pi} run particle minecraft:happy_villager {trap_cell(c, r)[0] + 0.5} {Y + 1.1} {trap_cell(c, r)[1] + 0.5} 0.25 0 0.25 0 2 force @a[tag=sol.ro1]"
                  for (c, r) in path]
    dp.fn("r4/s5_show", show5)
    # cases piégées marquées SOUS le sol (y-1, invisible) ; test sur le bloc exactement sous les pieds du joueur
    for pi, path in enumerate(TRAP_PATHS):
        paint = []
        for c in range(5):
            for r in range(5):
                tx, tz = trap_cell(c, r)
                paint.append(setblock(tx, Y - 1, tz, "white_concrete" if (c, r) in path else "black_concrete"))
        dp.fn(f"r4/s5_paint{pi}", paint)
    dp.add("r4/setup5", [f"execute if score #s5 {V} matches {pi} run function solstice:r4/s5_paint{pi}" for pi in range(len(TRAP_PATHS))])
    dp.fn("r4/s5_ptick", [f"execute if block ~ ~-1 ~ polished_tuff if block ~ ~-2 ~ black_concrete run function solstice:r4/zap"])
    dp.fn("r4/zap", ["damage @s 3 minecraft:hot_floor", f"tp @s {TRAP_START[0]} {TRAP_START[1]} {TRAP_START[2]} {TRAP_START[3]} 0",
                     "playsound minecraft:entity.generic.burn master @a ~ ~ ~ 1 1",
                     "particle minecraft:flame ~ ~0.2 ~ 0.3 0.1 0.3 0.02 20", actionbar("@s", "Piège ! Retour au bord.", "red")])
    dp.fn("r4/c/lever", [f"execute unless score #step {V} matches 5 run return 0", "function solstice:r4/solved",
                         "playsound minecraft:block.lever.click master @a ~ ~ ~ 1 0.8"])
    # --- étape 6 : offrande (butin des gardiens)
    OFFERS = [(2, 1, 0), (1, 1, 1), (2, 0, 1), (1, 2, 0), (0, 2, 1), (1, 0, 2)]
    dp.fn("r4/setup6", [f"execute store result score #s6 {V} run random value 0..{len(OFFERS) - 1}"] +
          [f"execute if score #s6 {V} matches {i} run function solstice:r4/s6set{i}" for i in range(len(OFFERS))])
    for i, (o, f_, c) in enumerate(OFFERS):
        dp.fn(f"r4/s6set{i}", [f"scoreboard players set #s6os {V} {o}", f"scoreboard players set #s6fil {V} {f_}", f"scoreboard players set #s6cen {V} {c}"])
    dp.fn("r4/instr6", [hdr(6), tellraw(H, T("   L’autel exige une offrande, prise sur les gardiens :", "white")),
                        tellraw(H, T("   Os consacrés : ", "white"), SC("#s6os", color="gold"), T("   Fils d’argent : ", "white"), SC("#s6fil", color="gold"),
                                T("   Cendres d’ombre : ", "white"), SC("#s6cen", color="gold")),
                        tellraw(H, T("   (squelettes → os · araignées → fil · zombies → cendre ; vos compagnons vous les apportent)", "gray"))])
    have = lambda key: f"execute store result score #h{key} {V} run clear @s {DROPS[key][0]}[custom_data~{{sol:{{{key}:1b}}}}] 0"
    dp.fn("r4/c/altar", [
        f"execute unless score #step {V} matches 6 run return run function solstice:r4/read",
        have("os"), have("fil"), have("cendre"),
        f"execute if score #hos {V} >= #s6os {V} if score #hfil {V} >= #s6fil {V} if score #hcendre {V} >= #s6cen {V} run return run function solstice:r4/offer",
        tellraw("@s", T("L’offrande est incomplète. Il vous faut : ", "red"), SC("#s6os"), T(" os, "), SC("#s6fil"), T(" fil(s), "), SC("#s6cen"),
                T(" cendre(s). Vous avez : "), SC("#hos"), T(" / "), SC("#hfil"), T(" / "), SC("#hcendre"))])
    dp.fn("r4/offer", [*[f"clear @s {DROPS[k][0]}[custom_data~{{sol:{{{k}:1b}}}}]" for k in DROPS],
                       "playsound minecraft:block.enchantment_table.use master @a ~ ~ ~ 1 0.8", "function solstice:r4/solved"])

    # ------------------------------------------------------------ clics (réservés au Guérisseur)
    keys = [f"g{k}" for k in range(5)] + [f"st{k}" for k in range(4)] + [f"b{k}" for k in range(6)] + ["reg", "lever", "altar"]
    clk = []
    for k in keys:
        clk.append(f"execute if entity @s[tag=sol.k4_{k}] if data entity @s interaction on target run function solstice:r4/cc/{k}")
        clk.append(f"execute if entity @s[tag=sol.k4_{k}] if data entity @s attack on attacker run function solstice:r4/cc/{k}")
        dp.fn(f"r4/cc/{k}", ["execute if score @s sol.cool matches 1.. run return 0", "scoreboard players set @s sol.cool 6",
                             f"execute if score #s4brk {V} matches 1.. run return 0",
                             "execute unless entity @s[tag=sol.ro1] run return run " +
                             actionbar("@s", "Seul le Guérisseur sait manier les sceaux. Protégez-le !", "red"),
                             f"function solstice:r4/c/{k}"])
    clk += ["data remove entity @s interaction", "data remove entity @s attack"]
    dp.fn("r4/clicked", clk)

    # ------------------------------------------------------------ capacités : soin, provocation
    dp.fn("r4/heal", [
        "execute if score @s sol.t matches 1.. run return run " + actionbar("@s", ["", T("Bâton de soin : recharge… ", "green"), SC("@s", "sol.t")]),
        "scoreboard players set @s sol.t 200",
        "effect give @a[distance=..8,tag=!sol.dn] instant_health 1 0 true",
        "effect give @a[distance=..8,tag=!sol.dn] regeneration 4 1 true",
        "particle minecraft:heart ~ ~1.5 ~ 3 0.8 3 0 25", "playsound minecraft:block.amethyst_block.resonate master @a ~ ~ ~ 1 1.6",
    ])
    dp.fn("r4/taunt", [
        "tag @s add sol.me",
        "execute as @e[tag=sol.r4mob,distance=..18] run damage @s 0.01 minecraft:player_attack by @a[tag=sol.me,limit=1]",
        "tag @s remove sol.me", "effect give @s glowing 5 0 true",
        actionbar("@s", "Les gardiens n’ont plus d’yeux que pour vous !", "blue"),
    ])
    dp.fn("r4/aura", [
        "tag @s add sol.me",
        "execute as @e[tag=sol.r4mob,distance=..5] run damage @s 0.01 minecraft:player_attack by @a[tag=sol.me,limit=1]",
        "tag @s remove sol.me",
    ])
    dp.fn("r4/ptick", [
        "execute if score @s sol.t matches 1.. run scoreboard players remove @s sol.t 1",
        f"execute if score @s sol.use matches 1.. if entity @s[tag=sol.ro1] if items entity @s weapon.mainhand {STAFF.id}[custom_data~{{sol:{{staff:1b}}}}] at @s run function solstice:r4/heal",
        "execute if score @s sol.horn matches 1.. if entity @s[tag=sol.ro3] at @s run function solstice:r4/taunt",
        f"execute if score #m20 {V} matches 10 if score #m60r4 {V} matches 0 if entity @s[tag=sol.ro3,tag=!sol.dn] at @s run function solstice:r4/aura",
        f"execute if score #step {V} matches 5 if entity @s[gamemode=!spectator] run function solstice:r4/s5_ptick",
        f"execute if items entity @s container.* {GANT[0]}[custom_data~{{sol:{{gant:1b}}}}] run function solstice:r4/gant",
        f"execute if score @s sol.y matches ..94 run function solstice:r4/cp",
    ])
    dp.fn("r4/gant", [f"clear @s {GANT[0]}[custom_data~{{sol:{{gant:1b}}}}]",
                      narr("Le Gardien des Jardins a lâché un gant de jardinage brodé d’un « L »…", "@a"),
                      "function solstice:story/found_gant"])
    dp.fn("r4/tick", [
        "execute as @e[type=interaction,tag=sol.r4i] at @s if data entity @s interaction run function solstice:r4/clicked",
        "execute as @e[type=interaction,tag=sol.r4i] at @s if data entity @s attack run function solstice:r4/clicked",
        f"scoreboard players operation #m60r4 {V} = #rt {V}", f"scoreboard players operation #m60r4 {V} %= #c60 {V}",
        f"execute if score #r4done {V} matches 1 run return 0",
        f"execute if score #s4brk {V} matches 1.. run scoreboard players remove #s4brk {V} 1",
        f"execute if score #s4brk {V} matches 1 run function solstice:r4/begin",
        f"execute if score #s4brk {V} matches 1.. run return 0",
        "function solstice:r4/wave_tick",
        f"execute if score #step {V} matches 2 if score #m20 {V} matches 0 run function solstice:r4/s2_check",
        f"execute if score #step {V} matches 5 if score #m4 {V} matches 0 run function solstice:r4/s5_show",
        # les gardiens restent dans l’arène
        f"execute as @e[tag=sol.r4mob] at @s unless entity @s[x={OX - 20},y={Y - 5},z=-20,dx=40,dy=30,dz=40] run tp @s {OX} {Y + 1} 0",
    ])
    # ------------------------------------------------------------ joueur, morts, anéantissement
    dp.fn("r4/cp", [f"tp @s {CP[0]} {CP[1]} {CP[2]} {CP[3]} 0", f"spawnpoint @s {int(CP[0])} {CP[1]} {int(CP[2])}"])
    dp.fn("r4/enter", ["function solstice:r4/cp", "function solstice:r4/gear"])
    dp.fn("r4/respawn", ["function solstice:r4/cp", "function solstice:r4/gear"])
    dp.fn("r4/wipe", [
        "kill @e[type=!player,tag=sol.r4mob]", "kill @e[type=item]",
        tellraw("@a", T("Le sceau ", "gray"), SC("#step", color="gold"), T(" reprend depuis le début (les sceaux déjà brisés le restent).", "gray")),
        f"execute if score #step {V} matches 1.. run scoreboard players remove #step {V} 1",
        f"scoreboard players set #s4brk {V} 60",
    ])
    hint_fn(dp, 4, {
        1: ("Guérisseur : lisez l’ordre des signes à voix haute. Les autres : collez-vous à lui.",
            "Touchez les piliers dans l’ordre exact donné par l’inscription (un seul Guérisseur peut les toucher)."),
        2: ("Le Guérisseur sait où chacun doit se tenir : écoutez-le.", "Chevalier et Tank sur les deux dalles de couleur annoncées, en même temps, 3 secondes."),
        3: ("La réponse à l’énigme est tenue par une statue.", "Cloche, lanterne, horloge, boussole : laquelle répond à l’énigme ? Le Guérisseur la touche."),
        4: ("Le Registre, au nord, décrit deux braseros.", "Bannière, bassin, piliers fendus, crâne, pot de fleurs : allumez les deux braseros décrits."),
        5: ("Seul le Guérisseur voit les dalles sûres.", "Il traverse le plancher piégé à l’ouest en suivant les étincelles vertes, puis actionne le levier."),
        6: ("Les gardiens portent l’offrande sur eux.", "Squelettes → os, araignées → fil, zombies → cendre. Rapportez-les au Guérisseur, qui touche l’autel."),
    })
    for key, typ, desc in (("s1", "glyph-order", "Toucher des piliers-glyphes dans l’ordre lu par le Guérisseur."),
                           ("s2", "plate-positions", "Le Guérisseur place ses coéquipiers sur des dalles de couleur."),
                           ("s3", "riddle-statue", "Répondre à une devinette en désignant la bonne statue."),
                           ("s4", "braziers-by-description", "Allumer les deux braseros décrits dans le registre."),
                           ("s5", "safe-path-callout", "Traverser un plancher piégé dont seul le Guérisseur voit les dalles sûres."),
                           ("s6", "offering-from-drops", "Réunir une offrande sur le butin des gardiens et la déposer.")):
        dp.puzzle(4, key, typ, desc)
    dp.test("siège : 6 sceaux affichés", "entity @e[type=text_display,tag=sol.seal6]")
    dp.test("siège : 4 statues", "entity @e[type=interaction,tag=sol.k4_st3]")
    dp.test("siège : levier du plancher piégé", "entity @e[type=interaction,tag=sol.k4_lever]")
    dp.meta.setdefault("rooms", {})["4"] = {
        "cp": CP, "pillars": PILLARS, "plates": [p[2] for p in PLATES], "statues": [s[1] for s in STATUES], "braz": BRAZ,
        "pairs": PAIRS, "lectern": LECTERN, "trap_cells": {f"{c},{r}": trap_cell(c, r) for c in range(5) for r in range(5)},
        "trap_start": TRAP_START, "trap_paths": TRAP_PATHS, "lever": TRAP_LEVER,
        "offers": OFFERS, "seqs": SEQS, "gates": GATES}
