from re import compile as regex

foi = {
    "*": [".*escription$", "^(.+/)?[Tt]ext$", "^(.+/)?[Dd]ialog/[^/]+/[^/]+/.*[0-9]+$",
          "^(.+/)?(sub)?[tT]itle(/value)?$", "^(.+/)+caption$", "^(.+/)?label$", "^(.+/)?message$", "^.+Name/value$",
          "^.*friendlyName$", ".*senderName$", ".*destinations/.+[Nn]ame$", ".+[lL]abel[a-zA-Z]*/value$",
          "bookmarkName"],
    ".object": ["^chatOptions/.+$", ],
    ".codex": ["contentPages/[0-9]+$"],
    ".matherial": [],
    ".config": ["shipStatus", "^(.+/)?lbl[a-zA-Z]+/value$", "^labels/.+$", "^otherDeed/.+$", "^.*Format$",
                "^enclosedArea/.+$", "^tagCriteria/.+$", "^hail/.+$", "^converse/.+$", "^follow/.+$", "^flee/.+$",
                "^encorage/.+$", "^severe/.+$", "^accuse/.+$", "^tout/.+$", "^rent/.+$", "^alert/.+$", "^welcome/.+$",
                "^beacon/.+$", "^safe/.+$", "^helpme/.+$", "^final/.+$", "^.+Text(/value)?$", "^gui.+/value$",
                ".+Title$", "^paneLayout/.+/value$", "areYouSure/value$", "^blueprintUnlock$",
                "^blueprintAlreadyKnown$", "^rotTimeDescriptions/.+/1$", "^[a-zA-Z]*[mM]essages/[a-zA-Z]+$",
                ".+[mM]essage$", "^.*(hint|regex|([a-zA-Z]*(Caption|[Tt]itle)))$", "^defaultPetNameLabel$",
                ".*descriptions/[0-9]+$", "^(un)?trackLabel$", "^modeTypeTextAndColor/[0-9]+/[0-9]+$"],
    "themes.config": ["^[0-9]+/1/[0-9]+/(0|(1/)?name)$"],
    "dungeonitems.config": ["^[0-9]+/1/[0-9]+/(0|(1/)?name)$"],
    "threats.config": ["^[0-9]+/1/[0-9]+/(0|(1/)?name)$"],
    "weapon.config": ["^[0-9]+/1/[0-9]+/(0|(1/)?name)$"],
    "monsters.config": ["^[0-9]+/1/[0-9]+/(0|(1/)?name)$"],
    "hatadjectives.config": ["^[0-9]+/1/[0-9]+/(0|(1/)?name)$"],
    "cockpit.config": [".*/displayName$", "^terraformedPlanetDescription/.+$", "^[a-zA-Z]Names/[^/]+$",
                       "worldTypeDescription/.+$", "^clusterMoons/[^/]+$", "^threatLevelText/[a-zA-Z]+/[0-9]+$",
                       "^visitableTypeDescription/.+$", "^objectThreatText/.+$", "^planetTypeNames/.+$",
                       "^starTypeNames/.+$", "^jumpDialog/[^/]+$", "^topLeftButtonTooltips/.*", ".+Caption/[^/]+",
                       "^systemTooltip/exploredLabel/.+$"],
    "statuses.config": ["^statuses/.+$"],
    "help.config": ["^[a-z]+Commands/.+$"],
    "hunger.config": ["^.*$"],
    "locations.config": [".*/name$"],
    "namegen.config": ["^names/1/[0-9]+/[0-9]+$"],
    "quests.config": ["^pronouns/.+$", "^objectiveDescriptions/.+"],
    ".species": ["^charGenTextLabels/[0-9]+$"],
    ".sbvn": ["^.+/options/[0-9]+/0$"],
    ".tech": [],
    ".cinematic": [],
    ".currency": [],
    ".liquid": [],
    ".biome": [],
    ".item": [],
    ".instrument": [],
    ".legs": [],
    ".chest": [],
    ".back": [],
    ".head": [],
    ".harvestingtool": [],
    ".flashlight": [],
    ".painttool": [],
    ".wiretool": [],
    ".tillingtool": [],
    ".miningtool": [],
    ".beamaxe": [],
    ".inspectiontool": ["^outOfRangeText/.+$", "^nothingThereText/.+$"],
    ".thrownitem": [],
    ".unlock": ["^unlockMessage$"],
    ".matitem": [],
    ".liqitem": [],
    ".augment": [".*/displayName$"],
    ".consumable": [],
    ".coinitem": [],
    ".activeitem": ["^altAbility/name$"],
    ".namesource": ["^sourceNames/[0-9]+$"],
    ".particle": [],
    ".damage": [],
    ".statuseffect": [],
    ".stagehand": ["^radioMessages/[^/]+/(0|2)$"],
    ".material": [],
    ".matmod": [],
    ".npctype": ["^scriptConfig/crew/role/(name|field)$", "^scriptConfig/crew/ranks/[0-9]+$", "^npcname$"],
    ".mat": [],
    ".radiomessages": [],
    ".bush": [],
    ".grass": [],
    ".monstertype": ["^(.+/)?dialog/.+$"],
    ".monsterskill": ["^label$"],
    ".aimission": [".*Text$"],
    ".questtemplate": ["^.+Text(/[^0-9]+([0-9]+/1)?/[0-9]+)?$",
                       "^scriptConfig/(descriptions|.+Note|parcel(Name|Description))/.+$", "^.+/example/name$"],
    ".tooltip": [],
    ".itemdescription": [],
    ".collection": [],
    ".animation": [],
    ".aicommand":['.+/buttonText$'],
    "madness.config":[".+research/.+$"],
    "system_objects.config":[".*/displayName$"],
    "parts.config":[".*/displayName$"]
}

files_of_interest = dict()
for ext, poi in foi.items():
    files_of_interest[ext] = list()
    for p in poi:
        # print(p)
        files_of_interest[ext].append(regex(p))
