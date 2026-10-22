#!/usr/bin/env python3
"""Write per-class roster JSON. Places are Census gazetteer names unless lon/lat is set."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "classes"


def place(gazetteer: str, display: str | None = None, lon: float | None = None, lat: float | None = None):
    item = {"gazetteer": gazetteer, "display": display or gazetteer}
    if lon is not None and lat is not None:
        item["lon"] = lon
        item["lat"] = lat
    return item


def team(district: int, school: str, *places, label="__school__"):
    record = {
        "district": district,
        "school": school,
        "places": list(places),
        "map_label": school if label == "__school__" else label,
    }
    return record


# Campus points so multiple high schools in one city do not stack on the Census centroid.
DM_EAST = place("Des Moines", lon=-93.6075, lat=41.5958)
DM_LINCOLN = place("Des Moines", lon=-93.6288, lat=41.5638)
DM_ROOSEVELT = place("Des Moines", lon=-93.6782, lat=41.5895)
DM_NORTH = place("Des Moines", lon=-93.6205, lat=41.6300)
IC_CITY = place("Iowa City", "Iowa City", lon=-91.5112, lat=41.6680)
IC_WEST = place("Iowa City", "Iowa City", lon=-91.5640, lat=41.6565)
IC_LIBERTY = place("North Liberty", lon=-91.6085, lat=41.7328)
CR_KENNEDY = place("Cedar Rapids", lon=-91.6665, lat=42.0339)
CR_JEFFERSON = place("Cedar Rapids", lon=-91.6990, lat=41.9595)
CR_PRAIRIE = place("Cedar Rapids", lon=-91.7235, lat=41.9315)
CR_WASHINGTON = place("Cedar Rapids", lon=-91.6395, lat=41.9678)
CR_XAVIER = place("Cedar Rapids", lon=-91.6678, lat=42.0455)
WAUKEE = place("Waukee", lon=-93.8660, lat=41.5985)
WAUKEE_NW = place("Waukee", lon=-93.8895, lat=41.6668)
SC_EAST = place("Sioux City", lon=-96.3548, lat=42.5048)
SC_NORTH = place("Sioux City", lon=-96.3705, lat=42.5235)
SC_WEST = place("Sioux City", lon=-96.3980, lat=42.4895)
SC_HEELAN = place("Sioux City", lon=-96.4005, lat=42.4965)
DBQ_SENIOR = place("Dubuque", lon=-90.6905, lat=42.5105)
DBQ_HEMPSTEAD = place("Dubuque", lon=-90.7235, lat=42.4920)
DBQ_WAHLERT = place("Dubuque", lon=-90.6890, lat=42.5155)
ANK_HS = place("Ankeny", lon=-93.6155, lat=41.7185)
ANK_CENT = place("Ankeny", lon=-93.5720, lat=41.7320)
DAV_CENTRAL = place("Davenport", lon=-90.5755, lat=41.5300)
DAV_NORTH = place("Davenport", lon=-90.5850, lat=41.5575)
DAV_WEST = place("Davenport", lon=-90.6185, lat=41.5380)
DAV_ASSUMPTION = place("Davenport", lon=-90.5920, lat=41.5385)
WLOO_WEST = place("Waterloo", lon=-92.3460, lat=42.5110)
WLOO_EAST = place("Waterloo", lon=-92.3320, lat=42.4985)
WLOO_COLUMBUS = place("Waterloo", lon=-92.3570, lat=42.4920)
CB_LINCOLN = place("Council Bluffs", lon=-95.8600, lat=41.2615)
CB_JEFFERSON = place("Council Bluffs", lon=-95.8815, lat=41.2618)
CB_STALBERT = place("Council Bluffs", lon=-95.8350, lat=41.2610)
CB_LEWIS = place("Council Bluffs", lon=-95.8370, lat=41.2295)
VALLEY = place("West Des Moines", lon=-93.7505, lat=41.5850)
DOWLING = place("West Des Moines", lon=-93.7755, lat=41.5955)
LINN_MAR = place("Marion", lon=-91.5965, lat=42.0485)
DMC = place("Urbandale", lon=-93.7360, lat=41.6385)
GVCS = place("Des Moines", lon=-93.5980, lat=41.6205)
SAYDEL = place("Saylorville", lon=-93.6160, lat=41.6505)
PELLA = place("Pella", lon=-92.9160, lat=41.4080)
PELLA_CHR = place("Pella", lon=-92.9050, lat=41.4000)
NEWMAN = place("Mason City", lon=-93.1850, lat=43.1480)
WESTERN_CHR = place("Hull", lon=-96.1341, lat=43.1895)
NORTH_LINN = place("Coggon", "Troy Mills", lon=-91.6828, lat=42.2894)


CLASSES = [
    {
        "id": "5A",
        "label": "Class 5A",
        "unit": "Group",
        "teams": [
            team(1, "Des Moines East", DM_EAST, label="East"),
            team(1, "Iowa City City High", IC_CITY, label="City High"),
            team(1, "Norwalk", place("Norwalk")),
            team(1, "Ottumwa", place("Ottumwa")),
            team(1, "Southeast Polk", place("Pleasant Hill"), label="SE Polk\nPleasant Hill"),
            team(1, "Waukee Northwest", WAUKEE_NW, label="Waukee NW"),
            team(2, "Cedar Rapids Kennedy", CR_KENNEDY, label="Kennedy"),
            team(2, "Dallas Center-Grimes", place("Grimes"), label="DC-G\nGrimes"),
            team(2, "Dowling Catholic", DOWLING, label="Dowling"),
            team(2, "Marshalltown", place("Marshalltown")),
            team(2, "Waterloo West", WLOO_WEST, label="West\nWaterloo"),
            team(2, "Waukee", WAUKEE),
            team(3, "Ames", place("Ames")),
            team(3, "Ankeny", ANK_HS),
            team(3, "Council Bluffs Abraham Lincoln", CB_LINCOLN, label="Abraham Lincoln"),
            team(3, "Des Moines Roosevelt", DM_ROOSEVELT, label="Roosevelt"),
            team(3, "Johnston", place("Johnston")),
            team(3, "Sioux City East", SC_EAST, label="East\nSioux City"),
            team(4, "Ankeny Centennial", ANK_CENT, label="Centennial"),
            team(4, "Des Moines Lincoln", DM_LINCOLN, label="Lincoln"),
            team(4, "Indianola", place("Indianola")),
            team(4, "Sioux City North", SC_NORTH, label="North\nSioux City"),
            team(4, "Urbandale", place("Urbandale")),
            team(4, "Valley", VALLEY, label="Valley"),
            team(5, "Bettendorf", place("Bettendorf")),
            team(5, "Cedar Falls", place("Cedar Falls")),
            team(5, "Cedar Rapids Jefferson", CR_JEFFERSON, label="Jefferson"),
            team(5, "Dubuque Hempstead", DBQ_HEMPSTEAD, label="Hempstead"),
            team(5, "Dubuque Senior", DBQ_SENIOR, label="Senior"),
            team(5, "Prairie", CR_PRAIRIE, label="Prairie"),
            team(6, "Davenport Central", DAV_CENTRAL, label="Central"),
            team(6, "Iowa City Liberty", IC_LIBERTY, label="Liberty"),
            team(6, "Iowa City West", IC_WEST, label="West"),
            team(6, "Linn-Mar", LINN_MAR, label="Linn-Mar"),
            team(6, "Muscatine", place("Muscatine")),
            team(6, "Pleasant Valley", place("Riverdale"), label="Pleasant Valley\nRiverdale"),
        ],
    },
    {
        "id": "4A",
        "label": "Class 4A",
        "unit": "District",
        "teams": [
            team(1, "Fort Dodge", place("Fort Dodge")),
            team(1, "LeMars", place("Le Mars"), label="LeMars"),
            team(1, "Sergeant Bluff-Luton", place("Sergeant Bluff"), label="Sergeant Bluff-\nLuton"),
            team(1, "Sioux City West", SC_WEST, label="West\nSioux City"),
            team(1, "Spencer", place("Spencer")),
            team(1, "Storm Lake", place("Storm Lake")),
            team(2, "Cedar Rapids Washington", CR_WASHINGTON, label="Washington"),
            team(2, "Decorah", place("Decorah")),
            team(2, "Mason City", place("Mason City")),
            team(2, "Waterloo East", WLOO_EAST, label="East\nWaterloo"),
            team(2, "Waverly-Shell Rock", place("Waverly"), label="Waverly-\nShell Rock"),
            team(2, "Xavier", CR_XAVIER, label="Xavier"),
            team(3, "Burlington", place("Burlington")),
            team(3, "Clinton", place("Clinton")),
            team(3, "Davenport North", DAV_NORTH, label="North"),
            team(3, "Davenport West", DAV_WEST, label="West"),
            team(3, "North Scott", place("Eldridge"), label="North Scott\nEldridge"),
            team(3, "Western Dubuque", place("Epworth"), label="Western Dubuque\nEpworth"),
            team(4, "Clear Creek-Amana", place("Tiffin"), label="Clear Creek-\nAmana"),
            team(4, "Grinnell", place("Grinnell")),
            team(4, "Marion", place("Marion")),
            team(4, "Newton", place("Newton")),
            team(4, "Oskaloosa", place("Oskaloosa")),
            team(4, "Pella", PELLA),
            team(5, "Ballard", place("Huxley"), label="Ballard\nHuxley"),
            team(5, "Bondurant-Farrar", place("Bondurant"), label="Bondurant-\nFarrar"),
            team(5, "Carlisle", place("Carlisle")),
            team(5, "Des Moines North", DM_NORTH, label="North\nDes Moines"),
            team(5, "Gilbert", place("Gilbert")),
            team(5, "North Polk", place("Alleman"), label="North Polk\nAlleman"),
            team(6, "ADM", place("Adel"), label="ADM\nAdel"),
            team(6, "Boone", place("Boone")),
            team(6, "Council Bluffs Thomas Jefferson", CB_JEFFERSON, label="Thomas Jefferson"),
            team(6, "Denison-Schleswig", place("Denison"), label="Denison-\nSchleswig"),
            team(6, "Glenwood", place("Glenwood")),
            team(6, "Lewis Central", CB_LEWIS, label="Lewis Central"),
        ],
    },
    {
        "id": "3A",
        "label": "Class 3A",
        "unit": "District",
        "teams": [
            team(1, "Algona", place("Algona")),
            team(1, "Bishop Heelan Catholic", SC_HEELAN, label="Heelan\nSioux City"),
            team(1, "Humboldt", place("Humboldt")),
            team(1, "MOC-Floyd Valley", place("Orange City"), label="MOC-FV\nOrange City"),
            team(1, "Sioux Center", place("Sioux Center")),
            team(1, "Webster City", place("Webster City")),
            team(2, "Benton Community", place("Van Horne"), label="Benton\nVan Horne"),
            team(2, "Charles City", place("Charles City")),
            team(2, "Clear Lake", place("Clear Lake")),
            team(2, "Independence", place("Independence")),
            team(2, "Iowa Falls-Alden", place("Iowa Falls"), label="Iowa Falls-\nAlden"),
            team(2, "West Delaware", place("Manchester"), label="West Delaware\nManchester"),
            team(3, "Assumption", DAV_ASSUMPTION, label="Assumption"),
            team(3, "Center Point-Urbana", place("Center Point"), label="Center Point-\nUrbana"),
            team(3, "Central DeWitt", place("DeWitt"), label="Central DeWitt"),
            team(3, "Maquoketa", place("Maquoketa")),
            team(3, "Mount Vernon", place("Mount Vernon")),
            team(3, "Wahlert Catholic", DBQ_WAHLERT, label="Wahlert"),
            team(4, "Fairfield", place("Fairfield")),
            team(4, "Fort Madison", place("Fort Madison")),
            team(4, "Keokuk", place("Keokuk")),
            team(4, "Mount Pleasant", place("Mount Pleasant")),
            team(4, "Solon", place("Solon")),
            team(4, "Washington", place("Washington")),
            team(5, "Des Moines Christian", DMC, label="DM Christian"),
            team(5, "Knoxville", place("Knoxville")),
            team(5, "Nevada", place("Nevada")),
            team(5, "Saydel", SAYDEL, label="Saydel"),
            team(5, "Williamsburg", place("Williamsburg")),
            team(5, "Winterset", place("Winterset")),
            team(6, "Atlantic", place("Atlantic")),
            team(6, "Carroll", place("Carroll")),
            team(6, "Creston", place("Creston")),
            team(6, "Greene County", place("Jefferson"), label="Greene County\nJefferson"),
            team(6, "Harlan", place("Harlan")),
            team(6, "Perry", place("Perry")),
        ],
    },
    {
        "id": "2A",
        "label": "Class 2A",
        "unit": "District",
        "teams": [
            team(1, "Boyden-Hull/Rock Valley", place("Boyden"), place("Rock Valley"), label=None),
            team(1, "Central Lyon/George-Little Rock", place("Rock Rapids"), place("George"), label=None),
            team(1, "Cherokee", place("Cherokee")),
            team(1, "Sheldon", place("Sheldon")),
            team(1, "Unity Christian", place("Orange City"), label="Unity Christian\nOrange City"),
            team(1, "Western Christian", WESTERN_CHR, label="Western Christian\nHull"),
            team(2, "Estherville Lincoln Central", place("Estherville"), label="Estherville"),
            team(2, "Kuemper Catholic", place("Carroll"), label="Kuemper\nCarroll"),
            team(2, "OABCIG", place("Ida Grove"), label="OABCIG\nIda Grove"),
            team(2, "Okoboji", place("Milford"), label="Okoboji\nMilford"),
            team(2, "Southeast Valley", place("Gowrie"), label="SE Valley\nGowrie"),
            team(2, "Spirit Lake", place("Spirit Lake")),
            team(3, "Crestwood", place("Cresco"), label="Crestwood\nCresco"),
            team(3, "Forest City", place("Forest City")),
            team(3, "New Hampton", place("New Hampton")),
            team(3, "North Fayette Valley", place("West Union"), label="North Fayette\nWest Union"),
            team(3, "Osage", place("Osage")),
            team(3, "Waukon", place("Waukon")),
            team(4, "Denver", place("Denver")),
            team(4, "Dike-New Hartford", place("Dike"), label="Dike-NH"),
            team(4, "Hampton-Dumont-CAL", place("Hampton"), label="Hampton-Dumont"),
            team(4, "Oelwein", place("Oelwein")),
            team(4, "Roland-Story", place("Story City"), label="Roland-Story\nStory City"),
            team(4, "Vinton-Shellsburg", place("Vinton"), label="Vinton-\nShellsburg"),
            team(5, "Alburnett", place("Alburnett")),
            team(5, "Anamosa", place("Anamosa")),
            team(5, "Bellevue", place("Bellevue")),
            team(5, "Monticello", place("Monticello")),
            team(5, "Tipton", place("Tipton")),
            team(5, "West Branch", place("West Branch")),
            team(6, "Central Lee", place("Donnellson"), label="Central Lee\nDonnellson"),
            team(6, "Mediapolis", place("Mediapolis")),
            team(6, "Mid-Prairie", place("Wellman"), label="Mid-Prairie\nWellman"),
            team(6, "West Burlington/Notre Dame", place("West Burlington"), place("Burlington"), label=None),
            team(6, "West Liberty", place("West Liberty")),
            team(6, "Wilton", place("Wilton")),
            team(7, "Albia", place("Albia")),
            team(7, "Centerville", place("Centerville")),
            team(7, "Davis County", place("Bloomfield"), label="Davis County\nBloomfield"),
            team(7, "PCM", place("Monroe"), label="PCM\nMonroe"),
            team(7, "Pella Christian", PELLA_CHR, label="Pella Christian"),
            team(7, "South Tama County", place("Tama"), label="South Tama\nTama"),
            team(8, "Chariton", place("Chariton")),
            team(8, "Clarinda", place("Clarinda")),
            team(8, "Clarke", place("Osceola"), label="Clarke\nOsceola"),
            team(8, "Grand View Christian", GVCS, label="Grand View\nChristian"),
            team(8, "Van Meter", place("Van Meter")),
            team(8, "Woodward-Granger", place("Woodward"), label="Woodward-\nGranger"),
        ],
    },
    {
        "id": "1A",
        "label": "Class 1A",
        "unit": "District",
        "teams": [
            team(1, "Alta-Aurelia", place("Alta")),
            team(1, "Hinton", place("Hinton")),
            team(1, "Lawton-Bronson", place("Lawton")),
            team(1, "MVAOCOU", place("Mapleton"), label="MVAOCOU\nMapleton"),
            team(1, "Ridge View", place("Holstein"), label="Ridge View\nHolstein"),
            team(1, "West Lyon", place("Inwood"), label="West Lyon\nInwood"),
            team(2, "East Sac County", place("Lake View"), label="East Sac\nLake View"),
            team(2, "Emmetsburg", place("Emmetsburg")),
            team(2, "Manson Northwest Webster", place("Manson"), label="Manson NW"),
            team(2, "Pocahontas Area", place("Pocahontas"), label="Pocahontas"),
            team(2, "South Central Calhoun", place("Lake City"), label="S. Central Calhoun\nLake City"),
            team(2, "South Hamilton", place("Jewell Junction", "Jewell"), label="South Hamilton\nJewell"),
            team(3, "Central Springs", place("Manly"), label="Central Springs\nManly"),
            team(3, "Clarion-Goldfield-Dows", place("Clarion"), label="Clarion"),
            team(3, "Eagle Grove", place("Eagle Grove")),
            team(3, "Garner-Hayfield-Ventura", place("Garner"), label="Garner-Hayfield"),
            team(3, "Grundy Center", place("Grundy Center")),
            team(3, "South Hardin", place("Eldora"), label="South Hardin\nEldora"),
            team(4, "Aplington-Parkersburg", place("Parkersburg"), label="Aplington-\nParkersburg"),
            team(4, "Columbus Catholic", WLOO_COLUMBUS, label="Columbus Catholic\nWaterloo"),
            team(4, "Hudson", place("Hudson")),
            team(4, "Jesup", place("Jesup")),
            team(4, "Sumner-Fredericksburg", place("Sumner"), label="Sumner-\nFredericksburg"),
            team(4, "Union", place("La Porte City"), label="Union\nLa Porte City"),
            team(5, "Beckman Catholic", place("Dyersville"), label="Beckman\nDyersville"),
            team(5, "Camanche", place("Camanche")),
            team(5, "Cascade", place("Cascade")),
            team(5, "Lisbon", place("Lisbon")),
            team(5, "MFL MarMac", place("Monona"), label="MFL MarMac\nMonona"),
            team(5, "Northeast", place("Goose Lake"), label="Northeast\nGoose Lake"),
            team(6, "Cardinal", place("Eldon"), label="Cardinal\nEldon"),
            team(6, "Durant", place("Durant")),
            team(6, "Eddyville-Blakesburg-Fremont", place("Eddyville"), label="Eddyville"),
            team(6, "Louisa-Muscatine", place("Letts"), label="Louisa-Muscatine\nLetts"),
            team(6, "Regina", place("Iowa City", lon=-91.5030, lat=41.6610), label="Regina\nIowa City"),
            team(6, "Sigourney/Keota", place("Sigourney"), place("Keota"), label=None),
            team(7, "Interstate 35", place("Truro"), label="Interstate 35\nTruro"),
            team(7, "Ogden", place("Ogden")),
            team(7, "Panorama", place("Panora"), label="Panorama\nPanora"),
            team(7, "Pleasantville", place("Pleasantville")),
            team(7, "West Central Valley", place("Stuart"), label="West Central Valley\nStuart"),
            team(7, "West Marshall", place("State Center"), label="West Marshall\nState Center"),
            team(8, "Missouri Valley", place("Missouri Valley")),
            team(8, "Red Oak", place("Red Oak")),
            team(8, "Shenandoah", place("Shenandoah")),
            team(8, "Treynor", place("Treynor")),
            team(8, "Tri-Center", place("Neola"), label="Tri-Center\nNeola"),
            team(8, "Underwood", place("Underwood")),
        ],
    },
    {
        "id": "A",
        "label": "Class A",
        "unit": "District",
        "teams": [
            team(1, "Gehlen Catholic", place("Le Mars"), label="Gehlen\nLe Mars"),
            team(1, "Hartley-Melvin-Sanborn", place("Hartley"), label="HMS\nHartley"),
            team(1, "MMCRU", place("Marcus"), label="MMCRU\nMarcus"),
            team(1, "Sibley-Ocheyedan", place("Sibley")),
            team(1, "Sioux Central", place("Sioux Rapids"), label="Sioux Central\nSioux Rapids"),
            team(1, "South O'Brien", place("Paullina"), label="South O'Brien\nPaullina"),
            team(1, "West Sioux", place("Hawarden"), label="West Sioux\nHawarden"),
            team(2, "AGWSR", place("Ackley"), label="AGWSR\nAckley"),
            team(2, "BCLUW", place("Conrad"), label="BCLUW\nConrad"),
            team(2, "Belmond-Klemme", place("Belmond")),
            team(2, "Lake Mills", place("Lake Mills")),
            team(2, "Newman Catholic", NEWMAN, label="Newman\nMason City"),
            team(2, "West Fork", place("Sheffield"), label="West Fork\nSheffield"),
            team(2, "West Hancock", place("Britt"), label="West Hancock\nBritt"),
            team(3, "Clayton Ridge", place("Guttenberg"), label="Clayton Ridge\nGuttenberg"),
            team(3, "Nashua-Plainfield", place("Nashua")),
            team(3, "North Butler", place("Greene"), label="North Butler\nGreene"),
            team(3, "Postville", place("Postville")),
            team(3, "Saint Ansgar", place("St. Ansgar"), label="St. Ansgar"),
            team(3, "South Winneshiek", place("Calmar"), label="S. Winneshiek\nCalmar"),
            team(3, "Starmont", place("Arlington"), label="Starmont\nArlington"),
            team(4, "East Marshall", place("Le Grand"), label="East Marshall\nLe Grand"),
            team(4, "East Buchanan", place("Winthrop"), label="East Buchanan\nWinthrop"),
            team(4, "Maquoketa Valley", place("Delhi"), label="Maquoketa Valley\nDelhi"),
            team(4, "Midland", place("Wyoming"), label="Midland\nWyoming"),
            team(4, "North Cedar", place("Stanwood"), label="North Cedar\nStanwood"),
            team(4, "North Linn", NORTH_LINN, label="North Linn\nTroy Mills"),
            team(4, "Wapsie Valley", place("Fairbank"), label="Wapsie Valley\nFairbank"),
            team(5, "Columbus Community", place("Columbus Junction"), label="Columbus\nJunction"),
            team(5, "Danville", place("Danville")),
            team(5, "Highland", place("Riverside"), label="Highland\nRiverside"),
            team(5, "New London", place("New London")),
            team(5, "Pekin", place("Packwood"), label="Pekin\nPackwood"),
            team(5, "Van Buren County", place("Keosauqua"), label="Van Buren\nKeosauqua"),
            team(5, "Wapello", place("Wapello")),
            team(6, "BGM", place("Brooklyn"), label="BGM\nBrooklyn"),
            team(6, "Colfax-Mingo", place("Colfax")),
            team(6, "Earlham", place("Earlham")),
            team(6, "Lynnville-Sully", place("Sully")),
            team(6, "Madrid", place("Madrid")),
            team(6, "Martensdale-St. Marys", place("Martensdale"), label="Martensdale-\nSt. Marys"),
            team(6, "North Mahaska", place("New Sharon"), label="North Mahaska\nNew Sharon"),
            team(7, "ACGC", place("Guthrie Center"), label="ACGC\nGuthrie Center"),
            team(7, "AHSTW", place("Avoca"), label="AHSTW\nAvoca"),
            team(7, "Central Decatur", place("Leon"), label="Central Decatur\nLeon"),
            team(7, "Mount Ayr", place("Mount Ayr")),
            team(7, "Nodaway Valley", place("Greenfield"), label="Nodaway Valley\nGreenfield"),
            team(7, "Riverside", place("Oakland"), label="Riverside\nOakland"),
            team(7, "Southwest Valley", place("Corning"), label="SW Valley\nCorning"),
            team(8, "Akron-Westfield", place("Akron")),
            team(8, "IKM-Manning", place("Manning"), label="IKM-Manning"),
            team(8, "Logan-Magnolia", place("Logan")),
            team(8, "St. Albert", CB_STALBERT, label="St. Albert"),
            team(8, "West Monona", place("Onawa"), label="West Monona\nOnawa"),
            team(8, "Westwood", place("Sloan"), label="Westwood\nSloan"),
            team(8, "Woodbury Central", place("Moville"), label="Woodbury Central\nMoville"),
        ],
    },
]


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    for spec in CLASSES:
        path = ROOT / f"{spec['id']}.json"
        path.write_text(json.dumps(spec, indent=2) + "\n")
        print(path, "teams", len(spec["teams"]))


if __name__ == "__main__":
    main()
